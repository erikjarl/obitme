const PASSWORD = 'Bergsget432';
const FORM = document.getElementById('loginForm');

if (FORM) {
  FORM.addEventListener('submit', (event) => {
    event.preventDefault();
    const password = document.getElementById('password').value;
    const error = document.getElementById('loginError');
    if (password === PASSWORD) {
      sessionStorage.setItem('jarlAdamssonAccess', 'granted');
      window.location.href = './portal.html';
    } else {
      error.hidden = false;
    }
  });
}

if (window.location.pathname.endsWith('portal.html') || window.location.pathname.endsWith('psykologidashboard.html') || window.location.pathname.endsWith('familjeekonomi.html') || window.location.pathname.endsWith('varuovervakare.html')) {
  if (sessionStorage.getItem('jarlAdamssonAccess') !== 'granted') {
    window.location.href = './index.html';
  }
}
