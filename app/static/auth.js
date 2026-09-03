(function () {

async function api(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Request failed');
  }
  return res.json();
}

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 2200);
}

function setAuth(token, user) {
  localStorage.setItem('auth_token', token);
  localStorage.setItem('auth_user', JSON.stringify(user));
  updateAuthUI();
}

function clearAuth() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  updateAuthUI();
}

function getAuth() {
  const token = localStorage.getItem('auth_token');
  const user = localStorage.getItem('auth_user');
  return token && user ? { token, user: JSON.parse(user) } : null;
}

function updateAuthUI() {
  const auth = getAuth();
  const nav = document.getElementById('auth-nav');
  if (!nav) return;

  nav.querySelectorAll('.auth-btn').forEach(btn => btn.remove());


  if (auth) {
    const userBtn = document.createElement('button');
    userBtn.className = 'btn link auth-btn';
    userBtn.textContent = auth.user.username;
    userBtn.id = 'userMenuBtn';

    const logoutBtn = document.createElement('button');
    logoutBtn.className = 'btn link auth-btn';
    logoutBtn.textContent = 'Logout';
    logoutBtn.id = 'logoutBtn';
    logoutBtn.addEventListener('click', () => {
      clearAuth();
      toast('Logged out successfully');
      if (window.location.pathname.includes('login.html') || window.location.pathname.includes('register.html')) {
        window.location.href = '/';
      }
    });

    nav.appendChild(userBtn);
    nav.appendChild(logoutBtn);
  } else {
    const loginBtn = document.createElement('button');
    loginBtn.className = 'btn link auth-btn';
    loginBtn.textContent = 'Login';
    loginBtn.addEventListener('click', () => window.location.href = '/login.html');

    const registerBtn = document.createElement('button');
    registerBtn.className = 'btn primary auth-btn';
    registerBtn.textContent = 'Sign Up';
    registerBtn.addEventListener('click', () => window.location.href = '/register.html');

    nav.appendChild(loginBtn);
    nav.appendChild(registerBtn);
  }
}

function highlightActiveNav() {
  const path = window.location.pathname;
  const nav = document.getElementById('main-nav');
  if (!nav) return;

  nav.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));

  if (path === '/' || path === '/index.html') {
    const homeBtn = document.getElementById('homeBtn');
    if (homeBtn) homeBtn.classList.add('active');
  } else if (path === '/login.html') {
    const loginBtn = nav.querySelector('.auth-btn');
    if (loginBtn && loginBtn.textContent === 'Login') loginBtn.classList.add('active');
  } else if (path === '/register.html') {
    const authButtons = nav.querySelectorAll('.auth-btn');
    if (authButtons.length >= 2) authButtons[1].classList.add('active');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  updateAuthUI();
  highlightActiveNav();

  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(loginForm);
      const data = {
        username: formData.get('username'),
        password: formData.get('password'),
      };

      try {
        const result = await api('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify(data),
        });
        setAuth(result.access_token, result.user);
        toast('Welcome back, ' + result.user.username + '!');
        window.location.href = '/menu';
      } catch (err) {
        toast(err.message);
      }
    });
  }

  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(registerForm);
      const password = formData.get('password');
      const confirmPassword = formData.get('confirmPassword');

      if (password !== confirmPassword) {
        toast('Passwords do not match');
        return;
      }

      const data = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: password,
      };

      try {
        const result = await api('/api/auth/register', {
          method: 'POST',
          body: JSON.stringify(data),
        });
        setAuth(result.access_token, result.user);
        toast('Account created! Welcome, ' + result.user.username + '!');
        window.location.href = '/menu';
      } catch (err) {
        toast(err.message);
      }
    });
  }
});

window.authApi = { api, toast, getAuth, setAuth, clearAuth, updateAuthUI };

})();