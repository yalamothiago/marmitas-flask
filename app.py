# app.py (Revisado)
from flask import Flask, session
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os

from models import db, Usuario, Carrinho
from config import Config
from utilities import converter_unidade 

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf = CSRFProtect()
    csrf.init_app(app)

    db.init_app(app)
    migrate = Migrate(app, db)

    # Context processor
    @app.context_processor
    def inject_usuario_logado():
        if 'usuario_id' in session:
            usuario = db.session.get(Usuario, session['usuario_id'])
            if usuario:
                carrinho_db = Carrinho.query.filter_by(user_id=usuario.id).first()
                total_itens_carrinho = sum(item.quantidade for item in carrinho_db.itens) if carrinho_db else 0
                return dict(usuario_logado=usuario, total_itens_carrinho=total_itens_carrinho)
        return dict(usuario_logado=None, total_itens_carrinho=0)


    @app.context_processor
    def inject_utility_functions():
        return dict(converter_unidade=converter_unidade)


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
