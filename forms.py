from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, ValidationError, Length
from models import Usuario, Ingrediente, Condimento

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

class CondimentoForm(FlaskForm):
    nome = StringField('Nome do Condimento', validators=[DataRequired()])
    rendimento = FloatField('Rendimento Total (na unidade selecionada)', validators=[DataRequired(), NumberRange(min=0.01)])
    unidade_medida_rendimento = SelectField('Unidade de Medida do Rendimento', choices=[
        ('kg', 'Quilogramas (kg)'),
        ('g', 'Gramas (g)'),
        ('L', 'Litros (L)'),
        ('ml', 'Mililitros (ml)'),
        ('porcao', 'Porções (porcao)') # Condimentos podem ser medidos em porções
    ], validators=[DataRequired()])
    submit = SubmitField('Adicionar Condimento')

    def validate_nome(self, nome):
        condimento = Condimento.query.filter_by(nome=nome.data).first()
        if condimento:
            raise ValidationError('Este condimento já existe.')

class MarmitaForm(FlaskForm):
    nome = StringField('Nome da Marmita', validators=[DataRequired()])
    preco = FloatField('Preço de Venda', validators=[DataRequired(), NumberRange(min=0.01)])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    unidade_medida = SelectField('Unidade de Medida da Marmita', choices=[
        ('un', 'Unidade'),
        ('g', 'Gramas'),
        ('kg', 'Quilogramas')
    ], validators=[DataRequired()])
    margem_lucro_percentual = FloatField('Margem de Lucro (%)', validators=[DataRequired(), NumberRange(min=0.01, max=100.0)])
    submit = SubmitField('Adicionar Marmita')