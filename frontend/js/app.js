// Smart API Base URL: auto-detects if served directly by FastAPI or standalone server/file
const API_BASE = (window.location.protocol === 'file:' || !window.location.port || window.location.port === '5500' || window.location.port === '3000') 
  ? 'http://localhost:8000' 
  : '';

let allTickets = [];
let currentFilterStatus = '';
let searchQuery = '';

const templates = {
  vpn: {
    name: "Anjan Sai",
    email: "anjan@example.com",
    desc: "My laptop cannot connect to the company VPN. I have tried restarting several times, but the VPN tunnel is still failing and I need urgent access to the internal database."
  },
  password: {
    name: "Sarah Miller",
    email: "sarah.m@company.com",
    desc: "I forgot my Active Directory password after vacation and entered it wrong 3 times. My work account is now completely locked out."
  },
  phishing: {
    name: "David Kim",
    email: "david.k@company.com",
    desc: "URGENT SECURITY: I received a suspicious email claiming to be from the CEO asking for wire transfer credentials. Possible phishing malware attempt."
  },
  hardware: {
    name: "Elena Rostova",
    email: "elena.r@company.com",
    desc: "My MacBook display is violently flickering with horizontal green lines and turning pitch black whenever I open Zoom meetings."
  }
};

function fillTemplate(key) {
  const item = templates[key];
  if (!item) return;
  document.getElementById('employeeName').value = item.name;
  document.getElementById('employeeEmail').value = item.email;
  document.getElementById('issueDescription').value = item.desc;
}

function showToast(message, isError = false) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${isError ? 'error' : ''}`;
  toast.innerHTML = `<span>${isError ? '⚠️' : '✅'}</span> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

async function fetchData() {
  try {
    // Fetch stats
    const statsRes = await fetch(`${API_BASE}/tickets/stats/summary`);
    if (statsRes.ok) {
      const stats = await statsRes.json();
      document.getElementById('statTotal').innerText = stats.total_tickets || 0;
      document.getElementById('statOpen').innerText = stats.open_tickets || 0;
      document.getElementById('statInProgress').innerText = stats.in_progress_tickets || 0;
      document.getElementById('statResolved').innerText = stats.resolved_tickets || 0;
      const criticalCount = stats.tickets_by_priority ? (stats.tickets_by_priority['Critical'] || 0) : 0;
      document.getElementById('statCritical').innerText = criticalCount;
    }

    // Fetch tickets list
    const ticketsRes = await fetch(`${API_BASE}/tickets`);
    if (ticketsRes.ok) {
      allTickets = await ticketsRes.json();
      renderTickets();
    }
  } catch (err) {
    console.error('Error fetching data:', err);
    showToast('Failed to connect to backend server at ' + (API_BASE || window.location.origin), true);
  }
}

function setFilter(type, value, btn) {
  currentFilterStatus = value;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderTickets();
}

function handleSearch(val) {
  searchQuery = val.toLowerCase().trim();
  renderTickets();
}

function renderTickets() {
  const listEl = document.getElementById('ticketsList');
  if (!listEl) return;

  const filtered = allTickets.filter(t => {
    const matchesStatus = !currentFilterStatus || t.status === currentFilterStatus;
    const matchesSearch = !searchQuery || 
      (t.employee_name && t.employee_name.toLowerCase().includes(searchQuery)) ||
      (t.employee_email && t.employee_email.toLowerCase().includes(searchQuery)) ||
      (t.issue_description && t.issue_description.toLowerCase().includes(searchQuery)) ||
      (t.category && t.category.toLowerCase().includes(searchQuery)) ||
      (t.assigned_team && t.assigned_team.toLowerCase().includes(searchQuery));
    return matchesStatus && matchesSearch;
  });

  document.getElementById('queueCount').innerText = `${filtered.length} of ${allTickets.length} Tickets`;

  if (filtered.length === 0) {
    listEl.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <p>No tickets found matching your filter.</p>
      </div>
    `;
    return;
  }

  listEl.innerHTML = filtered.map(t => {
    const priorityClass = `badge-priority-${(t.priority || 'medium').toLowerCase()}`;
    const statusSlug = (t.status || 'open').toLowerCase().replace(' ', '-');
    const statusClass = `badge-status-${statusSlug}`;
    const formattedDate = new Date(t.created_at).toLocaleString();

    return `
      <div class="ticket-card" id="ticket-${t.id}">
        <div class="ticket-header">
          <div>
            <div class="ticket-meta">
              <span class="ticket-id">#${t.id}</span>
              <span class="ticket-employee">${escapeHtml(t.employee_name)}</span>
              <span class="ticket-email">&lt;${escapeHtml(t.employee_email)}&gt;</span>
            </div>
          </div>
          <div class="ticket-badges">
            <span class="badge ${statusClass}">${t.status}</span>
            <span class="badge ${priorityClass}">${t.priority}</span>
            <span class="badge badge-category">${t.category}</span>
            <span class="badge badge-team">${t.assigned_team}</span>
          </div>
        </div>

        <div class="ticket-body">
          ${escapeHtml(t.issue_description)}
        </div>

        ${t.ai_summary ? `
          <div class="ticket-ai-summary">
            <strong>🤖 AI Summary:</strong> ${escapeHtml(t.ai_summary)}
            ${t.issue_type ? ` • <em>Type: ${escapeHtml(t.issue_type)}</em>` : ''}
          </div>
        ` : ''}

        <div class="ticket-footer">
          <span>Submitted: ${formattedDate}</span>
          <div class="ticket-actions">
            <select class="action-select" onchange="updateTicketStatus(${t.id}, this.value)">
              <option value="Open" ${t.status === 'Open' ? 'selected' : ''}>Open</option>
              <option value="In Progress" ${t.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
              <option value="Resolved" ${t.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
              <option value="Closed" ${t.status === 'Closed' ? 'selected' : ''}>Closed</option>
            </select>
            <button class="btn-action-icon btn-action-ai" title="Re-Analyze with AI" onclick="reanalyzeTicket(${t.id})">
              ⚡ Re-Analyze
            </button>
            <button class="btn-action-icon" title="Delete Ticket" onclick="deleteTicket(${t.id})">
              🗑️
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const submitBtn = document.getElementById('submitBtn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>⏳ Running AI Triage...</span>`;

  const payload = {
    employee_name: document.getElementById('employeeName').value.trim(),
    employee_email: document.getElementById('employeeEmail').value.trim(),
    issue_description: document.getElementById('issueDescription').value.trim()
  };

  try {
    const res = await fetch(`${API_BASE}/tickets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Failed to submit ticket');
    }

    const data = await res.json();
    showToast(`Ticket #${data.id} created & triaged successfully!`);

    // Show AI classification box
    const aiBox = document.getElementById('aiResultBox');
    const aiDetails = document.getElementById('aiResultDetails');
    aiDetails.innerHTML = `
      <div><strong>Category:</strong> <span style="color: #38bdf8;">${data.category}</span></div>
      <div><strong>Priority:</strong> <span style="color: #fbbf24;">${data.priority}</span></div>
      <div><strong>Assigned Team:</strong> <span style="color: #c084fc;">${data.assigned_team}</span></div>
      <div><strong>Summary:</strong> ${escapeHtml(data.ai_summary || '')}</div>
    `;
    aiBox.style.display = 'block';

    // Clear input description
    document.getElementById('issueDescription').value = '';

    // Reload data
    await fetchData();

  } catch (err) {
    showToast(err.message, true);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<span>🚀 Run AI Triage & Submit Ticket</span>`;
  }
}

async function updateTicketStatus(id, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/tickets/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    if (!res.ok) throw new Error('Status update failed');
    showToast(`Ticket #${id} status updated to ${newStatus}`);
    await fetchData();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function reanalyzeTicket(id) {
  try {
    showToast(`Re-analyzing ticket #${id} via AI...`);
    const res = await fetch(`${API_BASE}/tickets/${id}/analyze`, { method: 'POST' });
    if (!res.ok) throw new Error('AI analysis failed');
    const updated = await res.json();
    showToast(`Ticket #${id} re-classified as [${updated.category} | ${updated.priority}]`);
    await fetchData();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function deleteTicket(id) {
  if (!confirm(`Are you sure you want to delete ticket #${id}?`)) return;
  try {
    const res = await fetch(`${API_BASE}/tickets/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete ticket');
    showToast(`Ticket #${id} deleted.`);
    await fetchData();
  } catch (err) {
    showToast(err.message, true);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
  // Update header links with API_BASE
  const docsLink = document.getElementById('docsLink');
  const healthLink = document.getElementById('healthLink');
  if (docsLink) docsLink.href = `${API_BASE}/docs`;
  if (healthLink) healthLink.href = `${API_BASE}/health`;

  fetchData();
});
