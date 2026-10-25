/**
 * Sentinel Enterprise AI Fabric — Interactive Portal Logic
 * Client-side sandbox simulators for RAG, Agent Governance, ETL, and Telemetry
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initNavigation();
  initTabs();
  initRagSimulator();
  initAgentSimulator();
  initEtlVisualizer();
  initTelemetrySimulator();
});

// Theme Management
function initThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle');
  if (!toggleBtn) return;

  const savedTheme = localStorage.getItem('sentinel_theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  toggleBtn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('sentinel_theme', newTheme);
    updateThemeIcon(newTheme);
  });
}

function updateThemeIcon(theme) {
  const toggleBtn = document.getElementById('theme-toggle');
  if (!toggleBtn) return;
  if (theme === 'dark') {
    toggleBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`;
  } else {
    toggleBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
  }
}

// Navigation scroll tracking
function initNavigation() {
  const links = document.querySelectorAll('.nav-link');
  const sections = document.querySelectorAll('section[id]');

  window.addEventListener('scroll', () => {
    let current = '';
    const scrollY = window.pageYOffset;
    sections.forEach(section => {
      const sectionTop = section.offsetTop - 120;
      const sectionHeight = section.offsetHeight;
      if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
        current = section.getAttribute('id');
      }
    });

    links.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('active');
      }
    });
  });
}

// Tabs System
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');

      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const activeContent = document.getElementById(target);
      if (activeContent) {
        activeContent.classList.add('active');
      }
    });
  });
}

// Workstream B: Multi-Tenant RAG Simulator
function initRagSimulator() {
  const runBtn = document.getElementById('btn-run-rag');
  const queryInput = document.getElementById('rag-query-input');
  const tenantSelect = document.getElementById('rag-tenant');
  const clearanceSelect = document.getElementById('rag-clearance');
  const departmentSelect = document.getElementById('rag-dept');
  const outputConsole = document.getElementById('rag-console-body');
  const presetBtns = document.querySelectorAll('.rag-preset');

  if (!runBtn) return;

  presetBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const query = btn.getAttribute('data-query');
      const tenant = btn.getAttribute('data-tenant');
      const clearance = btn.getAttribute('data-clearance');
      const dept = btn.getAttribute('data-dept');

      if (queryInput) queryInput.value = query;
      if (tenantSelect && tenant) tenantSelect.value = tenant;
      if (clearanceSelect && clearance) clearanceSelect.value = clearance;
      if (departmentSelect && dept) departmentSelect.value = dept;
    });
  });

  runBtn.addEventListener('click', () => {
    const query = queryInput ? queryInput.value.trim() : '';
    const tenant = tenantSelect ? tenantSelect.value : 'alpha';
    const clearance = clearanceSelect ? clearanceSelect.value : 'INTERNAL';
    const department = departmentSelect ? departmentSelect.value : 'engineering';

    if (!query) return;

    outputConsole.innerHTML = '';
    appendLog(outputConsole, 'info', `Executing authorized query pipeline for Tenant: ${tenant.toUpperCase()}, Clearance: ${clearance}`);
    appendLog(outputConsole, 'info', `Query: "${query}"`);

    // Adversarial Prompt Injection Check
    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('ignore previous instructions') || lowerQuery.includes('system prompt') || lowerQuery.includes('dump credentials')) {
      setTimeout(() => {
        appendLog(outputConsole, 'warn', 'Security Gate Alert: Potential prompt injection / adversarial evasion pattern detected.');
        appendLog(outputConsole, 'block', 'Pre-retrieval Guardrail triggered: Input sanitized. Raw instructions stripped from retrieval context.');
        appendLog(outputConsole, 'info', 'Zero-Trust Enforcement: Strict metadata query envelope isolated to tenant boundaries.');
        appendLog(outputConsole, 'pass', 'Result: Safe abstention triggered. No unauthorized data or internal instructions leaked.');
      }, 350);
      return;
    }

    // Clearance Authorization Check
    const clearanceLadder = ['PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'SECRET', 'TOP_SECRET'];
    const userClearanceIndex = clearanceLadder.indexOf(clearance);

    // If query asks for confidential data
    const isConfidentialQuery = lowerQuery.includes('compensation') || lowerQuery.includes('salary') || lowerQuery.includes('forecast') || lowerQuery.includes('financial');
    const requiredClearanceIndex = isConfidentialQuery ? clearanceLadder.indexOf('CONFIDENTIAL') : clearanceLadder.indexOf('INTERNAL');

    setTimeout(() => {
      appendLog(outputConsole, 'info', `Evaluating pre-retrieval clearance filter (User: ${clearance} [Rank ${userClearanceIndex}], Target Doc: ${clearanceLadder[requiredClearanceIndex]} [Rank ${requiredClearanceIndex}])`);

      if (userClearanceIndex < requiredClearanceIndex) {
        appendLog(outputConsole, 'block', `ACCESS DENIED: Insufficient clearance level for document category. Pre-retrieval query filter eliminated candidate chunks before vector scoring.`);
        appendLog(outputConsole, 'pass', `Zero-Trust Abstention: "I am unable to answer this query based on the authorized documentation available for your clearance level."`);
        return;
      }

      appendLog(outputConsole, 'pass', `Authorization Verified: Query filtered by ChromaDB metadata: { tenant: "${tenant}", clearance_rank: {"$lte": ${userClearanceIndex}} }`);
      appendLog(outputConsole, 'info', `Dense Semantic Search: Cosine top-k retrieved 8 candidate vectors`);
      appendLog(outputConsole, 'info', `Sparse Okapi BM25: Keyword search retrieved 6 lexical candidate vectors`);
      appendLog(outputConsole, 'pass', `Reciprocal Rank Fusion (RRF, k=60): Merged 10 unified candidates with cross-encoder rerank threshold >= 0.45`);

      setTimeout(() => {
        appendLog(outputConsole, 'pass', `Synthesis Grounded in Evidence Block:`);
        if (isConfidentialQuery) {
          appendLog(outputConsole, 'info', `According to [FINANCIAL_REPORT_2026.pdf, Page 14], projected Q3 revenue growth is tracking at 18.4% YoY with gross operating margins sustained above 64%.`);
        } else {
          appendLog(outputConsole, 'info', `According to [ARCHITECTURE.md, Line 42], Sentinel utilizes an asynchronous 9-stage ETL ingestion pipeline with SHA-256 document chunk deduplication and atomic vector index synchronization.`);
        }
        appendLog(outputConsole, 'pass', `Citation Verification: 100% precision (Zero hallucinations, exactly matched to ingested evidence chunks).`);
      }, 400);
    }, 250);
  });
}

// Workstream C: Governed Agent & Two-Phase Approval Gate
function initAgentSimulator() {
  const toolSelect = document.getElementById('agent-tool-select');
  const runAgentBtn = document.getElementById('btn-run-agent');
  const agentConsole = document.getElementById('agent-console-body');
  const approvalBox = document.getElementById('approval-gate-box');
  const btnApprove = document.getElementById('btn-approve-action');
  const btnReject = document.getElementById('btn-reject-action');

  let currentPendingToken = null;
  let isTokenConsumed = false;

  if (!runAgentBtn) return;

  runAgentBtn.addEventListener('click', () => {
    const selectedTool = toolSelect.value;
    agentConsole.innerHTML = '';
    isTokenConsumed = false;
    approvalBox.style.display = 'none';

    appendLog(agentConsole, 'info', `Agent received request for tool: "${selectedTool}"`);
    appendLog(agentConsole, 'info', `Inspecting tool signature in typed Pydantic Tool Registry...`);

    const readOnlyTools = ['inventory_lookup', 'customer_lookup', 'ticket_status_lookup'];
    const isReadOnly = readOnlyTools.includes(selectedTool);

    setTimeout(() => {
      if (isReadOnly) {
        appendLog(agentConsole, 'pass', `Tool Permission Check: Policy classifies "${selectedTool}" as READ-ONLY.`);
        appendLog(agentConsole, 'pass', `Direct Execution Authorized: Querying mock transactional ERP backend...`);
        setTimeout(() => {
          if (selectedTool === 'inventory_lookup') {
            appendLog(agentConsole, 'info', `Result: Item ID "SKU-8821" - In Stock: 412 units across North America Hub.`);
          } else {
            appendLog(agentConsole, 'info', `Result: Customer ID "CUST-901" - Tier: Enterprise SLA (Active).`);
          }
          appendLog(agentConsole, 'pass', `Audit Log Appended: Correlation ID: corr-${Date.now().toString(36)}`);
        }, 300);
      } else {
        appendLog(agentConsole, 'warn', `CRITICAL POLICY GATE: Tool "${selectedTool}" is a STATE-CHANGING WRITE.`);
        appendLog(agentConsole, 'block', `Autonomous execution suspended. Two-Phase Cryptographic Approval Gate required.`);

        const operationId = `op-${Math.random().toString(36).substring(2, 9)}`;
        const paramHash = Array.from(crypto.getRandomValues(new Uint8Array(16))).map(b => b.toString(16).padStart(2, '0')).join('');
        currentPendingToken = `tok-hmac-sha256-${operationId}-${paramHash.substring(0, 8)}`;

        document.getElementById('gate-op-id').textContent = operationId;
        document.getElementById('gate-hash').textContent = paramHash;
        document.getElementById('gate-token').textContent = currentPendingToken;

        approvalBox.style.display = 'flex';
        appendLog(agentConsole, 'warn', `Generated HMAC-SHA256 Token bound to (operation_id, param_hash). Awaiting human signature...`);
      }
    }, 250);
  });

  if (btnApprove) {
    btnApprove.addEventListener('click', () => {
      if (isTokenConsumed) {
        appendLog(agentConsole, 'block', `SECURITY VIOLATION: Replay Attack Defense triggered. Token "${currentPendingToken}" has already been consumed or invalidated.`);
        return;
      }
      isTokenConsumed = true;
      appendLog(agentConsole, 'pass', `Cryptographic Signature Validated: HMAC-SHA256 matches authorization key.`);
      appendLog(agentConsole, 'pass', `Executing state-changing transaction on mock ERP/CRM database...`);
      setTimeout(() => {
        appendLog(agentConsole, 'info', `Transaction Status: 200 OK (Committed atomically). Idempotency Key stored.`);
        appendLog(agentConsole, 'pass', `Immutable Audit Trail written with operator signature.`);
        approvalBox.style.display = 'none';
      }, 300);
    });
  }

  if (btnReject) {
    btnReject.addEventListener('click', () => {
      isTokenConsumed = true;
      appendLog(agentConsole, 'block', `Operation Rejected by Human Operator. Approval token revoked.`);
      appendLog(agentConsole, 'info', `Rollback confirmed. Zero ERP state mutations occurred.`);
      approvalBox.style.display = 'none';
    });
  }
}

// Workstream A: Vector ETL Pipeline Stepper
function initEtlVisualizer() {
  const startEtlBtn = document.getElementById('btn-run-etl');
  const docSelect = document.getElementById('etl-doc-select');
  const etlConsole = document.getElementById('etl-console-body');
  const pipelineSteps = document.querySelectorAll('.pipeline-step');

  if (!startEtlBtn) return;

  const stageDescriptions = [
    { name: 'DISCOVER', desc: 'Discovered document in staging directory. Calculated source fingerprint.' },
    { name: 'VALIDATE', desc: 'MIME validation confirmed structure. Size within boundary limit.' },
    { name: 'EXTRACT', desc: 'Extracted text preserving page metadata and tabular row identifiers.' },
    { name: 'NORMALIZE', desc: 'Normalized unicode, stripped control characters, standard markdown headers.' },
    { name: 'CHUNK', desc: 'Boundary-aware sliding window splitting. Formed 4 semantic chunks.' },
    { name: 'EMBED', desc: 'Generated 384-dimensional dense vectors with cosine normalization.' },
    { name: 'INDEX', desc: 'Committed to ChromaDB vector collection and sparse Okapi BM25 table.' },
    { name: 'VERIFY', desc: 'Post-index vector probe confirmed 100% retrieval recall.' },
    { name: 'REPORT', desc: 'Ingestion manifest published. Deduplication cache updated.' }
  ];

  startEtlBtn.addEventListener('click', () => {
    const selectedDoc = docSelect.value;
    etlConsole.innerHTML = '';
    pipelineSteps.forEach(s => s.classList.remove('active', 'completed'));

    appendLog(etlConsole, 'info', `Starting 9-Stage ETL Ingestion for: "${selectedDoc}"`);

    let currentStep = 0;
    function runNextStep() {
      if (currentStep >= stageDescriptions.length) {
        appendLog(etlConsole, 'pass', `ETL Pipeline Completed Successfully. Document is ready for multi-tenant RAG.`);
        return;
      }

      pipelineSteps.forEach((s, idx) => {
        if (idx < currentStep) {
          s.classList.add('completed');
          s.classList.remove('active');
        } else if (idx === currentStep) {
          s.classList.add('active');
        }
      });

      const stage = stageDescriptions[currentStep];
      appendLog(etlConsole, 'pass', `[Stage ${currentStep + 1}/9] ${stage.name}: ${stage.desc}`);
      currentStep++;
      setTimeout(runNextStep, 220);
    }

    runNextStep();
  });
}

// Workstream D: Telemetry & Observability Simulator
function initTelemetrySimulator() {
  const redactInput = document.getElementById('redact-input');
  const redactOutput = document.getElementById('redact-output');

  if (redactInput && redactOutput) {
    redactInput.addEventListener('input', () => {
      const rawText = redactInput.value;
      // Regex masks
      const bearerMasked = rawText.replace(/Bearer\s+([A-Za-z0-9_\-\.]+)/gi, 'Bearer [REDACTED_TOKEN]');
      const secretMasked = bearerMasked.replace(/(?:api[_-]?key|secret|password|token)\s*[:=]\s*['"]?([^\s'"]+)['"]?/gi, 'secret: "[REDACTED_SECRET]"');
      const emailMasked = secretMasked.replace(/([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})/gi, '***@$2.$3');
      const ssnMasked = emailMasked.replace(/\b\d{3}-\d{2}-\d{4}\b/g, '***-**-****');
      redactOutput.textContent = ssnMasked;
    });
  }
}

// Utility: Append to interactive console
function appendLog(container, type, message) {
  if (!container) return;
  const time = new Date().toISOString().split('T')[1].substring(0, 8);
  const entry = document.createElement('div');
  entry.className = 'log-entry';

  let tagClass = 'tag-info';
  let tagLabel = 'INFO';
  if (type === 'pass') { tagClass = 'tag-pass'; tagLabel = 'PASS'; }
  else if (type === 'block') { tagClass = 'tag-block'; tagLabel = 'BLOCK'; }
  else if (type === 'warn') { tagClass = 'tag-warn'; tagLabel = 'WARN'; }

  entry.innerHTML = `
    <span class="log-time">${time}</span>
    <span class="log-tag ${tagClass}">${tagLabel}</span>
    <span class="log-text">${escapeHtml(message)}</span>
  `;
  container.appendChild(entry);
  container.scrollTop = container.scrollHeight;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
