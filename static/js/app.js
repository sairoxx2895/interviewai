/* InterviewAI — frontend logic
   Talks to the Flask API (/api/generate, /api/history, /api/export)
   and renders everything without any framework. */

const els = {
  form: document.getElementById('generate-form'),
  btnGenerate: document.getElementById('btn-generate'),
  btnGenerateLabel: document.getElementById('btn-generate-label'),
  btnNew: document.getElementById('btn-new-session'),
  errorBanner: document.getElementById('error-banner'),

  panelGenerator: document.getElementById('panel-generator'),
  panelResults: document.getElementById('panel-results'),
  emptyState: document.getElementById('empty-state'),

  resultsRole: document.getElementById('results-role'),
  resultsMeta: document.getElementById('results-meta'),
  resultsNotes: document.getElementById('results-notes'),
  questionList: document.getElementById('question-list'),
  btnExport: document.getElementById('btn-export'),

  ledgerList: document.getElementById('ledger-list'),
  ledgerCount: document.getElementById('ledger-count'),
};

let currentSessionId = null;

// ---------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------

function showError(message) {
  els.errorBanner.textContent = message;
  els.errorBanner.hidden = false;
}

function clearError() {
  els.errorBanner.hidden = true;
  els.errorBanner.textContent = '';
}

function setGenerating(isGenerating) {
  els.btnGenerate.disabled = isGenerating;
  els.btnGenerateLabel.textContent = isGenerating ? 'Generating' : 'Generate questions';
  els.btnGenerateLabel.classList.toggle('dots', isGenerating);
}

function formatMeta(session) {
  return [
    `Level: ${capitalize(session.experience_level)}`,
    `Type: ${capitalize(session.interview_type)}`,
    `${(session.questions || []).length} questions`,
  ].join('   •   ');
}

function capitalize(s) {
  if (!s) return '—';
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

// ---------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------

function renderSession(session) {
  currentSessionId = session.id;

  els.panelResults.hidden = false;
  els.emptyState.hidden = true;

  els.resultsRole.textContent = session.role || 'Untitled role';
  els.resultsMeta.textContent = formatMeta(session);
  els.resultsNotes.textContent = session.overall_evaluation_notes || '';
  els.resultsNotes.hidden = !session.overall_evaluation_notes;

  els.questionList.innerHTML = '';
  (session.questions || []).forEach((q, i) => {
    els.questionList.appendChild(renderQuestionCard(q, i + 1));
  });

  els.panelResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderQuestionCard(q, index) {
  const card = document.createElement('article');
  card.className = 'q-card';

  const greenItems = (q.green_flags || []).map(f => `<li>${escapeHtml(f)}</li>`).join('');
  const redItems = (q.red_flags || []).map(f => `<li>${escapeHtml(f)}</li>`).join('');

  const scoring = q.scoring_guide || {};
  const scoringRows = [
    ['1-2 (Weak)', scoring['1_2']],
    ['3 (Adequate)', scoring['3']],
    ['4-5 (Strong)', scoring['4_5']],
  ].filter(([, v]) => !!v)
   .map(([label, v]) => `<div><b>${label}:</b> ${escapeHtml(v)}</div>`)
   .join('');

  card.innerHTML = `
    <div class="q-head">
      <span class="q-index">Q${index}</span>
      <span class="q-category">${escapeHtml(q.category || 'General')}</span>
    </div>
    <p class="q-text">${escapeHtml(q.question || '')}</p>
    <div class="signal-gauge" aria-hidden="true"></div>
    ${q.follow_up ? `<p class="q-sub"><span class="label">Follow-up</span>${escapeHtml(q.follow_up)}</p>` : ''}
    ${q.evaluation_tip ? `<p class="q-sub"><span class="label">What a strong answer looks like</span>${escapeHtml(q.evaluation_tip)}</p>` : ''}
    <div class="flags-grid">
      <div class="flags-col green">
        <div class="flags-title">● Green flags</div>
        <ul>${greenItems || '<li>—</li>'}</ul>
      </div>
      <div class="flags-col red">
        <div class="flags-title">● Red flags</div>
        <ul>${redItems || '<li>—</li>'}</ul>
      </div>
    </div>
    ${scoringRows ? `<div class="scoring">${scoringRows}</div>` : ''}
  `;
  return card;
}

function renderLedger(sessions) {
  els.ledgerCount.textContent = sessions.length;

  if (!sessions.length) {
    els.ledgerList.innerHTML = '<p class="ledger-empty">No sessions yet. Generate your first question set to see it here.</p>';
    return;
  }

  els.ledgerList.innerHTML = '';
  sessions.forEach(s => {
    const item = document.createElement('div');
    item.className = 'ledger-item' + (s.id === currentSessionId ? ' active' : '');
    item.innerHTML = `
      <button class="li-delete" title="Delete session" data-id="${s.id}">×</button>
      <p class="li-role">${escapeHtml(s.role || 'Untitled role')}</p>
      <p class="li-meta">${capitalize(s.experience_level)} · ${capitalize(s.interview_type)} · ${s.num_questions}q</p>
    `;
    item.addEventListener('click', (e) => {
      if (e.target.closest('.li-delete')) return;
      loadSession(s.id);
    });
    item.querySelector('.li-delete').addEventListener('click', async (e) => {
      e.stopPropagation();
      await deleteSession(s.id);
    });
    els.ledgerList.appendChild(item);
  });
}

// ---------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------

async function fetchHistory() {
  const res = await fetch('/api/history');
  const data = await res.json();
  renderLedger(data);
}

async function loadSession(id) {
  clearError();
  const res = await fetch(`/api/history/${id}`);
  if (!res.ok) {
    showError('Could not load that session — it may have been deleted.');
    return;
  }
  const session = await res.json();
  renderSession(session);
  fetchHistory(); // refresh active-state highlighting
}

async function deleteSession(id) {
  await fetch(`/api/history/${id}`, { method: 'DELETE' });
  if (id === currentSessionId) {
    currentSessionId = null;
    els.panelResults.hidden = true;
    els.emptyState.hidden = false;
  }
  fetchHistory();
}

async function generateQuestions(payload) {
  const res = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || 'Something went wrong while generating questions.');
  }
  return data;
}

async function exportSession(id) {
  const res = await fetch(`/api/export/${id}`, { method: 'POST' });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Export failed.');
  }
  const blob = await res.blob();
  const disposition = res.headers.get('Content-Disposition') || '';
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : 'interview-questions.docx';

  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------
// Event wiring
// ---------------------------------------------------------------------

els.form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearError();

  const payload = {
    role: document.getElementById('role').value.trim(),
    experience_level: document.getElementById('experience_level').value,
    interview_type: document.getElementById('interview_type').value,
    num_questions: parseInt(document.getElementById('num_questions').value, 10) || 5,
    notes: document.getElementById('notes').value.trim(),
  };

  if (!payload.role) {
    showError('Please enter a job role.');
    return;
  }

  setGenerating(true);
  try {
    const session = await generateQuestions(payload);
    renderSession(session);
    fetchHistory();
  } catch (err) {
    showError(err.message);
  } finally {
    setGenerating(false);
  }
});

els.btnNew.addEventListener('click', () => {
  currentSessionId = null;
  els.form.reset();
  els.panelResults.hidden = true;
  els.emptyState.hidden = false;
  clearError();
  fetchHistory();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

els.btnExport.addEventListener('click', async () => {
  if (!currentSessionId) return;
  els.btnExport.disabled = true;
  const originalLabel = els.btnExport.textContent;
  els.btnExport.textContent = 'Exporting…';
  try {
    await exportSession(currentSessionId);
  } catch (err) {
    showError(err.message);
  } finally {
    els.btnExport.disabled = false;
    els.btnExport.textContent = originalLabel;
  }
});

// ---------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------

fetchHistory();
