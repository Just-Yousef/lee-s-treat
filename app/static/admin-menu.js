const itemsList = document.getElementById('adminItemsList');
const modal = document.getElementById('itemModal');

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

async function loadItems() {
  const items = await api('/admin/api/items');
  if (!items.length) {
    itemsList.innerHTML = '<p class="empty">No menu items yet.</p>';
    return;
  }
  itemsList.innerHTML = items.map(it => `
    <div class="admin-item">
      <img src="${esc(it.image || '')}" alt="${esc(it.name)}" loading="lazy" decoding="async">
      <div class="info">
        <h4>${esc(it.name)}</h4>
        <small>${esc(it.category)}${it.description ? ' · ' + esc(it.description) : ''}</small><br>
        <span class="price">₦${it.price.toFixed(2)}</span>
      </div>
      <div class="item-actions">
        <button class="btn edit-btn" data-id="${it.id}">Edit</button>
        <button class="btn danger del-btn" data-id="${it.id}">Delete</button>
      </div>
    </div>
  `).join('');

  itemsList.querySelectorAll('.edit-btn').forEach(btn =>
    btn.addEventListener('click', () => openItemModal(Number(btn.dataset.id), items))
  );
  itemsList.querySelectorAll('.del-btn').forEach(btn =>
    btn.addEventListener('click', async () => {
      if (!confirm('Delete this item?')) return;
      try {
        await api(`/admin/api/items/${btn.dataset.id}`, { method: 'DELETE' });
        toast('Item deleted');
        await loadItems();
      } catch (e) {
        toast(e.message);
      }
    })
  );
}

function openItemModal(id, items) {
  const it = items.find(x => x.id === id);
  document.getElementById('itemModalTitle').textContent = it ? 'Edit Item' : 'New Item';
  document.getElementById('f_id').value = it ? it.id : '';
  document.getElementById('f_name').value = it ? it.name : '';
  document.getElementById('f_description').value = it ? it.description : '';
  document.getElementById('f_price').value = it ? it.price : '';
  document.getElementById('f_category').value = it ? it.category : '';
  document.getElementById('f_image').value = it ? (it.image || '') : '';
  modal.classList.remove('hidden');
}

async function submitItem(e) {
  e.preventDefault();
  const id = document.getElementById('f_id').value;
  const payload = {
    name: document.getElementById('f_name').value.trim(),
    description: document.getElementById('f_description').value.trim(),
    price: parseFloat(document.getElementById('f_price').value),
    category: document.getElementById('f_category').value.trim() || 'Other',
    image: document.getElementById('f_image').value.trim() || null,
  };
  try {
    await api(id ? `/admin/api/items/${id}` : '/admin/api/items', {
      method: id ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    toast(id ? 'Item updated' : 'Item added');
    modal.classList.add('hidden');
    await loadItems();
  } catch (err) {
    toast(err.message);
  }
}

document.getElementById('newItemBtn').addEventListener('click', () => openItemModal(null, []));
document.getElementById('cancelBtn').addEventListener('click', () => modal.classList.add('hidden'));
document.getElementById('itemForm').addEventListener('submit', submitItem);

loadItems();