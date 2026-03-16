async function fetchDashboard() {
  const response = await fetch('/api/dashboard');
  const payload = await response.json();
  render(payload);
}

function item(title, body, meta = '') {
  return `<article class="item"><strong>${title}</strong><div>${body}</div>${meta ? `<div class="meta">${meta}</div>` : ''}</article>`;
}

function render(payload) {
  const metrics = payload.metrics;
  document.getElementById('metrics').innerHTML = [
    item('Signals processed', metrics.total_signals),
    item('Average risk score', metrics.average_score),
    item('Critical alerts', metrics.critical_alerts),
    item('Channels', Object.entries(metrics.channels).map(([key, value]) => `${key}: ${value}`).join(' · ')),
  ].join('');

  document.getElementById('signals').innerHTML = payload.signals.map((signal) =>
    item(`${signal.channel.toUpperCase()} · ${signal.sender}`, signal.content, `Country ${signal.country} · Hour ${signal.hour}`)
  ).join('');

  document.getElementById('playbooks').innerHTML = payload.playbooks.map((playbook) =>
    item(playbook.title, playbook.steps.map((step) => `• ${step}`).join('<br />'))
  ).join('');

  if (payload.alerts.length) {
    const alert = payload.alerts[0];
    document.getElementById('latest-alert').innerHTML = `
      <article class="item severity-${alert.severity}">
        <strong>${alert.summary}</strong>
        <div>${alert.reasons.map((reason) => `• ${reason}`).join('<br />')}</div>
        <div class="meta">${alert.action}</div>
      </article>
    `;
  }
}

document.getElementById('signal-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    channel: document.getElementById('channel').value,
    sender: document.getElementById('sender').value,
    content: document.getElementById('content').value,
    country: document.getElementById('country').value,
    hour: Number(document.getElementById('hour').value),
    amount: Number(document.getElementById('amount').value),
    new_device: document.getElementById('new-device').checked,
    new_ip: document.getElementById('new-ip').checked,
    ai_voice_flag: document.getElementById('ai-voice').checked,
  };
  const response = await fetch('/api/signals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  render(data.dashboard);
  document.getElementById('latest-alert').innerHTML = `
    <article class="item severity-${data.alert.severity}">
      <strong>${data.alert.summary}</strong>
      <div>${data.alert.reasons.map((reason) => `• ${reason}`).join('<br />')}</div>
      <div class="meta">${data.alert.action}</div>
    </article>
  `;
  document.getElementById('signal-form').reset();
});

fetchDashboard();
