from flask import Flask, session
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os

from models import db, Usuario, Carrinho # Importe todos os modelos necessários
from config import Config # Importa a classe de configuração

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) # Carrega as configurações da classe Config

    db.init_app(app)
    migrate = Migrate(app, db)
    csrf = CSRFProtect(app)

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

    # Registro de Blueprints (ver próximo item)
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.main import main_bp
    from routes.carrinho import carrinho_bp 

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin') # Prefixo para rotas de admin
    app.register_blueprint(main_bp)
    app.register_blueprint(carrinho_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)