const cartState = {};
let currentCategory = null;

const menuEl = document.getElementById('menu');
const cartEl = document.getElementById('cart');
const ordersEl = document.getElementById('orders');
const categoriesEl = document.getElementById('categories');

function saveCart() {
  localStorage.setItem(getCartStorageKey(), JSON.stringify(cartState));
}

function getCartStorageKey() {
  const auth = getAuth();
  return auth
    ? `lees_treats_cart_user_${auth.user.id}`
    : 'lees_treats_cart_guest';
}

function restoreCart() {
  try {
    const savedCart = JSON.parse(localStorage.getItem(getCartStorageKey()) || '{}');
    Object.entries(savedCart).forEach(([itemId, quantity]) => {
      const parsedQuantity = Number(quantity);
      if (Number.isInteger(parsedQuantity) && parsedQuantity > 0) {
        cartState[itemId] = parsedQuantity;
      }
    });
  } catch {
    localStorage.removeItem(getCartStorageKey());
  }
}

async function switchCartForCurrentUser() {
  Object.keys(cartState).forEach(itemId => delete cartState[itemId]);
  restoreCart();
  updateCartCount();
  await renderCart();
}

// Use shared auth functions
const { api, toast, getAuth, updateAuthUI } = window.authApi || {
  api: async function(path, options = {}) {
    const res = await fetch(path, options);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || 'Request failed');
    }
    return res.json();
  },
  toast: function(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.remove('hidden');
    setTimeout(() => t.classList.add('hidden'), 2200);
  },
  getAuth: function() {
    return null;
  },
  updateAuthUI: function() {},
};

async function loadCategories() {
  const cats = await api('/api/categories');

  categoriesEl.innerHTML =
    `<button class="cat-chip ${currentCategory === null ? 'active' : ''}" data-cat="">All</button>` +
    cats.map(c => `<button class="cat-chip" data-cat="${c}">${c}</button>`).join('');

  categoriesEl.querySelectorAll('.cat-chip').forEach(btn =>
    btn.addEventListener('click', () => {
      currentCategory = btn.dataset.cat || null;

      categoriesEl.querySelectorAll('.cat-chip')
        .forEach(b => b.classList.toggle('active', b === btn));

      loadMenu();
    })
  );
}

async function loadMenu() {
  const q = currentCategory
    ? `?category=${encodeURIComponent(currentCategory)}`
    : '';

  const items = await api('/api/items' + q);

  menuEl.innerHTML = items.map(it => `
    <div class="card">
      <img src="${it.image}" alt="${it.name}" loading="lazy" decoding="async">

      <div class="card-body">
        <h3>${it.name}</h3>
        <p>${it.description}</p>

        <div class="card-footer">
          <span class="price">₦${it.price.toFixed(2)}</span>
          <button class="add-btn" data-id="${it.id}">Add</button>
        </div>
      </div>
    </div>
  `).join('');

  menuEl.querySelectorAll('.add-btn').forEach(btn =>
    btn.addEventListener('click', () =>
      addToCart(Number(btn.dataset.id))
    )
  );
}

function addToCart(itemId) {
  cartState[itemId] = (cartState[itemId] || 0) + 1;
  saveCart();

  updateCartCount();
  renderCart();
  toast('Added to cart');
}

function updateCartCount() {
  const total = Object.values(cartState)
    .reduce((a, b) => a + b, 0);

  document.getElementById('cartCount').textContent = total;
}

async function renderCart() {
  const ids = Object.keys(cartState);

  if (!ids.length) {
    cartEl.querySelector('#cartItems').innerHTML =
      '<p class="empty">Your cart is empty.</p>';

    document.getElementById('cartTotal').textContent = '';

    const bd = cartEl.querySelector('.cart-breakdown');
    if (bd) bd.remove();

    return;
  }

  const items = await Promise.all(
    ids.map(id => api('/api/items/' + id))
  );

  let subtotal = 0;

  for (const it of items) {
    const qty = cartState[it.id];
    subtotal += it.price * qty;
  }

  const deliveryFee = subtotal > 0 ? 5.99 : 0;
  const taxRate = 0.1;
  const tax = subtotal * taxRate;
  const total = subtotal + deliveryFee + tax;

  const breakdown = `
    <div class="cart-breakdown">
      <div class="breakdown-row">
        <span>Subtotal</span>
        <span>₦${subtotal.toFixed(2)}</span>
      </div>

      ${subtotal > 0 ? `
      <div class="breakdown-row">
        <span>Delivery Fee</span>
        <span>₦${deliveryFee.toFixed(2)}</span>
      </div>
      ` : ''}

      <div class="breakdown-row">
        <span>Estimated Tax</span>
        <span>₦${tax.toFixed(2)}</span>
      </div>

      <div class="breakdown-row breakdown-total">
        <span>Final Total</span>
        <span>₦${total.toFixed(2)}</span>
      </div>
    </div>
  `;

  let rows = '';

  for (const it of items) {
    const qty = cartState[it.id];

    rows += `
      <div class="cart-item">
        <img
          src="${it.image}"
          alt="${it.name}"
          class="cart-thumbnail"
          loading="lazy"
        >

        <span>
          <strong>${it.name}</strong>
        </span>

        <div class="qty-control">
          <input
            type="number"
            min="1"
            value="${qty}"
            data-id="${it.id}"
            class="qty-input"
          >
        </div>

        <small>${it.price.toFixed(2)} each</small>

        <button
          class="remove-btn"
          data-id="${it.id}"
        >
          ×
        </button>
      </div>
    `;
  }

  cartEl.querySelector('#cartItems').innerHTML = rows;

  let bd = cartEl.querySelector('.cart-breakdown');

  if (!bd) {
    bd = document.createElement('div');
    bd.className = 'cart-breakdown';
    cartEl.appendChild(bd);
  }

  bd.innerHTML = breakdown;

  cartEl.querySelectorAll('.qty-input').forEach(input => {
    input.addEventListener('change', e => {
      const newQty = Math.max(
        1,
        Number(e.target.value)
      );

      cartState[e.target.dataset.id] = newQty;
      saveCart();

      updateCartCount();
      renderCart();
    });
  });

  document.getElementById('cartTotal').textContent =
    `Total: ₦${total.toFixed(2)}`;

  cartEl.querySelectorAll('.remove-btn').forEach(btn =>
    btn.addEventListener('click', e => {
      e.stopPropagation();

      if (
        confirm(
          'Are you sure you want to remove this item from your cart?'
        )
      ) {
        removeFromCart(Number(btn.dataset.id));
      }
    })
  );
}

function changeQty(id, delta) {
  cartState[id] += delta;

  if (cartState[id] <= 0) {
    removeFromCart(id);
  } else {
    updateCartCount();
    renderCart();
  }
}

function removeFromCart(id) {
  delete cartState[id];
  saveCart();

  updateCartCount();
  renderCart();
}

function clearCart() {
  if (
    confirm('Are you sure you want to clear your entire cart?')
  ) {
    Object.keys(cartState).forEach(k =>
      delete cartState[k]
    );
    saveCart();

    updateCartCount();
    renderCart();
  }
}

async function placeOrder() {
  const name = document
    .getElementById('custName')
    .value
    .trim();

  const address = document
    .getElementById('custAddress')
    .value
    .trim();

  const phone = document
    .getElementById('custPhone')
    .value
    .trim();

  if (!name) {
    return toast('Please enter your name');
  }

  const items = Object.entries(cartState).map(
    ([item_id, quantity]) => ({
      item_id: Number(item_id),
      quantity
    })
  );

  await api('/api/orders', {
    method: 'POST',
    body: JSON.stringify({
      customer_name: name,
      address,
      phone,
      items
    }),
  });

  Object.keys(cartState).forEach(k =>
    delete cartState[k]
  );
  saveCart();

  updateCartCount();
  renderCart();

  document.getElementById('custName').value = '';
  document.getElementById('custAddress').value = '';
  document.getElementById('custPhone').value = '';

  toast('Order placed! 🎉');

  showSection('orders');
  loadOrders();
}

async function loadOrders() {
  const orders = await api('/api/orders');

  if (!orders.length) {
    ordersEl.querySelector('#ordersList').innerHTML =
      '<p class="empty">No orders yet.</p>';

    return;
  }

  ordersEl.querySelector('#ordersList').innerHTML =
    orders.map(o => `
      <div class="order-card">
        <div class="meta">
          <span>
            Order #${o.id} · ${o.created_at}
          </span>

          <span class="badge">
            ${o.status}
          </span>
        </div>

        <div class="lines">
          ${o.items
            .map(i =>
              `${i.item_name} × ${i.quantity}`
            )
            .join('<br>')}
        </div>

        <div class="total">
          Total: ₦${o.total.toFixed(2)}
        </div>
      </div>
    `).join('');
}

function showSection(name) {
  menuEl.classList.toggle(
    'hidden',
    name !== 'menu'
  );

  cartEl.classList.toggle(
    'hidden',
    name !== 'cart'
  );

  ordersEl.classList.toggle(
    'hidden',
    name !== 'orders'
  );

  document
    .getElementById('categories')
    .classList.toggle(
      'hidden',
      name !== 'menu'
    );

  // Update active nav button
  document.querySelectorAll('#main-nav .btn').forEach(btn => btn.classList.remove('active'));
  if (name === 'menu') {
    const homeBtn = document.getElementById('homeBtn');
    if (homeBtn) homeBtn.classList.add('active');
  } else if (name === 'cart') {
    const cartBtn = document.getElementById('cartBtn');
    if (cartBtn) cartBtn.classList.add('active');
  } else if (name === 'orders') {
    const ordersBtn = document.getElementById('viewOrdersBtn');
    if (ordersBtn) ordersBtn.classList.add('active');
  }

  if (name === 'menu') {
    menuEl.scrollIntoView({
      block: 'start'
    });
  } else if (name === 'cart') {
    cartEl.scrollIntoView({
      block: 'start'
    });
  } else if (name === 'orders') {
    ordersEl.scrollIntoView({
      block: 'start'
    });
  }
}

document
  .getElementById('cartBtn')
  .addEventListener('click', () =>
    showSection('cart')
  );

document
  .getElementById('homeBtn')
  .addEventListener('click', () => {
    showSection('menu');

    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });

document
  .getElementById('viewOrdersBtn')
  .addEventListener('click', () => {
    showSection('orders');
    loadOrders();
  });

document
  .getElementById('placeOrderBtn')
  .addEventListener(
    'click',
    placeOrder
  );

window.addEventListener('authchange', switchCartForCurrentUser);

setTimeout(() => {
  const backBtn =
    document.getElementById('backToMenuBtn');

  if (backBtn) {
    backBtn.addEventListener(
      'click',
      () => showSection('menu')
    );
  }
}, 0);

(async function init() {
  restoreCart();
  updateCartCount();
  await loadCategories();
  await loadMenu();
  await renderCart();
})();