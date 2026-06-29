"""
models.py — Modelos do banco de dados (SQLAlchemy).

Mapeia as três tabelas definidas na arquitetura:
  - Jogador          → tabela de ranking
  - TemaCustomizado  → temas criados pelos usuários
  - Imagem           → imagens vinculadas a um tema

Conceito aplicado — Composição/Agregação (ORM):
  TemaCustomizado possui uma lista de Imagens (relationship "imagens").
  Isso espelha a classe BancoDeImagens de game_logic.py no nível do banco.
"""

import secrets
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ---------------------------------------------------------------------------
# Tabela: Jogadores
# ---------------------------------------------------------------------------

class Jogador(db.Model):
    __tablename__ = "jogadores"

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(80), unique=True, nullable=False)
    pontuacao_global = db.Column(db.Integer, default=0, nullable=False)

    session_token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_hex(32))
    # Um jogador pode criar vários temas
    temas = db.relationship("TemaCustomizado", back_populates="criador", lazy="select")

    def adicionar_pontos(self, pontos: int) -> None:
        """Incrementa a pontuação do jogador e persiste."""
        self.pontuacao_global += max(pontos, 0)
        db.session.commit()

    def renovar_token(self) -> str:
        """Gera e salva um novo session_token (útil para logout/segurança)."""
        self.session_token = secrets.token_hex(32)
        db.session.commit()
        return self.session_token

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nickname": self.nickname,
            "pontuacao_global": self.pontuacao_global,
        }

    def __repr__(self) -> str:
        return f"<Jogador {self.nickname} | pts={self.pontuacao_global}>"


# ---------------------------------------------------------------------------
# Tabela: TemasCustomizados
# ---------------------------------------------------------------------------

class TemaCustomizado(db.Model):
    __tablename__ = "temas_customizados"

    id = db.Column(db.Integer, primary_key=True)
    nome_tema = db.Column(db.String(120), nullable=False)

    # FK → Jogadores
    criador_id = db.Column(db.Integer, db.ForeignKey("jogadores.id"), nullable=False)
    criador = db.relationship("Jogador", back_populates="temas")

    # Composição: um tema é composto por muitas imagens.
    # cascade="all, delete-orphan" garante que imagens órfãs sejam removidas.
    imagens = db.relationship(
        "Imagem",
        back_populates="tema",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome_tema": self.nome_tema,
            "criador_id": self.criador_id,
            "total_imagens": len(self.imagens),
        }

    def __repr__(self) -> str:
        return f"<TemaCustomizado {self.nome_tema}>"


# ---------------------------------------------------------------------------
# Tabela: Imagens
# ---------------------------------------------------------------------------

class Imagem(db.Model):
    __tablename__ = "imagens"

    id = db.Column(db.Integer, primary_key=True)
    url_imagem = db.Column(db.String(500), nullable=False)
    palavras_chave = db.Column(db.String(500), nullable=False)  # gabarito

    # FK → TemasCustomizados
    tema_id = db.Column(db.Integer, db.ForeignKey("temas_customizados.id"), nullable=False)
    tema = db.relationship("TemaCustomizado", back_populates="imagens")

    def lista_gabaritos(self) -> list[str]:
        return [p.strip().lower() for p in self.palavras_chave.split(",") if p.strip()]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url_imagem": self.url_imagem,
            "tema_id": self.tema_id,
        }
        
    def to_dict_admin(self) -> dict:
        """Serialização completa para rotas administrativas de cadastro."""
        return {
            "id":             self.id,
            "url_imagem":     self.url_imagem,
            "palavras_chave": self.palavras_chave,
            "tema_id":        self.tema_id,
        }
    
    def __repr__(self) -> str:
        return f"<Imagem '{self.palavras_chave}' | tema_id={self.tema_id}>"
