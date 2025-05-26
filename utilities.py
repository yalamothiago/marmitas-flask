from flask import session, flash, redirect, url_for # Adicione estas importações
from functools import wraps # Adicione esta importação
from models import db, Carrinho, CarrinhoItem, Marmita

def get_user_carrinho_db():
    if 'usuario_id' not in session:
        return None
        
    user_id = session['usuario_id']
    carrinho = Carrinho.query.filter_by(user_id=user_id).first()
        
    if not carrinho:
        carrinho = Carrinho(user_id=user_id)
        db.session.add(carrinho)
        db.session.commit()
    return carrinho

def obter_carrinho_detalhes_db():
    if 'usuario_id' not in session:
        return [], 0

    carrinho_db = get_user_carrinho_db()
    if not carrinho_db:
        return [], 0

    itens_detalhes = []
    total_carrinho = 0

    for carrinho_item in carrinho_db.itens:
        marmita = carrinho_item.marmita
        if marmita:
            try:
                subtotal = carrinho_item.preco_unitario * carrinho_item.quantidade
            except ValueError:
                subtotal = 0.0
                print(f"Warning: Price for carrinho item {carrinho_item.id} is not a valid number.")

            total_carrinho += subtotal
            itens_detalhes.append({
                'marmita': marmita,
                'quantidade': carrinho_item.quantidade,
                'subtotal': subtotal,
                'carrinho_item_id': carrinho_item.id,
                'preco_unitario': carrinho_item.preco_unitario
            })
    return itens_detalhes, total_carrinho

# Outras funções úteis que você possa criar
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'info')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper