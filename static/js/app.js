
// Config
let API_BASE_URL = localStorage.getItem('apiBaseUrl') || 'http://localhost:5000';
let API_TOKEN = localStorage.getItem('apiToken') || '';

// DOM Elements
const baseUrlInput = document.getElementById('baseUrl');
const apiTokenInput = document.getElementById('apiToken');
const saveConfigBtn = document.getElementById('saveConfig');
const navLinks = document.querySelectorAll('.nav-link');
const dashboardSections = document.querySelectorAll('.dashboard-section');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  baseUrlInput.value = API_BASE_URL;
  apiTokenInput.value = API_TOKEN;

  // Load pending approvals by default
  loadPendingApprovals();
});

// Save API config
saveConfigBtn.addEventListener('click', () => {
  API_BASE_URL = baseUrlInput.value;
  API_TOKEN = apiTokenInput.value;

  localStorage.setItem('apiBaseUrl', API_BASE_URL);
  localStorage.setItem('apiToken', API_TOKEN);

  alert('Configuration saved!');
});

// Navigation switching
navLinks.forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const targetSection = link.getAttribute('data-section');

    // Update active nav link
    navLinks.forEach(nav => nav.classList.remove('active'));
    link.classList.add('active');

    // Show the selected section
    dashboardSections.forEach(section => {
      section.style.display = section.id === targetSection ? 'block' : 'none';
    });
  });
});

// ===== API FUNCTIONS ===== //

// Load pending approvals
async function loadPendingApprovals() {
  try {
    const response = await fetch(`${API_BASE_URL}/transfers/approvals-pending`, {
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Cache-Control': 'no-cache'
      }
    });

    if (!response.ok) throw new Error('Failed to fetch pending approvals');
    const data = await response.json();

    const tableBody = document.querySelector('#pendingTable tbody');
    tableBody.innerHTML = data.map(transfer => `
      <tr>
        <td>${transfer.status_code || 'N/A'}</td>
        <td>${transfer.transaction_count || 0}</td>
        <td>${transfer.total_amount || 0}</td>
        <td>
          <button class="btn btn-sm btn-success" onclick="approveBatch('${transfer.tracking_id}')">
            <i class="fas fa-check"></i> Approve
          </button>
          <button class="btn btn-sm btn-danger ms-2" onclick="rejectBatch('${transfer.tracking_id}')">
            <i class="fas fa-times"></i> Reject
          </button>
        </td>
      </tr>
    `).join('');
  } catch (error) {
    console.error('Error:', error);
    showAlert('Failed to load pending approvals. Check console for details.' , 3000);
  }
}

// Better confirmation dialog system
async function showConfirmation(options) {
  return new Promise((resolve) => {
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    const titleEl = document.getElementById('confirmationTitle');
    const messageEl = document.getElementById('confirmationMessage');
    const confirmBtn = document.getElementById('confirmActionBtn');
    
    // Set dialog content
    titleEl.textContent = options.title || 'Are you sure?';
    messageEl.textContent = options.message || '';
    
    if (options.icon) {
      messageEl.innerHTML = `<i class="${options.icon} me-2"></i>` + messageEl.innerHTML;
    }
    
    // Set button text
    confirmBtn.textContent = options.confirmText || 'Confirm';
    confirmBtn.className = `btn btn-${options.confirmType || 'primary'}`;
    
    // Clear previous handlers
    const confirmClone = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(confirmClone, confirmBtn);
    
    // Setup new handler
    confirmClone.addEventListener('click', () => {
      modal.hide();
      resolve(true);
    });
    
    // Show modal
    modal.show();
    
    // Handle dismissal
    document.getElementById('confirmationModal').addEventListener('hidden.bs.modal', () => {
      resolve(false);
    }, { once: true });
  });
}

// Updated approveBatch function
async function approveBatch(batchId) {
  const confirmed = await showConfirmation({
    title: 'Approve Batch',
    message: `Are you sure you want to approve batch ${batchId}?`,
    icon: 'fas fa-check-circle',
    confirmText: 'Approve',
    confirmType: 'success'
  });
  
  if (!confirmed) return;

  try {
    // Show loading state
    const approveBtn = document.querySelector(`button[onclick="approveBatch('${batchId}')"]`);
    const originalHtml = approveBtn.innerHTML;
    approveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Approving...';
    approveBtn.disabled = true;

    const response = await fetch(`${API_BASE_URL}/transfers/approve`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ batch_id: batchId })
    });

    if (!response.ok) throw new Error('Approval failed');
    
    showAlert('success', `Batch ${batchId} approved successfully!`);
    loadPendingApprovals(); // Refresh the list
    
  } catch (error) {
    console.error('Error:', error);
    showAlert('danger', `Failed to approve batch: ${error.message}`);
  } 
  finally {
  // Restore button state
  const approveBtn = document.querySelector(`button[onclick="approveBatch('${batchId}')"]`);
  if (approveBtn) {
    approveBtn.innerHTML = '<i class="fas fa-check"></i> Approve';
    approveBtn.disabled = false;
  }

}}

async function rejectBatch(batchId) {
  const confirmed = await showConfirmation({
    title: 'Reject Batch',
    message: `Are you sure you want to reject batch ${batchId}? This action cannot be undone.`,
    icon: 'fas fa-exclamation-triangle',
    confirmText: 'Reject',
    confirmType: 'danger'
  });

  if (!confirmed) return;

  try {
    // Show loading state
    const rejectBtn = document.querySelector(`button[onclick="rejectBatch('${batchId}')"]`);
    const originalHtml = rejectBtn.innerHTML;
    rejectBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Rejecting...';
    rejectBtn.disabled = true;

    const response = await fetch(`${API_BASE_URL}/transfers/deny`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tracking_id: batchId }) // Changed from batch_id to tracking_id
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Rejection failed');
    }

    showAlert('success', `Batch ${batchId} rejected successfully!`);
    loadPendingApprovals(); // Refresh the list

  } catch (error) {
    console.error('Rejection error:', error);
    showAlert('danger', `Failed to reject batch: ${error.message}`);
  } finally {
    // Restore button state
    const rejectBtn = document.querySelector(`button[onclick="rejectBatch('${batchId}')"]`);
    if (rejectBtn) {
      rejectBtn.innerHTML = '<i class="fas fa-times"></i> Reject';
      rejectBtn.disabled = false;
    }
  }
}



// Single transfer submission
document.getElementById('singleTransferForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  // Get form elements
  const form = e.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalBtnText = submitBtn.innerHTML;

  try {
    // Show loading state
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processing...';
    submitBtn.disabled = true;

    const payload = {
      records: {
        name: document.getElementById('singleName').value,
        phone: document.getElementById('singlePhone').value,
        amount: parseFloat(document.getElementById('singleAmount').value)
      },
      requires_approval: "YES"
    };

    const response = await fetch(`${API_BASE_URL}/transfers/initiate/single`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Transfer failed');
    }

    const result = await response.json();
    showAlert('success', `Transfer initiated! Tracking ID: ${result.tracking_id}`, 5000);
    form.reset();

  } catch (error) {
    console.error('Transfer error:', error);
    showAlert('danger', `Failed to initiate transfer: ${error.message}`, 5000);
  } finally {
    // Restore button state
    submitBtn.innerHTML = originalBtnText;
    submitBtn.disabled = false;
  }
});

// Bulk transfer logic (similar to single, but with array)
document.getElementById('bulkTransferForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  // Create loading overlay
  const overlay = document.createElement('div');
  overlay.className = 'loading-overlay';
  overlay.innerHTML = `
    <div class="loading-content">
      <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;"></div>
      <p class="mt-3">Processing bulk transfer...</p>
    </div>
  `;
  document.body.appendChild(overlay);
  
  // Disable form elements
  const form = e.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalBtnText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  form.querySelectorAll('input, button').forEach(el => el.disabled = true);

  try {
    // Validate entries first
    const entries = Array.from(document.querySelectorAll('.bulk-entry')).map(entry => {
      const inputs = entry.querySelectorAll('input');
      if (!inputs[0].value || !inputs[1].value || !inputs[2].value) {
        throw new Error('All fields are required for each recipient');
      }
      return {
        name: inputs[0].value,
        phone: inputs[1].value,
        amount: parseFloat(inputs[2].value)
      };
    });

    if (entries.length === 0) {
      throw new Error('Please add at least one recipient');
    }

    const payload = {
      records: entries,
      requires_approval: "YES"
    };

    const response = await fetch(`${API_BASE_URL}/transfers/initiate/bulk`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Bulk transfer failed');
    }

    const result = await response.json();
    showAlert('success', `
      <i class="fas fa-check-circle"></i> Bulk transfer initiated!<br>
      <small>Tracking ID: ${result.tracking_id}</small>
    `, 5000);
    
    // Reset form but keep one empty entry
    form.reset();
    document.getElementById('bulkEntries').innerHTML = `
      <div class="bulk-entry mb-3">
        <div class="row">
          <div class="col-md-4">
            <input type="text" class="form-control" placeholder="Name" required>
          </div>
          <div class="col-md-4">
            <input type="text" class="form-control" placeholder="Phone" required>
          </div>
          <div class="col-md-3">
            <input type="number" class="form-control" placeholder="Amount" required>
          </div>
          <div class="col-md-1">
            <button type="button" class="btn btn-danger remove-entry" disabled>
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>
    `;

  } catch (error) {
    console.error('Bulk transfer error:', error);
    showAlert('danger', `
      <i class="fas fa-exclamation-triangle"></i> ${error.message}
    `, 5000);
  } finally {
    // Remove overlay and restore form
    overlay.remove();
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnText;
    form.querySelectorAll('input, button').forEach(el => el.disabled = false);
    document.querySelectorAll('.remove-entry').forEach(btn => {
      btn.disabled = document.querySelectorAll('.bulk-entry').length <= 1;
    });
  }
});


// Add/remove bulk entries with improved UI feedback
document.getElementById('addBulkEntry').addEventListener('click', () => {
  const addBtn = document.getElementById('addBulkEntry');
  const originalBtnText = addBtn.innerHTML;
  try {

    
    // Show loading state briefly for visual feedback
    addBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Adding...';
    addBtn.disabled = true;

    const newEntry = document.createElement('div');
    newEntry.className = 'bulk-entry mb-3';
    newEntry.innerHTML = `
      <div class="row">
        <div class="col-md-4">
          <input type="text" class="form-control" placeholder="Name" required>
        </div>
        <div class="col-md-4">
          <input type="text" class="form-control" placeholder="Phone" required>
        </div>
        <div class="col-md-3">
          <input type="number" class="form-control" placeholder="Amount" required>
        </div>
        <div class="col-md-1">
          <button type="button" class="btn btn-danger remove-entry">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    `;

    document.getElementById('bulkEntries').appendChild(newEntry);
    
    // Scroll to the new entry
    newEntry.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Show visual highlight
    newEntry.style.transition = 'all 0.3s';
    newEntry.style.boxShadow = '0 0 0 2px rgba(13, 110, 253, 0.5)';
    setTimeout(() => {
      newEntry.style.boxShadow = 'none';
    }, 1000);

    // Show success feedback
    showAlert('success', 'New recipient added', 2000);

  } catch (error) {
    console.error('Error adding bulk entry:', error);
    showAlert('danger', 'Failed to add recipient', 3000);
  } finally {
    // Restore button state after a small delay for better UX
    setTimeout(() => {
      const addBtn = document.getElementById('addBulkEntry');
      if (addBtn) {
        addBtn.innerHTML = originalBtnText;
        addBtn.disabled = false;
      }
    }, 300);
  }
});

// Enhanced entry removal with confirmation
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('remove-entry')) {
    const entry = e.target.closest('.bulk-entry');
    const entryCount = document.querySelectorAll('.bulk-entry').length;
    
    // Don't allow removing the last entry
    if (entryCount <= 1) {
      showAlert('warning', 'You must keep at least one recipient', 3000);
      return;
    }

    // Visual feedback before removal
    entry.style.transition = 'all 0.3s';
    entry.style.opacity = '0.5';
    entry.style.transform = 'translateX(-10px)';
    
    setTimeout(() => {
      entry.remove();
      showAlert('info', 'Recipient removed', 2000);
    }, 300);
  }
});

// Dynamic removal of bulk entries
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('remove-entry')) {
    e.target.closest('.bulk-entry').remove();
  }
});


// Add these helper functions to your app.js
function getStatusBadgeClass(statusCode) {
  const statusMap = {
    'BP104': 'bg-primary',
    'COMPLETED': 'bg-success',
    'FAILED': 'bg-danger',
    'PENDING': 'bg-warning'
  };
  return statusMap[statusCode] || 'bg-secondary';
  }
  
  function formatDateTime(dateTimeString) {
  const date = new Date(dateTimeString);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  }
  
  function formatCurrency(amount) {
  const num = parseFloat(amount);
  return 'Ksh' + num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }


async function checkAndShowTransferStatus(trackingId) {
  try {
    // Switch to the status check section
    document.querySelector('.nav-link[data-section="check-status"]').click();
    
    // Fill the tracking ID field
    document.getElementById('trackingId').value = trackingId;
    
    // Trigger the status check
    const response = await fetch(`${API_BASE_URL}/transfers/check-status`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tracking_id: trackingId })
    });

    if (!response.ok) throw new Error('Status check failed');
    const result = await response.json();

      // Display the result
      document.getElementById('statusResult').innerHTML = `
      <div class="transfer-status-card">
        <h4 class="mb-4"><i class="fas fa-info-circle"></i> Transfer Status Details</h4>
        
        ${result.data.map(transfer => `
          <div class="transfer-details">
            <div class="row">
              <div class="col-md-6">
                <div class="detail-item">
                  <span class="detail-label">Tracking ID:</span>
                  <span class="detail-value">${transfer.tracking_id}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Status:</span>
                  <span class="detail-value badge ${getStatusBadgeClass(transfer.status_code)}">
                    ${transfer.status_code}
                  </span>
                </div>
              </div>
              <div class="col-md-6">
                <div class="detail-item">
                  <span class="detail-label">Date:</span>
                  <span class="detail-value">${formatDateTime(transfer.created_at)}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Transactions:</span>
                  <span class="detail-value">${transfer.number_transaction}</span>
                </div>
              </div>
            </div>
            <div class="detail-item amount-item">
              <span class="detail-label">Total Amount:</span>
              <span class="detail-value">${formatCurrency(transfer.total_amount)}</span>
            </div>
          </div>
        `).join('')}
        
      <div class="mt-3 text-muted">
        <small>Last updated: ${new Date().toLocaleString()}</small>
      </div>
    </div>
    `;


    
    return result;
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to check status: ' + error.message);
    throw error;
  }
}

// Update your existing form submit handler
document.getElementById('statusCheckForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const trackingId = document.getElementById('trackingId').value;
  await checkAndShowTransferStatus(trackingId);
});


async function checkAndUpdateStatus(batch_id) {

  const response = await fetch(`${API_BASE_URL}/transfers/update`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${API_TOKEN}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ tracking_id: batch_id })
      });

      if (!response.ok){
        const errorData = await response.json();
      showAlert('danger', `Failed to update status: ${errorData.message}`);
        return;
      }
      const result = await response.json();

      showAlert('success', `Status updated successfully!`);
  
}


document.getElementById('inspectForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const baseUrl = document.getElementById('baseUrl').value;
  const token = document.getElementById('apiToken').value;
  const date = document.getElementById('inspectDate').value;
  const logic = document.getElementById('inspectLogic').value;

  const submitBtn = e.target.querySelector('button[type="submit"]');
  const originalBtnText = submitBtn.innerHTML;


  try {
    // Show loading state

    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Loading...';
    submitBtn.disabled = true;

    const response = await fetch(`${baseUrl}/transfers/inspect`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ date, logic })
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Inspection failed');

    if (!(result.data && Array.isArray(result.data))) {
      document.getElementById('inspectResults').innerHTML = '<p class="text-muted">No data found.</p>';
      return;
    }

    renderInspectResults(result.data);
  
  } catch (error) {
    showAlert('danger', error.message);
    console.error('Inspection error:', error);
  } finally {
    // Restore button state
    const submitBtn = e.target.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.innerHTML = originalBtnText;
      submitBtn.disabled = false;
    }
  }
});

function renderInspectResults(data) {
  const display = data.map(item => {
    console.log("The status code is "+ item.status_code);
    const isPending = item.status_code === 'BP103';
    // const needsUpdate = item.status_code !== 'BP100' && item.status_code !== 'BP103';
    const needsUpdate = !['BC100', 'BP103'].includes(item.status_code);
    console.log(item.tracking_id, item.status_code,"Needs update: ", needsUpdate);
    return `
    <div class="card mb-3" id="batch-${item.tracking_id}">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <h5 class="card-title">${item.tracking_id}</h5>
            <p class="${isPending ? 'text-warning' : 'text-success'}">
              <strong>Status:</strong> ${item.status_code}
            </p>
            <p><strong>Amount:</strong> ${item.total_amount}</p>
            <p><strong>Transactions:</strong> ${item.number_transaction}</p>
            <p><strong>Created:</strong> ${item.created_at}</p>
          </div>
          <div class="btn-group-vertical">
            <button class="btn btn-sm btn-outline-primary mb-1" 
              onclick="inspectBatchransfers('${item.tracking_id}')">
              <i class="fas fa-eye"></i> Details
            </button>
            <button class="btn btn-sm btn-outline-info mb-1" 
              onclick="checkAndShowTransferStatus('${item.tracking_id}')">
              <i class="fas fa-search"></i> Status
            ${needsUpdate ? `
              <button class="btn btn-sm btn-warning" 
                      onclick="checkAndUpdateStatus('${item.tracking_id}')">
                <i class="fas fa-check"></i> Check and Update Status
              </button>` : ''}

            ${isPending ? `
            <div class="btn-group mt-1">
              <button class="btn btn-sm btn-success" 
                onclick="approveBatch('${item.tracking_id}')">
                <i class="fas fa-check"></i> Approve
              </button>
              <button class="btn btn-sm btn-danger" 
                onclick="rejectBatch('${item.tracking_id}')">
                <i class="fas fa-times"></i> Reject
              </button>
            </div>
            ` : ''}
          </div>
        </div>
      </div>
    </div>
    `;
  }).join('');

  document.getElementById('inspectResults').innerHTML = display || "<p>No data found.</p>";

  // Setup auto-refresh only for BP100 (pending) status

  const pendingBatches = data.filter(item => item.status_code === 'BP103');
  console.log("Pending batches: ", pendingBatches);
  console.log("Pending batches length: ", pendingBatches.length);

  if (pendingBatches && pendingBatches.length > 0) {
    console.log("setting up an auto refresh interval")
    setupAutoRefresh();
  }
  else {
    console.log("No pending batches, clearing auto refresh interval")
    if (window.autoRefreshInterval) {
      clearInterval(window.autoRefreshInterval);
      showAlert('success', 'No pending batches found.', 1000);
    }
  }
}

// Simplified auto-refresh focused only on BP100 status
function setupAutoRefresh() {
  // Clear previous interval if exists
  if (window.autoRefreshInterval) {
    clearInterval(window.autoRefreshInterval);
  }
  
  // Set new interval (every 15 seconds)
  window.autoRefreshInterval = setInterval(() => {
    const inspectForm = document.getElementById('inspectForm');
    if (inspectForm) {
      inspectForm.dispatchEvent(new Event('submit'));
    }
  }, 20000); //
  
  // Show refresh notification
  showAlert('info', 'Auto-refresh enabled for pending batches (BP103)', 2000);
}

// Clear refresh when leaving page
window.addEventListener('beforeunload', () => {
  if (window.autoRefreshInterval) {
    clearInterval(window.autoRefreshInterval);
  }
});



// New function to show update dialog
async function showUpdateStatusDialog(trackingId) {
  const confirmed = await showConfirmation({
    title: 'Update Status',
    message: `Manually check for updates on batch ${trackingId.substring(0, 8)}...?`,
    icon: 'fas fa-sync-alt',
    confirmText: 'Check Now',
    confirmType: 'primary'
  });
  
  if (confirmed) {
    try {
      const response = await fetch(`${API_BASE_URL}/transfers/check-status`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${API_TOKEN}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tracking_id: trackingId })
      });
      
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Update failed');
      
      showAlert('success', 'Status updated successfully!');
      document.getElementById('inspectForm').dispatchEvent(new Event('submit'));
    } catch (error) {
      showAlert('danger', 'Update failed: ' + error.message);
    }
  }
}


async function inspectBatchransfers (trackingId)  {
  const baseUrl = document.getElementById('baseUrl').value;
  const token = document.getElementById('apiToken').value;

  try {
    const response = await fetch(`${baseUrl}/transfers/transactions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tracking_id: trackingId })
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Failed to fetch transfer data.');

    const transfers = result.data;
    if (!transfers || transfers.length === 0) {
      document.getElementById('inspectModalBody').innerHTML = '<p class="text-muted">No transfers found for this batch.</p>';
    } else {
      let html = `
        <p><strong>Tracking ID:</strong> ${trackingId}</p>
        <div class="table-responsive">
          <table class="table table-striped table-bordered table-sm">
            <thead class="table-light">
              <tr>
                <th>Account</th>
                <th>Name</th>
                <th>Amount</th>
                <th>Charges</th>
                <th>Status</th>
                <th>Created At</th>
                <th>Reference ID</th>
              </tr>
            </thead>
            <tbody>`;

      for (const t of transfers) {
        html += `
          <tr>
            <td>${t.account}</td>
            <td>${t.name}</td>
            <td>${parseFloat(t.amount).toFixed(2)}</td>
            <td>${parseFloat(t.charges).toFixed(2)}</td>
            <td>${t.status_code}</td>
            <td>${t.created_at}</td>
            <td>${t.reference_id}</td>
          </tr>`;
      }

      html += `</tbody></table></div>`;
      document.getElementById('inspectModalBody').innerHTML = html;
    }

    const modal = new bootstrap.Modal(document.getElementById('inspectModal'));
    modal.show();

  } catch (error) {
    alert('Error: ' + error.message);
    console.error(error);
  }
};




// Add these variables with your other DOM elements
const loadOverviewBtn = document.getElementById('loadOverviewChart');
const loadBatchBtn = document.getElementById('loadBatchChart');
const chartGroupBy = document.getElementById('chartGroupBy');
const chartStatusFilter = document.getElementById('chartStatusFilter');
let overviewChart = null;
let batchChart = null;

// Add these event listeners
loadOverviewBtn.addEventListener('click', loadOverviewChartData);
loadBatchBtn.addEventListener('click', loadBatchChartData);

// New functions
async function loadOverviewChartData() {
  try {
    const groupBy = chartGroupBy.value;
    const response = await fetch(`${API_BASE_URL}/transfers/inspect`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        date: new Date().toISOString().split('T')[0],
        logic: 'le' 
      })
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Failed to fetch overview data');
    
    renderOverviewChart(result.data, groupBy);
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to load overview chart: ' + error.message);
  }
}

function renderOverviewChart(data, groupBy) {
  const ctx = document.getElementById('overviewChart').getContext('2d');
  
  // Group data
  const groupedData = {};
  data.forEach(item => {
    const key = groupBy === 'date' 
      ? item.created_at.split('T')[0] 
      : item.status_code;
    if (!groupedData[key]) {
      groupedData[key] = {
        count: 0,
        totalAmount: 0,
        batches: []
      };
    }
    groupedData[key].count++;
    groupedData[key].totalAmount += parseFloat(item.total_amount);
    groupedData[key].batches.push(item);
  });

  // Prepare chart data
  const labels = Object.keys(groupedData);
  const counts = labels.map(label => groupedData[label].count);
  const amounts = labels.map(label => groupedData[label].totalAmount);

  // Destroy previous chart
  if (overviewChart) overviewChart.destroy();

  overviewChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Number of Batches',
          data: counts,
          backgroundColor: 'rgba(54, 162, 235, 0.7)',
          yAxisID: 'y'
        },
        {
          label: 'Total Amount',
          data: amounts,
          backgroundColor: 'rgba(75, 192, 192, 0.7)',
          yAxisID: 'y1',
          type: 'line'
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `Batches Grouped by ${groupBy.toUpperCase()}`
        },
        tooltip: {
          callbacks: {
            afterBody: function(context) {
              const label = context[0].label;
              return [
                `Total Amount: ${groupedData[label].totalAmount.toFixed(2)}`,
                `Batches: ${groupedData[label].count}`
              ];
            }
          }
        }
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: { display: true, text: 'Number of Batches' }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: { display: true, text: 'Total Amount' },
          grid: { drawOnChartArea: false }
        }
      },
      onClick: (e, elements) => {
        if (elements.length > 0) {
          const index = elements[0].index;
          const label = labels[index];
          loadBatchDetails(groupedData[label].batches);
        }
      }
    }
  });
}

async function loadBatchChartData() {
  try {
    const statusFilter = chartStatusFilter.value;
    const response = await fetch(`${API_BASE_URL}/transfers/inspect`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        date: new Date().toISOString().split('T')[0],
        logic: 'le',
        ...(statusFilter && { status_code: statusFilter })
      })
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Failed to fetch batch data');
    
    renderBatchChart(result.data);
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to load batch chart: ' + error.message);
  }
}

function renderBatchChart(data) {
  const ctx = document.getElementById('batchChart').getContext('2d');
  
  // Prepare data - limit to 20 batches for better visibility
  const displayData = data.slice(0, 20);
  const labels = displayData.map(item => 
    `Batch ${item.tracking_id.substring(0, 6)}...`
  );
  const amounts = displayData.map(item => parseFloat(item.total_amount));
  const transactions = displayData.map(item => item.number_transaction);

  // Destroy previous chart
  if (batchChart) batchChart.destroy();

  batchChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Total Amount',
          data: amounts,
          backgroundColor: 'rgba(153, 102, 255, 0.7)',
          yAxisID: 'y'
        },
        {
          label: 'Number of Transactions',
          data: transactions,
          backgroundColor: 'rgba(255, 159, 64, 0.7)',
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Batch Details Analysis'
        },
        tooltip: {
          callbacks: {
            afterBody: function(context) {
              const index = context[0].dataIndex;
              return [
                `Status: ${displayData[index].status_code}`,
                `Created: ${displayData[index].created_at.split('T')[0]}`
              ];
            }
          }
        }
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: { display: true, text: 'Total Amount' }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: { display: true, text: 'Number of Transactions' },
          grid: { drawOnChartArea: false }
        }
      },
      onClick: (e, elements) => {
        if (elements.length > 0) {
          const index = elements[0].index;
          inspectBatchransfers(displayData[index].tracking_id);
        }
      }
    }
  });
}

function loadBatchDetails(batches) {
  // You can implement this to show details in a modal or table
  console.log('Selected batches:', batches);
  // For now, we'll just show the first batch
  if (batches.length > 0) {
    inspectBatchransfers(batches[0].tracking_id);
  }
}



async function generateStatusOptions() {
  const statusSelect = document.getElementById('chartStatusFilter');
  
  try {
    // Show loading state
    statusSelect.disabled = true;
    statusSelect.innerHTML = '<option value="">Loading statuses...</option>';

    const response = await fetch(`${API_BASE_URL}/transfers/fetch-statuses`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    
    if (!data?.data) {
      throw new Error('Invalid response format from server');
    }

    // Clear and add default option
    statusSelect.innerHTML = '<option value="">All Statuses</option>';
    
    // Add status options
    data.data.forEach(status => {
      const option = document.createElement('option');
      option.value = status.code;
      option.textContent = status.description || status.code; // Fallback to code if no description
      statusSelect.appendChild(option);
    });


  } catch (error) {
    console.error('Error fetching statuses:', error);
    statusSelect.innerHTML = `<option value="">Error loading statuses</option>`;
    showAlert('danger', 'Failed to load status filters', 5000);
  
  } finally {
    statusSelect.disabled = false;
  }
}

function showAlert(type, message, duration = 5000) {
  const container = document.getElementById('globalAlertContainer');
  const alertId = `alert-${Date.now()}`;
  
  const alertDiv = document.createElement('div');
  alertDiv.id = alertId;
  alertDiv.className = `global-alert global-alert-${type}`;
  alertDiv.innerHTML = `
    <span>${message}</span>
    <button class="global-alert-close" onclick="removeAlert('${alertId}')">&times;</button>
  `;
  
  container.appendChild(alertDiv);
  
  // Trigger animation
  setTimeout(() => {
    alertDiv.classList.add('show');
  }, 10);
  
  // Auto-remove if duration specified
  if (duration > 0) {
    setTimeout(() => {
      removeAlert(alertId);
    }, duration);
  }
  
  return alertId;
}

function removeAlert(alertId) {
  const alert = document.getElementById(alertId);
  if (alert) {
    alert.classList.remove('show');
    setTimeout(() => {
      alert.remove();
    }, 300); // Match this with CSS transition duration
  }
}

showAlert('welcome', 'Welcome to the dashboard!' , 1000); // Example alert on load
generateStatusOptions();