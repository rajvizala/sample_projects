async function fetchDashboard() {
  const response = await fetch('/api/dashboard');
  const payload = await response.json();
  render(payload);
}

function card(title, body, meta = '') {
  return `
    <article class="item">
      <strong>${title}</strong>
      <div>${body}</div>
      ${meta ? `<div class="meta">${meta}</div>` : ''}
    </article>
  `;
}

function render(payload) {
  document.getElementById('digest').textContent = payload.digest;
  document.getElementById('people-count').textContent = `${payload.people.length} people`;

  const peopleList = document.getElementById('people-list');
  peopleList.innerHTML = payload.people.map((person) => `
    <div class="pill">
      <strong>${person.name}</strong>
      <div>${person.role}</div>
      <div class="meta">Love language: ${person.love_language}</div>
      <div class="meta">Current focus: ${person.focus}</div>
    </div>
  `).join('');

  const selector = document.getElementById('person-id');
  selector.innerHTML = payload.people.map((person) => `<option value="${person.id}">${person.name}</option>`).join('');

  document.getElementById('updates').innerHTML = payload.updates.map((update) => `
    <article class="item">
      <strong>${update.person_name} · ${update.category}</strong>
      <div>${update.text}</div>
      <div class="tag-row">${update.tags.map((tag) => `<span class="tag">${tag}</span>`).join('')}</div>
      <div class="meta">Mood: ${update.mood}</div>
    </article>
  `).join('');

  document.getElementById('suggestions').innerHTML = payload.suggestions.map((item) =>
    card(item.title, item.rationale, item.kind)
  ).join('');

  document.getElementById('memories').innerHTML = payload.memories.map((memory) => `
    <article class="item">
      <strong>${memory.title}</strong>
      <div>${memory.detail}</div>
      <div class="meta">People: ${memory.people.join(', ')} · Importance ${memory.importance}/5</div>
    </article>
  `).join('');

  document.getElementById('graph').innerHTML = payload.graph.edges.map((edge) =>
    card(`${edge.source} -> ${edge.target}`, `Strength score: ${edge.weight}`)
  ).join('');
}

document.getElementById('update-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    person_id: Number(document.getElementById('person-id').value),
    category: document.getElementById('category').value,
    mood: document.getElementById('mood').value,
    text: document.getElementById('text').value,
  };
  await fetch('/api/updates', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  document.getElementById('update-form').reset();
  fetchDashboard();
});

fetchDashboard();
