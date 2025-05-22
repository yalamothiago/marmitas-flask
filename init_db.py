from app import app
from models import db, Usuario

with app.app_context():
    db.create_all()  # Cria as tabelas, se ainda não existirem

    # Verificar se já existe admin
    if not Usuario.query.filter_by(email='admin@email.com').first():
        admin = Usuario(
            nome='Admin',
            email='admin@email.com',
            administrador=True
        )
        admin.set_senha('123456')
        db.session.add(admin)
        db.session.commit()
        print('Admin criado com sucesso!')
    else:
        print('Admin já existe.')
