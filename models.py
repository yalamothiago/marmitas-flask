from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(db.Text), nullable=False)
    endereco = db.Column(db.String(200), nullable=True)
    administrador = db.Column(db.Boolean, default=False)

    vendas = db.relationship('Venda', backref='usuario', lazy=True)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Ingrediente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)


class Marmita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    descricao = db.Column(db.String(500), nullable=True)

    itens = db.relationship('MarmitaItem', backref='marmita', lazy=True)
    venda_itens = db.relationship('VendaItem', back_populates='marmita', cascade='all, delete-orphan')


class MarmitaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id'), nullable=False)
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingrediente.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)

    ingrediente = db.relationship('Ingrediente')


class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)

    itens = db.relationship('VendaItem', backref='venda', lazy=True)


class VendaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id'), nullable=False)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id', ondelete='CASCADE'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)

    marmita = db.relationship('Marmita', back_populates='venda_itens')