from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from models import Usuario # Importe o modelo de Usuário para validação customizada

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