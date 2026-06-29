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
            {"url": "https://image.tmdb.org/t/p/original/q6y0Go1tsGEsmtFryDOJo3dENv1.jpg", "palavras": "um sonho de liberdade"},
            {"url": "https://image.tmdb.org/t/p/original/3bhkrj58Vtu7enYsRolD1fZdja1.jpg", "palavras": "o poderoso chefao"},
            {"url": "https://image.tmdb.org/t/p/original/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "palavras": "batman o cavaleiro das trevas"},
            {"url": "https://image.tmdb.org/t/p/original/hek3koDUyRQk7FIhPXsa6mT2Zc3.jpg", "palavras": "o poderoso chefao 2"},
            {"url": "https://image.tmdb.org/t/p/original/d5iIlFn5s0ImszYzBPb8SPFCWKy.jpg", "palavras": "pulp fiction"},
            {"url": "https://image.tmdb.org/t/p/original/sF1U4EUQS8YHUYjN18wsON1BcdE.jpg", "palavras": "a lista de schindler"},
            {"url": "https://image.tmdb.org/t/p/original/rCzpDGLbOoPwLjy3OAm5OUcvUZ.jpg", "palavras": "o senhor dos aneis o retorno do rei"},
            {"url": "https://image.tmdb.org/t/p/original/f2gA1h0xHqYc1yN9o68uB62A41M.jpg", "palavras": "tres homens em conflito"},
            {"url": "https://image.tmdb.org/t/p/original/omoYw5x55hX0AXXWwP61uH4j7rZ.jpg", "palavras": "o senhor dos aneis a sociedade do anel"},
            {"url": "https://image.tmdb.org/t/p/original/r3pPehX4ikrmIUkM7GqjD5hIitq.jpg", "palavras": "clube da luta"},
            {"url": "https://image.tmdb.org/t/p/original/yA1vO8B6I1aL9mQzI9u5eN4cQ42.jpg", "palavras": "star wars o imperio contra ataca"},
            {"url": "https://image.tmdb.org/t/p/original/lZpWprJqbIFpEV566x6Qy5zEbA1.jpg", "palavras": "matrix"},
            {"url": "https://image.tmdb.org/t/p/original/5VTN0pR8gcqV3EPUxEw1Q11kFq5.jpg", "palavras": "o senhor dos aneis as duas torres"},
            {"url": "https://image.tmates.info/t/p/original/aKuFiU82s5ISJpGZpA1y18gN5iQ.jpg", "palavras": "os bons companheiros"},
            {"url": "https://image.tmdb.org/t/p/original/qZ2Z5J4X1E3yR2I5J3M7j8k5Y8Q.jpg", "palavras": "um estranho no ninho"}
        ]
    },
    {
        "nome": "Animais",
        "imagens": [
            {"url": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=600&auto=format&fit=crop&q=80", "palavras": "cachorro"},
            {"url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&auto=format&fit=crop&q=80", "palavras": "gato"},
            {"url": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=600&auto=format&fit=crop&q=80", "palavras": "leao"},
            {"url": "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?w=600&auto=format&fit=crop&q=80", "palavras": "elefante"},
            {"url": "https://images.unsplash.com/photo-1507666480-4344b606c4a2?w=600&auto=format&fit=crop&q=80", "palavras": "girafa"},
            {"url": "https://images.unsplash.com/photo-1540573133985-87b6da6d54a9?w=600&auto=format&fit=crop&q=80", "palavras": "macaco"},
            {"url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=600&auto=format&fit=crop&q=80", "palavras": "cavalo"},
            {"url": "https://images.unsplash.com/photo-1508817628294-5a453fa0b8fb?w=600&auto=format&fit=crop&q=80", "palavras": "tigre"},
            {"url": "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?w=600&auto=format&fit=crop&q=80", "palavras": "urso"},
            {"url": "https://images.unsplash.com/photo-1589656966895-2f33e7653819?w=600&auto=format&fit=crop&q=80", "palavras": "lobo"},
            {"url": "https://images.unsplash.com/photo-1611689342806-0863700ce1e4?w=600&auto=format&fit=crop&q=80", "palavras": "aguia"},
            {"url": "https://images.unsplash.com/photo-1560275669-46c5a88d6a4c?w=600&auto=format&fit=crop&q=80", "palavras": "tubarao"},
            {"url": "https://images.unsplash.com/photo-1568430462989-4b16f61d2cfc?w=600&auto=format&fit=crop&q=80", "palavras": "baleia"},
            {"url": "https://images.unsplash.com/photo-1598439210625-5067c578f3f6?w=600&auto=format&fit=crop&q=80", "palavras": "pinguim"},
            {"url": "https://images.unsplash.com/photo-1531386151447-fd762733099e?w=600&auto=format&fit=crop&q=80", "palavras": "cobra"}
        ]
    },
    {
        "nome": "Bandeiras",
        "imagens": [
            {"url": "https://flagcdn.com/w640/br.png", "palavras": "brasil"},
            {"url": "https://flagcdn.com/w640/ar.png", "palavras": "argentina"},
            {"url": "https://flagcdn.com/w640/us.png", "palavras": "estados unidos"},
            {"url": "https://flagcdn.com/w640/ca.png", "palavras": "canada"},
            {"url": "https://flagcdn.com/w640/gb.png", "palavras": "reino unido"},
            {"url": "https://flagcdn.com/w640/fr.png", "palavras": "franca"},
            {"url": "https://flagcdn.com/w640/it.png", "palavras": "italia"},
            {"url": "https://flagcdn.com/w640/es.png", "palavras": "espanha"},
            {"url": "https://flagcdn.com/w640/de.png", "palavras": "alemanha"},
            {"url": "https://flagcdn.com/w640/jp.png", "palavras": "japao"},
            {"url": "https://flagcdn.com/w640/au.png", "palavras": "australia"},
            {"url": "https://flagcdn.com/w640/za.png", "palavras": "africa do sul"},
            {"url": "https://flagcdn.com/w640/in.png", "palavras": "india"},
            {"url": "https://flagcdn.com/w640/cn.png", "palavras": "china"},
            {"url": "https://flagcdn.com/w640/kr.png", "palavras": "coreia do sul"}
        ]
    },
    {
        "nome": "Times de Futebol",
        "imagens": [
            {"url": "https://images.thehkphotos.com/teams/real_madrid.png", "palavras": "real madrid"},
            {"url": "https://images.thehkphotos.com/teams/bayern_munich.png", "palavras": "bayern de munique"},
            {"url": "https://images.thehkphotos.com/teams/manchester_city.png", "palavras": "manchester city"},
            {"url": "https://images.thehkphotos.com/teams/barcelona.png", "palavras": "barcelona"},
            {"url": "https://images.thehkphotos.com/teams/liverpool.png", "palavras": "liverpool"},
            {"url": "https://images.thehkphotos.com/teams/juventus.png", "palavras": "juventus"},
            {"url": "https://images.thehkphotos.com/teams/psg.png", "palavras": "paris saint-germain"},
            {"url": "https://images.thehkphotos.com/teams/milan.png", "palavras": "milan"},
            {"url": "https://images.thehkphotos.com/teams/manchester_united.png", "palavras": "manchester united"},
            {"url": "https://images.thehkphotos.com/teams/arsenal.png", "palavras": "arsenal"},
            {"url": "https://images.thehkphotos.com/teams/flamengo.png", "palavras": "flamengo"},
            {"url": "https://images.thehkphotos.com/teams/palmeiras.png", "palavras": "palmeiras"},
            {"url": "https://images.thehkphotos.com/teams/sao_paulo.png", "palavras": "sao paulo"},
            {"url": "https://images.thehkphotos.com/teams/corinthians.png", "palavras": "corinthians"},
            {"url": "https://images.thehkphotos.com/teams/santos.png", "palavras": "santos"}
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