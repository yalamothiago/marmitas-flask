from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, ValidationError, Length
# Importe todos os modelos necessários para os SelectFields
# Importamos Precificacao e Estoque para popular choices
from models import Usuario, Ingrediente, Condimento, Marmita, Precificacao, Estoque


# Formulário de Registro
class RegistrationForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(message='Email inválido.'), Length(max=120)])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6, message='A senha deve ter pelo menos 6 caracteres.')])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('senha', message='As senhas não conferem.')])
    submit = SubmitField('Registrar')

    # Validação customizada para checar se o email já existe
    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError('Este email já está cadastrado. Por favor, escolha outro.')

# Formulário de Login
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message='Email inválido.')])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

# Formulário para Ingredientes
class IngredienteForm(FlaskForm):
    nome = StringField('Nome do Ingrediente', validators=[DataRequired()])
    quantidade_comprada = FloatField('Quantidade Comprada', validators=[DataRequired(), NumberRange(min=0.01)])
    unidade_medida = SelectField('Unidade de Medida', choices=[
        ('kg', 'Quilogramas (kg)'),
        ('g', 'Gramas (g)'),
        ('L', 'Litros (L)'),
        ('ml', 'Mililitros (ml)'),
        ('un', 'Unidades (un)')
    ], validators=[DataRequired()])
    total_pago = FloatField('Total Pago', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Adicionar Ingrediente')

    def validate_nome(self, nome):
        ingrediente = Ingrediente.query.filter_by(nome=nome.data).first()
        if ingrediente:
            raise ValidationError('Este ingrediente já existe. Considere atualizar o estoque.')

# Formulário para Condimentos
class CondimentoForm(FlaskForm):
    nome = StringField('Nome do Condimento', validators=[DataRequired()])
    rendimento = FloatField('Rendimento Total (na unidade selecionada)', validators=[DataRequired(), NumberRange(min=0.01)])
    unidade_medida_rendimento = SelectField('Unidade de Medida do Rendimento', choices=[
        ('kg', 'Quilogramas (kg)'),
        ('g', 'Gramas (g)'),
        ('L', 'Litros (L)'),
        ('ml', 'Mililitros (ml)'),
        ('porcao', 'Porções (porcao)')
    ], validators=[DataRequired()])
    submit = SubmitField('Adicionar Condimento')

    def validate_nome(self, nome):
        condimento = Condimento.query.filter_by(nome=nome.data).first()
        if condimento:
            raise ValidationError('Este condimento já existe.')

# NOVO: Formulário para adicionar Ingredientes a um Condimento (CondimentoItem)
class CondimentoItemForm(FlaskForm):
    # O choices será preenchido dinamicamente na rota
    ingrediente_id = SelectField('Ingrediente', coerce=int, validators=[DataRequired()])
    quantidade_do_ingrediente = FloatField('Quantidade do Ingrediente', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Adicionar Ingrediente ao Condimento')

# Formulário para Marmitas (Receitas) - Ajustado
class MarmitaForm(FlaskForm):
    nome = StringField('Nome da Marmita', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    rendimento_receita = FloatField('Rendimento da Receita (em porções)', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Adicionar Marmita')

# NOVO: Formulário para associar Condimentos a uma Marmita (MarmitaCondimento)
class MarmitaCondimentoForm(FlaskForm):
    # O choices será preenchido dinamicamente na rota
    condimento_id = SelectField('Condimento', coerce=int, validators=[DataRequired()])
    quantidade_do_condimento = FloatField('Quantidade do Condimento', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Associar Condimento à Marmita')

# NOVO: Formulário para Precificação
class PrecificacaoForm(FlaskForm):
    # O choices será preenchido dinamicamente na rota com as marmitas disponíveis
    marmita_id = SelectField('Marmita', coerce=int, validators=[DataRequired()])
    valor_de_venda = FloatField('Valor de Venda', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Definir Precificação')

    def validate_marmita_id(self, marmita_id):
        # Valida se já existe uma precificação para esta marmita
        precificacao_existente = Precificacao.query.filter_by(marmita_id=marmita_id.data).first()
        if precificacao_existente:
            raise ValidationError('Já existe uma precificação para esta marmita. Por favor, edite a existente.')

# NOVO: Formulário para Estoque (Produção) - AJUSTADO
class EstoqueForm(FlaskForm):
    # O choices será preenchido dinamicamente na rota com as PRECIFICAÇÕES disponíveis
    # Agora selecionamos a precificação diretamente para o estoque
    precificacao_id = SelectField('Marmita Precificada', coerce=int, validators=[DataRequired()])
    quantidade = IntegerField('Quantidade a Produzir', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Produzir para Estoque')

    def validate_precificacao_id(self, precificacao_id):
        # Valida se já existe um registro de estoque para esta precificação
        estoque_existente = Estoque.query.filter_by(precificacao_id=precificacao_id.data).first()
        if estoque_existente:
            raise ValidationError('Já existe um registro de estoque para esta precificação. Por favor, ajuste a quantidade no estoque existente.')


# NOVO: Formulário para Pedidos - AJUSTADO
class PedidoForm(FlaskForm):
    nome_cliente = StringField('Nome do Cliente', validators=[DataRequired(), Length(min=2, max=100)])
    email_cliente = StringField('Email do Cliente', validators=[Email(message='Email inválido.'), Length(max=120)])
    contato_cliente = StringField('Contato do Cliente', validators=[Length(max=50)])
    # O choices será preenchido dinamicamente na rota com os ITENS EM ESTOQUE disponíveis
    # Agora selecionamos um item de estoque diretamente para o pedido
    estoque_id = SelectField('Marmita em Estoque', coerce=int, validators=[DataRequired()])
    quantidade_marmita_id = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Registrar Pedido')

    def validate_quantidade_marmita_id(self, quantidade_marmita_id):
        # Validação para garantir que há estoque suficiente
        estoque_id_selecionado = self.estoque_id.data
        if estoque_id_selecionado:
            estoque_item = Estoque.query.filter_by(id=estoque_id_selecionado).first()
            if not estoque_item or estoque_item.quantidade < quantidade_marmita_id.data:
                raise ValidationError(f'Quantidade solicitada excede o estoque disponível ({estoque_item.quantidade if estoque_item else 0} unidades).')