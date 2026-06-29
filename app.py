"""
app.py — Ponto de entrada da aplicação.
Inicializa o Flask, o SocketIO e registra as rotas e eventos principais.
"""

import os

from flask import Flask, jsonify, request, session, make_response, render_template
from flask_socketio import SocketIO, join_room, leave_room, emit
import urllib.request
import io
from flask import send_file

from models import db, Jogador, TemaCustomizado, Imagem
from game_logic import (
    lobby,
    criar_sala,
    entrar_sala,
    iniciar_partida_sala,
    remover_sala,
    PartidaSolo,
    RODADAS_PADRAO,
)

# ---------------------------------------------------------------------------
# Configuração da aplicação
# ---------------------------------------------------------------------------

# CORREÇÃO 2: Essa linha PRECISA existir aqui para criar o objeto do servidor!
app = Flask(__name__) 

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'jogo.db')}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# async_mode='threading' para desenvolvimento local está correto
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def renderizar_home():
    return render_template("index.html")

# ==========================================
# SOLUÇÃO NATIVA PARA O CORS (COM SUPORTE A SESSÃO/COOKIES)
# ==========================================
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = make_response()
        origin = request.headers.get("Origin")
        if origin:
            res.headers.add("Access-Control-Allow-Origin", origin)
        else:
            res.headers.add("Access-Control-Allow-Origin", "*")
        res.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        res.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        res.headers.add("Access-Control-Allow-Credentials", "true") # Libera os cookies
        return res, 204

@app.after_request
def adicionar_cors(response):
    origin = request.headers.get("Origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "true" # Libera os cookies
    return response
# ==========================================

# ==========================================
# PROXY PARA BURLAR O CORS DE IMAGENS EXTERNAS
# ==========================================
@app.route("/proxy-imagem")
def proxy_imagem():
    url = request.args.get("url")
    if not url:
        return jsonify({"erro": "URL não fornecida"}), 400
    
    try:
        # Finge ser um navegador real para os servidores (TMDB) não bloquearem
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            imagem_bytes = response.read()
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
        return send_file(io.BytesIO(imagem_bytes), mimetype=content_type)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ---------------------------------------------------------------------------
# Criação das tabelas (executado uma única vez na inicialização)
# ---------------------------------------------------------------------------

with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Rotas REST
# ---------------------------------------------------------------------------

@socketio.on("entrar_sala")
def on_entrar_sala(dados):
    pin = dados.get("pin")
    nickname = dados.get("nickname")

    if not nickname:
        emit("erro", {"mensagem": "Nickname não fornecido."})
        return

    resultado = entrar_sala(pin, nickname)
    if "erro" in resultado:
        emit("erro", resultado)
    else:
        join_room(pin)
        sala = resultado["sala"]
        
        # 👇 Mapeia o request.sid para o nickname (Evita o bug de jogador não encontrado)
        if not hasattr(sala, "sid_para_nickname"):
            sala.sid_para_nickname = {}
        sala.sid_para_nickname[request.sid] = nickname

        emit("jogador_entrou", {"jogadores": sala.jogadores}, to=pin)

@socketio.on("palpite")
def on_palpite(dados):
    pin = dados.get("pin")
    palpite = dados.get("palpite")
    
    sala = lobby.get(pin)
    if not sala or not sala.partida:
        emit("erro", {"mensagem": "Sala ou partida não encontrada."})
        return

    # Tenta resgatar pelo sid_para_nickname, com fallback para o payload enviado pelo front
    nickname = getattr(sala, "sid_para_nickname", {}).get(request.sid, dados.get("nickname"))

    if not nickname:
        emit("erro", {"mensagem": "Jogador não autenticado."})
        return

    # 👇 Despacha corretamente de acordo com a assinatura do método (Corrige o TypeError do Solo)
    if isinstance(sala.partida, PartidaSolo):
        resultado = sala.partida.processar_palpite(palpite)
    else:
        resultado = sala.partida.processar_palpite(nickname, palpite)

    if "erro" in resultado:
        emit("erro", resultado)
        return

    emit("resultado_palpite", resultado["resposta_individual"])
    
    if "placar_parcial" in resultado:
        emit("placar_atualizado", {"placar": resultado["placar_parcial"]}, to=pin)

    if resultado.get("broadcast") is not None:
        broadcast = resultado["broadcast"]
        emit("evento_rodada", broadcast, to=pin)

        if broadcast.get("evento") == "partida_encerrada":
            with app.app_context():
                try:
                    for entrada in broadcast.get("placar_final", []):
                        j = Jogador.query.filter_by(nickname=entrada["nickname"]).first()
                        if j:
                            j.adicionar_pontos(entrada["pontuacao"])
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Erro ao salvar pontuação: {e}")
            remover_sala(pin)

# 👇 Novo evento para ouvir o tempo esgotado que o Frontend manda
@socketio.on("tempo_esgotado")
def on_tempo_esgotado(dados):
    pin = dados.get("pin")
    sala = lobby.get(pin)

    if not sala or not sala.partida:
        return

    if hasattr(sala.partida, "aplicar_timeout_rodada"):
        resultado = sala.partida.aplicar_timeout_rodada()
        
        if resultado and resultado.get("broadcast"):
            emit("evento_rodada", resultado["broadcast"], to=pin)

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

def _jogador_da_sessao():
    """Função auxiliar para buscar o jogador atual baseado no cookie de sessão."""
    token = session.get("session_token")
    if not token:
        return None
    return Jogador.query.filter_by(session_token=token).first()

@app.route("/temas", methods=["GET"])
def listar_temas():
    """Lista todos os temas disponíveis com contagem de imagens."""
    temas = TemaCustomizado.query.all()
    return jsonify([t.to_dict() for t in temas])


@app.route("/temas", methods=["POST"])
def criar_tema():
    """
    Cria um tema customizado.
    Requer sessão ativa — o criador é identificado pelo session_token.
    """
    jogador = _jogador_da_sessao()
    if not jogador:
        return jsonify({"erro": "Não autenticado."}), 401

    dados     = request.get_json(silent=True) or {}
    nome_tema = dados.get("nome_tema", "").strip()

    if not nome_tema:
        return jsonify({"erro": "nome_tema obrigatório"}), 400

    tema = TemaCustomizado(nome_tema=nome_tema, criador_id=jogador.id)
    db.session.add(tema)
    db.session.commit()

    return jsonify(tema.to_dict()), 201

@app.route("/temas/<int:tema_id>/imagens", methods=["POST"])
def adicionar_imagem(tema_id: int):
    """
    Adiciona uma imagem a um tema.

    Body JSON esperado:
      {
        "url_imagem":    "https://...",
        "palavras_chave": "gato,felino,bichano"
      }

    `palavras_chave` é uma string separada por vírgulas.
    O servidor normaliza e armazena como recebida; parsing ocorre em models.py.
    """
    jogador = _jogador_da_sessao()
    if not jogador:
        return jsonify({"erro": "Não autenticado."}), 401

    tema = TemaCustomizado.query.get_or_404(tema_id)
    if tema.criador_id != jogador.id:
        return jsonify({"erro": "Somente o criador pode adicionar imagens."}), 403

    dados         = request.get_json(silent=True) or {}
    url_imagem    = dados.get("url_imagem", "").strip()
    palavras_chave = dados.get("palavras_chave", "").strip()

    if not url_imagem or not palavras_chave:
        return jsonify({"erro": "url_imagem e palavras_chave são obrigatórios"}), 400

    imagem = Imagem(
        url_imagem=url_imagem,
        palavras_chave=palavras_chave,
        tema_id=tema_id,
    )
    db.session.add(imagem)
    db.session.commit()

    return jsonify(imagem.to_dict_admin()), 201


@app.route("/jogador", methods=["POST"])
def criar_jogador():
    dados = request.json or {}
    nickname = dados.get("nickname", "").strip()

    if not nickname:
        return jsonify({"erro": "Nickname obrigatório"}), 400

    jogador = Jogador.query.filter_by(nickname=nickname).first()
    if not jogador:
        jogador = Jogador(nickname=nickname)
        db.session.add(jogador)
        db.session.commit()

    # SALVA A SESSÃO AQUI (Decision #7):
    session["session_token"] = jogador.session_token

    resposta = jogador.to_dict()
    resposta["session_token"] = jogador.session_token
    return jsonify(resposta), 200


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
    pin = dados.get("pin")
    tema_id = dados.get("tema_id") # O jogador escolhe o tema do SQLite agora
    qtd_rodadas = dados.get("rodadas", RODADAS_PADRAO)

    sucesso, resultado = iniciar_partida_sala(pin, tema_id, qtd_rodadas)

    if not sucesso:
        emit("erro", {"mensagem": resultado})
        return

    # Avisa todos na sala que o jogo começou e manda a primeira imagem limpa (sem gabarito)
    emit("partida_iniciada", resultado, to=pin)


# ---------------------------------------------------------------------------
# Eventos WebSocket — Mecânica de Palpite
# ---------------------------------------------------------------------------

@socketio.on("palpite")
def on_palpite(dados):
    """
    Evento de palpite seguro: o cliente manda apenas o PIN e o texto.
    Gabarito, vidas e regras ficam restritas ao back-end.
    """
    pin = dados.get("pin")
    palpite = dados.get("palpite", "").strip()

    # 1. Verifica quem é o jogador pelo token (Segurança)
    token = session.get("session_token")
    if not token:
        emit("erro", {"mensagem": "Sessão inválida. Atualize a página."})
        return
        
    jogador = Jogador.query.filter_by(session_token=token).first()
    if not jogador:
        emit("erro", {"mensagem": "Jogador não encontrado."})
        return

    # 2. Resgata a partida atual
    sala = lobby.get(pin)
    if sala is None or sala.partida is None:
        emit("erro", {"mensagem": "Sala ou partida não encontrada."})
        return

    # 3. Processa o palpite na Lógica do Jogo (Onde as regras de negócio vivem)
    resultado = sala.partida.processar_palpite(jogador.nickname, palpite)

    if "erro" in resultado:
        emit("erro", resultado)
        return

    # 4. Resposta individual (vidas, resultado) — só para quem jogou
    emit("resultado_palpite", resultado["resposta_individual"])

    # 5. Broadcast do placar parcial para todos na sala
    emit("placar_atualizado", {"placar": resultado["placar_parcial"]}, to=pin)

    # 6. Se a rodada ou a partida acabou, avisa todos (Decision #3 e #4)
    if resultado.get("broadcast") is not None:
        broadcast = resultado["broadcast"]
        emit("evento_rodada", broadcast, to=pin)

        # Fim de partida: salva pontuações no banco (Decision #4)
        if broadcast.get("evento") == "partida_encerrada":
            with app.app_context():
                for entrada in broadcast.get("placar_final", []):
                    j = Jogador.query.filter_by(nickname=entrada["nickname"]).first()
                    if j:
                        j.adicionar_pontos(entrada["pontuacao"])
            remover_sala(pin)

# ---------------------------------------------------------------------------
# Ponto de entrada para desenvolvimento local
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    print("Lendo o bloco principal...")
    socketio.run(app, host="0.0.0.0", port=porta, allow_unsafe_werkzeug=True)
