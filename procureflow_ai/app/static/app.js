async function fetchDashboard() {
  const response = await fetch('/api/dashboard');
  const payload = await response.json();
  render(payload);
}

function block(title, body, meta = '') {
  return `<article class="item"><strong>${title}</strong><div>${body}</div>${meta ? `<div class="meta">${meta}</div>` : ''}</article>`;
}

function render(payload) {
  document.getElementById('forecast-strip').innerHTML = payload.forecasts.map((forecast) =>
    block(`${forecast.category} forecast`, `${forecast.last_observed} last week -> ${forecast.next_week_forecast} next week`, `Trend: ${forecast.trend}`)
  ).join('');

  document.getElementById('anomalies').innerHTML = payload.price_anomalies.length
    ? payload.price_anomalies.map((item) =>
        block(`${item.supplier} · ${item.category}`, `$${item.unit_price} vs benchmark $${item.benchmark}`, item.message)
      ).join('')
    : block('No anomalies detected', 'Current quote set is within expected range.');

  document.getElementById('suppliers').innerHTML = payload.suppliers.map((supplier) =>
    block(supplier.name, `${supplier.category} · lead time ${supplier.lead_time_days} days`, `On-time ${Math.round(supplier.on_time_rate * 100)}% · Quality ${supplier.quality_score} · Risk ${supplier.risk_score}`)
  ).join('');

  document.getElementById('requisitions').innerHTML = payload.requisitions.map((req) => {
    const rec = payload.recommendations[String(req.id)] || payload.recommendations[req.id];
    const recommendation = rec
      ? `Best source: ${rec.supplier} · score ${rec.score}<br />${rec.why.map((entry) => `• ${entry}`).join('<br />')}`
      : 'No quotes yet';
    return block(req.title, `${req.category} · qty ${req.quantity}`, recommendation);
  }).join('');
}

document.getElementById('requisition-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const certs = document.getElementById('certifications').value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
  const payload = {
    title: document.getElementById('title').value,
    category: document.getElementById('category').value,
    quantity: Number(document.getElementById('quantity').value),
    needed_by: document.getElementById('needed-by').value,
    priority: document.getElementById('priority').value,
    required_certifications: certs,
  };
  const response = await fetch('/api/requisitions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  render(data.dashboard);
  document.getElementById('requisition-form').reset();
});

fetchDashboard();
