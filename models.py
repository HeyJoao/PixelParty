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

    # Um jogador pode criar vários temas
    temas = db.relationship("TemaCustomizado", back_populates="criador", lazy="select")

    def adicionar_pontos(self, pontos: int) -> None:
        """Incrementa a pontuação do jogador e persiste."""
        self.pontuacao_global += pontos
        db.session.commit()

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
    palavra_chave = db.Column(db.String(100), nullable=False)  # gabarito
    dica_texto = db.Column(db.String(255), nullable=True)

    # FK → TemasCustomizados
    tema_id = db.Column(db.Integer, db.ForeignKey("temas_customizados.id"), nullable=False)
    tema = db.relationship("TemaCustomizado", back_populates="imagens")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url_imagem": self.url_imagem,
            "palavra_chave": self.palavra_chave,
            "dica_texto": self.dica_texto,
            "tema_id": self.tema_id,
        }

    def __repr__(self) -> str:
        return f"<Imagem '{self.palavra_chave}' | tema_id={self.tema_id}>"
