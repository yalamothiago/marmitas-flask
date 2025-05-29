from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, ValidationError, Length
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
        # Massa
        ('kg', 'Quilogramas (kg)'),
        ('g', 'Gramas (g)'),
        ('mg', 'Miligramas (mg)'),
        # Volume
        ('L', 'Litros (L)'),
        ('ml', 'Mililitros (ml)'),
        # Contagem/Unidades
        ('un', 'Unidades (un)'),
        ('dz', 'Dúzia (dz)'),
        ('pct', 'Pacote (pct)')
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
        # Massa
        ('kg', 'Quilogramas (kg)'),
        ('g', 'Gramas (g)'),
        ('mg', 'Miligramas (mg)'),
        # Volume
        ('L', 'Litros (L)'),
        ('ml', 'Mililitros (ml)'),
        # Contagem/Porções
        ('un', 'Unidades (un)'),
        ('porcao', 'Porções (porcao)'), # Condimentos podem render em porções
        ('dz', 'Dúzia (dz)'),
        ('pct', 'Pacote (pct)')
    ], validators=[DataRequired()])
    submit = SubmitField('Adicionar Condimento')

    def validate_nome(self, nome):
        condimento = Condimento.query.filter_by(nome=nome.data).first()
        if condimento:
            raise ValidationError('Este condimento já existe.')


class CondimentoItemForm(FlaskForm):
    ingrediente_id = SelectField('Ingrediente', coerce=int, validators=[DataRequired()])
    # A unidade aqui é a unidade em que você adiciona o ingrediente ao condimento
    # Se você está usando 500g de frango, a unidade é 'g'
    quantidade_do_ingrediente = FloatField('Quantidade do Ingrediente', validators=[DataRequired(), NumberRange(min=0.01)])
    unidade_do_ingrediente_na_receita = SelectField('Unidade na Receita', choices=[
        # Massa
        ('kg', 'Quilogramas (kg)'),
        ('g', 'Gramas (g)'),
        ('mg', 'Miligramas (mg)'),
        # Volume
        ('L', 'Litros (L)'),
        ('ml', 'Mililitros (ml)'),
        # Contagem/Unidades
        ('un', 'Unidades (un)'),
        ('dz', 'Dúzia (dz)'),
        ('pct', 'Pacote (pct)')
    ], validators=[DataRequired()])
    submit = SubmitField('Adicionar Ingrediente ao Condimento')


class MarmitaForm(FlaskForm):
    nome = StringField('Nome da Marmita', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    rendimento_receita = FloatField('Rendimento da Receita', validators=[DataRequired(), NumberRange(min=0.01)])
 
    unidade_medida_producao = SelectField('Unidade de Medida do Rendimento', choices=[
        ('porcao', 'Porção (porcao)'), 
        ('un', 'Unidade (un)'),
        # Massa
        ('kg', 'Quilogramas (kg)'),
        ('g', 'Gramas (g)'),
        ('mg', 'Miligramas (mg)'),
        # Volume
        ('L', 'Litros (L)'),
        ('ml', 'Mililitros (ml)'),
    ], validators=[DataRequired()])
    submit = SubmitField('Adicionar Marmita')

class MarmitaCondimentoForm(FlaskForm):
    condimento_id = SelectField('Condimento', coerce=int, validators=[DataRequired()])
    quantidade_do_condimento = FloatField('Quantidade do Condimento', validators=[DataRequired(), NumberRange(min=0.01)])
    unidade_do_condimento_na_marmita = SelectField('Unidade na Marmita', choices=[
        # Massa
        ('kg', 'Quilogramas (kg)'),
        ('g', 'Gramas (g)'),
        ('mg', 'Miligramas (mg)'),
        # Volume
        ('L', 'Litros (L)'),
        ('ml', 'Mililitros (ml)'),
        # Contagem/Unidades
        ('un', 'Unidades (un)'),
        ('dz', 'Dúzia (dz)'),
        ('pct', 'Pacote (pct)'),
        ('porcao', 'Porção (porcao)') # Se um condimento pode ser usado em porções na marmita
    ], validators=[DataRequired()])
    submit = SubmitField('Associar Condimento à Marmita')


class PrecificacaoForm(FlaskForm):  
    marmita_id = SelectField('Marmita', coerce=int, validators=[DataRequired()])
    valor_de_venda = FloatField('Valor de Venda', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Definir Precificação')

    def validate_marmita_id(self, marmita_id):
       
        precificacao_existente = Precificacao.query.filter_by(marmita_id=marmita_id.data).first()
        if precificacao_existente:
            raise ValidationError('Já existe uma precificação para esta marmita. Por favor, edite a existente.')


class EstoqueForm(FlaskForm):

    precificacao_id = SelectField('Marmita Precificada', coerce=int, validators=[DataRequired()])
    quantidade = IntegerField('Quantidade a Produzir', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Produzir para Estoque')

    def validate_precificacao_id(self, precificacao_id):
        # Valida se já existe um registro de estoque para esta precificação
        estoque_existente = Estoque.query.filter_by(precificacao_id=precificacao_id.data).first()
        if estoque_existente:
            raise ValidationError('Já existe um registro de estoque para esta precificação. Por favor, ajuste a quantidade no estoque existente.')


class PedidoForm(FlaskForm):
    nome_cliente = StringField('Nome do Cliente', validators=[DataRequired(), Length(min=2, max=100)])
    email_cliente = StringField('Email do Cliente', validators=[Email(message='Email inválido.'), Length(max=120)])
    contato_cliente = StringField('Contato do Cliente', validators=[Length(max=50)])
  
    estoque_id = SelectField('Marmita em Estoque', coerce=int, validators=[DataRequired()])
    quantidade_marmita_id = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Registrar Pedido')

    def validate_quantidade_marmita_id(self, quantidade_marmita_id):
     
        estoque_id_selecionado = self.estoque_id.data
        if estoque_id_selecionado:
            estoque_item = Estoque.query.filter_by(id=estoque_id_selecionado).first()
            if not estoque_item or estoque_item.quantidade < quantidade_marmita_id.data:
                raise ValidationError(f'Quantidade solicitada excede o estoque disponível ({estoque_item.quantidade if estoque_item else 0} unidades).')