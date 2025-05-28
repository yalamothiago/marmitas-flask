# app.py (Revisado para depuração CSRF)
from flask import Flask, session
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect # Mantenha esta importação
#import os

# NÃO importe load_dotenv e nem tenha prints de SECRET_KEY aqui
# A SECRET_KEY deve estar FIXA no config.py
from flask import Flask, session
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
# REMOVER: from dotenv import load_dotenv
import os # Manter se usado para algo mais, mas não para SECRET_KEY

from models import db, Usuario, Carrinho
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf = CSRFProtect() # Não passe 'app' direto aqui
    csrf.init_app(app)


    db.init_app(app)
    migrate = Migrate(app, db)
    # Remova qualquer outra linha csrf = ... se existir

    # Context processor (permanece como está)
    @app.context_processor
    def inject_usuario_logado():
        if 'usuario_id' in session:
            usuario = db.session.get(Usuario, session['usuario_id'])
            if usuario:
                carrinho_db = Carrinho.query.filter_by(user_id=usuario.id).first()
                total_itens_carrinho = sum(item.quantidade for item in carrinho_db.itens) if carrinho_db else 0
                return dict(usuario_logado=usuario, total_itens_carrinho=total_itens_carrinho)
        return dict(usuario_logado=None, total_itens_carrinho=0)

    # Registro de Blueprints (permanece como está)
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.main import main_bp
    from routes.carrinho import carrinho_bp 

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    app.register_blueprint(carrinho_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)