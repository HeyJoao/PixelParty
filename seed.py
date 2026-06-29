# seed.py
import os
from app import app
from models import db, Jogador, TemaCustomizado, Imagem

# Força o caminho absoluto para o banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'jogo.db')}")

# ==============================================================================
# 1. LISTA MESTRE DE TEMAS E IMAGENS
# ==============================================================================
TEMAS_PARA_CADASTRAR = [
    {
        "nome": "Filmes Clássicos",
        "imagens": [
            {"url": "/static/img/umsonhodelibertada.jpeg", "palavras": "um sonho de liberdade"},
            {"url": "/static/img/poderosochefao.jpg", "palavras": "o poderoso chefao"},
            {"url": "/static/img/batman.batman.jpeg", "palavras": "batman"},
            {"url": "/static/img/florestgump.jpeg", "palavras": "forrest gump"},
            {"url": "/static/img/pulp.jpeg", "palavras": "pulp fiction"},
            {"url": "/static/img/lista.jpeg", "palavras": "a lista de schindler"},
            {"url": "/static/img/senhor.jpeg", "palavras": "senhor dos aneis"},
            {"url": "/static/img/conflito.jpeg", "palavras": "tres homens em conflito"},
            {"url": "/static/img/interestelar.jpeg", "palavras": "interestelar"},
            {"url": "/static/img/clube.jpeg", "palavras": "clube da luta"},
            {"url": "/static/img/starwars.jpeg", "palavras": "star wars"},
            {"url": "/static/img/matrix.jpeg", "palavras": "matrix"},
            {"url": "/static/img/futuro.jpeg", "palavras": "de volta para o futuro"},
            {"url": "/static/img/companheiros.jpeg", "palavras": "os bons companheiros"},
            {"url": "/static/img/ninho.jpeg", "palavras": "um estranho no ninho"}
        ]
    },
    {
        "nome": "Animais",
        "imagens": [
            {"url": "/static/img/cachorro.jpeg", "palavras": "cachorro"},
            {"url": "/static/img/gato.jpeg", "palavras": "gato"},
            {"url": "/static/img/leao.jpeg", "palavras": "leao"},
            {"url": "/static/img/elefante.jpg", "palavras": "elefante"},
            {"url": "/static/img/girafa.jpeg", "palavras": "girafa"},
            {"url": "/static/img/macaco.jpeg", "palavras": "macaco"},
            {"url": "/static/img/cavalo.jpeg", "palavras": "cavalo"},
            {"url": "/static/img/tigre.jpeg", "palavras": "tigre"},
            {"url": "/static/img/urso.jpeg", "palavras": "urso"},
            {"url": "/static/img/lobo.jpeg", "palavras": "lobo"},
            {"url": "/static/img/aguia.jpeg", "palavras": "aguia"},
            {"url": "/static/img/tubarao.jpeg", "palavras": "tubarao"},
            {"url": "/static/img/baleia.jpeg", "palavras": "baleia"},
            {"url": "/static/img/pinguim.jpeg", "palavras": "pinguim"},
            {"url": "/static/img/cobra.jpeg", "palavras": "cobra"}
        ]
    },
    {
        "nome": "Bandeiras",
        "imagens": [
            {"url": "/static/img/brasil.jpeg", "palavras": "brasil"},
            {"url": "/static/img/argentina.jpg", "palavras": "argentina"},
            {"url": "/static/img/estadosunidos.png", "palavras": "estados unidos"},
            {"url": "/static/img/canada.png", "palavras": "canada"},
            {"url": "/static/img/reino.png", "palavras": "reino unido"},
            {"url": "/static/img/franca.png", "palavras": "franca"},
            {"url": "/static/img/italia.jpeg", "palavras": "italia"},
            {"url": "/static/img/espanha.png", "palavras": "espanha"},
            {"url": "/static/img/alemanha.png", "palavras": "alemanha"},
            {"url": "/static/img/japao.jpeg", "palavras": "japao"},
            {"url": "/static/img/australia.png", "palavras": "australia"},
            {"url": "/static/img/africa.png", "palavras": "africa do sul"},
            {"url": "/static/img/india.png", "palavras": "india"},
            {"url": "/static/img/china.png", "palavras": "china"},
            {"url": "/static/img/sul.png", "palavras": "coreia do sul"}
        ]
    },
    {
        "nome": "Times de Futebol",
        "imagens": [
            {"url": "/static/img/real.jpeg", "palavras": "real madrid"},
            {"url": "/static/img/munique.png", "palavras": "bayern de munique"},
            {"url": "/static/img/city.png", "palavras": "manchester city"},
            {"url": "/static/img/barcelona.png", "palavras": "barcelona"},
            {"url": "/static/img/liberpool.jpeg", "palavras": "liverpool"},
            {"url": "/static/img/juventus.jpeg", "palavras": "juventus"},
            {"url": "/static/img/paris.png", "palavras": "paris saint germain"},
            {"url": "/static/img/milan.png", "palavras": "milan"},
            {"url": "/static/img/united.jpeg", "palavras": "manchester united"},
            {"url": "/static/img/arsenal.png", "palavras": "arsenal"},
            {"url": "/static/img/flamengo.png", "palavras": "flamengo"},
            {"url": "/static/img/palmeiras.png", "palavras": "palmeiras"},
            {"url": "/static/img/paulo.png", "palavras": "sao paulo"},
            {"url": "/static/img/corinthians.png", "palavras": "corinthians"},
            {"url": "/static/img/santos.png", "palavras": "santos"}
        ]
    }
]

def popular_banco():
    with app.app_context():
        print("🌱 Iniciando o Seeding do banco de dados...")
        
        try:
            db.create_all()

            admin = Jogador.query.filter_by(nickname="Admin").first()
            if not admin:
                admin = Jogador(nickname="Admin")
                db.session.add(admin)
                db.session.commit()
                print("👤 Jogador 'Admin' criado.")

            for dados_tema in TEMAS_PARA_CADASTRAR:
                nome_do_tema = dados_tema["nome"]
                imagens_do_tema = dados_tema["imagens"]

                tema_existente = TemaCustomizado.query.filter_by(nome_tema=nome_do_tema).first()
                
                if not tema_existente:
                    novo_tema = TemaCustomizado(nome_tema=nome_do_tema, criador_id=admin.id)
                    db.session.add(novo_tema)
                    db.session.commit()

                    for img in imagens_do_tema:
                        nova_img = Imagem(
                            url_imagem=img["url"],
                            palavras_chave=img["palavras"],
                            tema_id=novo_tema.id
                        )
                        db.session.add(nova_img)

                    db.session.commit()
                    print(f"✅ Tema '{nome_do_tema}' cadastrado com {len(imagens_do_tema)} imagens!")
                else:
                    print(f"⚠️ O tema '{nome_do_tema}' já existe no banco. Pulando...")

            print("🚀 Banco de dados completamente populado!")
        
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro crítico ao popular o banco de dados: {e}")

if __name__ == "__main__":
    popular_banco()
