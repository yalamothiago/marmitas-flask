from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False) # Email para identificação/login
    senha_hash = db.Column(db.Text, nullable=False) # Para proteger o acesso do usuário


    administrador = db.Column(db.Boolean, default=False) # Seu amigo ou outros que gerenciam

    # Relacionamento de um para um com Carrinho (o cliente tem um carrinho ativo)
    carrinho = db.relationship('Carrinho', back_populates='usuario', uselist=False, cascade='all, delete-orphan')
    # Vendas realizadas POR este usuário (cliente)
    vendas = db.relationship('Venda', back_populates='usuario', lazy=True)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)



class Ingrediente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0) # Quantidade comprado na medida selecionada
    total_pago = db.Column(db.Float, nullable=True)
    custo_por_unidade = db.Column(db.Float, nullable=True)
    unidade_medida = db.Column(db.String(50), nullable=True)
    #marca_produto = db.Column(db.String(100), nullable=True)
    #local_compra = db.Column(db.String(100), nullable=True)

    condimento_items = db.relationship('CondimentoItem', back_populates='ingrediente', lazy=True)


class Condimento(db.Model):
    """
    Representa um condimento que é composto por ingredientes e usado em marmitas.
    """
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), unique=True, nullable=False)
    custo_total = db.Column(db.Float, nullable=True)
    rendimento = db.Column(db.Float, nullable=True)
    unidade_medida = db.Column(db.String(50), nullable=True)
    custo_unitario = db.Column(db.Float, nullable=True)

    itens = db.relationship('CondimentoItem', back_populates='condimento', cascade='all, delete-orphan', lazy=True)
    marmita_condimentos = db.relationship('MarmitaCondimento', back_populates='condimento', lazy=True)


class CondimentoItem(db.Model):
    """
    Representa um ingrediente específico usado na composição de um Condimento.
    """
    id = db.Column(db.Integer, primary_key=True)
    condimento_id = db.Column(db.Integer, db.ForeignKey('condimento.id'), nullable=False)
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingrediente.id'), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)

    condimento = db.relationship('Condimento', back_populates='itens')
    ingrediente = db.relationship('Ingrediente', back_populates='condimento_items')


class Marmita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0) # Quantidade em estoque
    descricao = db.Column(db.String(500), nullable=True)

    unidade_medida = db.Column(db.String(50), nullable=True)
    custo_producao_base = db.Column(db.Float, nullable=True)
    margem_lucro_percentual = db.Column(db.Float, nullable=True)
    valor_redstore = db.Column(db.Float, nullable=True)

    condimento_itens = db.relationship('MarmitaCondimento', back_populates='marmita', cascade='all, delete-orphan', lazy=True)

    venda_itens = db.relationship('VendaItem', back_populates='marmita', cascade='all, delete-orphan', lazy=True)
    producoes = db.relationship('ProducaoMarmita', back_populates='marmita', lazy=True, cascade='all, delete-orphan')

    carrinho_itens = db.relationship('CarrinhoItem', back_populates='marmita', cascade='all, delete-orphan', lazy=True)


class MarmitaCondimento(db.Model):
    """
    Representa um Condimento específico usado na composição de uma Marmita.
    """
    id = db.Column(db.Integer, primary_key=True)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id'), nullable=False)
    condimento_id = db.Column(db.Integer, db.ForeignKey('condimento.id'), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)

    marmita = db.relationship('Marmita', back_populates='condimento_itens')
    condimento = db.relationship('Condimento', back_populates='marmita_condimentos')


class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # usuario_id refere-se ao CLIENTE que fez a compra (o colega de trabalho)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)

    forma_pagamento = db.Column(db.String(50), nullable=False) # "Pix" ou "Cartao"
    

    lucro_obtido = db.Column(db.Float, nullable=True)

    usuario = db.relationship('Usuario', back_populates='vendas')

    itens = db.relationship('VendaItem', backref='venda', lazy=True)


class VendaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id'), nullable=False)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id', ondelete='CASCADE'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)

    marmita = db.relationship('Marmita', back_populates='venda_itens')


class ProducaoMarmita(db.Model):
    """
    Rastreia a produção de lotes de marmitas, útil para gestão de estoque e custos.
    """
    id = db.Column(db.Integer, primary_key=True)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id'), nullable=False)
    data_producao = db.Column(db.DateTime, default=datetime.utcnow)
    quantidade_produzida = db.Column(db.Integer, nullable=False)
    custo_producao_total = db.Column(db.Float, nullable=True)

    marmita = db.relationship('Marmita', back_populates='producoes')


class Carrinho(db.Model):
    """
    Representa o carrinho de compras de um USUÁRIO (cliente) no ambiente de trabalho.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), unique=True, nullable=False) # Um usuário tem UM carrinho ativo
    timestamp_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', back_populates='carrinho')

    itens = db.relationship('CarrinhoItem', back_populates='carrinho', cascade='all, delete-orphan', lazy=True)


class CarrinhoItem(db.Model):
    """
    Representa um item (marmita) dentro de um Carrinho de compras.
    """
    id = db.Column(db.Integer, primary_key=True)
    carrinho_id = db.Column(db.Integer, db.ForeignKey('carrinho.id'), nullable=False)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Float, nullable=False) # Para registrar o preço no momento da adição ao carrinho

    carrinho = db.relationship('Carrinho', back_populates='itens')
    marmita = db.relationship('Marmita', back_populates='carrinho_itens')