const STATUSES = ['placed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled'];

const ordersList = document.getElementById('adminOrdersList');

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 2200);
}

async function api(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Request failed');
  }
  if (res.status === 204) return null;
  return res.json();
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

async function loadOrders() {
  const orders = await api('/admin/api/orders');
  if (!orders.length) {
    ordersList.innerHTML = '<p class="empty">No orders yet.</p>';
    return;
  }
  ordersList.innerHTML = orders.map(o => `
    <div class="order-card">
      <div class="meta"><span>Order #${o.id} · ${o.created_at}</span><span class="badge">${o.status}</span></div>
      <div class="customer">${esc(o.customer_name)}${o.address ? ' · ' + esc(o.address) : ''}${o.phone ? ' · ' + esc(o.phone) : ''}</div>
      <div class="lines">${o.items.map(i => `${esc(i.item_name)} × ${i.quantity} — $${i.unit_price.toFixed(2)}`).join('<br>')}</div>
      <div class="total">Total: $${o.total.toFixed(2)}</div>
      <div class="status-select">
        <select data-order="${o.id}">
          ${STATUSES.map(s => `<option value="${s}" ${s === o.status ? 'selected' : ''}>${s}</option>`).join('')}
        </select>
      </div>
    </div>
  `).join('');

  ordersList.querySelectorAll('select[data-order]').forEach(sel =>
    sel.addEventListener('change', async () => {
      try {
        await api(`/admin/api/orders/${sel.dataset.order}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: sel.value }),
        });
        toast('Status updated');
        loadOrders();
      } catch (e) {
        toast(e.message);
      }
    })
  );
}

document.getElementById('refreshOrdersBtn').addEventListener('click', loadOrders);

loadOrders();
setInterval(loadOrders, 5000);