const $ = id => document.getElementById(id);
let state, saved = [], polling = false;
let sourceDoc = '', sourcePage = 1;
async function request(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}
function notice(text, error = false) { $('notice').textContent = text; $('notice').className = error ? 'error' : ''; }
function source(doc, page) {
  sourceDoc = doc; sourcePage = page;
  const url = `/pdf/${encodeURIComponent(doc)}#page=${page}`;
  const image = `/page/${encodeURIComponent(doc)}/${page}`;
  $('page-error').hidden = true;
  $('pdf').src = image; $('pdf').alt = `${doc}, original PDF page ${page}`;
  $('page-image-link').href = image; $('page-label').textContent = `PDF page ${page}`;
  $('full-report').href = url; $('page-number').value = page;
  $('page-number').max = state.documents.find(d => d.document_id === doc).pdf_pages;
}
$('pdf').onerror = () => { $('page-error').hidden = false; $('page-error').textContent = 'Page unavailable. Check the local report download.'; };
$('page-number').onchange = () => {
  const page = Number($('page-number').value);
  if (Number.isInteger(page) && page >= 1 && page <= Number($('page-number').max)) source(sourceDoc, page);
  else $('page-number').value = sourcePage;
};
$('page-number').onkeydown = event => { if (event.key === 'Enter') $('page-number').onchange(); };
function metadata() {
  const doc = state.documents.find(d => d.document_id === $('document').value);
  $('doc-meta').textContent = `${doc.company} · FY${doc.year} · ${doc.pdf_pages} pages`;
}
function metric(label, value) {
  const box = document.createElement('div'), term = document.createElement('dt'), desc = document.createElement('dd');
  term.textContent = label; desc.textContent = value; box.append(term, desc); return box;
}
function render(row, recorded = false) {
  const answer = row.answer;
  $('answer').textContent = answer?.answer === 'insufficient_evidence'
    ? 'The retrieved excerpts do not provide enough evidence to answer this question.'
    : answer ? answer.answer : (row.error || 'No answer returned.');
  $('run-kind').textContent = recorded ? 'Saved run' : 'Live result';
  $('run-kind').className = 'badge ' + (answer?.status === 'answered' ? '' : 'warn');
  $('metrics').replaceChildren(metric('Status', answer?.status === 'answered' ? 'Answered' : row.generation_skipped ? 'Scope refusal' : 'Refused'),
    metric('Evidence supplied', String(row.supplied_ids?.length || 0)),
    metric('Wall time', row.wall_seconds ? `${row.wall_seconds.toFixed(2)} s` : '—'));
  $('citation').hidden = answer?.status !== 'answered';
  if (answer?.status === 'answered') {
    $('source-name').textContent = `${answer.document_id} · PDF page ${answer.pdf_page}`;
    $('quote').textContent = answer.quote; $('chunk').textContent = answer.chunk_id;
    $('open-pdf').href = `/pdf/${encodeURIComponent(answer.document_id)}#page=${answer.pdf_page}`;
    source(answer.document_id, answer.pdf_page);
  } else {
    source($('document').value, 1);
  }
  $('checks').replaceChildren();
  if (row.generation_skipped) {
    const li = document.createElement('li'); li.textContent = 'Outside report scope; model not called.'; $('checks').append(li);
  }
  for (const [name, passed] of Object.entries(row.checks || {})) {
    const li = document.createElement('li'), status = document.createElement('span');
    li.textContent = name.replaceAll('_', ' '); status.textContent = passed ? 'Pass' : 'Fail';
    status.className = passed ? 'pass' : 'fail'; li.append(status); $('checks').append(li);
  }
  $('retrieved').replaceChildren();
  for (const hit of row.retrieved || []) {
    const li = document.createElement('li'), link = document.createElement('a'), detail = document.createElement('span');
    link.href = `/pdf/${encodeURIComponent(hit.document_id)}#page=${hit.pdf_page}`;
    link.textContent = `PDF page ${hit.pdf_page} · ${hit.id}`;
    link.onclick = event => { event.preventDefault(); source(hit.document_id, hit.pdf_page); };
    detail.textContent = row.supplied_ids?.includes(hit.id) ? 'Supplied to model' : 'Not supplied';
    li.append(link, detail); $('retrieved').append(li);
  }
  notice(recorded ? `Recorded development result · ${row.recording}` : 'Question completed.');
}
$('saved').onchange = () => {
  if ($('saved').value === '') return;
  const row = saved[Number($('saved').value)]; $('document').value = row.document_id;
  $('numeric-mode').checked = (row.answer_kind || 'numeric') === 'numeric';
  $('fact-mode').checked = row.answer_kind === 'fact';
  $('question').value = row.question; metadata(); render(row, true);
};
$('document').onchange = () => {
  if ($('saved').value !== '') $('question').value = '';
  metadata(); $('saved').value = ''; $('citation').hidden = true;
  $('answer').textContent = 'No result for the selected report.';
  $('metrics').replaceChildren(); $('checks').replaceChildren(); $('retrieved').replaceChildren();
  $('run-kind').textContent = 'No result'; source($('document').value, 1);
  notice('');
};
for (const id of ['numeric-mode','fact-mode']) $(id).onchange = () => {
  if ($('saved').value !== '') $('question').value = '';
  $('document').onchange();
};
$('question-form').onsubmit = async event => {
  event.preventDefault(); if (polling) return;
  const question = $('question').value.trim();
  if (!question) return notice('Enter a question.', true);
  polling = true; $('ask').disabled = true; $('document').disabled = true; $('saved').disabled = true; $('question').disabled = true;
  $('numeric-mode').disabled = true; $('fact-mode').disabled = true;
  $('saved').value = ''; $('run-kind').textContent = 'Running';
  $('answer').textContent = 'Waiting for local result.'; $('citation').hidden = true;
  $('metrics').replaceChildren(); $('checks').replaceChildren(); $('retrieved').replaceChildren();
  try {
    const {job_id} = await request('/api/question', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({document_id:$('document').value, question, answer_kind:$('fact-mode').checked ? 'fact' : 'numeric'})});
    for (;;) {
      const job = await request(`/api/jobs/${job_id}`);
      if (job.status === 'error') throw new Error([job.error, job.cleanup_error].filter(Boolean).join(' '));
      if (job.status === 'complete') { render(job.result); if(job.cleanup_error) notice(job.cleanup_error, true); break; }
      notice(job.status === 'preparing' ? 'Preparing local document index…' : job.status === 'unloading' ? 'Releasing local model memory…' : 'Retrieving evidence and generating answer…');
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  } catch(error) { notice(error.message, true); $('run-kind').textContent = 'Request failed'; $('answer').textContent = 'No answer: the local request failed.'; $('citation').hidden = true; $('metrics').replaceChildren(); $('checks').replaceChildren(); $('retrieved').replaceChildren(); }
  finally { polling = false; $('ask').disabled = !state.allow_gpu; $('document').disabled = false; $('saved').disabled = false; $('question').disabled = false; $('numeric-mode').disabled = false; $('fact-mode').disabled = false; }
};
(async () => {
  try {
    state = await request('/api/state'); saved = await request('/api/saved');
    for (const doc of state.documents) $('document').add(new Option(`${doc.company} · ${doc.year} Annual Report`, doc.document_id));
    saved.forEach((row, i) => $('saved').add(new Option(row.question || row.case_id, String(i))));
    $('runtime').textContent = state.allow_gpu ? 'Local inference enabled' : 'GPU inference off';
    $('runtime').className = 'badge ' + (state.allow_gpu ? '' : 'muted');
    $('ask').disabled = !state.allow_gpu; $('ask').title = state.allow_gpu ? 'Run local question' : 'GPU inference disabled for this session';
    metadata();
    if (saved.length) { $('saved').value = '0'; $('saved').onchange(); } else source($('document').value, 1);
  } catch(error) { notice(error.message, true); $('runtime').textContent = 'Service error'; }
})();
