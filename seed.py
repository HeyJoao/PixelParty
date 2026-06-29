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
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR4NFdgaOu1_XMSI7us7NxvwXRfNWNrMLz_5IN_cL1n9A&s=10", "palavras": "um sonho de liberdade"},
            {"url": "https://br.web.img3.acsta.net/c_310_420/medias/nmedia/18/90/93/20/20120876.jpg", "palavras": "o poderoso chefao"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRNbZowa1QT7OZGaJyu_rlJ7X_mxShrB9auucA3a4yo1Q&s=10", "palavras": "batman"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZR08QfbrXogTIyeI-3JJrZ25pbniDVZQKNMjnjQ9Wxw&s=10", "palavras": "forrest gump"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRaK-qBL3iAaK1HmQqyXbOLmNYTfXZFQDqx6Urija0SXQ&s=10", "palavras": "pulp fiction"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQP-JpiDvWF_ogP5LQJgOxnqI0hkPde68yOSVb7tIH6Qg&s=10", "palavras": "a lista de schindler"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSnd5jniIFTLJdrk4ai1szGDULsmUsTPCsylDsxO7GSSg&s", "palavras": "senhor dos aneis"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRsRv8v4WkwLX2C_KeugHEqiXRhZr6R76lTr25kFPLmQw&s=10", "palavras": "tres homens em conflito"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTzB8plhqk7i5-MspMJGJy20i8sERE0fHHMZ4GZUap4Bg&s=10", "palavras": "interestelar"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQiJkMd5g3PtEdKcDvkflbUrsl8VoSysBa9GyxvFtTe5g&s=10", "palavras": "clube da luta"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQmNp2Bs8gtul3qxQIHawqQDCxKzW7RmUpAo4e5qCeeMw&s", "palavras": "star wars"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSEbjrQIyuZlEZBypKX7sIJf2NDSCYJ_3ioCOfekqIR7A&s", "palavras": "matrix"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ_IhT98ZF6GFMjz57Md9VNuI3ZXu92p0ZhLiMC-jGXoQ&s", "palavras": "de volta para o futuro"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQb9OsZk3FMzglAupDRZMNyYAPOjFnOQhwvmhohrAG1mw&s=10", "palavras": "os bons companheiros"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6cT19VxhTjt--O3e0EMuICZ4kSrWDFsHilqefa3jZ_Q&s=10", "palavras": "um estranho no ninho"}
        ]
    },
    {
        "nome": "Animais",
        "imagens": [
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGiIxr1J45-o--9SWSYnoP43Lg14VoDSbLhq82U9-g2A&s=10", "palavras": "cachorro"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcThdgu-UO2Md37PIofCAgxEycfh3m_KnjkTMwSKFTJXGw&s=10", "palavras": "gato"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSV4t6asbaZ7vJa-JDWj5rD5Qbq_nAzCnnC1zPTdMBpCw&s=10", "palavras": "leao"},
            {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/African_Bush_Elephant.jpg/250px-African_Bush_Elephant.jpg", "palavras": "elefante"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPJjYPKMpsf90EZg0N9weeSVxmohZaKl_yG5PJzQgAAw&s=10", "palavras": "girafa"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRxXgh_v8PTmv8UIYKScj4PiGxW5vz_-WmchHBf5wj5yQ&s=10", "palavras": "macaco"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRPXP0hlxgzh4vikuAy_WuFG64m4Xi0GKw2c4Z3y2Cw5g&s=10", "palavras": "cavalo"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRmwU59m-M1wn5ZKF28ijQUKi-P8l0awTKpWJkMB9_vdg&s=10", "palavras": "tigre"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQSTvhpIGmCCNECSwWM1OR_pMFQFOEdzc-wVcQJKkr5CQ&s=10", "palavras": "urso"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQc1_o0xZ3ghlK_O2itKgJVgOJ8MLilBoGvlczmW4glvA&s=10", "palavras": "lobo"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT0WeQe0KYOX7EvyW8FAeRENHBsmjJSshYQc7qhxP9r4g&s", "palavras": "aguia"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQn5M5gM178SUk6Ao8211DfaVzIrBJLRuGODqWStIpZIw&s=10", "palavras": "tubarao"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTJbVCI-ztjrgKfntt6iLuwQIM4g35crAmOHjfgG5nzYQ&s=10", "palavras": "baleia"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQINN6GuHnn4aJIlQM64X9F725XbyWxraPEVX2ZPJIhLg&s=10", "palavras": "pinguim"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRLEop5uuEMX91aSAd9IIHA0lnmFcMmiXuA2SCYOfMv-w&s=10", "palavras": "cobra"}
        ]
    },
    {
        "nome": "Bandeiras",
        "imagens": [
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT3p72rvtVrd4BxotdIeEyCX99Ynk5xrANffFdgsKwBQg&s=10", "palavras": "brasil"},
            {"url": "https://upload.wikimedia.org/wikipedia/commons/1/1a/Flag_of_Argentina.svg", "palavras": "argentina"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSWfSMkDlpxRaj7v6JrXQn_HjhPbEScwWvb0r280aJo0w&s=10", "palavras": "estados unidos"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRe5fcjhzXBdT704WVjUu1VEXTKBTXS6arK0Cwseo0tYw&s=10", "palavras": "canada"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR5ru4dgWIV7btQYcaWXw-s8dUBtRwgH3gfoe82qS9aEA&s=10", "palavras": "reino unido"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTRooTsrYT0dXqoBmTWuaSz24P2oj6D0IoG5F6OLJwp7Q&s", "palavras": "franca"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTQjFqWlom-4dShrqn9XqxgWnu37ajoXuUqVESKNeSlfg&s=10", "palavras": "italia"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQItZbX2oR7I9HCqW1FwdMo8p6jfn_kUCpncyLpUbR4fg&s=10", "palavras": "espanha"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTdtzZ68YcCgOhfoYT6NVkdHNxSF4lg718lObL9jQ9tag&s", "palavras": "alemanha"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRE1ZZENz5hJ2Wwj-TZ0EkkiI8Y2CtGPZguMYTX74J7RA&s=10", "palavras": "japao"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRPCVT-VuL2hzazgl28vhoYK15RHlf_3K2FJgfU8DEABg&s=10", "palavras": "australia"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYwiMwQuQBHif3h3Jdag1OyRGiVjIFmZkTuCSZ537h3A&s=10", "palavras": "africa do sul"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSIjjkQEmPHB-t7GuRFJ85g8-xPWHsWDey9wTDvFhyz4Q&s", "palavras": "india"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcScVCVLfEggi0cyYjuOkr00corkd16D-I2r_dLA9xmHxA&s=10", "palavras": "china"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR4kvBDum_l0NSP1v5PX-PHMAaBuUU7e78_ol3kiT1dNg&s=10", "palavras": "coreia do sul"}
        ]
    },
    {
        "nome": "Times de Futebol",
        "imagens": [
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRaHRSQFca93ewbUH5zTwqgahEji3Q0TiuVZzAUlhPEbA&s=10", "palavras": "real madrid"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGq0AOpMZiySyCSWtYIOh2aN0XPv3Q3YtyPBhYR7BAsA&s=10", "palavras": "bayern de munique"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSulpkMidFNaMKGEEQjlMl5s6Sc5SFOzgCnMvqVi-c8fw&s", "palavras": "manchester city"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQplSOJgBOt4Fzm2ALsLUWdKitF23eeeSkqMGQA62IQ-A&s=10", "palavras": "barcelona"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQplSOJgBOt4Fzm2ALsLUWdKitF23eeeSkqMGQA62IQ-A&s=10", "palavras": "liverpool"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSLdasTcZbaZdMXzQ50LdCAeGMSFr5WeHcbyHUQorgg_A&s=10", "palavras": "juventus"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSttrUJyv8KrWnQwRtcEf87Wch5XmgyMNn13leJHUfzOw&s", "palavras": "paris saint germain"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSi8vUKYA9UttFQYw5V3BauRMMXmLn30mJbJFq5VKgbgQ&s=10", "palavras": "milan"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_9Rt4p8S3Cd8xgJh91smIkGFiRfIJi9dMenU17hyp0Q&s=10", "palavras": "manchester united"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSR6NDVMrvQRxCyv8N6mRe9D3J0SneGPVUrRPaoUKDC1g&s=10", "palavras": "arsenal"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT5b5IIMkZEkXpyrY3DwUMeSBxNDKj3M7C_U6I2VAA97A&s=10", "palavras": "flamengo"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSt-P8bjWWYeasrSfPQyRuhTyxubSOLvbVkHnTW9Z8dqg&s=10", "palavras": "palmeiras"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS25VtuNZzEhoOmkhDySvdCX60CBHM54rs2vyAZZd4oGA&s=10", "palavras": "sao paulo"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTLtYwTLJ2QhTR3u0cLHjSjqALIbvmQe0AlJfrWJCh-Kw&s=10", "palavras": "corinthians"},
            {"url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRhAriJGX60TUAuOL_FioDHI7xaQQGQ4KioX4OtXRfWhw&s=10", "palavras": "santos"}
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
