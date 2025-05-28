# init_db.py (ou reset_db.py)
from app import create_app, db, Usuario # Importe a instância 'app' diretamente
from sqlalchemy import text
from flask_migrate import upgrade, stamp, current # Importe os comandos de migração
import os
# from models import db, Usuario # Remova esta linha se db e Usuario já estiverem importados de app

app = create_app()

with app.app_context():
    # PASSO 1: DELETAR TODO O SCHEMA (inclusive tabelas com dependências)
    print("Deletando todas as tabelas e dependências do banco de dados com CASCADE...")
    with db.engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("COMMIT")) # Garante que o DROP/CREATE SCHEMA seja persistido
    print("Schema resetado com sucesso.")

    # PASSO 2: CRIAR TODAS AS NOVAS TABELAS
    print("Criando novas tabelas com base no models.py...")
    db.create_all() # db.create_all() funciona perfeitamente para este propósito
    print("Novas tabelas criadas com sucesso.")

    # PASSO 3: INICIALIZAR OU MARCAR O BANCO DE DADOS COM A REVISÃO MAIS RECENTE DO ALEMBIC
    # Isso diz ao Flask-Migrate que o DB já está atualizado com o HEAD da migração
    print("Marcando o banco de dados com a revisão mais recente do Alembic...")
    
    from alembic.config import Config
    from alembic import command

    # Caminho absoluto para o alembic.ini
    alembic_ini_path = os.path.join(app.root_path, 'alembic.ini') # app.root_path aponta para a raiz do seu projeto
    
    # Verifique se o arquivo alembic.ini existe
    if not os.path.exists(alembic_ini_path):
        print(f"Erro: O arquivo alembic.ini não foi encontrado em: {alembic_ini_path}")
        print("Certifique-se de ter executado 'flask db init' na raiz do seu projeto.")
        exit(1) # Sai do script com erro
        
    alembic_cfg = Config(alembic_ini_path) # Carrega a configuração do alembic.ini
    alembic_cfg.set_main_option("script_location", os.path.join(app.root_path, 'migrations'))
    
    with app.app_context():
        command.stamp(alembic_cfg, "head")
    print("Banco de dados carimbado com sucesso.")

    # PASSO 4: Criar usuário admin
    existing_admin = Usuario.query.filter_by(email='admin@email.com').first()
    if not existing_admin:
        admin = Usuario(
            nome='Admin',
            email='admin@email.com',
            administrador=True
        )
        admin.set_senha('123456')
        db.session.add(admin)
        db.session.commit()
        print("Usuário admin criado com sucesso!")
    else:
        print("Usuário admin já existe.")

    print("Processo de reinicialização do banco de dados concluído!")