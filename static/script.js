/**
 * script.js — PixelParty Frontend v2
 *
 * Estratégia de integração com o back-end:
 *   - Solo usa o mesmo fluxo de sala que o multi (criar_sala → iniciar_partida).
 *     A sala é privada (1 jogador). Todos os eventos socket.io são compartilhados.
 *   - Eventos emitidos pelo FRONT que o BACK ouve:
 *       criar_sala, entrar_sala, iniciar_partida, palpite
 *   - Eventos emitidos pelo BACK que o FRONT ouve:
 *       sala_criada, jogador_entrou, partida_iniciada,
 *       resultado_palpite, placar_atualizado, evento_rodada, erro
 *   - Chamadas REST: POST /jogador, GET /temas, POST /temas,
 *                    POST /temas/:id/imagens, GET /ranking, GET /sessao
 *
 * O front NUNCA gerencia vidas, gabaritos ou pontuação.
 * Toda a lógica de jogo vive no game_logic.py (servidor).
 */

"use strict";

// =============================================================
// 1. REFERÊNCIAS DO DOM
// =============================================================

const screens = {
  home:        document.getElementById("homeScreen"),
  soloConfig:  document.getElementById("soloConfigScreen"),
  join:        document.getElementById("joinScreen"),
  create:      document.getElementById("createScreen"),
  lobby:       document.getElementById("lobbyScreen"),
  game:        document.getElementById("gameScreen"),
  endSolo:     document.getElementById("endSoloScreen"),
  endMulti:    document.getElementById("endMultiScreen"),
  ranking:     document.getElementById("rankingScreen"),
  createTheme: document.getElementById("createThemeScreen"),
};

// Home
const usernameInput    = document.getElementById("usernameInput");
const menuPrincipal    = document.getElementById("menuPrincipal");
const menuJogar        = document.getElementById("menuJogar");
const homeMsg          = document.getElementById("homeMsg");

// Solo config
const temaSelectSolo   = document.getElementById("temaSelectSolo");
const rodadasSolo      = document.getElementById("rodadasSolo");
const soloMsg          = document.getElementById("soloMsg");

// Join
const pinInput         = document.getElementById("pinInput");
const joinMsg          = document.getElementById("joinMsg");

// Create
const temaSelectMulti  = document.getElementById("temaSelectMulti");
const rodadasMulti     = document.getElementById("rodadasMulti");
const createMsg        = document.getElementById("createMsg");

// Lobby
const lobbyPin         = document.getElementById("lobbyPin");
const listaJogadores   = document.getElementById("listaJogadores");
const lobbyMsg         = document.getElementById("lobbyMsg");
const btnIniciarMulti  = document.getElementById("btnIniciarMulti");

// Game
const timerBox         = document.getElementById("timerBox");
const timerVal         = document.getElementById("timerVal");
const scoreVal         = document.getElementById("scoreVal");
const vidasVal         = document.getElementById("vidasVal");
const rodadaVal        = document.getElementById("rodadaVal");
const rodadaTotal      = document.getElementById("rodadaTotal");
const gameImg          = document.getElementById("gameImg");
const guessInput       = document.getElementById("guessInput");
const statusMsg        = document.getElementById("statusMsg");
const placarMulti      = document.getElementById("placarMulti");
const placarLista      = document.getElementById("placarLista");
const btnEnviar        = document.getElementById("btnEnviar");
const btnFinalizar     = document.getElementById("btnFinalizar");

// End screens
const finalScoreSolo   = document.getElementById("finalScoreSolo");
const podiumArea       = document.getElementById("podiumArea");
const rankingBody      = document.getElementById("rankingBody");

// Create theme
const nomeTemaNovo     = document.getElementById("nomeTemaNovo");
const urlImagemNova    = document.getElementById("urlImagemNova");
const palavrasNova     = document.getElementById("palavrasNova");
const themeMsg         = document.getElementById("themeMsg");

// =============================================================
// 2. ESTADO GLOBAL DO CLIENTE
// =============================================================

const state = {
  nickname:        "",
  modoAtual:       "",      // "solo" | "multi"
  pinAtual:        "",
  ehHost:          false,
  scoreAtual:      0,
  vidasAtual:      3,
  tilesRevelados:  0,
  timerInterval:   null,
  telaAntesTema:   "home",
  selectOrigem:    null,
};

// =============================================================
// 3. SOCKET.IO
// =============================================================

const socket = io(, {
  withCredentials: true
});
// =============================================================
// 4. UTILITÁRIOS
// =============================================================

function showScreen(id) {
  Object.values(screens).forEach(s => {
    s.classList.remove("active");
    s.classList.add("hidden");
  });
  const t = screens[id];
  if (t) { t.classList.remove("hidden"); t.classList.add("active"); }
}

function showMsg(el, texto, tipo) {
  el.textContent = texto;
  el.style.color = tipo === "ok" ? "var(--success)" : "var(--danger)";
  el.classList.remove("hidden");
}
function hideMsg(el) { el.classList.add("hidden"); }

function nickOuAviso() {
  const n = usernameInput.value.trim();
  if (!n) { showMsg(homeMsg, "Digite seu apelido antes de continuar."); usernameInput.focus(); return null; }
  hideMsg(homeMsg);
  return n;
}

// =============================================================
// 5. NAVEGAÇÃO DA HOME
// =============================================================

document.getElementById("btnJogar").addEventListener("click", () => {
  menuPrincipal.classList.add("hidden");
  menuJogar.classList.remove("hidden");
});
document.getElementById("btnVoltarMenu").addEventListener("click", () => {
  menuJogar.classList.add("hidden");
  menuPrincipal.classList.remove("hidden");
});
document.getElementById("btnSolo").addEventListener("click", () => {
  if (!nickOuAviso()) return;
  carregarTemas(temaSelectSolo);
  showScreen("soloConfig");
});
document.getElementById("btnMulti").addEventListener("click", () => {
  if (!nickOuAviso()) return;
  showScreen("join");
});
document.getElementById("btnRankingMenu").addEventListener("click", () => {
  carregarRanking();
  showScreen("ranking");
});
document.getElementById("btnCriarMenu").addEventListener("click", () => {
  if (!nickOuAviso()) return;
  carregarTemas(temaSelectMulti);
  showScreen("create");
});
document.querySelectorAll(".btn-voltar-home").forEach(b => b.addEventListener("click", () => {
  pararTimer();
  menuJogar.classList.add("hidden");
  menuPrincipal.classList.remove("hidden");
  showScreen("home");
}));

// =============================================================
// 6. AUTENTICAÇÃO (REST)
// =============================================================

async function autenticar(nickname) {
  try {
    const r = await fetch("/jogador", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ nickname }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.erro || "Erro ao autenticar");
    state.nickname = d.nickname;
    return true;
  } catch (e) { console.error(e); return false; }
}

async function verificarSessao() {
  try {
    const r = await fetch("/sessao", { credentials: "include" });
    if (!r.ok) return;
    const d = await r.json();
    if (d.autenticado) { state.nickname = d.nickname; usernameInput.value = d.nickname; }
  } catch { /* silencioso */ }
}

// =============================================================
// 7. TEMAS (REST)
// =============================================================

async function carregarTemas(selectEl) {
  try {
    const r = await fetch("/temas");
    const temas = await r.json();

    while (selectEl.options.length) selectEl.remove(0);

    const optDef = document.createElement("option");
    optDef.value = "";
    optDef.textContent = temas.length ? "Selecione um tema" : "Nenhum tema — cadastre um";
    selectEl.appendChild(optDef);

    temas.forEach(t => {
      const o = document.createElement("option");
      o.value = t.id;
      o.textContent = `${t.nome_tema} (${t.total_imagens} img)`;
      selectEl.appendChild(o);
    });

    const optCad = document.createElement("option");
    optCad.value = "cadastrar";
    optCad.textContent = "➕ Cadastrar novo tema";
    selectEl.appendChild(optCad);
  } catch (e) { console.error("carregarTemas:", e); }
}

function ligarSelectCadastro(selectEl, telaOrigem) {
  selectEl.addEventListener("change", () => {
    if (selectEl.value !== "cadastrar") return;
    state.telaAntesTema = telaOrigem;
    state.selectOrigem  = selectEl;
    nomeTemaNovo.value = urlImagemNova.value = palavrasNova.value = "";
    hideMsg(themeMsg);
    showScreen("createTheme");
  });
}
ligarSelectCadastro(temaSelectSolo,  "soloConfig");
ligarSelectCadastro(temaSelectMulti, "create");

document.getElementById("btnSalvarTema").addEventListener("click", async () => {
  const nome    = nomeTemaNovo.value.trim();
  const url     = urlImagemNova.value.trim();
  const palavras = palavrasNova.value.trim();

  if (!nome) { showMsg(themeMsg, "Nome do tema é obrigatório."); return; }

  const nick = state.nickname || usernameInput.value.trim();
  const ok   = await autenticar(nick);
  if (!ok)   { showMsg(themeMsg, "Autentique-se antes de criar um tema."); return; }

  try {
    const r = await fetch("/temas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ nome_tema: nome }),
    });
    const tema = await r.json();
    if (!r.ok) throw new Error(tema.erro || "Erro ao criar tema");

    if (url && palavras) {
      const ri = await fetch(`/temas/${tema.id}/imagens`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ url_imagem: url, palavras_chave: palavras }),
      });
      if (!ri.ok) {
        const ei = await ri.json();
        showMsg(themeMsg, `Tema criado, mas erro na imagem: ${ei.erro}`);
        return;
      }
    }

    showMsg(themeMsg, `Tema "${nome}" criado com sucesso!`, "ok");
    await carregarTemas(temaSelectSolo);
    await carregarTemas(temaSelectMulti);

    if (state.selectOrigem) {
      for (const opt of state.selectOrigem.options) {
        if (String(opt.value) === String(tema.id)) { state.selectOrigem.value = opt.value; break; }
      }
    }
    setTimeout(() => showScreen(state.telaAntesTema), 900);
  } catch (e) { showMsg(themeMsg, e.message); }
});

document.getElementById("btnCancelarTema").addEventListener("click", () => {
  showScreen(state.telaAntesTema);
});

// =============================================================
// 8. MODO SOLO — usa o mesmo fluxo de sala (1 jogador)
// =============================================================

document.getElementById("btnIniciarSolo").addEventListener("click", async () => {
  hideMsg(soloMsg);
  const nick = usernameInput.value.trim();
  if (!nick) { showMsg(soloMsg, "Volte e informe seu apelido."); return; }

  const temaId  = temaSelectSolo.value;
  const rodadas = parseInt(rodadasSolo.value) || 5;

  if (!temaId || temaId === "cadastrar") {
    showMsg(soloMsg, "Selecione um tema para jogar."); return;
  }

  const ok = await autenticar(nick);
  if (!ok) { showMsg(soloMsg, "Erro ao conectar ao servidor."); return; }

  // Solo: cria sala privada de 1 jogador e inicia automaticamente
  state.modoAtual = "solo";
  state.ehHost    = true;

  socket.emit("criar_sala", {
    nickname: state.nickname,
    tema_id:  parseInt(temaId),
  });

  // Guarda as configurações para usar quando a sala for confirmada
  state._soloRodadas = rodadas;
  state._soloTemaId  = parseInt(temaId);
});

// =============================================================
// 9. MODO MULTIPLAYER — CRIAR SALA
// =============================================================

document.getElementById("btnGerarSala").addEventListener("click", async () => {
  hideMsg(createMsg);
  const nick = usernameInput.value.trim();
  if (!nick) { showMsg(createMsg, "Volte e informe seu apelido."); return; }

  const temaId = temaSelectMulti.value;
  if (!temaId || temaId === "cadastrar") {
    showMsg(createMsg, "Selecione um tema antes de gerar a sala."); return;
  }

  const ok = await autenticar(nick);
  if (!ok) { showMsg(createMsg, "Erro ao autenticar."); return; }

  state.modoAtual = "multi";
  state.ehHost    = true;

  socket.emit("criar_sala", {
    nickname: state.nickname,
    tema_id:  parseInt(temaId),
  });
});

// =============================================================
// 10. SOCKET: sala_criada
// =============================================================

socket.on("sala_criada", (dados) => {
  state.pinAtual = dados.pin;

  if (state.modoAtual === "solo") {
    // Solo: inicia a partida imediatamente sem passar pelo lobby
    socket.emit("iniciar_partida", {
      pin:     dados.pin,
      tema_id: state._soloTemaId,
      rodadas: state._soloRodadas,
    });
    return;
  }

  // Multi: vai para o lobby
  lobbyPin.textContent = dados.pin;
  atualizarListaLobby(dados.sala.jogadores, dados.sala.host);
  btnIniciarMulti.classList.remove("hidden");
  lobbyMsg.textContent = "Compartilhe o PIN com seus amigos e aguarde!";
  showScreen("lobby");
});

// =============================================================
// 11. MODO MULTIPLAYER — ENTRAR VIA PIN
// =============================================================

document.getElementById("btnEntrar").addEventListener("click", async () => {
  hideMsg(joinMsg);
  const nick = usernameInput.value.trim();
  if (!nick) { showMsg(joinMsg, "Volte e informe seu apelido."); return; }

  const pin = pinInput.value.trim().toUpperCase();
  if (pin.length !== 6) { showMsg(joinMsg, "O PIN deve ter 6 caracteres."); return; }

  const ok = await autenticar(nick);
  if (!ok) { showMsg(joinMsg, "Erro ao autenticar."); return; }

  state.modoAtual = "multi";
  state.ehHost    = false;
  state.pinAtual  = pin;

  socket.emit("entrar_sala", { pin, nickname: state.nickname });
});

socket.on("jogador_entrou", (dados) => {
  // Atualiza lista para quem já estava no lobby
  atualizarListaLobby(dados.sala.jogadores, dados.sala.host);

  // Se este cliente acabou de entrar, vai para o lobby
  const lobbyAtivo = screens.lobby.classList.contains("active");
  if (!lobbyAtivo) {
    state.pinAtual = dados.sala.pin || state.pinAtual;
    lobbyPin.textContent = state.pinAtual;
    btnIniciarMulti.classList.add("hidden");   // não é o host
    lobbyMsg.textContent = "Aguardando o host iniciar a partida…";
    showScreen("lobby");
  }
});

function atualizarListaLobby(jogadores, host) {
  listaJogadores.innerHTML = "";
  jogadores.forEach(nick => {
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="player-dot"></span>
      ${nick}
      ${nick === host ? '<span class="player-host">HOST</span>' : ""}
    `;
    listaJogadores.appendChild(li);
  });
}

document.getElementById("btnCopiarPin").addEventListener("click", () => {
  navigator.clipboard.writeText(state.pinAtual).catch(() => {});
});

// =============================================================
// 12. INICIAR PARTIDA MULTIPLAYER (HOST)
// =============================================================

btnIniciarMulti.addEventListener("click", () => {
  socket.emit("iniciar_partida", {
    pin:     state.pinAtual,
    tema_id: parseInt(temaSelectMulti.value) || null,
    rodadas: parseInt(rodadasMulti.value) || 5,
  });
});

// =============================================================
// 13. SOCKET: partida_iniciada (recebido por TODOS)
// =============================================================

socket.on("partida_iniciada", (dados) => {
  setupTelaJogo(dados);
});

// =============================================================
// 14. SETUP DA TELA DE JOGO
// =============================================================

function setupTelaJogo(dados) {
  // Reseta estado visual
  state.scoreAtual    = 0;
  state.vidasAtual    = 3;
  state.tilesRevelados = 0;

  scoreVal.textContent  = 0;
  vidasVal.textContent  = 3;
  statusMsg.textContent = "";
  guessInput.value      = "";
  guessInput.disabled   = false;
  btnEnviar.disabled    = false;

  // Rodadas
  rodadaVal.textContent   = dados.rodada_atual   || 1;
  rodadaTotal.textContent = dados.total_rodadas  || 5;

  // Timer: só no multi
  if (state.modoAtual === "multi") {
    timerBox.classList.remove("hidden");
    placarMulti.classList.remove("hidden");
    iniciarTimer(60);
    if (dados.jogadores) renderizarPlacar(dados.jogadores);
  } else {
    timerBox.classList.add("hidden");
    placarMulti.classList.add("hidden");
    pararTimer();
  }

  // 👇 CORREÇÃO: Pegando o nome correto da variável do banco de dados (url_imagem)
  const urlCorreta = dados.imagem?.url_imagem || dados.imagem?.url;
  if (urlCorreta) {
    carregarImagem(urlCorreta);
  } else {
    console.warn("Nenhuma URL de imagem recebida do servidor!");
  }

  showScreen("game");
}

// =============================================================
// 15. MECÂNICA DE AZULEJOS
// =============================================================

function carregarImagem(urlOriginal) {
  // 1. Criamos a URL apontando para o nosso servidor Python (Proxy)
  const proxyUrl = "http://127.0.0.1:5000/proxy-imagem?url=" + encodeURIComponent(urlOriginal);
  
  // 2. Avisamos o navegador para permitir o uso da imagem sem bloquear a tela
  gameImg.crossOrigin = "Anonymous"; 
  
  // 3. Colocamos a imagem para carregar usando o nosso Proxy
  gameImg.src = proxyUrl;
  
  state.tilesRevelados = 0;
  
  // Fecha todos os azulejos
  for (let i = 0; i < 6; i++) {
    document.getElementById(`tile-${i}`).classList.remove("revelado");
  }
  
  // Revela 1 azulejo inicial (conforme especificação)
  revelarAzulejo();
}

function revelarAzulejo() {
  const fechados = [];
  for (let i = 0; i < 6; i++) {
    const t = document.getElementById(`tile-${i}`);
    if (!t.classList.contains("revelado")) fechados.push(i);
  }
  if (!fechados.length) return;
  const idx = fechados[Math.floor(Math.random() * fechados.length)];
  document.getElementById(`tile-${idx}`).classList.add("revelado");
  state.tilesRevelados++;
}

function revelarTodos() {
  for (let i = 0; i < 6; i++) document.getElementById(`tile-${i}`).classList.add("revelado");
  state.tilesRevelados = 6;
}

// =============================================================
// 16. TIMER
// =============================================================

function iniciarTimer(segundos) {
  pararTimer();
  let t = segundos;
  timerVal.textContent = t;
  timerBox.style.color = "";

  state.timerInterval = setInterval(() => {
    t--;
    timerVal.textContent = t;
    if (t <= 10) timerBox.style.color = "var(--danger)";
    if (t <= 0) {
      pararTimer();
      statusMsg.textContent = "⏱ Tempo esgotado!";
      statusMsg.style.color = "var(--warn)";
      // Desabilita input — aguarda evento do servidor para avançar rodada
      guessInput.disabled = true;
      btnEnviar.disabled  = true;
    }
  }, 1000);
}

function pararTimer() {
  if (state.timerInterval) { clearInterval(state.timerInterval); state.timerInterval = null; }
  timerBox.style.color = "";
}

// =============================================================
// 17. ENVIO DE PALPITE
// =============================================================

function enviarPalpite() {
  const texto = guessInput.value.trim();
  if (!texto) return;
  guessInput.value      = "";
  statusMsg.textContent = "";

  // Em ambos os modos, o evento é "palpite" com o PIN da sala
  socket.emit("palpite", {
    pin:     state.pinAtual,
    palpite: texto,
  });
}

btnEnviar.addEventListener("click", enviarPalpite);
guessInput.addEventListener("keydown", e => { if (e.key === "Enter") enviarPalpite(); });

// =============================================================
// 18. SOCKET: resultado_palpite (individual — só para este cliente)
// =============================================================

socket.on("resultado_palpite", (dados) => {
  if (dados.resultado === "acerto") {
    revelarTodos();
    state.scoreAtual += dados.pontos_ganhos || 0;
    scoreVal.textContent = state.scoreAtual;
    statusMsg.textContent = `✅ Acertou! +${dados.pontos_ganhos || 0} pts`;
    statusMsg.style.color = "var(--success)";

    // 👇 CORREÇÃO: Buscando a URL correta da próxima imagem
    const urlProxima = dados.proxima_imagem?.url_imagem || dados.proxima_imagem?.url;
    
    if (dados.jogo_encerrado) {
      setTimeout(() => mostrarFimSolo(state.scoreAtual), 1200);
    } else if (urlProxima) {
      // Solo: avança imagem diretamente
      state.vidasAtual = dados.vidas ?? 3;
      vidasVal.textContent = state.vidasAtual;
      rodadaVal.textContent = parseInt(rodadaVal.textContent) + 1;
      setTimeout(() => {
        carregarImagem(urlProxima);
        statusMsg.textContent = "";
      }, 1000);
    }

  } else if (dados.resultado === "erro") {
    if (dados.revelar_azulejo) revelarAzulejo();

    const vidas = dados.vidas_restantes ?? (state.vidasAtual - 1);
    state.vidasAtual = Math.max(vidas, 0);
    vidasVal.textContent = state.vidasAtual;

    if (dados.eliminado_rodada) {
      statusMsg.textContent = "💀 Sem vidas! Aguardando próxima rodada…";
      statusMsg.style.color = "var(--danger)";
      guessInput.disabled = true;
      btnEnviar.disabled  = true;
    } else {
      statusMsg.textContent = `❌ Errou! ${"❤️".repeat(state.vidasAtual)}`;
      statusMsg.style.color = "var(--danger)";
    }

    // 👇 CORREÇÃO: Buscando a URL correta da próxima imagem
    const urlProxima = dados.proxima_imagem?.url_imagem || dados.proxima_imagem?.url;

    if (dados.jogo_encerrado) {
      setTimeout(() => mostrarFimSolo(state.scoreAtual), 1500);
    } else if (dados.eliminado_rodada && urlProxima) {
      // Solo: avança para próxima imagem mesmo sem acertar
      state.vidasAtual = dados.vidas ?? 3;
      vidasVal.textContent = state.vidasAtual;
      rodadaVal.textContent = parseInt(rodadaVal.textContent) + 1;
      guessInput.disabled = false;
      btnEnviar.disabled  = false;
      setTimeout(() => {
        carregarImagem(urlProxima);
        statusMsg.textContent = "";
      }, 1200);
    }
  }
});

// =============================================================
// 19. SOCKET: placar_atualizado (broadcast — todos na sala)
// =============================================================

socket.on("placar_atualizado", (dados) => {
  if (state.modoAtual === "multi") renderizarPlacar(dados.placar);
});

function renderizarPlacar(placar) {
  placarLista.innerHTML = "";
  placar.forEach(entry => {
    const li = document.createElement("li");
    const done = entry.status === "DONE";
    li.className = done ? "placar-done" : "";
    li.innerHTML = `
      <span>${entry.nickname}${done ? " ✓" : ""}</span>
      <span>${entry.pontuacao} pts ${"❤️".repeat(Math.max(entry.vidas, 0))}</span>
    `;
    placarLista.appendChild(li);
  });
}

// =============================================================
// 20. SOCKET: evento_rodada (broadcast — nova_rodada ou partida_encerrada)
// =============================================================

socket.on("evento_rodada", (dados) => {
  if (dados.evento === "nova_rodada") {
    pararTimer();

    // Reseta UI para nova rodada
    state.vidasAtual = 3;
    vidasVal.textContent   = 3;
    rodadaVal.textContent  = dados.rodada_atual;
    statusMsg.textContent  = "";
    guessInput.disabled    = false;
    btnEnviar.disabled     = false;

    const urlNova = dados.imagem?.url_imagem || dados.imagem?.url;
    if (urlNova) carregarImagem(urlNova);
    
    if (dados.placar_parcial) renderizarPlacar(dados.placar_parcial);

    if (state.modoAtual === "multi") iniciarTimer(60);

  } else if (dados.evento === "partida_encerrada") {
    pararTimer();
    if (state.modoAtual === "solo") {
      mostrarFimSolo(state.scoreAtual);
    } else {
      mostrarFimMulti(dados.placar_final || []);
    }
  }
});

// =============================================================
// 21. TELAS DE FIM DE JOGO
// =============================================================

function mostrarFimSolo(pts) {
  finalScoreSolo.textContent = pts;
  showScreen("endSolo");
}

function mostrarFimMulti(placar) {
  const ord = [...placar].sort((a, b) => b.pontuacao - a.pontuacao);
  const medalhas = ["🥇", "🥈", "🥉"];

  podiumArea.innerHTML = "";
  ord.forEach((entry, i) => {
    const div = document.createElement("div");
    div.className = "podium-item";
    div.innerHTML = `
      <span class="podium-medal">${medalhas[i] || `#${i + 1}`}</span>
      <span class="podium-nick">${entry.nickname}</span>
      <span class="podium-pts">${entry.pontuacao} pts</span>
    `;
    podiumArea.appendChild(div);
  });

  showScreen("endMulti");
}

// =============================================================
// 22. RANKING (REST)
// =============================================================

async function carregarRanking() {
  rankingBody.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--muted)">Carregando…</td></tr>`;
  try {
    const r    = await fetch("/ranking");
    const data = await r.json();

    rankingBody.innerHTML = "";
    if (!data.length) {
      rankingBody.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--muted)">Sem pontuações ainda.</td></tr>`;
      return;
    }
    data.forEach((j, i) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${i + 1}º</td><td>${j.nickname}</td><td style="color:var(--accent);font-weight:700">${j.pontuacao_global}</td>`;
      rankingBody.appendChild(tr);
    });
  } catch {
    rankingBody.innerHTML = `<tr><td colspan="3" style="color:var(--danger);text-align:center">Erro ao carregar ranking.</td></tr>`;
  }
}

document.getElementById("btnVerRanking").addEventListener("click", () => {
  carregarRanking();
  showScreen("ranking");
});

// =============================================================
// 23. FINALIZAR PARTIDA (DESISTÊNCIA)
// =============================================================

btnFinalizar.addEventListener("click", () => {
  pararTimer();
  if (state.modoAtual === "solo") {
    mostrarFimSolo(state.scoreAtual);
  } else {
    mostrarFimMulti([]);
  }
});

// =============================================================
// 24. ERROS DO SERVIDOR
// =============================================================

socket.on("erro", (dados) => {
  const msg = dados.mensagem || dados.erro || "Erro desconhecido do servidor.";
  console.error("[PixelParty] erro:", msg);

  const ativo = Object.keys(screens).find(k => screens[k].classList.contains("active"));
  const msgEls = { join: joinMsg, create: createMsg, lobby: lobbyMsg, soloConfig: soloMsg, createTheme: themeMsg };

  if (msgEls[ativo]) {
    showMsg(msgEls[ativo], msg);
  } else if (ativo === "game") {
    statusMsg.textContent = `⚠️ ${msg}`;
    statusMsg.style.color = "var(--warn)";
  } else {
    showMsg(homeMsg, msg);
    showScreen("home");
  }
});

// =============================================================
// 25. INICIALIZAÇÃO
// =============================================================

(async function init() {
  await verificarSessao();
  showScreen("home");
})();
