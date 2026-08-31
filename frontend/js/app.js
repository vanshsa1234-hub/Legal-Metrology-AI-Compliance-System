/**
 * Legal Lens - Core Application Frontend JavaScript
 * Smart India Hackathon Prototype
 */

// Global State
const state = {
  currentUser: null,
  activeView: 'login',
  activeInspection: null,
  activeRequest: null,
  scanStep: 1,
  uploadedImages: {
    front: null,
    back: null,
    left: null,
    right: null,
    top: null,
    bottom: null
  },
  barcodeData: '',
  cameraStream: null,
  charts: {}
};

// API Base
const API = {
  async get(endpoint) {
    try {
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error(await res.text());
      return await res.json();
    } catch (err) {
      console.error(`GET ${endpoint} failed:`, err);
      showToast(err.message || 'API request failed', 'danger');
      throw err;
    }
  },

  async post(endpoint, body, isFormData = false) {
    try {
      const options = {
        method: 'POST',
        body: isFormData ? body : JSON.stringify(body)
      };
      if (!isFormData) {
        options.headers = { 'Content-Type': 'application/json' };
      }
      const res = await fetch(endpoint, options);
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || 'API error');
      }
      return await res.json();
    } catch (err) {
      console.error(`POST ${endpoint} failed:`, err);
      showToast(err.message || 'Action failed', 'danger');
      throw err;
    }
  }
};

// Application Initialization
document.addEventListener('DOMContentLoaded', () => {
  // Check stored user session
  const storedUser = localStorage.getItem('legallens_user');
  if (storedUser) {
    try {
      state.currentUser = JSON.parse(storedUser);
      updateNavForUser();
      navigate(state.currentUser.role === 'officer' ? 'officer-dashboard' : 'user-dashboard');
    } catch (e) {
      localStorage.removeItem('legallens_user');
      navigate('login');
    }
  } else {
    navigate('login');
  }

  // Setup Global Event Listeners
  setupNavigationEvents();
  setupLoginForm();
  setupScanWorkflow();
  setupRequestForm();
});

// Toast notification helper
function showToast(message, type = 'primary') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toastEl = document.createElement('div');
  toastEl.className = `toast align-items-center text-white bg-${type === 'danger' ? 'danger' : type === 'warning' ? 'warning' : type === 'success' ? 'success' : 'dark'} border-0 show shadow-lg mb-2`;
  toastEl.setAttribute('role', 'alert');
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body d-flex align-items-center gap-2">
        <i class="bi ${type === 'danger' ? 'bi-exclamation-triangle-fill' : type === 'success' ? 'bi-check-circle-fill' : 'bi-info-circle-fill'}"></i>
        <span>${message}</span>
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
    </div>
  `;
  container.appendChild(toastEl);
  setTimeout(() => {
    toastEl.remove();
  }, 4500);
}

// Navigation & View Router
function navigate(viewName, params = {}) {
  // Authentication Guard
  if (viewName !== 'login' && !state.currentUser) {
    viewName = 'login';
  }

  // Role Protection
  if (state.currentUser && state.currentUser.role === 'user' && viewName.startsWith('officer-')) {
    showToast('Access restricted: Officer credentials required', 'warning');
    viewName = 'user-dashboard';
  }

  state.activeView = viewName;

  // Hide all views
  document.querySelectorAll('.view-section').forEach(el => el.classList.add('d-none'));

  // Update active nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.target === viewName);
  });

  // Show target view
  const targetEl = document.getElementById(`view-${viewName}`);
  if (targetEl) {
    targetEl.classList.remove('d-none');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Load view-specific data
  switch (viewName) {
    case 'login':
      resetLoginForm();
      break;
    case 'user-dashboard':
      loadUserDashboard();
      break;
    case 'scan-product':
      resetScanWorkflow();
      break;
    case 'user-reports':
      loadUserReports();
      break;
    case 'user-requests':
      loadUserRequests();
      break;
    case 'officer-dashboard':
      loadOfficerDashboard();
      break;
    case 'officer-requests':
      loadOfficerRequests();
      break;
    case 'officer-request-detail':
      loadOfficerRequestDetail(params.requestId);
      break;
    case 'officer-inspections':
      loadOfficerInspections();
      break;
    case 'officer-products':
      loadOfficerProducts();
      break;
    case 'officer-reports':
      loadOfficerReports();
      break;
    case 'officer-rules':
      loadRuleRepository();
      break;
    case 'officer-audit':
      loadAuditTrail();
      break;
  }
}

// Navigation Events
function setupNavigationEvents() {
  document.querySelectorAll('[data-navigate]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const target = el.dataset.navigate;
      navigate(target);
    });
  });

  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      state.currentUser = null;
      localStorage.removeItem('legallens_user');
      updateNavForUser();
      showToast('Logged out successfully', 'info');
      navigate('login');
    });
  }
}

function updateNavForUser() {
  const userNav = document.getElementById('nav-user-items');
  const officerNav = document.getElementById('nav-officer-items');
  const userChip = document.getElementById('user-profile-chip');
  const loginNavBtn = document.getElementById('nav-login-btn');

  if (state.currentUser) {
    if (loginNavBtn) loginNavBtn.classList.add('d-none');
    if (userChip) {
      userChip.classList.remove('d-none');
      document.getElementById('user-display-name').textContent = state.currentUser.full_name;
      document.getElementById('user-role-badge').textContent = state.currentUser.role === 'officer' ? 'Enforcement Officer' : 'Consumer';
    }

    if (state.currentUser.role === 'officer') {
      if (userNav) userNav.classList.add('d-none');
      if (officerNav) officerNav.classList.remove('d-none');
    } else {
      if (userNav) userNav.classList.remove('d-none');
      if (officerNav) officerNav.classList.add('d-none');
    }
  } else {
    if (userNav) userNav.classList.add('d-none');
    if (officerNav) officerNav.classList.add('d-none');
    if (userChip) userChip.classList.add('d-none');
    if (loginNavBtn) loginNavBtn.classList.remove('d-none');
  }
}

// -------------------------------------------------------------
// 1. Authentication
// -------------------------------------------------------------
function setupLoginForm() {
  const form = document.getElementById('form-login');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const role = document.getElementById('login-role').value;

    try {
      const res = await API.post('/api/auth/login', { email, password, role });
      state.currentUser = res.user;
      localStorage.setItem('legallens_user', JSON.stringify(res.user));
      updateNavForUser();
      showToast(`Welcome, ${res.user.full_name}!`, 'success');
      navigate(res.user.role === 'officer' ? 'officer-dashboard' : 'user-dashboard');
    } catch (err) {
      // Error handled by API.post
    }
  });

  // Demo Quick-Fill Buttons
  const fillCitizenBtn = document.getElementById('btn-quick-citizen');
  if (fillCitizenBtn) {
    fillCitizenBtn.addEventListener('click', () => {
      document.getElementById('login-email').value = 'user@legallens.demo';
      document.getElementById('login-password').value = 'user123';
      document.getElementById('login-role').value = 'user';
    });
  }

  const fillOfficerBtn = document.getElementById('btn-quick-officer');
  if (fillOfficerBtn) {
    fillOfficerBtn.addEventListener('click', () => {
      document.getElementById('login-email').value = 'admin@legallens.demo';
      document.getElementById('login-password').value = 'admin123';
      document.getElementById('login-role').value = 'officer';
    });
  }
}

function resetLoginForm() {
  const form = document.getElementById('form-login');
  if (form) form.reset();
}

// -------------------------------------------------------------
// 2. User Dashboard
// -------------------------------------------------------------
async function loadUserDashboard() {
  try {
    const data = await API.get(`/api/dashboard/user?user_id=${state.currentUser?.id || 1}`);
    
    document.getElementById('user-stat-scanned').textContent = data.stats.products_scanned;
    document.getElementById('user-stat-reports').textContent = data.stats.reports_generated;
    document.getElementById('user-stat-requests').textContent = data.stats.requests_raised;

    const tbody = document.getElementById('user-recent-inspections-tbody');
    tbody.innerHTML = '';

    if (!data.recent_inspections || data.recent_inspections.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted"><i class="bi bi-inbox fs-3 d-block mb-1"></i>No products scanned yet. Click 'Scan Product' to start.</td></tr>`;
      return;
    }

    data.recent_inspections.forEach(item => {
      const badgeClass = item.overall_result === 'No Issue Detected' ? 'badge-no-issue' : item.overall_result === 'Review Required' ? 'badge-review' : 'badge-non-compliance';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="fw-bold">${item.inspection_code}</td>
        <td>
          <div class="fw-semibold">${item.product_name}</div>
          <small class="text-muted">${item.brand} &bull; ${item.category}</small>
        </td>
        <td><span class="${badgeClass}">${item.overall_result}</span></td>
        <td>${item.date}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="viewInspectionReportDirect(${item.id})">
            <i class="bi bi-file-earmark-pdf me-1"></i>Report
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load user dashboard:', err);
  }
}

// -------------------------------------------------------------
// 3. Scan Product Multi-Step Workflow
// -------------------------------------------------------------
function setupScanWorkflow() {
  // Stepper Back/Next Controls
  document.getElementById('btn-step1-next')?.addEventListener('click', () => {
    if (!state.uploadedImages.front && !state.uploadedImages.back) {
      showToast('Please capture or upload at least the Front and Back packaging images', 'warning');
      return;
    }
    setScanStep(2);
  });

  document.getElementById('btn-step2-prev')?.addEventListener('click', () => setScanStep(1));
  
  document.getElementById('btn-step2-submit')?.addEventListener('click', () => {
    const manualBarcode = document.getElementById('input-barcode-manual')?.value.trim();
    if (manualBarcode) {
      state.barcodeData = manualBarcode;
    } else if (!state.barcodeData) {
      state.barcodeData = '8901234567890'; // Default demo barcode
    }
    startProcessingPipeline();
  });

  // Demo Samples Quick-Load (CrunchBite Chips)
  document.getElementById('btn-load-demo-images')?.addEventListener('click', () => {
    simulateDemoImages();
  });

  // Image Upload Inputs
  ['front', 'back', 'left', 'right', 'top', 'bottom'].forEach(side => {
    const input = document.getElementById(`upload-${side}`);
    if (input) {
      input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
          handleImageUpload(side, file);
        }
      });
    }
  });

  // Quick Demo Barcode Selectors
  document.querySelectorAll('.btn-demo-barcode').forEach(btn => {
    btn.addEventListener('click', () => {
      const code = btn.dataset.barcode;
      const input = document.getElementById('input-barcode-manual');
      if (input) input.value = code;
      state.barcodeData = code;
      document.getElementById('barcode-detected-alert')?.classList.remove('d-none');
      document.getElementById('detected-barcode-text').textContent = code;
    });
  });

  // Modal Evidence Links
  document.getElementById('btn-download-result-pdf')?.addEventListener('click', () => {
    if (state.activeInspection) {
      window.open(`/api/inspections/${state.activeInspection.id}/report`, '_blank');
    }
  });

  document.getElementById('btn-raise-request-from-result')?.addEventListener('click', () => {
    openRaiseRequestFormFromInspection(state.activeInspection);
  });
}

function resetScanWorkflow() {
  state.scanStep = 1;
  state.activeInspection = null;
  state.barcodeData = '';
  state.uploadedImages = { front: null, back: null, left: null, right: null, top: null, bottom: null };

  ['front', 'back', 'left', 'right', 'top', 'bottom'].forEach(side => {
    const box = document.getElementById(`dropzone-${side}`);
    if (box) {
      box.classList.remove('has-file');
      box.innerHTML = `
        <i class="bi bi-camera fs-2 text-muted mb-2 d-block"></i>
        <div class="fw-semibold small">Capture ${side.toUpperCase()}</div>
        <div class="text-muted extra-small">${side === 'front' || side === 'back' ? '(Required)' : '(Optional)'}</div>
      `;
    }
  });

  document.getElementById('barcode-detected-alert')?.classList.add('d-none');
  const barcodeInput = document.getElementById('input-barcode-manual');
  if (barcodeInput) barcodeInput.value = '';

  setScanStep(1);
}

function setScanStep(stepNumber) {
  state.scanStep = stepNumber;

  // Update Stepper UI
  for (let i = 1; i <= 5; i++) {
    const stepItem = document.getElementById(`stepper-node-${i}`);
    if (stepItem) {
      stepItem.classList.remove('active', 'completed');
      if (i < stepNumber) stepItem.classList.add('completed');
      if (i === stepNumber) stepItem.classList.add('active');
    }
    const pane = document.getElementById(`scan-step-${i}`);
    if (pane) {
      pane.classList.toggle('d-none', i !== stepNumber);
    }
  }
}

function handleImageUpload(side, file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    state.uploadedImages[side] = {
      file: file,
      dataUrl: e.target.result
    };
    renderImagePreview(side, e.target.result, file.name);
  };
  reader.readAsDataURL(file);
}

function renderImagePreview(side, dataUrl, filename) {
  const box = document.getElementById(`dropzone-${side}`);
  if (box) {
    box.classList.add('has-file');
    box.innerHTML = `
      <img src="${dataUrl}" class="preview-thumb mb-2" alt="${side} package" />
      <div class="fw-semibold small text-success"><i class="bi bi-check-circle me-1"></i>${side.toUpperCase()} Attached</div>
      <span class="badge bg-success mt-1">Quality: Good (High Res)</span>
      <div class="mt-2">
        <button type="button" class="btn btn-xs btn-outline-danger" onclick="removeImage('${side}', event)">Remove</button>
      </div>
    `;
  }
}

function removeImage(side, event) {
  if (event) event.stopPropagation();
  state.uploadedImages[side] = null;
  const box = document.getElementById(`dropzone-${side}`);
  if (box) {
    box.classList.remove('has-file');
    box.innerHTML = `
      <i class="bi bi-camera fs-2 text-muted mb-2 d-block"></i>
      <div class="fw-semibold small">Capture ${side.toUpperCase()}</div>
      <div class="text-muted extra-small">${side === 'front' || side === 'back' ? '(Required)' : '(Optional)'}</div>
    `;
  }
}

function simulateDemoImages() {
  // Realistic simulated package artwork for demo
  const frontCanvas = document.createElement('canvas');
  frontCanvas.width = 600; frontCanvas.height = 800;
  const fctx = frontCanvas.getContext('2d');
  fctx.fillStyle = '#0f172a'; fctx.fillRect(0,0,600,800);
  fctx.fillStyle = '#f59e0b'; fctx.fillRect(20,20,560,760);
  fctx.fillStyle = '#1e3a8a'; fctx.font = 'bold 36px sans-serif';
  fctx.fillText('CrunchBite', 180, 120);
  fctx.font = '24px sans-serif';
  fctx.fillText('Classic Potato Chips', 150, 180);
  fctx.fillStyle = '#15803d'; fctx.fillRect(50, 60, 40, 40); // Veg Logo
  fctx.fillStyle = '#ffffff'; fctx.beginPath(); fctx.arc(70, 80, 12, 0, 2*Math.PI); fctx.fill();
  fctx.fillStyle = '#1e293b'; fctx.font = 'bold 22px sans-serif';
  fctx.fillText('Net Qty: 100 g', 220, 650);

  const backCanvas = document.createElement('canvas');
  backCanvas.width = 600; backCanvas.height = 800;
  const bctx = backCanvas.getContext('2d');
  bctx.fillStyle = '#f8fafc'; bctx.fillRect(0,0,600,800);
  bctx.fillStyle = '#1e293b'; bctx.font = 'bold 20px sans-serif';
  bctx.fillText('NUTRITIONAL INFORMATION', 120, 80);
  bctx.font = '14px sans-serif';
  bctx.fillText('Energy: 530 kcal | Protein: 6.5 g | Carbs: 54 g', 60, 120);
  bctx.fillText('[Trans fat & Added sugar breakdown blurred/incomplete]', 60, 150);
  bctx.font = 'bold 18px sans-serif';
  bctx.fillText('MRP: Rs. 50.00 (Incl. of all taxes)', 60, 240);
  bctx.fillText('Batch: CB24082401  Mfg: 08/2026', 60, 280);
  bctx.fillText('FSSAI Lic. No: 10018012000456', 60, 320);

  const frontUrl = frontCanvas.toDataURL('image/jpeg');
  const backUrl = backCanvas.toDataURL('image/jpeg');

  state.uploadedImages.front = { dataUrl: frontUrl, file: new Blob() };
  state.uploadedImages.back = { dataUrl: backUrl, file: new Blob() };

  renderImagePreview('front', frontUrl, 'crunchbite_front.jpg');
  renderImagePreview('back', backUrl, 'crunchbite_back.jpg');

  showToast('Demo packaging images (CrunchBite Potato Chips) loaded!', 'success');
}

// -------------------------------------------------------------
// 4. Processing Pipeline & Deterministic Compliance Results
// -------------------------------------------------------------
async function startProcessingPipeline() {
  setScanStep(3);

  const stages = [
    { text: 'Image quality & lighting verification', delay: 400 },
    { text: 'Detecting declaration regions & bounding boxes', delay: 500 },
    { text: 'Extracting package text using OCR & NLP', delay: 600 },
    { text: 'Validating barcode against product master', delay: 400 },
    { text: 'Structuring product metadata & declarations', delay: 500 },
    { text: 'Matching applicable provisions from 26 master rules', delay: 600 },
    { text: 'Evaluating deterministic legal compliance criteria', delay: 600 },
    { text: 'Compiling evidence-first report & findings', delay: 400 }
  ];

  const listContainer = document.getElementById('processing-steps-list');
  const progressBar = document.getElementById('processing-progress-bar');
  if (listContainer) listContainer.innerHTML = '';

  for (let i = 0; i < stages.length; i++) {
    const s = stages[i];
    const row = document.createElement('div');
    row.className = 'processing-step-row in-progress';
    row.innerHTML = `<div class="spinner-border spinner-border-sm text-primary"></div><span>${s.text}...</span>`;
    listContainer.appendChild(row);

    const percent = Math.round(((i + 1) / stages.length) * 100);
    if (progressBar) {
      progressBar.style.width = `${percent}%`;
      progressBar.textContent = `${percent}%`;
    }

    await new Promise(r => setTimeout(r, s.delay));

    row.className = 'processing-step-row done';
    row.innerHTML = `<i class="bi bi-check-circle-fill text-success fs-5"></i><span>${s.text}</span>`;
  }

  // Submit to Backend API
  try {
    // 1. Create inspection session
    const ins = await API.post('/api/inspections', {
      barcode: state.barcodeData,
      category: 'Packaged Food'
    });

    // 2. Process inspection with rule engine
    const formData = new FormData();
    formData.append('barcode', state.barcodeData || '8901234567890');
    
    const processed = await API.post(`/api/inspections/${ins.id}/process`, formData, true);
    state.activeInspection = processed;

    // Render results
    renderStructuredRecord(processed);
    renderComplianceResults(processed);

    setScanStep(4); // Move to Structured Record
    showToast('Inspection analysis complete!', 'success');
  } catch (err) {
    showToast('Failed to complete inspection analysis: ' + err.message, 'danger');
    setScanStep(2);
  }
}

function renderStructuredRecord(inspection) {
  document.getElementById('struct-prod-name').textContent = inspection.product_name || 'Packaged Commodity';
  document.getElementById('struct-brand').textContent = inspection.brand || 'Brand';
  document.getElementById('struct-category').textContent = inspection.category || 'Packaged Food';
  document.getElementById('struct-barcode').textContent = inspection.barcode || 'N/A';
  document.getElementById('struct-inspection-code').textContent = inspection.inspection_code;

  const tbody = document.getElementById('structured-declarations-tbody');
  tbody.innerHTML = '';

  if (inspection.declarations) {
    inspection.declarations.forEach(d => {
      const confBadge = d.confidence_level === 'High' ? 'bg-success' : d.confidence_level === 'Medium' ? 'bg-warning text-dark' : 'bg-danger';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="fw-semibold">${d.field_name}</td>
        <td>${d.detected_value || '<span class="text-muted">Not detected</span>'}</td>
        <td><span class="badge ${confBadge}">${d.confidence.toFixed(1)}% (${d.confidence_level})</span></td>
        <td><span class="badge bg-light text-dark border">${d.evidence_image_type.toUpperCase()} Image</span></td>
        <td>
          <button class="btn btn-xs btn-outline-secondary" onclick="openEvidenceModal('${d.field_name}', '${d.detected_value}', '${d.evidence_image_type}', ${d.confidence})">
            <i class="bi bi-eye me-1"></i>View Evidence
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  document.getElementById('btn-continue-to-results')?.addEventListener('click', () => {
    setScanStep(5);
  });
}

function renderComplianceResults(inspection) {
  const overallCard = document.getElementById('results-overall-banner');
  const isNonComp = inspection.overall_result === 'Potential Non-Compliance';
  const isReview = inspection.overall_result === 'Review Required';

  overallCard.className = `card-custom p-4 mb-4 ${isNonComp ? 'border-danger bg-danger-subtle' : isReview ? 'border-warning bg-warning-subtle' : 'border-success bg-success-subtle'}`;
  
  document.getElementById('results-overall-status').textContent = inspection.overall_result.toUpperCase();
  document.getElementById('results-overall-status').className = `fs-4 fw-bold ${isNonComp ? 'text-danger' : isReview ? 'text-warning-emphasis' : 'text-success'}`;
  
  document.getElementById('stat-rules-checked').textContent = inspection.rules_checked_count;
  document.getElementById('stat-no-issue').textContent = inspection.no_issue_count;
  document.getElementById('stat-review-req').textContent = inspection.review_required_count;
  document.getElementById('stat-non-comp').textContent = inspection.non_compliance_count;

  // Show / Hide Raise Request CTA
  const requestCtaBanner = document.getElementById('results-request-cta-banner');
  if (requestCtaBanner) {
    requestCtaBanner.classList.toggle('d-none', !isNonComp && !isReview);
  }

  // Render Rule-by-Rule breakdown
  const tbody = document.getElementById('results-rules-tbody');
  tbody.innerHTML = '';

  if (inspection.compliance_results) {
    inspection.compliance_results.forEach(r => {
      const badgeClass = r.status === 'NO ISSUE DETECTED' ? 'badge-no-issue' : r.status === 'REVIEW REQUIRED' ? 'badge-review' : 'badge-non-compliance';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <div class="fw-bold">${r.rule_id}</div>
          <small class="text-muted">${r.clause || ''} &bull; ${r.version_amendment || ''}</small>
        </td>
        <td>
          <div class="fw-semibold">${r.rule_title}</div>
          <div class="extra-small text-muted mb-1">${r.applicable_regulation}</div>
          <div class="small text-secondary"><span class="fw-semibold">Finding:</span> ${r.reason}</div>
        </td>
        <td><span class="${badgeClass}">${r.status}</span></td>
        <td><span class="badge bg-secondary">${r.confidence.toFixed(0)}%</span></td>
        <td><span class="badge bg-light text-dark border">${r.evidence_type}</span></td>
        <td>
          <button class="btn btn-xs btn-outline-info" onclick="openRuleDetailModal('${r.rule_id}')">
            <i class="bi bi-journal-text me-1"></i>Rule Info
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }
}

// -------------------------------------------------------------
// 5. Citizen Request Form (Complaint Submission)
// -------------------------------------------------------------
function setupRequestForm() {
  const form = document.getElementById('form-raise-request');
  if (!form) return;

  // GPS Geolocation Button
  document.getElementById('btn-get-gps-location')?.addEventListener('click', () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          document.getElementById('req-latitude').value = pos.coords.latitude.toFixed(4);
          document.getElementById('req-longitude').value = pos.coords.longitude.toFixed(4);
          document.getElementById('req-city').value = 'Dehradun';
          document.getElementById('req-state').value = 'Uttarakhand';
          showToast('GPS coordinates acquired successfully!', 'success');
        },
        (err) => {
          showToast('Unable to retrieve GPS: ' + err.message + '. Please fill address manually.', 'warning');
        }
      );
    } else {
      showToast('Geolocation not supported in browser.', 'warning');
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
      inspection_id: state.activeInspection ? state.activeInspection.id : null,
      product_name: document.getElementById('req-product-name').value,
      brand: document.getElementById('req-brand').value,
      barcode: document.getElementById('req-barcode').value,
      mrp: document.getElementById('req-mrp').value,
      category: 'Packaged Food',
      purchase_date: document.getElementById('req-purchase-date').value || '24 Aug 2026',
      place_of_purchase: document.getElementById('req-place-purchase').value,
      shop_name: document.getElementById('req-shop-name').value,
      shop_address: document.getElementById('req-shop-address').value,
      city: document.getElementById('req-city').value,
      state: document.getElementById('req-state').value,
      market_area: document.getElementById('req-market-area').value,
      citizen_name: document.getElementById('req-citizen-name').value,
      citizen_phone: document.getElementById('req-citizen-phone').value,
      citizen_email: document.getElementById('req-citizen-email').value,
      preferred_contact: document.getElementById('req-preferred-contact').value,
      description: document.getElementById('req-description').value,
      priority: document.getElementById('req-priority').value
    };

    try {
      const res = await API.post('/api/requests', payload);
      
      // Upload shop photo if attached
      const shopPhotoInput = document.getElementById('req-shop-photo');
      if (shopPhotoInput && shopPhotoInput.files[0]) {
        const fd = new FormData();
        fd.append('evidence_type', 'shop');
        fd.append('file', shopPhotoInput.files[0]);
        await API.post(`/api/requests/${res.id}/evidence`, fd, true);
      }

      showToast(`Request ${res.request_code} submitted successfully for Officer review!`, 'success');
      
      // Show confirmation dialog / navigate to requests
      navigate('user-requests');
    } catch (err) {
      // Handled
    }
  });
}

function openRaiseRequestFormFromInspection(inspection) {
  if (!inspection) return;

  document.getElementById('req-product-name').value = inspection.product_name || 'CrunchBite Potato Chips';
  document.getElementById('req-brand').value = inspection.brand || 'CrunchBite';
  document.getElementById('req-barcode').value = inspection.barcode || '8901234567890';
  document.getElementById('req-mrp').value = '₹50';
  document.getElementById('req-purchase-date').value = new Date().toLocaleDateString('en-GB');

  if (state.currentUser) {
    document.getElementById('req-citizen-name').value = state.currentUser.full_name;
    document.getElementById('req-citizen-phone').value = '+91 98765 43210';
    document.getElementById('req-citizen-email').value = state.currentUser.email;
  }

  navigate('raise-request');
}

// -------------------------------------------------------------
// 6. User "My Reports" & "My Requests"
// -------------------------------------------------------------
async function loadUserReports() {
  try {
    const list = await API.get(`/api/inspections?user_id=${state.currentUser?.id || 1}`);
    const tbody = document.getElementById('user-reports-tbody');
    tbody.innerHTML = '';

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No reports generated yet.</td></tr>`;
      return;
    }

    list.forEach(ins => {
      const badgeClass = ins.overall_result === 'No Issue Detected' ? 'badge-no-issue' : ins.overall_result === 'Review Required' ? 'badge-review' : 'badge-non-compliance';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="fw-bold">${ins.inspection_code}</td>
        <td>
          <div class="fw-semibold">${ins.product_name}</div>
          <small class="text-muted">Barcode: ${ins.barcode || 'N/A'}</small>
        </td>
        <td>${new Date(ins.created_at).toLocaleDateString('en-GB')}</td>
        <td><span class="${badgeClass}">${ins.overall_result}</span></td>
        <td><span class="badge bg-secondary">${ins.confidence_score.toFixed(1)}%</span></td>
        <td>
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-primary" onclick="viewInspectionReportDirect(${ins.id})">
              <i class="bi bi-file-earmark-pdf me-1"></i>Download PDF
            </button>
            ${ins.non_compliance_count > 0 ? `<button class="btn btn-outline-danger" onclick="openRaiseRequestForId(${ins.id})"><i class="bi bi-flag me-1"></i>Raise Request</button>` : ''}
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load user reports:', err);
  }
}

async function loadUserRequests() {
  try {
    const list = await API.get(`/api/requests?user_id=${state.currentUser?.id || 1}`);
    const tbody = document.getElementById('user-requests-tbody');
    tbody.innerHTML = '';

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No requests raised yet.</td></tr>`;
      return;
    }

    list.forEach(r => {
      const stBadge = r.status === 'Submitted' ? 'bg-primary' : r.status === 'Under Review' ? 'bg-warning text-dark' : r.status === 'Action Initiated' ? 'bg-danger' : 'bg-success';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="fw-bold text-primary">${r.request_code}</td>
        <td>
          <div class="fw-semibold">${r.product_name}</div>
          <small class="text-muted">${r.shop_name}, ${r.city}</small>
        </td>
        <td>${new Date(r.created_at).toLocaleDateString('en-GB')}</td>
        <td><span class="badge ${stBadge}">${r.status}</span></td>
        <td><span class="badge bg-light text-dark border">${r.priority}</span></td>
        <td>
          <button class="btn btn-sm btn-outline-secondary" onclick="viewRequestCitizenModal(${r.id})">
            <i class="bi bi-eye me-1"></i>Details
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load user requests:', err);
  }
}

// -------------------------------------------------------------
// 7. Officer / Admin Dashboard & Charts
// -------------------------------------------------------------
async function loadOfficerDashboard() {
  try {
    const data = await API.get('/api/dashboard/admin');

    document.getElementById('admin-stat-inspections').textContent = data.stats.total_inspections;
    document.getElementById('admin-stat-no-issue').textContent = data.stats.no_issue_count;
    document.getElementById('admin-stat-review').textContent = data.stats.review_required_count;
    document.getElementById('admin-stat-non-comp').textContent = data.stats.non_compliance_count;
    document.getElementById('admin-stat-requests').textContent = data.stats.requests_raised;
    document.getElementById('admin-stat-cases-active').textContent = data.stats.cases_under_review;

    // Render Chart.js
    renderOfficerCharts(data.charts);

    // Load recent raised requests queue
    loadOfficerDashboardRequests();
  } catch (err) {
    console.error('Failed to load officer dashboard:', err);
  }
}

function renderOfficerCharts(chartsData) {
  if (typeof Chart === 'undefined') return;

  // 1. Compliance Distribution (Doughnut)
  const ctxDist = document.getElementById('chart-compliance-dist')?.getContext('2d');
  if (ctxDist) {
    if (state.charts.dist) state.charts.dist.destroy();
    state.charts.dist = new Chart(ctxDist, {
      type: 'doughnut',
      data: {
        labels: chartsData.compliance_distribution.labels,
        datasets: [{
          data: chartsData.compliance_distribution.data,
          backgroundColor: chartsData.compliance_distribution.colors,
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
        }
      }
    });
  }

  // 2. Inspections Trend (Line)
  const ctxTrend = document.getElementById('chart-inspections-trend')?.getContext('2d');
  if (ctxTrend) {
    if (state.charts.trend) state.charts.trend.destroy();
    state.charts.trend = new Chart(ctxTrend, {
      type: 'line',
      data: {
        labels: chartsData.inspections_trend.labels,
        datasets: [{
          label: 'Inspections',
          data: chartsData.inspections_trend.data,
          borderColor: '#1e40af',
          backgroundColor: 'rgba(30, 64, 175, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  // 3. Category Breakdown (Bar)
  const ctxCat = document.getElementById('chart-categories-bar')?.getContext('2d');
  if (ctxCat) {
    if (state.charts.cat) state.charts.cat.destroy();
    state.charts.cat = new Chart(ctxCat, {
      type: 'bar',
      data: {
        labels: chartsData.categories.labels,
        datasets: [{
          label: 'Products Inspected',
          data: chartsData.categories.data,
          backgroundColor: '#3b82f6',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }
}

async function loadOfficerDashboardRequests() {
  const list = await API.get('/api/requests');
  const tbody = document.getElementById('admin-recent-requests-tbody');
  tbody.innerHTML = '';

  if (!list || list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-muted">No requests submitted yet.</td></tr>`;
    return;
  }

  list.slice(0, 5).forEach(r => {
    const pBadge = r.priority === 'Urgent' ? 'bg-danger' : r.priority === 'High' ? 'bg-warning text-dark' : 'bg-secondary';
    const sBadge = r.status === 'Submitted' ? 'badge-review' : r.status === 'Action Initiated' ? 'badge-non-compliance' : 'badge-no-issue';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="fw-bold text-primary">${r.request_code}</td>
      <td>
        <div class="fw-semibold">${r.product_name}</div>
        <small class="text-muted">${r.shop_name}</small>
      </td>
      <td>${r.city}</td>
      <td><span class="badge ${pBadge}">${r.priority}</span></td>
      <td><span class="${sBadge}">${r.status}</span></td>
      <td>
        <button class="btn btn-xs btn-primary" onclick="openOfficerCaseReview(${r.id})">
          <i class="bi bi-shield-check me-1"></i>Review
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// -------------------------------------------------------------
// 8. Officer Case Review Workspace (Human-in-the-Loop)
// -------------------------------------------------------------
async function loadOfficerRequests() {
  const statusFilter = document.getElementById('filter-officer-req-status')?.value || 'All';
  const priorityFilter = document.getElementById('filter-officer-req-priority')?.value || 'All';
  const search = document.getElementById('search-officer-req')?.value || '';

  const list = await API.get(`/api/requests?status_filter=${statusFilter}&priority_filter=${priorityFilter}&search=${encodeURIComponent(search)}`);
  const tbody = document.getElementById('officer-requests-table-tbody');
  tbody.innerHTML = '';

  if (!list || list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No requests match criteria.</td></tr>`;
    return;
  }

  list.forEach(r => {
    const pBadge = r.priority === 'Urgent' ? 'bg-danger' : r.priority === 'High' ? 'bg-warning text-dark' : 'bg-secondary';
    const sBadge = r.status === 'Submitted' ? 'badge-review' : r.status === 'Action Initiated' ? 'badge-non-compliance' : 'badge-no-issue';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="fw-bold text-primary">${r.request_code}</td>
      <td>
        <div class="fw-semibold">${r.product_name}</div>
        <small class="text-muted">${r.brand || ''}</small>
      </td>
      <td>${r.citizen_name}<br/><small class="text-muted">${r.citizen_phone}</small></td>
      <td>${r.shop_name}<br/><small class="text-muted">${r.city}, ${r.state}</small></td>
      <td>${new Date(r.created_at).toLocaleDateString('en-GB')}</td>
      <td><span class="badge ${pBadge}">${r.priority}</span></td>
      <td><span class="${sBadge}">${r.status}</span></td>
      <td>
        <button class="btn btn-sm btn-primary" onclick="openOfficerCaseReview(${r.id})">
          <i class="bi bi-folder2-open me-1"></i>Open Case
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function openOfficerCaseReview(requestId) {
  navigate('officer-request-detail', { requestId });
}

async function loadOfficerRequestDetail(requestId) {
  try {
    const req = await API.get(`/api/requests/${requestId}`);
    state.activeRequest = req;

    document.getElementById('case-code-title').textContent = req.request_code;
    document.getElementById('case-status-badge').textContent = req.status;
    document.getElementById('case-priority-badge').textContent = req.priority;

    // Citizen Info
    document.getElementById('case-citizen-name').textContent = req.citizen_name;
    document.getElementById('case-citizen-phone').textContent = req.citizen_phone;
    document.getElementById('case-citizen-email').textContent = req.citizen_email || 'N/A';
    document.getElementById('case-preferred-contact').textContent = req.preferred_contact;

    // Location & Shop
    document.getElementById('case-shop-name').textContent = req.shop_name;
    document.getElementById('case-shop-address').textContent = req.shop_address;
    document.getElementById('case-city-state').textContent = `${req.city}, ${req.state} (${req.market_area || 'Market'})`;
    document.getElementById('case-description').textContent = req.description;

    // Product Info
    document.getElementById('case-prod-name').textContent = req.product_name;
    document.getElementById('case-prod-brand').textContent = req.brand || 'N/A';
    document.getElementById('case-prod-barcode').textContent = req.barcode || 'N/A';
    document.getElementById('case-prod-mrp').textContent = req.mrp || 'N/A';

    // Action Form Pre-fill
    document.getElementById('officer-action-status').value = req.status;
    document.getElementById('officer-action-remarks').value = req.officer_remarks || '';

    // Action History Timeline
    const historyList = document.getElementById('case-action-history-list');
    historyList.innerHTML = '';
    if (req.officer_actions && req.officer_actions.length > 0) {
      req.officer_actions.forEach(act => {
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.innerHTML = `
          <div class="d-flex justify-content-between">
            <span class="fw-semibold">${act.action_type}</span>
            <small class="text-muted">${new Date(act.created_at).toLocaleString('en-GB')}</small>
          </div>
          <div class="small text-secondary mt-1"><b>Officer:</b> ${act.officer_name}</div>
          ${act.remarks ? `<div class="small text-dark mt-1 bg-light p-2 rounded border">"${act.remarks}"</div>` : ''}
        `;
        historyList.appendChild(li);
      });
    } else {
      historyList.innerHTML = `<li class="list-group-item text-muted text-center py-3">No officer actions recorded yet.</li>`;
    }

    // Save Action Event Listener
    const saveBtn = document.getElementById('btn-save-officer-action');
    saveBtn.onclick = async () => {
      const newStatus = document.getElementById('officer-action-status').value;
      const remarks = document.getElementById('officer-action-remarks').value.trim();

      if (!remarks) {
        showToast('Please enter mandatory officer inspection remarks', 'warning');
        return;
      }

      try {
        await API.post(`/api/requests/${req.id}/action?officer_id=${state.currentUser?.id || 2}`, {
          new_status: newStatus,
          remarks: remarks
        });

        showToast('Officer action and audit trail successfully recorded!', 'success');
        loadOfficerRequestDetail(req.id);
      } catch (err) {
        // Handled
      }
    };

    // Download Report Button
    const rptBtn = document.getElementById('btn-case-download-report');
    if (rptBtn) {
      rptBtn.onclick = () => {
        if (req.inspection_id) {
          window.open(`/api/inspections/${req.inspection_id}/report`, '_blank');
        } else {
          showToast('Standalone request without attached automated inspection run.', 'info');
        }
      };
    }
  } catch (err) {
    console.error('Failed to load request detail:', err);
  }
}

// -------------------------------------------------------------
// 9. Rule Repository Explorer (26 Master Rules)
// -------------------------------------------------------------
async function loadRuleRepository() {
  const catFilter = document.getElementById('filter-rules-category')?.value || 'All';
  const search = document.getElementById('search-rules-input')?.value || '';

  try {
    const list = await API.get(`/api/rules?category=${encodeURIComponent(catFilter)}&search=${encodeURIComponent(search)}`);
    const tbody = document.getElementById('rules-repository-tbody');
    tbody.innerHTML = '';

    document.getElementById('rules-count-badge').textContent = `${list.length} Rules Active`;

    list.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="fw-bold text-primary">${r.rule_id}</td>
        <td>
          <div class="fw-semibold">${r.rule_title}</div>
          <small class="text-muted">${r.description}</small>
        </td>
        <td><span class="badge bg-light text-dark border">${r.product_category}</span></td>
        <td>
          <div class="small">${r.applicable_regulation}</div>
          <small class="text-muted">Clause: ${r.clause || 'General'}</small>
        </td>
        <td><span class="badge ${r.mandatory_conditional === 'Mandatory' ? 'bg-dark' : 'bg-info'}">${r.mandatory_conditional}</span></td>
        <td>
          <button class="btn btn-xs btn-outline-primary" onclick="openRuleDetailModal('${r.rule_id}')">
            <i class="bi bi-info-circle me-1"></i>Full Specs
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load rules:', err);
  }
}

async function openRuleDetailModal(ruleId) {
  try {
    const rule = await API.get(`/api/rules/${ruleId}`);
    
    document.getElementById('modal-rule-id').textContent = rule.rule_id;
    document.getElementById('modal-rule-title').textContent = rule.rule_title;
    document.getElementById('modal-rule-cat').textContent = rule.product_category;
    document.getElementById('modal-rule-reg').textContent = rule.applicable_regulation;
    document.getElementById('modal-rule-clause').textContent = rule.clause || 'N/A';
    document.getElementById('modal-rule-version').textContent = rule.version_amendment || 'N/A';
    document.getElementById('modal-rule-effective').textContent = rule.effective_date || 'N/A';
    document.getElementById('modal-rule-req').textContent = rule.legal_requirement;
    document.getElementById('modal-rule-desc').textContent = rule.description;
    document.getElementById('modal-rule-evidence').textContent = rule.evidence_required || 'Artwork / Packaging Label';
    document.getElementById('modal-rule-remarks').textContent = rule.remarks || 'Standard enforcement rule.';

    const modal = new bootstrap.Modal(document.getElementById('modal-rule-detail'));
    modal.show();
  } catch (err) {
    // Handled
  }
}

// -------------------------------------------------------------
// 10. Audit Trail Explorer
// -------------------------------------------------------------
async function loadAuditTrail() {
  const entityFilter = document.getElementById('filter-audit-entity')?.value || 'All';
  const roleFilter = document.getElementById('filter-audit-role')?.value || 'All';

  try {
    const list = await API.get(`/api/audit?entity_type=${entityFilter}&user_role=${roleFilter}`);
    const tbody = document.getElementById('audit-trail-tbody');
    tbody.innerHTML = '';

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No audit records found.</td></tr>`;
      return;
    }

    list.forEach(a => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><small class="font-monospace text-muted">${new Date(a.timestamp).toLocaleString('en-GB')}</small></td>
        <td>
          <div class="fw-semibold">${a.user_email}</div>
          <span class="badge bg-secondary extra-small">${a.user_role}</span>
        </td>
        <td><span class="fw-bold">${a.action}</span></td>
        <td><span class="badge bg-light text-dark border">${a.entity_type} ${a.entity_id ? `(${a.entity_id})` : ''}</span></td>
        <td><small class="text-secondary">${a.details || ''}</small></td>
        <td><small class="text-muted font-monospace">${a.ip_address || '127.0.0.1'}</small></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load audit logs:', err);
  }
}

// -------------------------------------------------------------
// 11. Reports & Products Repository
// -------------------------------------------------------------
async function loadOfficerReports() {
  try {
    const list = await API.get('/api/reports');
    const tbody = document.getElementById('officer-reports-tbody');
    tbody.innerHTML = '';

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No reports in repository.</td></tr>`;
      return;
    }

    list.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="fw-bold text-primary">${r.report_code}</td>
        <td>${r.product_name || 'Packaged Product'}</td>
        <td>${new Date(r.created_at).toLocaleDateString('en-GB')}</td>
        <td><span class="${r.overall_result === 'No Issue Detected' ? 'badge-no-issue' : 'badge-non-compliance'}">${r.overall_result || 'Completed'}</span></td>
        <td><small class="text-muted">${r.summary || 'Official PDF'}</small></td>
        <td>
          <a href="/api/reports/${r.id}/download" target="_blank" class="btn btn-sm btn-outline-primary">
            <i class="bi bi-download me-1"></i>Download PDF
          </a>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load reports:', err);
  }
}

async function loadOfficerProducts() {
  try {
    const list = await API.get('/api/products');
    const tbody = document.getElementById('officer-products-tbody');
    tbody.innerHTML = '';

    list.forEach(p => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <div class="fw-bold">${p.product_name}</div>
          <small class="text-muted">${p.manufacturer || ''}</small>
        </td>
        <td>${p.brand}</td>
        <td><span class="badge bg-light text-dark border">${p.category}</span></td>
        <td><code>${p.barcode || 'N/A'}</code></td>
        <td><b>${p.mrp || 'N/A'}</b></td>
        <td>${p.net_quantity || 'N/A'}</td>
        <td>
          <button class="btn btn-xs btn-outline-secondary" onclick="viewProductInspectionsModal(${p.id})">
            <i class="bi bi-clock-history me-1"></i>History
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load products:', err);
  }
}

async function loadOfficerInspections() {
  try {
    const list = await API.get('/api/inspections');
    const tbody = document.getElementById('officer-inspections-tbody');
    tbody.innerHTML = '';

    list.forEach(ins => {
      const badgeClass = ins.overall_result === 'No Issue Detected' ? 'badge-no-issue' : ins.overall_result === 'Review Required' ? 'badge-review' : 'badge-non-compliance';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="fw-bold">${ins.inspection_code}</td>
        <td>
          <div class="fw-semibold">${ins.product_name}</div>
          <small class="text-muted">${ins.brand} &bull; <code>${ins.barcode || ''}</code></small>
        </td>
        <td>${new Date(ins.created_at).toLocaleDateString('en-GB')}</td>
        <td><span class="${badgeClass}">${ins.overall_result}</span></td>
        <td><span class="badge bg-secondary">${ins.confidence_score.toFixed(1)}%</span></td>
        <td><span class="badge bg-info">${ins.officer_review_status}</span></td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="viewInspectionReportDirect(${ins.id})">
            <i class="bi bi-file-earmark-pdf me-1"></i>PDF
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load inspections:', err);
  }
}

// -------------------------------------------------------------
// Helper Modals
// -------------------------------------------------------------
function openEvidenceModal(fieldName, detectedValue, imageType, confidence) {
  document.getElementById('modal-evidence-field').textContent = fieldName;
  document.getElementById('modal-evidence-value').textContent = detectedValue;
  document.getElementById('modal-evidence-conf').textContent = `${confidence.toFixed(1)}%`;
  document.getElementById('modal-evidence-src').textContent = `${imageType.toUpperCase()} Package Image`;

  const imgEl = document.getElementById('modal-evidence-img');
  if (state.uploadedImages[imageType] && state.uploadedImages[imageType].dataUrl) {
    imgEl.src = state.uploadedImages[imageType].dataUrl;
  } else {
    imgEl.src = '/static/assets/sample_back.jpg';
  }

  const modal = new bootstrap.Modal(document.getElementById('modal-evidence-viewer'));
  modal.show();
}

function viewInspectionReportDirect(inspectionId) {
  window.open(`/api/inspections/${inspectionId}/report`, '_blank');
}

function openRaiseRequestForId(inspectionId) {
  API.get(`/api/inspections/${inspectionId}`).then(ins => {
    openRaiseRequestFormFromInspection(ins);
  });
}
