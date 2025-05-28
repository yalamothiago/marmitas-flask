from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.Text, nullable=False)
    administrador = db.Column(db.Boolean, default=False)

    carrinho = db.relationship('Carrinho', back_populates='usuario', uselist=False, cascade='all, delete-orphan')
    vendas = db.relationship('Venda', back_populates='usuario', lazy=True)
    pedidos = db.relationship('Pedido', back_populates='cliente', lazy=True) # Relacionamento para Pedido

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Ingrediente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    unidade_medida = db.Column(db.String(50), nullable=True)
    quantidade_comprada = db.Column(db.Float, nullable=False, default=0)
    total_pago = db.Column(db.Float, nullable=True)
    custo_por_unidade = db.Column(db.Float, nullable=True)

    condimento_items = db.relationship('CondimentoItem', back_populates='ingrediente', lazy=True)


class Condimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), unique=True, nullable=False)
    custo_total = db.Column(db.Float, nullable=True)
    rendimento = db.Column(db.Float, nullable=True)
    unidade_medida_rendimento = db.Column(db.String(50), nullable=True)
    custo_unitario = db.Column(db.Float, nullable=True)

    itens = db.relationship('CondimentoItem', back_populates='condimento', cascade='all, delete-orphan', lazy=True)
    marmita_condimentos = db.relationship('MarmitaCondimento', back_populates='condimento', lazy=True)


class CondimentoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    condimento_id = db.Column(db.Integer, db.ForeignKey('condimento.id'), nullable=False)
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingrediente.id'), nullable=False)
    quantidade_do_ingrediente = db.Column(db.Float, nullable=False)

    condimento = db.relationship('Condimento', back_populates='itens')
    ingrediente = db.relationship('Ingrediente', back_populates='condimento_items')


class Marmita(db.Model):
    """
    Representa a 'receita' ou a definição de uma marmita, com seus condimentos.
    Não armazena estoque ou preço de venda final aqui.
    """
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.String(500), nullable=True)
    rendimento_receita = db.Column(db.Float, nullable=True)
    custo_unitario_producao = db.Column(db.Float, nullable=True)

    condimento_itens = db.relationship('MarmitaCondimento', back_populates='marmita', cascade='all, delete-orphan', lazy=True)

    precificacao = db.relationship('Precificacao', back_populates='marmita', uselist=False, cascade='all, delete-orphan')

    # Removido o relacionamento direto com Estoque, pois Estoque agora se relaciona com Precificacao
    # estoque = db.relationship('Estoque', back_populates='marmita', uselist=False, cascade='all, delete-orphan')

    # Removido o relacionamento direto com Pedido, pois Pedido agora se relaciona com Estoque
    # pedidos = db.relationship('Pedido', back_populates='marmita_escolhida', lazy=True)

    # VendaItem e CarrinhoItem ainda se relacionam com Marmita (a receita)
    venda_itens = db.relationship('VendaItem', back_populates='marmita', cascade='all, delete-orphan', lazy=True)
    producoes = db.relationship('ProducaoMarmita', back_populates='marmita', lazy=True, cascade='all, delete-orphan')
    carrinho_itens = db.relationship('CarrinhoItem', back_populates='marmita', cascade='all, delete-orphan', lazy=True)


class MarmitaCondimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id'), nullable=False)
    condimento_id = db.Column(db.Integer, db.ForeignKey('condimento.id'), nullable=False)
    quantidade_do_condimento = db.Column(db.Float, nullable=False)

    marmita = db.relationship('Marmita', back_populates='condimento_itens')
    condimento = db.relationship('Condimento', back_populates='marmita_condimentos')


class Precificacao(db.Model):
    """
    PRECIFICAÇÃO
    - Nome_Marmita (Puxa o Marmita_Id da tabela MARMITAS)
    - Custo_marmita (Puxa o Custo Total relacionado ao Marmita_Id da tabela MARMITAS)
    - Valor de Venda
    - Margem de Lucro ((Valor de Venda - Custo_Marmita)/Valor de Venda)
    - Valor do Lucro ([Valor de Venda - Custo_marmita])
    """
    id = db.Column(db.Integer, primary_key=True)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id'), unique=True, nullable=False)
    valor_de_venda = db.Column(db.Float, nullable=False)

    custo_marmita = db.Column(db.Float, nullable=True)
    margem_de_lucro_percentual = db.Column(db.Float, nullable=True)
    valor_do_lucro = db.Column(db.Float, nullable=True)

    marmita = db.relationship('Marmita', back_populates='precificacao')
    # Relacionamento com Estoque: uma precificação pode ter um registro de estoque
    estoque_referencia = db.relationship('Estoque', back_populates='precificacao_referencia', uselist=False, cascade='all, delete-orphan')


class Estoque(db.Model):
    """
    ESTOQUE
    - Nome_Marmita (Puxa o Nome_Marmita da tabela PRECIFICAÇÃO)
    - Custo_marmita (Puxa o Custo_marmita da tabela PRECIFICAÇÃO)
    - Quantidade
    """
    id = db.Column(db.Integer, primary_key=True)
    # CHAVE ESTRANGEIRA PARA PRECIFICAÇÃO - CORREÇÃO DO ERRO
    precificacao_id = db.Column(db.Integer, db.ForeignKey('precificacao.id'), unique=True, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)

    # O custo_marmita aqui é o custo unitário da precificação, para referência.
    # Pode ser acessado via precificacao_referencia.custo_marmita. Mantido para clareza.
    custo_marmita_precificacao = db.Column(db.Float, nullable=True)

    # Relacionamento de volta para Precificacao
    precificacao_referencia = db.relationship('Precificacao', back_populates='estoque_referencia')

    # Removido o relacionamento direto com Marmita, pois agora a Marmita é acessada via Precificacao
    # marmita = db.relationship('Marmita', back_populates='estoque')

    # Relacionamento para Pedido (um item de estoque pode estar em vários pedidos)
    pedidos_relacionados = db.relationship('Pedido', back_populates='estoque_item_pedido', lazy=True)


class Pedido(db.Model):
    """
    PEDIDO
    - Nome_cliente
    - E-mail_cliente
    - Contato_cliente
    - Marmita_Id (A marmita que ele escolheu) -> Agora puxa do Estoque
    - Custo_marmita (Puxa o Custo_marmita da tabela ESTOQUE)
    - Quantidade_marmita_id
    - Total da Compra ([Custo_marmita x Quantidade_marmita_id])
    """
    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    email_cliente = db.Column(db.String(100), nullable=True)
    contato_cliente = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # CHAVE ESTRANGEIRA PARA ESTOQUE - CORREÇÃO
    estoque_id = db.Column(db.Integer, db.ForeignKey('estoque.id'), nullable=False)
    quantidade_marmita_id = db.Column(db.Integer, nullable=False)

    custo_marmita = db.Column(db.Float, nullable=True) # Custo_marmita (Puxa o Custo_marmita da tabela ESTOQUE)
    total_da_compra = db.Column(db.Float, nullable=True)

    # Relacionamento de volta para Estoque
    estoque_item_pedido = db.relationship('Estoque', back_populates='pedidos_relacionados')

    # Relacionamento para o usuário (cliente) que fez o pedido, se for um usuário registrado
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    cliente = db.relationship('Usuario', back_populates='pedidos')


class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=False)
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
    id = db.Column(db.Integer, primary_key=True)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id'), nullable=False)
    data_producao = db.Column(db.DateTime, default=datetime.utcnow)
    quantidade_produzida = db.Column(db.Integer, nullable=False)
    custo_producao_total = db.Column(db.Float, nullable=True)

    marmita = db.relationship('Marmita', back_populates='producoes')

class Carrinho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), unique=True, nullable=False)
    timestamp_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', back_populates='carrinho')
    itens = db.relationship('CarrinhoItem', back_populates='carrinho', cascade='all, delete-orphan', lazy=True)

class CarrinhoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    carrinho_id = db.Column(db.Integer, db.ForeignKey('carrinho.id'), nullable=False)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Float, nullable=False)

    carrinho = db.relationship('Carrinho', back_populates='itens')
    marmita = db.relationship('Marmita', back_populates='carrinho_itens')