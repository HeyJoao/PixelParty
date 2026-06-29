"""
game_logic.py — Lógica central do jogo.

Conceitos acadêmicos aplicados:
  1. Herança + Classe Abstrata (abc): `Partida` é abstrata; `PartidaSolo` e
     `PartidaMultiplayer` herdam dela e implementam o método abstrato `iniciar()`.
  2. Composição: `BancoDeImagens` contém uma lista de objetos `ImagemJogo`.
  3. Hashing / Dicionário: `lobby` é um dict { PIN(str) -> Sala } que vive
     na memória do servidor enquanto o processo está ativo.
  4. Consumo de API: `buscar_imagem_api()` usa `requests` para obter imagens
     aleatórias de uma API externa (Picsum/Lorem Picsum, gratuita e sem key).
"""

import random
import string
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto  # Faltou importar isso!
from typing import Optional


import requests

# Constantes do Jogo
RODADAS_PADRAO = 5
TEMPO_RODADA = 30
VIDAS_INICIAIS = 3  # Faltou definir as vidas!

# Status para controlar se o jogador já terminou a rodada
class StatusJogador(Enum):
    ATIVO = auto()
    DONE = auto()

# ---------------------------------------------------------------------------
# 1. Classe de Dados: ImagemJogo
#    Representa uma imagem em memória durante a partida (≠ model do banco).
# ---------------------------------------------------------------------------

@dataclass
class ImagemJogo:
    url: str
    gabaritos: list[str]  # Lista de palavras corretas

    def validar_palpite(self, palpite: str) -> bool:
        """Verifica se o palpite do jogador está na lista de gabaritos válidos."""
        return palpite.strip().lower() in self.gabaritos

    def para_cliente(self) -> dict:
        """Apenas a URL vai para o Front-end! Segurança total."""
        return {"url": self.url}

# ---------------------------------------------------------------------------
# 2. Composição: BancoDeImagens contém uma lista de ImagemJogo
# ---------------------------------------------------------------------------

class BancoDeImagens:
    """
    Composição: BancoDeImagens É COMPOSTO por objetos ImagemJogo.
    Se o BancoDeImagens for destruído, suas imagens também são (sem existência
    independente no contexto de uma partida).
    """

    def __init__(self):
        self._imagens: list[ImagemJogo] = []

    def adicionar(self, imagem: ImagemJogo) -> None:
        self._imagens.append(imagem)

    def embaralhar(self) -> None:
        random.shuffle(self._imagens)

    def proxima(self) -> Optional[ImagemJogo]:
        """Remove e retorna a próxima imagem da fila."""
        return self._imagens.pop(0) if self._imagens else None

    def esta_vazia(self) -> bool:
        return len(self._imagens) == 0

    def __len__(self) -> int:
        return len(self._imagens)


# ---------------------------------------------------------------------------
# 4. Carregamento do banco SQLite → BancoDeImagens (Decision #5)
# ---------------------------------------------------------------------------

def carregar_banco_do_sqlite(tema_id: Optional[int] = None,
                              limite: int = RODADAS_PADRAO) -> "BancoDeImagens":
    """
    Carrega imagens do SQLite e retorna um BancoDeImagens populado.

    Importação local para evitar circular import com models.py / app.py.
    `tema_id=None` carrega imagens de todos os temas disponíveis.
    """

    from models import db, Imagem, TemaCustomizado
    banco = BancoDeImagens()

    query = Imagem.query
    if tema_id is not None:
        query = query.filter_by(tema_id=tema_id)

    imagens_db = query.order_by(Imagem.id).all()

    if not imagens_db:
        return banco   # banco vazio; app.py trata este caso

    random.shuffle(imagens_db)
    for img in imagens_db[:limite]:
        banco.adicionar(
            ImagemJogo(
                url=img.url_imagem,
                gabaritos=img.lista_gabaritos(),   # método de models.py
            )
        )

    return banco

# ---------------------------------------------------------------------------
# 5. Classe abstrata: Partida (ABC) — requisito acadêmico
# ---------------------------------------------------------------------------

class Partida(ABC):
    """
    Classe base ABSTRATA para qualquer modo de jogo.
    `iniciar()` é abstrato — cada subclasse define o comportamento de início.
    """

    def __init__(self, total_rodadas: int = RODADAS_PADRAO, tema_id: Optional[int] = None):
        self.total_rodadas:   int = total_rodadas
        self.rodada_atual:    int = 0
        self.tema_id:         Optional[int] = tema_id
        self.banco:           Optional[BancoDeImagens] = None
        self.imagem_atual:    Optional[ImagemJogo] = None
        self.encerrada:       bool = False

    @abstractmethod
    def iniciar(self) -> dict:
        """
        Inicializa a partida e retorna os dados da 1ª imagem para o cliente
        (sem expor gabaritos).
        """
        ...

    def _carregar_banco(self) -> None:
        """Popula `self.banco` a partir do SQLite."""
        self.banco = carregar_banco_do_sqlite(
            tema_id=self.tema_id,
            limite=self.total_rodadas,
        )

    def _avancar_imagem(self) -> Optional[ImagemJogo]:
        """Pega a próxima imagem da fila e atualiza `imagem_atual`."""
        if self.banco is None or self.banco.esta_vazia():
            return None
        self.imagem_atual = self.banco.proxima()
        self.rodada_atual += 1
        return self.imagem_atual

    def calcular_pontos(self, vidas_restantes: int) -> int:
        """
        Fórmula canônica de pontuação:
        3 vidas = 30 pts | 2 vidas = 20 pts | 1 vida = 10 pts
        """
        return max(vidas_restantes, 0) * 10

    @property
    def partida_encerrada(self) -> bool:
        """True quando todas as rodadas foram jogadas."""
        return self.rodada_atual >= self.total_rodadas


# ---------------------------------------------------------------------------
# 5a. PartidaSolo
# ---------------------------------------------------------------------------

class PartidaSolo(Partida):
    """Partida para um único jogador. Herda de Partida."""

    def __init__(self, nickname: str,
                 total_rodadas: int = RODADAS_PADRAO,
                 tema_id: Optional[int] = None):
        super().__init__(total_rodadas=total_rodadas, tema_id=tema_id)
        self.nickname:  str = nickname
        self.pontuacao: int = 0
        self.vidas:     int = VIDAS_INICIAIS   # SERVIDOR controla as vidas

    def iniciar(self) -> dict:
        """Carrega banco e retorna dados da 1ª imagem."""
        self._carregar_banco()
        self._avancar_imagem()
        return self._estado_para_cliente()

    def processar_palpite(self, palpite: str) -> dict:
        """
        Processa um palpite recebido do cliente.
        O cliente envia APENAS o texto — gabarito e vidas ficam aqui.
        """
        if self.imagem_atual is None or self.encerrada:
            return {"erro": "Nenhuma partida ativa."}

        acertou = self.imagem_atual.validar_palpite(palpite)

        if acertou:
            pontos = self.calcular_pontos(self.vidas)
            self.pontuacao += pontos

            # Avança para próxima imagem ou encerra
            proxima = self._avancar_imagem()
            if proxima is None or self.partida_encerrada:
                self.encerrada = True
                return {
                    "resultado":      "acerto",
                    "pontos_ganhos":  pontos,
                    "pontuacao_total": self.pontuacao,
                    "jogo_encerrado": True,
                    "proxima_imagem": None,
                }

            # Reseta vidas para a nova rodada
            self.vidas = VIDAS_INICIAIS
            return {
                "resultado":      "acerto",
                "pontos_ganhos":  pontos,
                "pontuacao_total": self.pontuacao,
                "jogo_encerrado": False,
                "proxima_imagem": self.imagem_atual.para_cliente(),
                "vidas":          self.vidas,
            }

        # --- Erro: único tipo de erro, sem distinção ---
        self.vidas -= 1
        eliminado = self.vidas <= 0

        if eliminado:
            # Zera vidas: avança rodada mesmo sem acertar
            proxima = self._avancar_imagem()
            if proxima is None or self.partida_encerrada:
                self.encerrada = True
                return {
                    "resultado":      "erro",
                    "revelar_azulejo": True,
                    "vidas_restantes": 0,
                    "eliminado_rodada": True,
                    "jogo_encerrado":  True,
                    "pontuacao_total": self.pontuacao,
                    "proxima_imagem":  None,
                }
            self.vidas = VIDAS_INICIAIS
            return {
                "resultado":       "erro",
                "revelar_azulejo": True,
                "vidas_restantes": 0,
                "eliminado_rodada": True,
                "jogo_encerrado":  False,
                "proxima_imagem":  self.imagem_atual.para_cliente(),
                "vidas":           self.vidas,
            }

        return {
            "resultado":       "erro",
            "revelar_azulejo": True,      # sempre revela azulejo no erro
            "vidas_restantes": self.vidas,
            "eliminado_rodada": False,
            "jogo_encerrado":  False,
        }

    def _estado_para_cliente(self) -> dict:
        return {
            "modo":          "solo",
            "jogador":       self.nickname,
            "vidas":         self.vidas,
            "rodada_atual":  self.rodada_atual,
            "total_rodadas": self.total_rodadas,
            "imagem":        self.imagem_atual.para_cliente() if self.imagem_atual else None,
        }


# ---------------------------------------------------------------------------
# 5b. PartidaMultiplayer
# ---------------------------------------------------------------------------

@dataclass
class EstadoJogador:
    """
    Estado individual de um jogador dentro de uma rodada multiplayer.
    Encapsula vidas e status — tudo no servidor de forma segura.
    """
    nickname:   str
    vidas:      int   = field(default_factory=lambda: VIDAS_INICIAIS)
    pontuacao:  int   = 0
    status:     StatusJogador = field(default=StatusJogador.ATIVO)

    def marcar_done(self) -> None:
        self.status = StatusJogador.DONE

    def esta_ativo(self) -> bool:
        return self.status == StatusJogador.ATIVO

    def to_dict(self) -> dict:
        """Serialização segura para broadcast (sem gabaritos)."""
        return {
            "nickname":  self.nickname,
            "vidas":     self.vidas,
            "pontuacao": self.pontuacao,
            "status":    self.status.name,
        }


class PartidaMultiplayer(Partida):
    """
    Partida simultânea para múltiplos jogadores.
    Rodada avança apenas quando TODOS os jogadores estão com status DONE.
    """

    def __init__(self, sala_id: str, nicknames: list[str],
                 total_rodadas: int = RODADAS_PADRAO,
                 tema_id: Optional[int] = None):
        super().__init__(total_rodadas=total_rodadas, tema_id=tema_id)
        self.sala_id = sala_id

        # Dicionário { nickname → EstadoJogador } — Hashing (requisito acadêmico)
        self.jogadores: dict[str, EstadoJogador] = {
            nick: EstadoJogador(nickname=nick) for nick in nicknames
        }

    def iniciar(self) -> dict:
        """Carrega banco e retorna estado inicial para broadcast."""
        self._carregar_banco()
        self._avancar_imagem()
        self._resetar_estados_rodada()
        return self._estado_broadcast()

    def processar_palpite(self, nickname: str, palpite: str) -> dict:
        """
        Processa o palpite de UM jogador.
        O cliente envia apenas nickname + texto do palpite — nada mais.
        """
        estado = self.jogadores.get(nickname)
        if estado is None:
            return {"erro": "Jogador não encontrado na partida."}

        if not estado.esta_ativo():
            return {"erro": "Jogador já finalizou esta rodada."}

        if self.imagem_atual is None or self.encerrada:
            return {"erro": "Nenhuma rodada ativa."}

        acertou = self.imagem_atual.validar_palpite(palpite)

        if acertou:
            pontos = self.calcular_pontos(estado.vidas)
            estado.pontuacao += pontos
            estado.marcar_done()

            resposta_individual = {
                "resultado":     "acerto",
                "pontos_ganhos": pontos,
                "vidas":         estado.vidas,
            }
        else:
            # Erro: -1 vida, revela azulejo
            estado.vidas -= 1
            eliminado_rodada = estado.vidas <= 0

            if eliminado_rodada:
                estado.marcar_done()

            resposta_individual = {
                "resultado":       "erro",
                "revelar_azulejo": True,
                "vidas_restantes": estado.vidas,
                "eliminado_rodada": eliminado_rodada,
            }

        # Verifica se TODOS terminaram esta rodada
        todos_done = all(not e.esta_ativo() for e in self.jogadores.values())
        broadcast = None

        if todos_done:
            broadcast = self._avancar_rodada_multipayer()

        return {
            "resposta_individual": resposta_individual,
            "broadcast":           broadcast,
            "placar_parcial":      [e.to_dict() for e in self.jogadores.values()],
        }

    def _avancar_rodada_multipayer(self) -> dict:
        """
        Chamado quando todos os jogadores estão DONE.
        Avança para a próxima imagem ou encerra a partida.
        """
        proxima = self._avancar_imagem()
        partida_fim = (proxima is None or self.partida_encerrada)

        if partida_fim:
            self.encerrada = True
            return {
                "evento":          "partida_encerrada",
                "placar_final":    [e.to_dict() for e in self.jogadores.values()],
            }

        self._resetar_estados_rodada()
        return {
            "evento":         "nova_rodada",
            "rodada_atual":   self.rodada_atual,
            "total_rodadas":  self.total_rodadas,
            "imagem":         self.imagem_atual.para_cliente(),
            "placar_parcial": [e.to_dict() for e in self.jogadores.values()],
        }

    def _resetar_estados_rodada(self) -> None:
        """Reseta vidas e status de todos os jogadores para a nova rodada."""
        for estado in self.jogadores.values():
            estado.vidas  = VIDAS_INICIAIS
            estado.status = StatusJogador.ATIVO

    def _estado_broadcast(self) -> dict:
        """Estado inicial da partida para broadcast a todos na sala."""
        return {
            "modo":           "multiplayer",
            "sala_id":        self.sala_id,
            "rodada_atual":   self.rodada_atual,
            "total_rodadas":  self.total_rodadas,
            "imagem":         self.imagem_atual.para_cliente() if self.imagem_atual else None,
            "jogadores":      [e.to_dict() for e in self.jogadores.values()],
        }

    def pontuacao_final(self) -> list[dict]:
        """Retorna placar final ordenado por pontuação."""
        return sorted(
            [e.to_dict() for e in self.jogadores.values()],
            key=lambda x: x["pontuacao"],
            reverse=True,
        )
    def aplicar_timeout_rodada(self):
        """Marca todos os jogadores ativos como DONE e finaliza a rodada quando o tempo esgota."""
        for nick, estado in self.jogadores.items():
            if estado.esta_ativo():
                estado.marcar_done()
            
        # Invoca o nome EXATO do teu método para avançar a rodada
        return {"broadcast": self._avancar_rodada_multipayer()}


# ---------------------------------------------------------------------------
# 6. Lobby Global — dicionário em memória (Requisito acadêmico)
#    Estrutura: { PIN(str) → Sala }
# ---------------------------------------------------------------------------

@dataclass
class Sala:
    """
    Representa uma sala no lobby.
    Armazena a instância `partida` ativa para manter o estado no back-end.
    """
    pin:      str
    host:     str
    tema_id:  Optional[int]        = None
    jogadores: list[str]           = field(default_factory=list)
    ativa:    bool                 = False
    partida:  Optional[PartidaMultiplayer] = field(default=None, repr=False)
    sid_para_nickname: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pin":      self.pin,
            "host":     self.host,
            "tema_id":  self.tema_id,
            "jogadores": self.jogadores,
            "ativa":    self.ativa,
        }


# Lobby global: chave = PIN, valor = Sala
lobby: dict[str, Sala] = {}


def _gerar_pin(tamanho: int = 6) -> str:
    """Gera PIN alfanumérico único não existente no lobby."""
    while True:
        pin = "".join(random.choices(string.ascii_uppercase + string.digits, k=tamanho))
        if pin not in lobby:
            return pin


def criar_sala(nickname: str, tema_id: Optional[int] = None) -> tuple[str, Sala]:
    """
    Cria sala, registra no lobby e retorna (pin, sala).
    Acesso O(1) por hashing do dicionário.
    """
    pin  = _gerar_pin()
    sala = Sala(pin=pin, host=nickname, tema_id=tema_id, jogadores=[nickname])
    lobby[pin] = sala
    return pin, sala


def entrar_sala(pin: str, nickname: str) -> dict:
    """
    Adiciona jogador a sala existente.
    Retorna erro se: sala inexistente ou partida já ativa.
    """
    if pin not in lobby:
        return {"erro": "Sala não encontrada. Verifique o PIN."}

    sala = lobby[pin]

    if sala.ativa:
        return {"erro": "Partida já iniciada. Aguarde a próxima."}

    if nickname not in sala.jogadores:
        sala.jogadores.append(nickname)

    return {"sala": sala}


def iniciar_partida_sala(pin: str, tema_id: Optional[int] = None,
                         total_rodadas: int = RODADAS_PADRAO) -> tuple[bool, any]:
    """
    Inicializa a PartidaMultiplayer, armazena no objeto Sala
    e marca a sala como ativa para travar novos entrantes.
    """
    if pin not in lobby:
        return False, "Sala não encontrada."

    sala = lobby[pin]

    if sala.ativa:
        return False, "Partida já em andamento."
        
    # Se um novo tema_id foi passado no clique, atualiza a sala
    if tema_id is not None:
        sala.tema_id = tema_id

    partida = PartidaMultiplayer(
        sala_id=pin,
        nicknames=sala.jogadores,
        total_rodadas=total_rodadas,
        tema_id=sala.tema_id,
    )

    estado_inicial = partida.iniciar()

    if estado_inicial.get("imagem") is None:
        return False, "Nenhuma imagem disponível para este tema. Cadastre imagens antes de iniciar."

    sala.partida = partida   # persiste a instância na Sala
    sala.ativa   = True      # trava o lobby

    return True, estado_inicial


def remover_sala(pin: str) -> None:
    """Remove a sala do lobby ao fim da partida."""
    lobby.pop(pin, None)
