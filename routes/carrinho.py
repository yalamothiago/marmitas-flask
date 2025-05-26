from flask import Blueprint, session, jsonify, flash, redirect, url_for
from models import db, Marmita, CarrinhoItem
from utilities import get_user_carrinho_db # Importar funções úteis

carrinho_bp = Blueprint('carrinho', __name__)

@carrinho_bp.route('/adicionar/<int:marmita_id>', methods=['POST'])
def adicionar(marmita_id):
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para adicionar itens ao carrinho.", "info")
        return redirect(url_for('auth.login'))

    marmita = db.session.get(Marmita, marmita_id)
    if not marmita:
        flash('Marmita não encontrada.', 'danger')
        return redirect(url_for('main.index'))

    carrinho_db = get_user_carrinho_db()
    if not carrinho_db:
        flash('Erro ao carregar o carrinho do usuário.', 'danger')
        return redirect(url_for('main.index'))

    carrinho_item = CarrinhoItem.query.filter_by(
        carrinho_id=carrinho_db.id,
        marmita_id=marmita.id
    ).first()

    if carrinho_item:
        if carrinho_item.quantidade < marmita.quantidade:
            carrinho_item.quantidade += 1
            flash(f'Mais uma unidade de {marmita.nome} adicionada ao carrinho.', 'info')
        else:
            flash(f"Estoque insuficiente para adicionar mais de {marmita.nome}.", 'warning')
    else:
        if marmita.quantidade > 0:
            novo_carrinho_item = CarrinhoItem(
                carrinho_id=carrinho_db.id,
                marmita_id=marmita.id,
                quantidade=1,
                preco_unitario=marmita.preco
            )
            db.session.add(novo_carrinho_item)
            flash(f'{marmita.nome} adicionada ao carrinho.', 'success')
        else:
            flash(f"Estoque insuficiente para {marmita.nome}.", 'warning')
            
    db.session.commit()
    return redirect(url_for('main.index'))

@carrinho_bp.route('/aumentar/<int:carrinho_item_id>', methods=['POST'])
def aumentar(carrinho_item_id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'mensagem': 'Usuário não logado.'}), 401

    carrinho_item = db.session.get(CarrinhoItem, carrinho_item_id)
    if not carrinho_item:
        return jsonify({'success': False, 'mensagem': 'Item do carrinho não encontrado.'}), 404
        
    carrinho_do_usuario = get_user_carrinho_db()
    if not carrinho_do_usuario or carrinho_item.carrinho_id != carrinho_do_usuario.id:
        return jsonify({'success': False, 'mensagem': 'Acesso negado.'}), 403

    marmita = carrinho_item.marmita
    if not marmita:
        return jsonify({'success': False, 'mensagem': 'Marmita associada não encontrada.'}), 404

    if carrinho_item.quantidade < marmita.quantidade:
        carrinho_item.quantidade += 1
        db.session.commit()
        return jsonify({'success': True, 'nova_quantidade': carrinho_item.quantidade})
    else:
        return jsonify({'success': False, 'mensagem': 'Estoque insuficiente.'}), 400

@carrinho_bp.route('/diminuir/<int:carrinho_item_id>', methods=['POST'])
def diminuir(carrinho_item_id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'mensagem': 'Usuário não logado.'}), 401

    carrinho_item = db.session.get(CarrinhoItem, carrinho_item_id)
    if not carrinho_item:
        return jsonify({'success': False, 'mensagem': 'Item do carrinho não encontrado.'}), 404

    carrinho_do_usuario = get_user_carrinho_db()
    if not carrinho_do_usuario or carrinho_item.carrinho_id != carrinho_do_usuario.id:
        return jsonify({'success': False, 'mensagem': 'Acesso negado.'}), 403

    if carrinho_item.quantidade > 1:
        carrinho_item.quantidade -= 1
        db.session.commit()
        return jsonify({'success': True, 'nova_quantidade': carrinho_item.quantidade})
    else:
        marmita_nome = carrinho_item.marmita.nome if carrinho_item.marmita else "Item Desconhecido"
        db.session.delete(carrinho_item)
        db.session.commit()
        flash(f'"{marmita_nome}" foi removida do seu carrinho.', 'info')
        return jsonify({'success': True, 'removido': True})
        
@carrinho_bp.route('/remover_item_completo/<int:carrinho_item_id>', methods=['POST'])
def remover_item_completo(carrinho_item_id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'mensagem': 'Usuário não logado.'}), 401

    carrinho_item = db.session.get(CarrinhoItem, carrinho_item_id)
    if not carrinho_item:
        return jsonify({'success': False, 'mensagem': 'Item do carrinho não encontrado.'}), 404
        
    carrinho_do_usuario = get_user_carrinho_db()
    if not carrinho_do_usuario or carrinho_item.carrinho_id != carrinho_do_usuario.id:
        return jsonify({'success': False, 'mensagem': 'Acesso negado.'}), 403

    marmita_nome = carrinho_item.marmita.nome if carrinho_item.marmita else "Item Desconhecido"    

    db.session.delete(carrinho_item)
    db.session.commit()
    flash(f'"{marmita_nome}" foi removida do seu carrinho.', 'info')
    return jsonify({'success': True, 'mensagem': 'Item removido com sucesso.'})