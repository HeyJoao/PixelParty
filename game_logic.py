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
from typing import Optional

import requests


# ---------------------------------------------------------------------------
# 1. Classe de Dados: ImagemJogo
#    Representa uma imagem em memória durante a partida (≠ model do banco).
# ---------------------------------------------------------------------------

@dataclass
class ImagemJogo:
    url: str
    palavra_chave: str
    dica_texto: str = ""

    def to_dict(self) -> dict:
        # Nunca expõe a palavra_chave diretamente ao cliente!
        return {"url": self.url, "dica_texto": self.dica_texto}


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
# 3. Consumo de API Externa (requests)
#    Usa Lorem Picsum (https://picsum.photos) — gratuita, sem API key.
#    Para produção, substitua pela Unsplash API com sua key.
# ---------------------------------------------------------------------------

PICSUM_URL = "https://picsum.photos/v2/list"

# Gabaritos de exemplo para associar às imagens aleatórias
_PALAVRAS_EXEMPLO = [
    "natureza", "cidade", "tecnologia", "esporte", "animais",
    "comida", "viagem", "arquitetura", "arte", "pessoas",
]


def buscar_imagem_api(quantidade: int = 5) -> BancoDeImagens:
    """
    Consome a API do Lorem Picsum para obter imagens aleatórias.
    Retorna um BancoDeImagens populado.

    Raises:
        RuntimeError: se a API estiver indisponível.
    """
    banco = BancoDeImagens()
    try:
        resposta = requests.get(
            PICSUM_URL,
            params={"limit": quantidade},
            timeout=5,
        )
        resposta.raise_for_status()
        dados = resposta.json()

        for i, item in enumerate(dados):
            imagem = ImagemJogo(
                url=f"https://picsum.photos/id/{item['id']}/800/600",
                palavra_chave=_PALAVRAS_EXEMPLO[i % len(_PALAVRAS_EXEMPLO)],
                dica_texto=f"Foto de {item.get('author', 'autor desconhecido')}",
            )
            banco.adicionar(imagem)

    except requests.RequestException as e:
        raise RuntimeError(f"Falha ao buscar imagens da API: {e}") from e

    banco.embaralhar()
    return banco


# ---------------------------------------------------------------------------
# 4. Herança + Classe Abstrata: Partida (ABC)
# ---------------------------------------------------------------------------

class Partida(ABC):
    """
    Classe base ABSTRATA para qualquer tipo de partida.
    Define a interface que TODOS os modos de jogo devem implementar.
    O método `iniciar()` é abstrato: cada subclasse define seu próprio
    comportamento de inicialização.
    """

    VIDAS_INICIAIS: int = 3

    def __init__(self, fonte: str = "api"):
        self.fonte = fonte            # 'api' ou 'banco'
        self.banco: Optional[BancoDeImagens] = None
        self.imagem_atual: Optional[ImagemJogo] = None
        self.encerrada: bool = False

    @abstractmethod
    def iniciar(self) -> dict:
        """
        Inicializa a partida e retorna os dados da primeira imagem
        (sem revelar o gabarito ao cliente).
        """
        ...

    def _carregar_banco(self) -> None:
        """Carrega o BancoDeImagens de acordo com a fonte configurada."""
        if self.fonte == "api":
            self.banco = buscar_imagem_api()
        else:
            # Fonte = banco SQLite: será implementado quando as rotas de
            # imagens customizadas estiverem prontas.
            self.banco = BancoDeImagens()

    def avancar_rodada(self) -> Optional[dict]:
        """Avança para a próxima imagem. Retorna None se o banco acabou."""
        if self.banco is None or self.banco.esta_vazia():
            self.encerrada = True
            return None
        self.imagem_atual = self.banco.proxima()
        return self.imagem_atual.to_dict()

    def calcular_pontos(self, vidas_restantes: int) -> int:
        """Regra de negócio: pontos = vidas_restantes × 10."""
        return max(vidas_restantes, 0) * 10


# ---------------------------------------------------------------------------
# 4a. Subclasse: PartidaSolo
# ---------------------------------------------------------------------------

class PartidaSolo(Partida):
    """
    Partida para um único jogador.
    Herda de Partida e implementa `iniciar()`.
    """

    def __init__(self, nickname: str, fonte: str = "api"):
        super().__init__(fonte=fonte)
        self.nickname = nickname
        self.pontuacao = 0
        self.vidas = self.VIDAS_INICIAIS

    def iniciar(self) -> dict:
        """Carrega o banco e retorna os dados da primeira imagem."""
        self._carregar_banco()
        self.imagem_atual = self.banco.proxima()
        return {
            "modo": "solo",
            "jogador": self.nickname,
            "vidas": self.vidas,
            "imagem": self.imagem_atual.to_dict() if self.imagem_atual else None,
        }

    def processar_palpite(self, texto: str) -> dict:
        """
        Processa um palpite e retorna o resultado com as atualizações
        de vidas e pontuação (toda a lógica fica no servidor).
        """
        if self.imagem_atual is None:
            return {"erro": "Nenhuma imagem ativa."}

        gabarito = self.imagem_atual.palavra_chave.lower()
        texto = texto.strip().lower()

        if texto == gabarito:
            pontos = self.calcular_pontos(self.vidas)
            self.pontuacao += pontos
            proxima = self.avancar_rodada()
            return {
                "resultado": "acerto",
                "pontos_ganhos": pontos,
                "pontuacao_total": self.pontuacao,
                "proxima_imagem": proxima,
            }

        self.vidas -= 1

        if texto in gabarito:
            return {
                "resultado": "quase",
                "vidas_restantes": self.vidas,
                "revelar_azulejo": True,
                "eliminado": self.vidas <= 0,
            }

        return {
            "resultado": "errou",
            "vidas_restantes": self.vidas,
            "dica": self.imagem_atual.dica_texto,
            "revelar_azulejo": False,
            "eliminado": self.vidas <= 0,
        }


# ---------------------------------------------------------------------------
# 4b. Subclasse: PartidaMultiplayer
# ---------------------------------------------------------------------------

@dataclass
class Sala:
    """
    Representa uma sala no lobby multiplayer.
    Usado como VALUE no dicionário `lobby`.
    """
    pin: str
    host: str
    jogadores: list[str] = field(default_factory=list)
    fonte: str = "api"
    ativa: bool = False

    def to_dict(self) -> dict:
        return {
            "pin": self.pin,
            "host": self.host,
            "jogadores": self.jogadores,
            "fonte": self.fonte,
            "ativa": self.ativa,
        }


class PartidaMultiplayer(Partida):
    """
    Partida para múltiplos jogadores.
    Herda de Partida e implementa `iniciar()`.
    """

    def __init__(self, sala_id: str, jogadores: list[str], fonte: str = "api"):
        super().__init__(fonte=fonte)
        self.sala_id = sala_id
        self.jogadores = jogadores
        # Vidas individuais: cada chave é um nickname → Hashing / Dicionário
        self.vidas_jogadores: dict[str, int] = {
            j: self.VIDAS_INICIAIS for j in jogadores
        }

    def iniciar(self) -> dict:
        """Carrega o banco e retorna os dados da primeira imagem para broadcast."""
        self._carregar_banco()
        self.imagem_atual = self.banco.proxima()
        return {
            "modo": "multiplayer",
            "sala_id": self.sala_id,
            "jogadores": self.jogadores,
            "imagem": self.imagem_atual.to_dict() if self.imagem_atual else None,
        }

    def eliminar_jogador(self, nickname: str) -> None:
        """Remove o jogador da partida quando suas vidas acabam."""
        self.vidas_jogadores.pop(nickname, None)


# ---------------------------------------------------------------------------
# 5. Lobby Global — Dicionário em memória
#    Estrutura: { "PIN" (str) → Sala }
#    A chave (PIN) é usada como hash implicitamente pelo dict do Python.
# ---------------------------------------------------------------------------

lobby: dict[str, Sala] = {}


def _gerar_pin(tamanho: int = 6) -> str:
    """Gera um PIN alfanumérico único que ainda não existe no lobby."""
    while True:
        pin = "".join(random.choices(string.ascii_uppercase + string.digits, k=tamanho))
        if pin not in lobby:
            return pin


def criar_sala(nickname: str, fonte: str = "api") -> tuple[str, Sala]:
    """
    Cria uma nova Sala, registra no lobby e retorna (pin, sala).
    O PIN é a CHAVE do dicionário → acesso O(1) por hashing.
    """
    pin = _gerar_pin()
    sala = Sala(pin=pin, host=nickname, jogadores=[nickname], fonte=fonte)
    lobby[pin] = sala          # Inserção no dicionário (hash map)
    return pin, sala


def entrar_sala(pin: str, nickname: str) -> dict:
    """
    Adiciona um jogador a uma sala existente.
    Busca pelo PIN com acesso O(1) via hashing do dicionário.
    """
    if pin not in lobby:       # Lookup O(1) no hash map
        return {"erro": "Sala não encontrada. Verifique o PIN."}

    sala = lobby[pin]

    if sala.ativa:
        return {"erro": "Partida já iniciada. Aguarde a próxima rodada."}

    if nickname not in sala.jogadores:
        sala.jogadores.append(nickname)

    return {"sala": sala}


def remover_sala(pin: str) -> None:
    """Remove a sala do lobby ao fim da partida."""
    lobby.pop(pin, None)
