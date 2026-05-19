/* ========================
   TAB NAVIGATION
======================== */
const navBtns = document.querySelectorAll('.nav-btn');
const tabs    = document.querySelectorAll('.tab-content');

function switchTab(tabId) {
  navBtns.forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
  tabs.forEach(t => t.classList.toggle('active', t.id === `tab-${tabId}`));
}

navBtns.forEach(btn => btn.addEventListener('click', () => switchTab(btn.dataset.tab)));

document.getElementById('go-to-appeal').addEventListener('click', () => switchTab('appeal'));

/* ========================
   PHONE MASK  +7 (xxx) xxx xx-xx
======================== */
const phoneInput = document.getElementById('phone');

phoneInput.addEventListener('input', function (e) {
  const selStart = this.selectionStart;
  let digits = this.value.replace(/\D/g, '');

  // Force start with 7
  if (digits.startsWith('8')) digits = '7' + digits.slice(1);
  if (!digits.startsWith('7')) digits = '7' + digits;
  digits = digits.slice(0, 11);

  let formatted = '+7';
  if (digits.length > 1) formatted += ' (' + digits.slice(1, 4);
  if (digits.length >= 4) formatted += ') ' + digits.slice(4, 7);
  if (digits.length >= 7) formatted += ' ' + digits.slice(7, 9);
  if (digits.length >= 9) formatted += '-' + digits.slice(9, 11);

  this.value = formatted;
});

phoneInput.addEventListener('keydown', function (e) {
  if (e.key === 'Backspace' && this.value === '+7') {
    e.preventDefault();
  }
});

phoneInput.addEventListener('focus', function () {
  if (!this.value) this.value = '+7';
});

/* ========================
   FORM VALIDATION & SUBMIT
======================== */
const form      = document.getElementById('appeal-form');
const successEl = document.getElementById('form-success');
const globalErr = document.getElementById('form-error');

function setError(field, msg) {
  const input = document.getElementById(field);
  const err   = document.getElementById(`err-${field}`);
  if (input)  input.classList.toggle('error', !!msg);
  if (err)    err.textContent = msg || '';
}

function clearErrors() {
  ['full_name','phone','email','subject','body'].forEach(f => setError(f, ''));
  globalErr.classList.add('hidden');
  globalErr.textContent = '';
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePhone(phone) {
  return /^\+7 \(\d{3}\) \d{3} \d{2}-\d{2}$/.test(phone);
}

function validateForm(data) {
  let valid = true;

  if (data.full_name.trim().split(/\s+/).length < 2) {
    setError('full_name', 'Укажите фамилию и имя');
    valid = false;
  }
  if (!validatePhone(data.phone)) {
    setError('phone', 'Формат: +7 (xxx) xxx xx-xx');
    valid = false;
  }
  if (!validateEmail(data.email)) {
    setError('email', 'Введите корректный e-mail');
    valid = false;
  }
  if (data.subject.trim().length < 5) {
    setError('subject', 'Тема слишком короткая (мин. 5 символов)');
    valid = false;
  }
  if (data.body.trim().length < 20) {
    setError('body', 'Текст слишком короткий (мин. 20 символов)');
    valid = false;
  }
  return valid;
}

form.addEventListener('submit', async function (e) {
  e.preventDefault();
  clearErrors();

  const data = {
    full_name: document.getElementById('full_name').value,
    phone:     document.getElementById('phone').value,
    email:     document.getElementById('email').value,
    subject:   document.getElementById('subject').value,
    body:      document.getElementById('body').value,
  };

  if (!validateForm(data)) return;

  const submitBtn = document.getElementById('submit-btn');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Отправка...';

  try {
    const res = await fetch('/api/appeals/', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(data),
    });

    const json = await res.json();

    if (!res.ok) {
      // Handle validation errors from backend
      if (json.detail && Array.isArray(json.detail)) {
        json.detail.forEach(err => {
          const field = err.loc?.[err.loc.length - 1];
          if (field) setError(field, err.msg);
        });
      } else {
        globalErr.textContent = json.detail || 'Ошибка при отправке обращения';
        globalErr.classList.remove('hidden');
      }
      return;
    }

    // Success
    document.getElementById('appeal-id').textContent = `#${json.id}`;
    form.classList.add('hidden');
    successEl.classList.remove('hidden');

  } catch (err) {
    globalErr.textContent = 'Ошибка соединения с сервером. Попробуйте позже.';
    globalErr.classList.remove('hidden');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Отправить обращение';
  }
});

document.getElementById('new-appeal-btn').addEventListener('click', function () {
  form.reset();
  phoneInput.value = '';
  clearErrors();
  form.classList.remove('hidden');
  successEl.classList.add('hidden');
});
