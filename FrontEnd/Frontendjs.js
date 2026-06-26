const homeScreen = document.getElementById("homeScreen");
const gameScreen = document.getElementById("gameScreen");
const rankingScreen = document.getElementById("rankingScreen");
const createMatchScreen = document.getElementById("createMatchScreen");

const playBtn = document.getElementById("playBtn");
const rankingBtn = document.getElementById("rankingBtn");
const createMatchBtn = document.getElementById("createMatchBtn");

const backBtn = document.getElementById("backBtn");
const restartBtn = document.getElementById("restartBtn");
const rankingBackBtn = document.getElementById("rankingBackBtn");
const createBackBtn = document.getElementById("createBackBtn");

const clearRankingBtn = document.getElementById("clearRankingBtn");

const usernameInput = document.getElementById("usernameInput");

const timerValueEl = document.getElementById("timerValue");
const scoreValueEl = document.getElementById("scoreValue");
const randomImageEl = document.getElementById("randomImage");
const guessInput = document.getElementById("guessInput");
const submitGuessBtn = document.getElementById("submitGuessBtn");
const statusMessage = document.getElementById("statusMessage");

const rankingBody = document.getElementById("rankingBody");
const rankingCount = document.getElementById("rankingCount");

const themeSelect = document.getElementById("themeSelect");
const roundsInput = document.getElementById("roundsInput");
const roomPassword = document.getElementById("roomPassword");
const generateRoomBtn = document.getElementById("generateRoomBtn");
const copyRoomCodeBtn = document.getElementById("copyRoomCodeBtn");
const roomCodeText = document.getElementById("roomCodeText");

const RANKING_KEY = "pixelparty_ranking_bestscore";
const ROOM_CONFIG_KEY = "pixelparty_room_config";

let score = 0;
let timeLeft = 30;
let timerInterval = null;
let gameOver = false;
let currentAnswerPT = "";
let isLoading = false;
let currentPlayer = "";

function normalizeText(text) {
  return (text || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function showScreen(screen) {
  homeScreen.classList.add("hidden");
  gameScreen.classList.add("hidden");
  rankingScreen.classList.add("hidden");
  createMatchScreen.classList.add("hidden");
  screen.classList.remove("hidden");
}

/* ------------------ Ranking ------------------ */
function getRankingData() {
  const raw = localStorage.getItem(RANKING_KEY);
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function saveRankingData(data) {
  localStorage.setItem(RANKING_KEY, JSON.stringify(data));
}

function upsertBestScore(playerName, points) {
  const ranking = getRankingData();
  const oldScore = ranking[playerName] || 0;
  if (points > oldScore) {
    ranking[playerName] = points;
    saveRankingData(ranking);
  }
}

function renderRanking() {
  const ranking = getRankingData();
  const entries = Object.entries(ranking)
    .map(([name, points]) => ({ name, points }))
    .sort((a, b) => b.points - a.points);

  rankingBody.innerHTML = "";

  if (!entries.length) {
    rankingBody.innerHTML = `<tr><td colspan="2">Sem pontuações ainda.</td></tr>`;
    rankingCount.textContent = "0";
    return;
  }

  entries.forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${item.name}</td><td>${item.points}</td>`;
    rankingBody.appendChild(tr);
  });

  rankingCount.textContent = String(entries.length);
}

function clearRanking() {
  localStorage.removeItem(RANKING_KEY);
  renderRanking();
}

/* ------------------ Game ------------------ */
function updateScore() {
  scoreValueEl.textContent = score;
}

function updateTimer() {
  timerValueEl.textContent = timeLeft;
}

function endByTimeout() {
  gameOver = true;
  clearInterval(timerInterval);
  timerInterval = null;
  statusMessage.textContent = "⛔ Tempo esgotado!";
  guessInput.disabled = true;
  submitGuessBtn.disabled = true;

  upsertBestScore(currentPlayer, score);
}

function startTimer() {
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    timeLeft -= 1;
    if (timeLeft <= 0) {
      timeLeft = 0;
      updateTimer();
      endByTimeout();
      return;
    }
    updateTimer();
  }, 1000);
}

async function fetchDogImage() {
  const res = await fetch("https://dog.ceo/api/breeds/image/random");
  if (!res.ok) throw new Error("Erro ao buscar cachorro");
  const data = await res.json();
  return data.message;
}

async function fetchCatImage() {
  const res = await fetch("https://api.thecatapi.com/v1/images/search");
  if (!res.ok) throw new Error("Erro ao buscar gato");
  const data = await res.json();
  return data?.[0]?.url;
}

function fetchCarImage() {
  const sig = Date.now();
  return `https://picsum.photos/seed/car-${sig}/400/400`;
}

async function loadNextImage() {
  isLoading = true;
  guessInput.disabled = true;
  submitGuessBtn.disabled = true;
  statusMessage.textContent = "Carregando imagem...";

  try {
    const rounds = [
      { type: "cachorro", loader: fetchDogImage },
      { type: "gato", loader: fetchCatImage },
      { type: "carro", loader: fetchCarImage }
    ];

    const selected = rounds[Math.floor(Math.random() * rounds.length)];
    const imageUrl = await selected.loader();

    randomImageEl.src = imageUrl;
    randomImageEl.alt = selected.type;
    currentAnswerPT = selected.type;

    statusMessage.textContent = "Imagem pronta! Digite seu chute.";
  } catch (error) {
    console.error(error);
    statusMessage.textContent = "Erro ao carregar imagem. Tente reiniciar.";
    currentAnswerPT = "";
  } finally {
    isLoading = false;
    if (!gameOver) {
      guessInput.disabled = false;
      submitGuessBtn.disabled = false;
      guessInput.focus();
    }
  }
}

function isCorrectGuess(guess, answer) {
  const g = normalizeText(guess);
  const a = normalizeText(answer);

  if (a === "cachorro") return ["cachorro", "cao", "cão", "dog"].includes(g);
  if (a === "gato") return ["gato", "cat"].includes(g);
  if (a === "carro")
    return ["carro", "automovel", "automóvel", "veiculo", "veículo"].includes(g);

  return g === a;
}

async function submitGuess() {
  if (gameOver || isLoading) return;

  const guess = guessInput.value;
  if (!normalizeText(guess)) {
    statusMessage.textContent = "Digite um chute antes de enviar.";
    return;
  }

  if (!currentAnswerPT) {
    statusMessage.textContent = "Aguardando imagem...";
    return;
  }

  if (isCorrectGuess(guess, currentAnswerPT)) {
    score += 1;
    updateScore();
    statusMessage.textContent = "✅ Acertou! Próxima imagem...";
    guessInput.value = "";
    await loadNextImage();
  } else {
    statusMessage.textContent = "❌ Errou! Tente novamente.";
  }
}

async function resetRound() {
  gameOver = false;
  timeLeft = 30;
  currentAnswerPT = "";
  statusMessage.textContent = "";
  guessInput.value = "";
  guessInput.disabled = false;
  submitGuessBtn.disabled = false;

  updateTimer();
  await loadNextImage();
  startTimer();
}

/* ------------------ Create Match ------------------ */
function generateRoomCode(size = 6) {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let code = "";
  for (let i = 0; i < size; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

function validateCreateMatchForm() {
  const rounds = Number(roundsInput.value);

  if (!themeSelect.value) {
    alert("Selecione um tema.");
    return false;
  }

  if (!Number.isInteger(rounds) || rounds <= 0) {
    alert("Rodadas deve ser um número inteiro maior que 0.");
    roundsInput.focus();
    return false;
  }

  return true;
}

function handleGenerateRoom() {
  if (!validateCreateMatchForm()) return;

  const config = {
    theme: themeSelect.value,
    rounds: Number(roundsInput.value),
    password: roomPassword.value.trim(),
    roomCode: generateRoomCode(6),
    createdAt: new Date().toISOString()
  };

  localStorage.setItem(ROOM_CONFIG_KEY, JSON.stringify(config));
  roomCodeText.textContent = config.roomCode;
}

async function copyRoomCode() {
  const code = roomCodeText.textContent.trim();
  if (!code || code === "-") {
    alert("Gere um código primeiro.");
    return;
  }

  try {
    await navigator.clipboard.writeText(code);
    alert("Código copiado!");
  } catch {
    alert("Não foi possível copiar automaticamente.");
  }
}

/* ------------------ Navegação ------------------ */
async function goToGameScreen() {
  const username = usernameInput.value.trim();
  if (!username) {
    alert("Digite um username antes de jogar.");
    usernameInput.focus();
    return;
  }

  currentPlayer = username;
  showScreen(gameScreen);

  score = 0;
  updateScore();
  await resetRound();
}

function goToRankingScreen() {
  renderRanking();
  showScreen(rankingScreen);
}

function goToCreateMatchScreen() {
  showScreen(createMatchScreen);
}

function goToHomeScreen() {
  clearInterval(timerInterval);
  timerInterval = null;
  showScreen(homeScreen);
}

/* ------------------ Eventos ------------------ */
playBtn.addEventListener("click", goToGameScreen);
rankingBtn.addEventListener("click", goToRankingScreen);
createMatchBtn.addEventListener("click", goToCreateMatchScreen);

backBtn.addEventListener("click", goToHomeScreen);
rankingBackBtn.addEventListener("click", goToHomeScreen);
createBackBtn.addEventListener("click", goToHomeScreen);

restartBtn.addEventListener("click", resetRound);
submitGuessBtn.addEventListener("click", submitGuess);

clearRankingBtn.addEventListener("click", clearRanking);
generateRoomBtn.addEventListener("click", handleGenerateRoom);
copyRoomCodeBtn.addEventListener("click", copyRoomCode);

guessInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") submitGuess();
});

// inicial
showScreen(homeScreen);