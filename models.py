from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.Text, nullable=False)

    cep = db.Column(db.String(10))
    estado = db.Column(db.String(2))
    cidade = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    rua = db.Column(db.String(100))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))

    administrador = db.Column(db.Boolean, default=False)

    vendas = db.relationship('Venda', backref='usuario', lazy=True)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def endereco_completo(self):
        partes = [
            f"{self.rua}, {self.numero}" if self.rua and self.numero else "",
            f"{self.bairro}" if self.bairro else "",
            f"{self.cidade} - {self.estado}" if self.cidade and self.estado else "",
            f"CEP: {self.cep}" if self.cep else "",
            f"Complemento: {self.complemento}" if self.complemento else ""
        ]
        return ', '.join([p for p in partes if p])


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

    endereco_entrega = db.Column(db.String(255), nullable=False) # Ou Text se for muito longo
    forma_pagamento = db.Column(db.String(50), nullable=False)
    troco_para = db.Column(db.Float, nullable=True) # Pode ser nulo se não precisar de troco

    itens = db.relationship('VendaItem', backref='venda', lazy=True)


class VendaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id'), nullable=False)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id', ondelete='CASCADE'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)

    marmita = db.relationship('Marmita', back_populates='venda_itens')
