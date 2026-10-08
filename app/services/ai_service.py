"""
OpenAI Integration Service.
Handles client configuration, secure authentication, API connectivity,
structured LLM response validation, and resilient fallback execution.
"""
import logging
from typing import Optional
from openai import (
    OpenAI,
    OpenAIError,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APITimeoutError
)
from app.config import settings
from app.schemas import (
    AIAnalysisResult,
    TicketCategory,
    TicketPriority,
    SupportTeam
)
from app.utils.prompts import (
    TICKET_ANALYSIS_SYSTEM_PROMPT,
    build_ticket_analysis_user_prompt
)

logger = logging.getLogger("it-support-ticket-assistant")


class AIServiceError(Exception):
    """Base exception for all AI service operations."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AIAuthenticationError(AIServiceError):
    """Raised when the OpenAI API key is missing, invalid, or unauthorized."""
    def __init__(self, message: str = "OpenAI API key is missing or invalid."):
        super().__init__(message, status_code=401)


class AIRateLimitError(AIServiceError):
    """Raised when OpenAI API rate limits or quotas are exceeded."""
    def __init__(self, message: str = "OpenAI rate limit or quota exceeded."):
        super().__init__(message, status_code=429)


class AIConnectionError(AIServiceError):
    """Raised when network, connection, or timeout issues occur."""
    def __init__(self, message: str = "Unable to connect to OpenAI service."):
        super().__init__(message, status_code=504)


class AIInvalidResponseError(AIServiceError):
    """Raised when the AI model returns invalid or unparseable output."""
    def __init__(self, message: str = "AI service returned an invalid or malformed response."):
        super().__init__(message, status_code=502)


class AIService:
    """
    Service class managing OpenAI client lifecycle, authentication,
    structured classification, and NLP fallback mechanisms.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self._client: Optional[OpenAI] = None

    def is_configured(self) -> bool:
        """
        Check whether an OpenAI API key is provided and not a placeholder.
        """
        if not self._api_key:
            return False
        if self._api_key.strip() in ("", "your_api_key_here", "your_openai_api_key_here"):
            return False
        return True

    def get_client(self) -> OpenAI:
        """
        Lazily initialize and return the authenticated OpenAI client.
        Raises AIAuthenticationError if API key is not configured.
        """
        if not self.is_configured():
            logger.error("AI client initialization failed: OpenAI API key is not configured.")
            raise AIAuthenticationError(
                "OpenAI API key is not configured. Please set a valid OPENAI_API_KEY in your .env file."
            )

        if self._client is None:
            masked_key = f"{self._api_key[:7]}...{self._api_key[-4:]}" if len(self._api_key) > 12 else "***"
            logger.info(f"Initializing OpenAI client with model '{self.model}' (Key: {masked_key})")
            self._client = OpenAI(
                api_key=self._api_key,
                timeout=30.0,
                max_retries=2
            )
        return self._client

    def verify_connection(self) -> dict:
        """
        Verify API connectivity and key validity against OpenAI.
        Useful for startup checks or system diagnostics.
        """
        logger.info("Verifying OpenAI connectivity...")
        try:
            client = self.get_client()
            models = client.models.list()
            logger.info("OpenAI connection successfully verified.")
            return {
                "status": "connected",
                "model": self.model,
                "available_models_count": len(models.data)
            }
        except AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {e}")
            raise AIAuthenticationError(f"Authentication failed with OpenAI: {str(e)}")
        except (APIConnectionError, APITimeoutError) as e:
            logger.error(f"OpenAI connection timeout/failure: {e}")
            raise AIConnectionError(f"Connection failure contacting OpenAI: {str(e)}")
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit hit: {e}")
            raise AIRateLimitError(f"Rate limit exceeded on OpenAI account: {str(e)}")
        except OpenAIError as e:
            logger.error(f"OpenAI general error: {e}")
            raise AIServiceError(f"OpenAI API error: {str(e)}")

    def rule_based_fallback_analysis(
        self,
        employee_name: str,
        employee_email: str,
        issue_description: str
    ) -> AIAnalysisResult:
        """
        Deterministic NLP rule-based triage fallback.
        Ensures 100% system availability when offline or before API key setup.
        """
        text = issue_description.lower()

        # Defaults
        category = TicketCategory.OTHER
        priority = TicketPriority.MEDIUM
        assigned_team = SupportTeam.GENERAL_IT_SUPPORT
        issue_type = "General Technical Support"

        if any(k in text for k in ["security", "phish", "malware", "virus", "breach", "hack", "ransomware", "unauthorized"]):
            category = TicketCategory.SECURITY
            assigned_team = SupportTeam.SECURITY_TEAM
            issue_type = "Security Incident"
            priority = TicketPriority.CRITICAL if any(k in text for k in ["breach", "hack", "ransomware", "urgent"]) else TicketPriority.HIGH

        elif any(k in text for k in ["vpn", "tunnel", "anyconnect"]):
            category = TicketCategory.VPN
            assigned_team = SupportTeam.NETWORK_SUPPORT
            issue_type = "Connectivity"
            priority = TicketPriority.HIGH if any(k in text for k in ["cannot", "not connecting", "fails", "blocked"]) else TicketPriority.MEDIUM

        elif any(k in text for k in ["wifi", "wi-fi", "internet", "network", "ethernet", "lan", "dns"]):
            category = TicketCategory.NETWORK
            assigned_team = SupportTeam.NETWORK_SUPPORT
            issue_type = "Connectivity"
            priority = TicketPriority.HIGH if any(k in text for k in ["outage", "entire", "down"]) else TicketPriority.MEDIUM

        elif any(k in text for k in ["password", "reset", "lock", "locked", "mfa", "2fa", "login"]):
            category = TicketCategory.PASSWORD
            assigned_team = SupportTeam.ACCESS_MANAGEMENT
            issue_type = "Authentication"
            priority = TicketPriority.MEDIUM

        elif any(k in text for k in ["email", "outlook", "mailbox", "exchange", "inbox"]):
            category = TicketCategory.EMAIL
            assigned_team = SupportTeam.EMAIL_SUPPORT
            issue_type = "Messaging"
            priority = TicketPriority.MEDIUM

        elif any(k in text for k in ["printer", "print", "spooler", "paper", "scanner"]):
            category = TicketCategory.PRINTER
            assigned_team = SupportTeam.HARDWARE_SUPPORT
            issue_type = "Peripheral"
            priority = TicketPriority.LOW

        elif any(k in text for k in ["access", "permission", "jira", "github", "drive", "sharepoint"]):
            category = TicketCategory.ACCESS_REQUEST
            assigned_team = SupportTeam.ACCESS_MANAGEMENT
            issue_type = "Access Request"
            priority = TicketPriority.LOW

        elif any(k in text for k in ["laptop", "monitor", "screen", "keyboard", "mouse", "battery", "charger", "dock"]):
            category = TicketCategory.HARDWARE
            assigned_team = SupportTeam.HARDWARE_SUPPORT
            issue_type = "Hardware Fault"
            priority = TicketPriority.MEDIUM

        elif any(k in text for k in ["software", "crash", "bug", "install", "slack", "zoom", "teams", "excel"]):
            category = TicketCategory.SOFTWARE
            assigned_team = SupportTeam.SOFTWARE_SUPPORT
            issue_type = "Application Issue"
            priority = TicketPriority.LOW

        clean_desc = issue_description.strip()
        summary = clean_desc if len(clean_desc) <= 120 else clean_desc[:117] + "..."

        return AIAnalysisResult(
            category=category,
            priority=priority,
            summary=summary,
            assigned_team=assigned_team,
            issue_type=issue_type,
            confidence=0.90
        )

    def analyze_ticket(
        self,
        employee_name: str,
        employee_email: str,
        issue_description: str,
        allow_fallback: bool = True
    ) -> AIAnalysisResult:
        """
        Analyze and classify an employee support ticket.
        Sends prompt to OpenAI with JSON enforcement, validates response with Pydantic,
        and provides resilient fallback handling.
        """
        logger.info(f"AI analysis started for ticket submitted by: {employee_email}")

        if not self.is_configured():
            if allow_fallback:
                logger.info("OpenAI API key not configured; routing through intelligent fallback triage.")
                result = self.rule_based_fallback_analysis(employee_name, employee_email, issue_description)
                logger.info(
                    f"AI analysis completed via fallback. Category: {result.category.value}, "
                    f"Priority: {result.priority.value}, Team: {result.assigned_team.value}"
                )
                return result
            else:
                logger.error("AI analysis failed: OpenAI API key is missing.")
                raise AIAuthenticationError("OpenAI API key is missing or not configured in .env.")

        try:
            client = self.get_client()
            user_prompt = build_ticket_analysis_user_prompt(
                employee_name=employee_name,
                employee_email=employee_email,
                issue_description=issue_description
            )

            # Request structured JSON format from OpenAI
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": TICKET_ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                logger.error("AI analysis failed: Empty response content returned by model.")
                raise AIInvalidResponseError("OpenAI returned empty message content.")

            # Validate against strict Pydantic model
            result = AIAnalysisResult.model_validate_json(raw_content)
            logger.info(
                f"AI analysis completed successfully. Category: {result.category.value}, "
                f"Priority: {result.priority.value}, Team: {result.assigned_team.value}"
            )
            return result

        except AuthenticationError as e:
            logger.error(f"AI analysis failed - AuthenticationError: {e}")
            if allow_fallback:
                logger.warning("Falling back to rule-based triage due to authentication failure.")
                return self.rule_based_fallback_analysis(employee_name, employee_email, issue_description)
            raise AIAuthenticationError(str(e))
        except (APIConnectionError, APITimeoutError) as e:
            logger.error(f"AI analysis failed - Network/Timeout Error: {e}")
            if allow_fallback:
                logger.warning("Falling back to rule-based triage due to connection timeout.")
                return self.rule_based_fallback_analysis(employee_name, employee_email, issue_description)
            raise AIConnectionError(str(e))
        except RateLimitError as e:
            logger.error(f"AI analysis failed - RateLimitError: {e}")
            if allow_fallback:
                logger.warning("Falling back to rule-based triage due to rate limiting.")
                return self.rule_based_fallback_analysis(employee_name, employee_email, issue_description)
            raise AIRateLimitError(str(e))
        except Exception as e:
            logger.error(f"AI analysis failed - Parsing/Validation Error: {e}")
            if allow_fallback:
                logger.warning("Falling back to rule-based triage due to invalid LLM output.")
                return self.rule_based_fallback_analysis(employee_name, employee_email, issue_description)
            raise AIInvalidResponseError(f"Failed to validate AI response: {str(e)}")


# Singleton instance for dependency injection across the application
ai_service = AIService()
