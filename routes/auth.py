from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from forms import RegistrationForm, LoginForm
from models import db, Usuario, Carrinho
from utilities import get_user_carrinho_db # Reutilize funções úteis

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistrationForm()
    if form.validate_on_submit():
        novo_usuario = Usuario(nome=form.nome.data, email=form.email.data)
        novo_usuario.set_senha(form.senha.data)
        db.session.add(novo_usuario)
        db.session.commit()

        novo_carrinho = Carrinho(usuario=novo_usuario)
        db.session.add(novo_carrinho)
        db.session.commit()

        session['usuario_id'] = novo_usuario.id
        session['admin'] = novo_usuario.administrador
        flash('Sua conta foi criada com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('main.index')) # Redireciona para a rota index do blueprint 'main'
    return render_template('auth/registro.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        senha = form.senha.data
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.verificar_senha(senha):
            session['usuario_id'] = usuario.id
            session['admin'] = usuario.administrador
            flash(f'Bem-vindo, {usuario.nome}!', 'success')
            return redirect(url_for('admin.painel_admin') if usuario.administrador else url_for('main.index'))
        else:
            flash('Login inválido. Verifique seu e-mail e senha.', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('main.index'))