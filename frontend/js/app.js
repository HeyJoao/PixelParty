const grid = document.getElementById('pixelGrid');
const yearEl = document.getElementById('year');
const joinForm = document.getElementById('joinForm');
const formMessage = document.getElementById('formMessage');
const startBtn = document.getElementById('startBtn');

const palette = ['#7c5cff', '#2de2e6', '#f9f871', '#ff6ad5', '#6dff9e'];

function createPixelGrid(size = 12) {
  if (!grid) return;

  const total = size * size;

  for (let i = 0; i < total; i += 1) {
    const cell = document.createElement('div');
    cell.className = 'pixel';

    cell.addEventListener('mouseenter', () => {
      const color = palette[Math.floor(Math.random() * palette.length)];
      cell.style.backgroundColor = color;
      cell.style.boxShadow = `0 0 8px ${color}80`;
    });

    cell.addEventListener('mouseleave', () => {
      cell.style.boxShadow = 'none';
    });

    grid.appendChild(cell);
  }
}

function setupForm() {
  if (!joinForm) return;

  joinForm.addEventListener('submit', (event) => {
    event.preventDefault();

    const username = document.getElementById('username')?.value?.trim();
    const room = document.getElementById('room')?.value?.trim();

    if (!username || !room) {
      formMessage.textContent = 'Please fill in both fields.';
      return;
    }

    const query = new URLSearchParams({ username, room });
    window.location.href = `./game.html?${query.toString()}`;
  });
}

function setupStartButton() {
  if (!startBtn) return;

  startBtn.addEventListener('click', () => {
    const target = document.getElementById('join');
    target?.scrollIntoView({ behavior: 'smooth' });
  });
}

function setYear() {
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }
}

createPixelGrid();
setupForm();
setupStartButton();
setYear();
