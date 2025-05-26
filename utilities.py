from flask import session, flash, redirect, url_for # Adicione estas importações
from functools import wraps # Adicione esta importação
from models import db, Carrinho, CarrinhoItem, Marmita, Ingrediente, Condimento, CondimentoItem, MarmitaCondimento

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


def calcular_custo_unitario_ingrediente(ingrediente):
    """Calcula e atualiza o custo por unidade de um ingrediente."""
    if ingrediente.quantidade > 0 and ingrediente.total_pago is not None:
        ingrediente.custo_por_unidade = ingrediente.total_pago / ingrediente.quantidade
    else:
        ingrediente.custo_por_unidade = 0.0 # Define como zero se não houver quantidade ou total pago
    db.session.add(ingrediente)
    db.session.commit()
    return ingrediente.custo_por_unidade


def calcular_custo_condimento(condimento):
    """Calcula o custo total e o custo unitário de um condimento."""
    custo_total_condimento = 0.0
    for item in condimento.itens: # Acessa os CondimentoItem
        if item.ingrediente and item.ingrediente.custo_por_unidade is not None:
            # Assumimos que as unidades de medida são compatíveis ou já normalizadas.
            # Em um sistema real, haveria conversão de unidades aqui.
            custo_total_condimento += item.quantidade * item.ingrediente.custo_por_unidade
        else:
            # Se um ingrediente não tem custo, ou não existe, podemos alertar ou assumir 0.
            print(f"Atenção: Ingrediente {item.ingrediente.nome if item.ingrediente else 'ID Desconhecido'} do Condimento {condimento.nome} não tem custo unitário definido.")

    condimento.custo_total = custo_total_condimento
    if condimento.rendimento and condimento.rendimento > 0:
        condimento.custo_unitario = condimento.custo_total / condimento.rendimento
    else:
        condimento.custo_unitario = 0.0
    
    db.session.add(condimento)
    db.session.commit()
    return condimento.custo_unitario


def calcular_custo_marmita(marmita):
    """Calcula o custo de produção base de uma marmita."""
    custo_total_marmita = 0.0
    for mc in marmita.condimento_itens: # Acessa os MarmitaCondimento
        if mc.condimento and mc.condimento.custo_unitario is not None:
            # Assumimos que as unidades de medida são compatíveis ou já normalizadas.
            custo_total_marmita += mc.quantidade * mc.condimento.custo_unitario
        else:
            print(f"Atenção: Condimento {mc.condimento.nome if mc.condimento else 'ID Desconhecido'} da Marmita {marmita.nome} não tem custo unitário definido.")
    
    marmita.custo_producao_base = custo_total_marmita
    
    # Calcular valor de venda sugerido (Valor_Redstore) e margem
    if marmita.margem_lucro_percentual is not None and marmita.margem_lucro_percentual > 0:
        # Fórmula: Preço = Custo / (1 - Margem/100)
        # Marmita.preco é o VALOR DE VENDA, Marmita.custo_producao_base é o CUSTO
        # margem_lucro_percentual é o % de lucro sobre o VALOR DE VENDA
        # Então, Valor de Venda = Custo_producao_base / (1 - margem_lucro_percentual/100)
        
        # Invertendo para calcular margem_lucro_percentual do preço existente (se já tiver um)
        # Ou se o preço ainda não está definido, podemos calcular um preço sugerido
        if marmita.preco and marmita.custo_producao_base > 0:
            marmita.margem_lucro_percentual = ((marmita.preco - marmita.custo_producao_base) / marmita.preco) * 100
            marmita.valor_redstore = marmita.preco # Valor que ela já tem no banco
        else: # Se não tem preço ou custo base, não podemos calcular a margem real.
            marmita.margem_lucro_percentual = 0.0 # Ou um default.
            marmita.valor_redstore = 0.0
            
    db.session.add(marmita)
    db.session.commit()
    return marmita.custo_producao_base