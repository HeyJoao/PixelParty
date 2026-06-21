"""
app.py — Ponto de entrada da aplicação.
Inicializa o Flask, o SocketIO e registra as rotas e eventos principais.
"""

import os
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, join_room, leave_room, emit

from models import db, Jogador, TemaCustomizado, Imagem
from game_logic import lobby, criar_sala, entrar_sala, PartidaSolo, PartidaMultiplayer

# ---------------------------------------------------------------------------
# Configuração da aplicação
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///jogo.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# async_mode='eventlet' obrigatório para suporte a WebSockets no deploy
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")


# ---------------------------------------------------------------------------
# Criação das tabelas (executado uma única vez na inicialização)
# ---------------------------------------------------------------------------

with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Rotas REST
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return jsonify({"status": "ok", "mensagem": "Servidor do Jogo de Adivinhação rodando!"})


@app.route("/ranking", methods=["GET"])
def ranking():
    """Retorna os 10 melhores jogadores ordenados por pontuação."""
    jogadores = (
        Jogador.query.order_by(Jogador.pontuacao_global.desc()).limit(10).all()
    )
    return jsonify([j.to_dict() for j in jogadores])


@app.route("/jogador", methods=["POST"])
def criar_jogador():
    """Cria ou recupera um jogador pelo nickname."""
    dados = request.get_json()
    nickname = dados.get("nickname", "").strip()
    if not nickname:
        return jsonify({"erro": "nickname obrigatório"}), 400

    jogador = Jogador.query.filter_by(nickname=nickname).first()
    if not jogador:
        jogador = Jogador(nickname=nickname)
        db.session.add(jogador)
        db.session.commit()

    return jsonify(jogador.to_dict()), 201


# ---------------------------------------------------------------------------
# Eventos WebSocket — Lobby Multiplayer
# ---------------------------------------------------------------------------

@socketio.on("criar_sala")
def on_criar_sala(dados):
    """
    Evento: cliente solicita criação de uma nova sala.
    O PIN gerado é a chave do dicionário `lobby` em game_logic.py.
    """
    nickname = dados.get("nickname")
    fonte = dados.get("fonte_imagens", "api")  # 'api' ou 'banco'

    pin, sala = criar_sala(nickname, fonte)
    join_room(pin)
    emit("sala_criada", {"pin": pin, "sala": sala.to_dict()})


@socketio.on("entrar_sala")
def on_entrar_sala(dados):
    """Evento: cliente entra em uma sala existente via PIN."""
    pin = dados.get("pin")
    nickname = dados.get("nickname")

    resultado = entrar_sala(pin, nickname)
    if "erro" in resultado:
        emit("erro", resultado)
        return

    join_room(pin)
    # Avisa TODOS na sala que um novo jogador chegou
    emit("jogador_entrou", {"nickname": nickname, "sala": resultado["sala"].to_dict()}, to=pin)


@socketio.on("iniciar_partida")
def on_iniciar_partida(dados):
    """Evento: host inicia a partida multiplayer."""
    pin = dados.get("pin")
    if pin not in lobby:
        emit("erro", {"mensagem": "Sala não encontrada."})
        return

    sala = lobby[pin]
    partida = PartidaMultiplayer(sala_id=pin, jogadores=sala.jogadores, fonte=sala.fonte)
    imagem_atual = partida.iniciar()

    # Broadcast para todos na sala
    emit("partida_iniciada", {"imagem": imagem_atual}, to=pin)


# ---------------------------------------------------------------------------
# Eventos WebSocket — Mecânica de Palpite
# ---------------------------------------------------------------------------

@socketio.on("palpite")
def on_palpite(dados):
    """
    Evento individual: processa o palpite de um jogador.
    - Acerto    → broadcast para toda a sala.
    - Parcial   → resposta apenas para quem errou (reveal azulejo).
    - Erro abs  → resposta apenas para quem errou (dica de texto).
    """
    pin = dados.get("pin")
    nickname = dados.get("nickname")
    texto = dados.get("texto", "").strip().lower()
    gabarito = dados.get("gabarito", "").strip().lower()
    dica_texto = dados.get("dica_texto", "")
    vidas = dados.get("vidas", 3)

    # Acerto exato
    if texto == gabarito:
        pontos = vidas * 10
        emit(
            "acerto",
            {"nickname": nickname, "pontos": pontos},
            to=pin,           # Broadcast global na sala
        )
        return

    # Palpite parcial (substring do gabarito)
    if texto and texto in gabarito:
        emit(
            "quase",
            {"mensagem": "Quase lá! Um azulejo revelado.", "revelar_azulejo": True},
            # Sem `to=pin` → resposta somente para o remetente (comportamento padrão do emit)
        )
        return

    # Erro absoluto
    emit(
        "errou",
        {"mensagem": "Errou!", "dica": dica_texto, "revelar_azulejo": False},
    )


# ---------------------------------------------------------------------------
# Ponto de entrada para desenvolvimento local
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
