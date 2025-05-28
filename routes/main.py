# routes/main.py
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
from utilities import get_user_carrinho_db, obter_carrinho_detalhes_db, processar_pedido

from models import (
    db,
    Marmita,
    Usuario,
    Venda,
    VendaItem,
    Carrinho,
    CarrinhoItem,
    Estoque,
    Precificacao,
    Pedido # <--- ADICIONE ESTA LINHA AQUI
)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Exibe a página inicial com as marmitas disponíveis em estoque.
    As marmitas são consideradas disponíveis se houver quantidade > 0 no Estoque.
    """
    estoque_items_em_estoque = Estoque.query.filter(Estoque.quantidade > 0).all()

    marmitas_disponiveis = []
    for item in estoque_items_em_estoque:
        if item.precificacao_referencia and item.precificacao_referencia.marmita:
            marmitas_disponiveis.append({
                'marmita': item.precificacao_referencia.marmita,
                'quantidade_em_estoque': item.quantidade,
                'valor_de_venda': item.precificacao_referencia.valor_de_venda,
                'estoque_id': item.id
            })

    mensagem = request.args.get('mensagem')
    form_adicionar_carrinho = FlaskForm()

    return render_template('main/index.html', marmitas_disponiveis=marmitas_disponiveis, mensagem=mensagem, form=form_adicionar_carrinho)


@main_bp.route('/carrinho')
def ver_carrinho():
    """
    Exibe o conteúdo do carrinho de compras do usuário.
    """
    itens, total = obter_carrinho_detalhes_db()
    return render_template('carrinho.html', itens=itens, total=total)


@main_bp.route('/adicionar_ao_carrinho/<int:estoque_id>', methods=['POST'])
def adicionar_ao_carrinho(estoque_id):
    """
    Adiciona uma marmita ao carrinho de compras do usuário.
    """
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para adicionar itens ao carrinho.", "info")
        return redirect(url_for('auth.login'))

    estoque_item = db.session.get(Estoque, estoque_id)
    if not estoque_item or estoque_item.quantidade <= 0:
        flash("Marmita não disponível em estoque.", "danger")
        return redirect(url_for('main.index'))

    preco_unitario = estoque_item.precificacao_referencia.valor_de_venda if estoque_item.precificacao_referencia else 0.0

    carrinho = get_user_carrinho_db()
    
    carrinho_item_existente = CarrinhoItem.query.filter_by(
        carrinho_id=carrinho.id,
        marmita_id=estoque_item.precificacao_referencia.marmita.id
    ).first()

    if carrinho_item_existente:
        if carrinho_item_existente.quantidade + 1 <= estoque_item.quantidade:
            carrinho_item_existente.quantidade += 1
            flash(f'Quantidade de {estoque_item.precificacao_referencia.marmita.nome} atualizada no carrinho!', 'success')
        else:
            flash(f'Estoque máximo de {estoque_item.precificacao_referencia.marmita.nome} atingido no carrinho.', 'warning')
    else:
        novo_item_carrinho = CarrinhoItem(
            carrinho_id=carrinho.id,
            marmita_id=estoque_item.precificacao_referencia.marmita.id,
            quantidade=1,
            preco_unitario=preco_unitario
        )
        db.session.add(novo_item_carrinho)
        flash(f'{estoque_item.precificacao_referencia.marmita.nome} adicionada ao carrinho!', 'success')

    db.session.commit()
    return redirect(url_for('main.ver_carrinho'))


@main_bp.route('/remover_do_carrinho/<int:item_id>', methods=['POST'])
def remover_do_carrinho(item_id):
    """
    Remove um item do carrinho de compras.
    """
    carrinho_item = db.session.get(CarrinhoItem, item_id)
    if carrinho_item:
        db.session.delete(carrinho_item)
        db.session.commit()
        flash('Item removido do carrinho.', 'info')
    else:
        flash('Item não encontrado no carrinho.', 'warning')
    return redirect(url_for('main.ver_carrinho'))


@main_bp.route('/atualizar_quantidade_carrinho/<int:item_id>', methods=['POST'])
def atualizar_quantidade_carrinho(item_id):
    """
    Atualiza a quantidade de um item no carrinho.
    """
    carrinho_item = db.session.get(CarrinhoItem, item_id)
    if not carrinho_item:
        flash('Item do carrinho não encontrado.', 'warning')
        return redirect(url_for('main.ver_carrinho'))

    try:
        nova_quantidade = int(request.form['quantidade'])
        if nova_quantidade <= 0:
            db.session.delete(carrinho_item)
            flash('Item removido do carrinho.', 'info')
        else:
            estoque_item = Estoque.query.filter_by(
                precificacao_id=carrinho_item.marmita.precificacao.id
            ).first()

            if not estoque_item or nova_quantidade > estoque_item.quantidade:
                flash(f"Estoque insuficiente para {carrinho_item.marmita.nome}. Quantidade máxima disponível: {estoque_item.quantidade if estoque_item else 0}.", "danger")
            else:
                carrinho_item.quantidade = nova_quantidade
                flash(f'Quantidade de {carrinho_item.marmita.nome} atualizada para {nova_quantidade}.', 'success')
        db.session.commit()
    except ValueError:
        flash('Quantidade inválida.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar quantidade: {e}', 'danger')
    return redirect(url_for('main.ver_carrinho'))


@main_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """
    Gerencia o processo de finalização da compra.
    """
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para finalizar a compra.", "info")
        return redirect(url_for('auth.login'))

    usuario = db.session.get(Usuario, session['usuario_id'])
    itens_carrinho_db, total_carrinho_db = obter_carrinho_detalhes_db()

    if request.method == 'POST':
        if not itens_carrinho_db:
            flash("Carrinho vazio. Adicione itens antes de finalizar a compra.", "warning")
            return render_template(
                'checkout.html',
                itens=itens_carrinho_db,
                total=total_carrinho_db
            )

        forma_pagamento = request.form.get('pagamento')
        if not forma_pagamento:
            flash("Forma de pagamento é obrigatória.", "danger")
            return render_template(
                'checkout.html',
                itens=itens_carrinho_db,
                total=total_carrinho_db
            )

        try:
            with db.session.begin_nested():
                # O bloco de código que usava 'Pedido' foi removido ou comentado
                # Se você o reintroduziu, precisa da importação.
                # Se não, o erro pode estar em outra parte do seu código.

                # Se você ainda tem o bloco de Pedido aqui, ele deve estar assim:
                novo_pedido_obj = Pedido( # <--- AQUI A CLASSE PEDIDO É USADA
                    nome_cliente=usuario.nome,
                    email_cliente=usuario.email,
                    contato_cliente=usuario.email,
                    cliente_id=usuario.id,
                    # estoque_id e quantidade_marmita_id seriam preenchidos aqui
                    # ou você criaria PedidoItem se um Pedido pudesse ter vários itens
                )
                db.session.add(novo_pedido_obj)
                db.session.flush() # Para ter o ID do pedido

                nova_venda = Venda(
                    usuario_id=usuario.id,
                    total=total_carrinho_db,
                    forma_pagamento=forma_pagamento
                )
                db.session.add(nova_venda)
                db.session.flush() # Para ter o ID da venda antes de adicionar os itens

                for item_do_carrinho in itens_carrinho_db:
                    precificacao_marmita = Precificacao.query.filter_by(marmita_id=item_do_carrinho['marmita'].id).first()
                    if not precificacao_marmita:
                        raise ValueError(f"Precificação não encontrada para a marmita {item_do_carrinho['marmita'].nome}.")

                    estoque_associado = Estoque.query.filter_by(precificacao_id=precificacao_marmita.id).first()
                    if not estoque_associado:
                        raise ValueError(f"Estoque não encontrado para a marmita {item_do_carrinho['marmita'].nome}.")

                    if estoque_associado.quantidade < item_do_carrinho['quantidade']:
                        flash(f"Estoque insuficiente para {item_do_carrinho['marmita'].nome}. Disponível: {estoque_associado.quantidade}.", "danger")
                        db.session.rollback()
                        return render_template(
                            'checkout.html',
                            itens=itens_carrinho_db,
                            total=total_carrinho_db
                        )

                    estoque_associado.quantidade -= item_do_carrinho['quantidade']
                    db.session.add(estoque_associado)

                    venda_item = VendaItem(
                        venda_id=nova_venda.id,
                        marmita_id=item_do_carrinho['marmita'].id,
                        quantidade=item_do_carrinho['quantidade'],
                        preco_unitario=item_do_carrinho['preco_unitario']
                    )
                    db.session.add(venda_item)

                carrinho_do_usuario = get_user_carrinho_db()
                for item in list(carrinho_do_usuario.itens):
                    db.session.delete(item)
                
                db.session.commit()

            flash(f'✅ Pedido realizado com sucesso! ID da Venda: {nova_venda.id}', 'success')
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
