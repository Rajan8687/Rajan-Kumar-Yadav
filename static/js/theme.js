function initializeIcons() {
  if (window.lucide) {
    lucide.createIcons();
  }
}

function initializeMobileMenu() {
  const menuButton = document.getElementById('mobile-menu-button');
  const mobileMenu = document.getElementById('mobile-menu');
  if (!menuButton || !mobileMenu) return;

  menuButton.addEventListener('click', function () {
    const isOpen = mobileMenu.classList.toggle('open');
    menuButton.setAttribute('aria-expanded', String(isOpen));
  });

  document.addEventListener('click', function (event) {
    if (!mobileMenu.classList.contains('open') || menuButton.contains(event.target) || mobileMenu.contains(event.target)) return;
    mobileMenu.classList.remove('open');
    menuButton.setAttribute('aria-expanded', 'false');
  });
}

initializeIcons();
initializeMobileMenu();
