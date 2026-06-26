import { API_CONFIG } from './config.js';

function endpoint(path) {
  return `${API_CONFIG.baseUrl}${path}`;
}

export async function joinRoom({ username, room }) {
  const res = await fetch(endpoint(API_CONFIG.endpoints.join), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, room }),
  });

  if (!res.ok) {
    throw new Error(`Join failed (${res.status})`);
  }

  return res.json().catch(() => ({ ok: true, room, username }));
}

export async function fetchState(room) {
  const url = new URL(endpoint(API_CONFIG.endpoints.state), window.location.origin);
  url.searchParams.set('room', room);

  const res = await fetch(url.toString(), { method: 'GET' });

  if (!res.ok) {
    throw new Error(`State fetch failed (${res.status})`);
  }

  return res.json().catch(() => ({ pixels: [] }));
}

export async function placePixel({ room, x, y, color, username }) {
  const res = await fetch(endpoint(API_CONFIG.endpoints.pixel), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ room, x, y, color, username }),
  });

  if (!res.ok) {
    throw new Error(`Pixel update failed (${res.status})`);
  }

  return res.json().catch(() => ({ ok: true }));
}
