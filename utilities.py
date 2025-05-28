from flask import session, flash, redirect, url_for
from functools import wraps
# Importe todos os modelos necessários
from models import db, Carrinho, CarrinhoItem, Marmita, Ingrediente, Condimento, CondimentoItem, MarmitaCondimento, Precificacao, Estoque, Pedido, Venda, VendaItem


def get_user_carrinho_db():
    """Obtém ou cria o carrinho de compras para o usuário logado."""
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
    """Obtém os detalhes dos itens no carrinho do usuário."""
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
            except (ValueError, TypeError): # Adicionado TypeError para robustez
                subtotal = 0.0
                print(f"Warning: Preço para o item do carrinho {carrinho_item.id} não é um número válido.")

            total_carrinho += subtotal
            itens_detalhes.append({
                'marmita': marmita,
                'quantidade': carrinho_item.quantidade,
                'subtotal': subtotal,
                'carrinho_item_id': carrinho_item.id,
                'preco_unitario': carrinho_item.preco_unitario
            })
    return itens_detalhes, total_carrinho

def login_required(f):
    """Decorador para rotas que exigem login do usuário."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'info')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper

# --- Funções de Cálculo e Lógica de Negócio ---

def calcular_custo_unitario_ingrediente(ingrediente):
    """Calcula e atualiza o custo por unidade de um ingrediente."""
    if ingrediente.quantidade_comprada > 0 and ingrediente.total_pago is not None:
        ingrediente.custo_por_unidade = ingrediente.total_pago / ingrediente.quantidade_comprada
    else:
        ingrediente.custo_por_unidade = 0.0
    # Não commit aqui, o commit deve ser feito na rota que chamou esta função.
    # db.session.add(ingrediente) # Já está no session se veio do db.session.get() ou foi adicionado
    return ingrediente.custo_por_unidade


def calcular_custo_condimento(condimento):
    """
    Calcula o custo total e o custo unitário de um condimento
    com base nos ingredientes e suas quantidades.
    """
    custo_total_condimento = 0.0
    for item in condimento.itens: # Acessa os CondimentoItem
        if item.ingrediente and item.ingrediente.custo_por_unidade is not None:
            # Assumimos que as unidades de medida são compatíveis ou já normalizadas.
            # Em um sistema real, haveria conversão de unidades aqui.
            custo_total_condimento += item.quantidade_do_ingrediente * item.ingrediente.custo_por_unidade
        else:
            print(f"Atenção: Ingrediente {item.ingrediente.nome if item.ingrediente else 'ID Desconhecido'} do Condimento {condimento.nome} não tem custo unitário definido.")

    condimento.custo_total = custo_total_condimento
    if condimento.rendimento and condimento.rendimento > 0:
        condimento.custo_unitario = condimento.custo_total / condimento.rendimento
    else:
        condimento.custo_unitario = 0.0
    # Não commit aqui, o commit deve ser feito na rota que chamou esta função.
    # db.session.add(condimento)
    return condimento.custo_unitario


def calcular_custo_unitario_marmita_receita(marmita):
    """
    Calcula o custo unitário de produção de uma marmita (receita)
    com base nos condimentos associados e seus custos unitários.
    """
    custo_total_receita = 0.0
    for mc in marmita.condimento_itens: # Acessa os MarmitaCondimento
        if mc.condimento and mc.condimento.custo_unitario is not None:
            # Custo x Quantidade do Condimento na Marmita
            custo_total_receita += mc.quantidade_do_condimento * mc.condimento.custo_unitario
        else:
            print(f"Atenção: Condimento {mc.condimento.nome if mc.condimento else 'ID Desconhecido'} da Marmita {marmita.nome} não tem custo unitário definido.")

    # O custo unitário da marmita é o custo total da receita dividido pelo rendimento da receita
    if marmita.rendimento_receita and marmita.rendimento_receita > 0:
        marmita.custo_unitario_producao = custo_total_receita / marmita.rendimento_receita
    else:
        marmita.custo_unitario_producao = 0.0

    # Não commit aqui
    return marmita.custo_unitario_producao


def calcular_precificacao(precificacao):
    """
    Calcula e atualiza a margem de lucro e o valor do lucro
    para uma precificação específica.
    """
    marmita = precificacao.marmita
    if not marmita or marmita.custo_unitario_producao is None:
        print(f"Atenção: Marmita {precificacao.marmita_id} ou seu custo de produção não encontrado para precificação.")
        precificacao.custo_marmita = 0.0
        precificacao.margem_de_lucro_percentual = 0.0
        precificacao.valor_do_lucro = 0.0
        return

    precificacao.custo_marmita = marmita.custo_unitario_producao

    if precificacao.valor_de_venda > 0:
        # Margem de Lucro = ((Valor de Venda - Custo_Marmita) / Valor de Venda) * 100
        precificacao.margem_de_lucro_percentual = ((precificacao.valor_de_venda - precificacao.custo_marmita) / precificacao.valor_de_venda) * 100
        precificacao.valor_do_lucro = precificacao.valor_de_venda - precificacao.custo_marmita
    else:
        precificacao.margem_de_lucro_percentual = 0.0
        precificacao.valor_do_lucro = 0.0

    # Não commit aqui
    return precificacao.margem_de_lucro_percentual, precificacao.valor_do_lucro


def atualizar_estoque_apos_producao(estoque_item, quantidade_produzida):
    """
    Atualiza a quantidade em estoque e o custo de referência do estoque.
    Assume que o estoque_item já existe ou foi criado na rota.
    """
    precificacao = estoque_item.precificacao_referencia
    if not precificacao:
        print(f"Atenção: Precificação não encontrada para o estoque da marmita {estoque_item.marmita_id}.")
        estoque_item.custo_marmita_precificacao = 0.0
    else:
        estoque_item.custo_marmita_precificacao = precificacao.custo_marmita

    estoque_item.quantidade += quantidade_produzida
    # Não commit aqui
    return estoque_item.quantidade


def processar_pedido(pedido):
    """
    Processa um pedido: calcula o total da compra e atualiza o estoque.
    """
    estoque_item = Estoque.query.filter_by(marmita_id=pedido.marmita_id).first()

    if not estoque_item or estoque_item.quantidade < pedido.quantidade_marmita_id:
        # Isso já deve ser validado no formulário, mas é uma segurança extra.
        print(f"Erro: Estoque insuficiente para a marmita {pedido.marmita_id}.")
        return False

    # Puxa o custo da marmita do estoque (que por sua vez puxa da precificação)
    pedido.custo_marmita = estoque_item.custo_marmita_precificacao
    pedido.total_da_compra = pedido.custo_marmita * pedido.quantidade_marmita_id

    # Diminui a quantidade no estoque
    estoque_item.quantidade -= pedido.quantidade_marmita_id

    # Não commit aqui
    return True