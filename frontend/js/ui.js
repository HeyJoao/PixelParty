export function setMessage(element, text) {
  if (!element) return;
  element.textContent = text || '';
}

export function setYear(element) {
  if (!element) return;
  element.textContent = new Date().getFullYear();
}

export function createPalette(container, colors, onSelect) {
  if (!container) return;
  container.innerHTML = '';

  colors.forEach((color, index) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'color-swatch';
    btn.style.backgroundColor = color;
    btn.setAttribute('aria-label', `Select color ${color}`);

    if (index === 0) btn.classList.add('active');

    btn.addEventListener('click', () => {
      container.querySelectorAll('.color-swatch').forEach((el) => el.classList.remove('active'));
      btn.classList.add('active');
      onSelect(color);
    });

    container.appendChild(btn);
  });
}
