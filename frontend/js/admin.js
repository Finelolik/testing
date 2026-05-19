/* ========================
   STATE
======================== */
let token       = localStorage.getItem('admin_token') || null;
let currentView = 'active';
let openAppeal  = null;

const loginScreen = document.getElementById('login-screen');
const adminPanel  = document.getElementById('admin-panel');

/* ========================
   AUTH INIT
======================== */
function showPanel() {
  loginScreen.classList.add('hidden');
  adminPanel.classList.remove('hidden');
  loadAppeals(currentView);
}

function showLogin() {
  token = null;
  localStorage.removeItem('admin_token');
  loginScreen.classList.remove('hidden');
  adminPanel.classList.add('hidden');
}

if (token) {
  showPanel();
}

/* ========================
   LOGIN FORM
======================== */
document.getElementById('login-form').addEventListener('submit', async function (e) {
  e.preventDefault();
  const errEl = document.getElementById('login-error');
  errEl.classList.add('hidden');
  errEl.textContent = '';

  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;

  if (!username || !password) {
    errEl.textContent = 'Введите логин и пароль';
    errEl.classList.remove('hidden');
    return;
  }

  const btn = this.querySelector('.btn-login');
  btn.disabled = true;
  btn.textContent = 'Вход...';

  try {
    const res = await fetch('/api/admin/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ username, password }),
    });

    const json = await res.json();

    if (!res.ok) {
      errEl.textContent = json.detail || 'Неверный логин или пароль';
      errEl.classList.remove('hidden');
      return;
    }

    token = json.access_token;
    localStorage.setItem('admin_token', token);
    showPanel();

  } catch {
    errEl.textContent = 'Ошибка соединения с сервером';
    errEl.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Войти';
  }
});

document.getElementById('logout-btn').addEventListener('click', showLogin);

/* ========================
   SIDEBAR NAVIGATION
======================== */
document.querySelectorAll('.sidebar-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    document.querySelectorAll('.sidebar-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    currentView = this.dataset.view;
    document.getElementById('panel-title').textContent =
      currentView === 'active' ? 'Входящие обращения' : 'Архив обращений';
    loadAppeals(currentView);
  });
});

/* ========================
   LOAD APPEALS
======================== */
async function loadAppeals(status) {
  const list = document.getElementById('appeals-list');
  list.innerHTML = '<div class="loading-state">Загрузка...</div>';

  try {
    const res = await fetch(`/api/appeals/?status=${status}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });

    if (res.status === 401) { showLogin(); return; }

    const appeals = await res.json();

    document.getElementById('appeals-count').textContent = appeals.length;

    if (appeals.length === 0) {
      list.innerHTML = '<div class="empty-state">Нет обращений</div>';
      return;
    }

    list.innerHTML = '';
    appeals.forEach(a => {
      const row = document.createElement('div');
      row.className = 'appeal-row';
      row.innerHTML = `
        <span class="appeal-id">#${a.id}</span>
        <span class="appeal-subject">${escHtml(a.subject)}</span>
        <span class="appeal-date">${formatDate(a.created_at)}</span>
        <button class="btn-open" data-id="${a.id}">Открыть</button>
      `;
      list.appendChild(row);
    });

    list.querySelectorAll('.btn-open').forEach(btn => {
      btn.addEventListener('click', () => openModal(Number(btn.dataset.id)));
    });

  } catch {
    list.innerHTML = '<div class="empty-state">Ошибка загрузки данных</div>';
  }
}

/* ========================
   MODAL
======================== */
const modalOverlay = document.getElementById('modal-overlay');

async function openModal(id) {
  try {
    const res = await fetch(`/api/appeals/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (res.status === 401) { showLogin(); return; }
    const a = await res.json();
    openAppeal = a;

    document.getElementById('modal-id').textContent      = `Обращение #${a.id}`;
    document.getElementById('modal-subject').textContent = a.subject;
    document.getElementById('modal-name').textContent    = a.full_name;
    document.getElementById('modal-phone').textContent   = a.phone;
    document.getElementById('modal-email').textContent   = a.email;
    document.getElementById('modal-date').textContent    = formatDate(a.created_at);
    document.getElementById('modal-body').textContent    = a.body;

    // Hide archive button if already archived
    const modalActions = document.getElementById('modal-actions');
    const archiveBtn   = document.getElementById('btn-archive');
    archiveBtn.style.display = a.status === 'archived' ? 'none' : '';

    modalOverlay.classList.remove('hidden');
    document.body.style.overflow = 'hidden';

  } catch {
    alert('Не удалось загрузить обращение');
  }
}

function closeModal() {
  modalOverlay.classList.add('hidden');
  document.body.style.overflow = '';
  openAppeal = null;
}

document.getElementById('modal-close').addEventListener('click', closeModal);
modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });

document.getElementById('btn-archive').addEventListener('click', async () => {
  if (!openAppeal) return;
  if (!confirm('Переместить обращение в архив?')) return;

  try {
    const res = await fetch(`/api/appeals/${openAppeal.id}/archive`, {
      method:  'PATCH',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (res.status === 401) { showLogin(); return; }
    if (res.ok) {
      closeModal();
      loadAppeals(currentView);
    }
  } catch { alert('Ошибка при архивировании'); }
});

document.getElementById('btn-delete').addEventListener('click', async () => {
  if (!openAppeal) return;
  if (!confirm(`Удалить обращение #${openAppeal.id}? Это действие необратимо.`)) return;

  try {
    const res = await fetch(`/api/appeals/${openAppeal.id}`, {
      method:  'DELETE',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (res.status === 401) { showLogin(); return; }
    if (res.ok) {
      closeModal();
      loadAppeals(currentView);
    }
  } catch { alert('Ошибка при удалении'); }
});

/* ========================
   HELPERS
======================== */
function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatDate(str) {
  if (!str) return '';
  const d = new Date(str.replace(' ', 'T') + (str.includes('T') ? '' : 'Z'));
  return d.toLocaleDateString('ru-RU', { day:'2-digit', month:'2-digit', year:'numeric' })
       + ' ' + d.toLocaleTimeString('ru-RU', { hour:'2-digit', minute:'2-digit' });
}
