import { fetchState, joinRoom, placePixel } from './api.js';
import { GAME_CONFIG } from './config.js';
import { createPalette, setMessage, setYear } from './ui.js';

const state = {
  username: '',
  room: '',
  selectedColor: GAME_CONFIG.palette[0],
  joined: false,
};

const elements = {
  year: document.getElementById('year'),
  joinForm: document.getElementById('gameJoinForm'),
  username: document.getElementById('gameUsername'),
  room: document.getElementById('gameRoom'),
  roomLabel: document.getElementById('roomLabel'),
  grid: document.getElementById('gameGrid'),
  message: document.getElementById('gameMessage'),
  refreshBtn: document.getElementById('refreshBtn'),
  palette: document.getElementById('palette'),
};

function cellId(x, y) {
  return `cell-${x}-${y}`;
}

function buildGrid(size) {
  elements.grid.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
  elements.grid.innerHTML = '';

  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const cell = document.createElement('button');
      cell.type = 'button';
      cell.className = 'game-cell';
      cell.id = cellId(x, y);
      cell.style.backgroundColor = GAME_CONFIG.defaultColor;
      cell.setAttribute('aria-label', `Pixel ${x}, ${y}`);

      cell.addEventListener('click', async () => {
        if (!state.joined) {
          setMessage(elements.message, 'Join a room first.');
          return;
        }

        const previousColor = cell.style.backgroundColor;
        cell.style.backgroundColor = state.selectedColor;

        try {
          await placePixel({
            room: state.room,
            x,
            y,
            color: state.selectedColor,
            username: state.username,
          });
          setMessage(elements.message, `Placed pixel at (${x}, ${y}).`);
        } catch (error) {
          cell.style.backgroundColor = previousColor;
          setMessage(elements.message, `Could not place pixel: ${error.message}`);
        }
      });

      elements.grid.appendChild(cell);
    }
  }
}

function applyPixels(pixels) {
  if (!Array.isArray(pixels)) return;

  pixels.forEach((px) => {
    if (typeof px?.x !== 'number' || typeof px?.y !== 'number' || !px?.color) return;
    const cell = document.getElementById(cellId(px.x, px.y));
    if (cell) cell.style.backgroundColor = px.color;
  });
}

async function refreshBoard() {
  if (!state.room) return;

  try {
    const data = await fetchState(state.room);
    applyPixels(data.pixels);
    setMessage(elements.message, 'Board refreshed.');
  } catch (error) {
    setMessage(elements.message, `Could not refresh board: ${error.message}`);
  }
}

function setupJoinForm() {
  elements.joinForm?.addEventListener('submit', async (event) => {
    event.preventDefault();

    const username = elements.username?.value?.trim();
    const room = elements.room?.value?.trim();

    if (!username || !room) {
      setMessage(elements.message, 'Please provide username and room.');
      return;
    }

    try {
      await joinRoom({ username, room });
      state.username = username;
      state.room = room;
      state.joined = true;
      elements.roomLabel.textContent = `Room: ${room} • User: ${username}`;
      setMessage(elements.message, 'Joined room successfully.');
      await refreshBoard();
    } catch (error) {
      setMessage(elements.message, `Could not join room: ${error.message}`);
    }
  });
}

function setupRefreshButton() {
  elements.refreshBtn?.addEventListener('click', refreshBoard);
}

function setupPalette() {
  createPalette(elements.palette, GAME_CONFIG.palette, (color) => {
    state.selectedColor = color;
    setMessage(elements.message, `Selected color ${color}.`);
  });
}

function init() {
  setYear(elements.year);
  buildGrid(GAME_CONFIG.gridSize);
  setupJoinForm();
  setupRefreshButton();
  setupPalette();
}

init();
