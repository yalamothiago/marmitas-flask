from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from models import db, Marmita
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def login_admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            flash('Você não tem permissão para acessar esta página.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return wrapper

@admin_bp.route('/', methods=['GET', 'POST'])
@login_admin_required
def painel_admin():
    if request.method == 'POST':
        # ... (lógica de adicionar marmita)
        try:
            nome = request.form['nome']
            preco = float(request.form['preco'])
            quantidade = int(request.form['quantidade'])
            descricao = request.form.get('descricao', '')

            marmita = Marmita(
                nome=nome,
                preco=preco,
                quantidade=quantidade,
                descricao=descricao
            )
            db.session.add(marmita)
            db.session.commit()
            flash('Marmita adicionada com sucesso!', 'success')
            return redirect(url_for('admin.painel_admin'))
        except ValueError:
            flash("Dados inválidos para a marmita. Verifique o preço e a quantidade.", "danger")
            return render_template('admin/admin.html', marmitas=Marmita.query.all())
            
    marmitas = Marmita.query.all()
    return render_template('admin/admin.html', marmitas=marmitas)

@admin_bp.route('/deletar/<int:id>')
@login_admin_required
def deletar_marmita(id):
    marmita = db.session.get(Marmita, id)
    if marmita:
        db.session.delete(marmita)
        db.session.commit()
        flash('Marmita deletada com sucesso!', 'success')
    else:
        flash('Marmita não encontrada.', 'warning')
    return redirect(url_for('admin.painel_admin'))

@admin_bp.route('/atualizar_estoque/<int:id>', methods=['POST'])
@login_admin_required
def atualizar_estoque(id):
    marmita = db.session.get(Marmita, id)
    if not marmita:
        flash('Marmita não encontrada.', 'warning')
        return redirect(url_for('admin.painel_admin'))

    try:
        adicional = int(request.form['quantidade_adicional'])
        if adicional > 0:
            marmita.quantidade += adicional
            db.session.commit()
            flash(f'Estoque de {marmita.nome} atualizado para {marmita.quantidade} unidades.', 'success')
        else:
            flash('Quantidade adicional deve ser maior que zero.', 'warning')
    except ValueError:
        flash('Quantidade adicional inválida.', 'danger')
    return redirect(url_for('admin.painel_admin'))