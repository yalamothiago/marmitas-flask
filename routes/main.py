from flask import (
    Blueprint,
    render_template,
    request,
    url_for,
    flash,
    session,
    redirect
)

from forms import FlaskForm
from utilities import get_user_carrinho_db, obter_carrinho_detalhes_db

from models import (
    db,
    Marmita,
    Usuario,
    Venda,
    VendaItem,
    Carrinho,
    CarrinhoItem
)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    marmitas = Marmita.query.filter(Marmita.quantidade > 0).all()
    mensagem = request.args.get('mensagem')
    form_adicionar_carrinho = FlaskForm()
    return render_template('main/index.html', marmitas=marmitas, mensagem=mensagem, form=form_adicionar_carrinho)

@main_bp.route('/carrinho')
def ver_carrinho():
    itens, total = obter_carrinho_detalhes_db()
    return render_template('carrinho.html', itens=itens, total=total)

@main_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para finalizar a compra.", "info")
        return redirect(url_for('auth.login'))

    usuario = db.session.get(Usuario, session['usuario_id'])
    itens_carrinho_db, total_carrinho_db = obter_carrinho_detalhes_db()

    if request.method == 'POST':

        # 1. Validação de carrinho vazio
        if not itens_carrinho_db:
            flash("Carrinho vazio. Adicione itens antes de finalizar a compra.", "warning")
            # Pode redirecionar para o carrinho ou renderizar o checkout com a mensagem
            return render_template(
                'checkout.html',
                itens=itens_carrinho_db,
                total=total_carrinho_db
            )

        # 2. Obter e validar a forma de pagamento
        forma_pagamento = request.form.get('pagamento')
        if not forma_pagamento:
            flash("Forma de pagamento é obrigatória.", "danger")
            return render_template(
                'checkout.html',
                itens=itens_carrinho_db,
                total=total_carrinho_db
            )

        # 3. Validação de estoque
        for item_do_carrinho in itens_carrinho_db:
            marmita_atualizada = db.session.get(Marmita, item_do_carrinho['marmita'].id)
            if not marmita_atualizada or marmita_atualizada.quantidade < item_do_carrinho['quantidade']:
                flash(f"Estoque insuficiente para {item_do_carrinho['marmita'].nome}. Por favor, ajuste a quantidade.", "danger")
                return render_template(
                    'checkout.html',
                    itens=itens_carrinho_db,
                    total=total_carrinho_db
                )

        try:
            with db.session.begin_nested():
                nova_venda = Venda(
                    usuario_id=usuario.id,
                    total=total_carrinho_db,
                    forma_pagamento=forma_pagamento 
                )
                db.session.add(nova_venda)
                db.session.flush()

                for item_do_carrinho in itens_carrinho_db:
                    venda_item = VendaItem(
                        venda_id=nova_venda.id,
                        marmita_id=item_do_carrinho['marmita'].id,
                        quantidade=item_do_carrinho['quantidade'],
                        preco_unitario=item_do_carrinho['preco_unitario']
                    )
                    db.session.add(venda_item)

                    marmita_no_estoque = db.session.get(Marmita, item_do_carrinho['marmita'].id)
                    marmita_no_estoque.quantidade -= item_do_carrinho['quantidade']
                
                carrinho_do_usuario = get_user_carrinho_db()
                for item in list(carrinho_do_usuario.itens):
                    db.session.delete(item)
                
                db.session.commit()

            flash(f'✅ Pedido realizado com sucesso! ID: {nova_venda.id}', 'success')
            return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            print(f"Erro ao finalizar compra: {e}")
            flash("Ocorreu um erro ao finalizar o pedido. Tente novamente.", 'danger')
            return render_template(
                'checkout.html',
                erro="Ocorreu um erro ao finalizar o pedido. Tente novamente.",
                itens=itens_carrinho_db,
                total=total_carrinho_db
            )
            
    return render_template('checkout.html', itens=itens_carrinho_db, total=total_carrinho_db)