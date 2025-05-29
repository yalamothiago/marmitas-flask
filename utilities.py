from flask import session, flash, redirect, url_for
from functools import wraps
# Importe todos os modelos necessários
from models import db, Carrinho, CarrinhoItem, Marmita, Ingrediente, Condimento, CondimentoItem, MarmitaCondimento, Precificacao, Estoque, Pedido, Venda, VendaItem

# Dicionário de fatores de conversão para uma unidade base (ex: gramas para massa, mililitros para volume)
# As chaves são (unidade, tipo_de_medida). Valores são o fator para converter para a unidade base.
# Ex: 1 kg = 1000 g, 1 L = 1000 ml. 'un' é 1 para si mesma.
UNIDADE_BASES = {
    'massa': 'g',
    'volume': 'ml',
    'contagem': 'un'
}

CONVERSAO_UNIDADES = {
    # Massa para Gramas (g)
    ('kg', 'massa'): 1000, # 1 kg = 1000 g
    ('g', 'massa'): 1,
    ('mg', 'massa'): 0.001,

    # Volume para Mililitros (ml)
    ('L', 'volume'): 1000,
    ('ml', 'volume'): 1,
    ('colher_cha', 'volume'): 5, # Exemplo: 1 colher de chá = 5ml
    ('colher_sopa', 'volume'): 15, # Exemplo: 1 colher de sopa = 15ml

    # Contagem para Unidade (un)
    ('un', 'contagem'): 1,
    ('pct', 'contagem'): 1, # Exemplo: 1 pacote = 1 unidade
    ('dz', 'contagem'): 12, # Exemplo: 1 dúzia = 12 unidades
}

# Mapeamento para inferir o tipo de medida de uma unidade
TIPO_MEDIDA_POR_UNIDADE = {
    'kg': 'massa', 'g': 'massa', 'mg': 'massa',
    'L': 'volume', 'ml': 'volume', 'colher_cha': 'volume', 'colher_sopa': 'volume',
    'un': 'contagem', 'pct': 'contagem', 'dz': 'contagem',
    'porcao': 'contagem' # Assumindo 'porcao' como uma unidade de contagem para rendimento
}


def converter_unidade(quantidade, unidade_origem, unidade_destino):
    """
    Converte uma quantidade de uma unidade para outra.
    Retorna a quantidade convertida ou None se a conversão não for possível.
    """
    tipo_origem = TIPO_MEDIDA_POR_UNIDADE.get(unidade_origem)
    tipo_destino = TIPO_MEDIDA_POR_UNIDADE.get(unidade_destino)

    if not tipo_origem or not tipo_destino or tipo_origem != tipo_destino:
        print(f"DEBUG CONVERSAO: Tipos de medida incompatíveis ou não definidos: {unidade_origem} ({tipo_origem}) para {unidade_destino} ({tipo_destino})")
        return None

    fator_origem_para_base = CONVERSAO_UNIDADES.get((unidade_origem, tipo_origem))
    fator_base_para_destino = 1 / CONVERSAO_UNIDADES.get((unidade_destino, tipo_destino))

    if fator_origem_para_base is None or fator_base_para_destino is None:
        print(f"DEBUG CONVERSAO: Fatores de conversão não definidos para {unidade_origem} ou {unidade_destino}.")
        return None

    quantidade_em_base = quantidade * fator_origem_para_base
    quantidade_convertida = quantidade_em_base * fator_base_para_destino
    
    print(f"DEBUG CONVERSAO: {quantidade} {unidade_origem} -> {quantidade_convertida} {unidade_destino}")

    return quantidade_convertida

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
    return ingrediente.custo_por_unidade


def calcular_custo_condimento(condimento):
    """
    Calcula o custo total e o custo unitário de um condimento
    com base nos ingredientes e suas quantidades, com conversão de unidades.
    """
    custo_total_condimento = 0.0
    
    unidade_destino_condimento = condimento.unidade_medida_rendimento
    tipo_destino_condimento = TIPO_MEDIDA_POR_UNIDADE.get(unidade_destino_condimento)

    if not tipo_destino_condimento:
        print(f"Atenção: Unidade de medida de rendimento do condimento '{unidade_destino_condimento}' não reconhecida ou sem tipo de medida definido.")
        condimento.custo_total = 0.0
        condimento.custo_unitario = 0.0
        return condimento.custo_unitario

    for item in condimento.itens: # Acessa os CondimentoItem (ingredientes que compõem o condimento)
        if item.ingrediente and item.ingrediente.custo_por_unidade is not None:
            unidade_ingrediente_na_receita = item.unidade_do_ingrediente_na_receita # Ex: 'g'
            quantidade_ingrediente = item.quantidade_do_ingrediente # Ex: 1000
            custo_unitario_ingrediente = item.ingrediente.custo_por_unidade # Ex: 12.00 (R$/kg)
            unidade_compra_ingrediente = item.ingrediente.unidade_medida # Ex: 'kg'

            print(f"\n--- DEBUG CALCULO CONDIMENTO: {condimento.nome} ---")
            print(f"Ingrediente: {item.ingrediente.nome}")
            print(f"Quant. na receita: {quantidade_ingrediente} {unidade_ingrediente_na_receita}")
            print(f"Custo unitário ingrediente (compra): {custo_unitario_ingrediente} R$/{unidade_compra_ingrediente}")
            print(f"Unidade de compra do ingrediente: {unidade_compra_ingrediente}")
            print(f"Unidade na receita do condimento: {unidade_ingrediente_na_receita}")


            # Converter a QUANTIDADE_DO_INGREDIENTE para a unidade de medida do INGREDIENTE COMPRADO.
            # Ex: Se custo é R$/kg, e quantidade na receita é em 'g', precisamos converter 'g' para 'kg'.
            quantidade_para_calculo = converter_unidade(
                quantidade_ingrediente,             # Ex: 1000
                unidade_ingrediente_na_receita,     # Ex: 'g'
                unidade_compra_ingrediente          # Ex: 'kg'
            )
            
            if quantidade_para_calculo is None:
                print(f"Atenção: Não foi possível converter a unidade para o ingrediente '{item.ingrediente.nome}'. Verifique as unidades '{unidade_ingrediente_na_receita}' e '{unidade_compra_ingrediente}'.")
                continue

            custo_contribuido_por_item = quantidade_para_calculo * custo_unitario_ingrediente
            print(f"Custo Contribuído por {item.ingrediente.nome}: {custo_contribuido_por_item}")
            custo_total_condimento += custo_contribuido_por_item
        else:
            print(f"Atenção: Ingrediente {item.ingrediente.nome if item.ingrediente else 'ID Desconhecido'} do Condimento {condimento.nome} não tem custo unitário definido.")

    print(f"Custo Total Condimento {condimento.nome}: {custo_total_condimento}")

    condimento.custo_total = custo_total_condimento
    if condimento.rendimento and condimento.rendimento > 0:
        condimento.custo_unitario = condimento.custo_total / condimento.rendimento
    else:
        condimento.custo_unitario = 0.0
    print(f"Custo Unitário Condimento {condimento.nome}: {condimento.custo_unitario}")
    return condimento.custo_unitario

def calcular_custo_unitario_marmita_receita(marmita):
    """
    Calcula o custo unitário de produção de uma marmita (receita)
    com base nos condimentos associados e seus custos unitários, com conversão de unidades.
    """
    custo_total_receita = 0.0
    
    unidade_rendimento_marmita = marmita.unidade_medida_producao # Usa a unidade de medida de produção da marmita
    tipo_rendimento_marmita = TIPO_MEDIDA_POR_UNIDADE.get(unidade_rendimento_marmita)
    
    if not tipo_rendimento_marmita:
        print(f"Atenção: Unidade de rendimento da marmita '{unidade_rendimento_marmita}' não reconhecida ou não definida.")
        marmita.custo_unitario_producao = 0.0
        return marmita.custo_unitario_producao

    for mc in marmita.condimento_itens: # Acessa os MarmitaCondimento
        if mc.condimento and mc.condimento.custo_unitario is not None:
            unidade_rendimento_do_condimento = mc.condimento.unidade_medida_rendimento
            quantidade_condimento_na_marmita = mc.quantidade_do_condimento
            unidade_da_quantidade_na_marmita = mc.unidade_do_condimento_na_marmita # Unidade da quantidade no MarmitaCondimento
            custo_unitario_condimento = mc.condimento.custo_unitario

            print(f"\n--- DEBUG CALCULO MARMITA: {marmita.nome} ---")
            print(f"Condimento: {mc.condimento.nome}")
            print(f"Quant. na marmita: {quantidade_condimento_na_marmita} {unidade_da_quantidade_na_marmita}")
            print(f"Custo unitário condimento: {custo_unitario_condimento} R$/{unidade_rendimento_do_condimento}")


            # Converter a QUANTIDADE_CONDIMENTO_NA_MARMITA para a UNIDADE DE RENDIMENTO DO CONDIMENTO.
            quantidade_para_calculo = converter_unidade(
                quantidade_condimento_na_marmita,     # Ex: 150
                unidade_da_quantidade_na_marmita,     # Ex: 'g' (unidade que o usuário digitou para o CondimentoItem)
                unidade_rendimento_do_condimento      # Ex: 'kg' (unidade do custo do condimento)
            )
            
            if quantidade_para_calculo is None:
                print(f"Atenção: Não foi possível converter a unidade para o condimento '{mc.condimento.nome}' na marmita. Verifique as unidades '{unidade_da_quantidade_na_marmita}' e '{unidade_rendimento_do_condimento}'.")
                continue

            custo_contribuido_por_condimento = quantidade_para_calculo * custo_unitario_condimento
            print(f"Custo Contribuído por {mc.condimento.nome}: {custo_contribuido_por_condimento}")
            custo_total_receita += custo_contribuido_por_condimento
        else:
            print(f"Atenção: Condimento {mc.condimento.nome if mc.condimento else 'ID Desconhecido'} da Marmita {marmita.nome} não tem custo unitário definido.")
    
    print(f"Custo Total Receita {marmita.nome}: {custo_total_receita}")

    if marmita.rendimento_receita and marmita.rendimento_receita > 0:
        marmita.custo_unitario_producao = custo_total_receita / marmita.rendimento_receita
    else:
        marmita.custo_unitario_producao = 0.0
    print(f"Custo Unitário Produção Marmita {marmita.nome}: {marmita.custo_unitario_producao}")
    return marmita.custo_unitario_producao


def consumir_ingredientes_para_marmita(marmita, quantidade_marmitas_produzidas):
    """
    Calcula e decrementa o estoque de ingredientes necessários para produzir uma quantidade de marmitas.
    Retorna True se o estoque for suficiente e a operação for bem-sucedida, False caso contrário.
    """
    ingredientes_necessarios_por_unidade = {} # {ingrediente_id: quantidade_em_unidade_base}

    for mc in marmita.condimento_itens: # Para cada condimento na receita da marmita
        condimento = mc.condimento
        if not condimento:
            print(f"Erro: Condimento associado à marmita {marmita.nome} não encontrado.")
            return False, f"Condimento não encontrado para a marmita {marmita.nome}."

        # 1. Calcular a quantidade total do condimento necessária para a produção
        # mc.quantidade_do_condimento é a quantidade numérica do condimento na receita da marmita
        # mc.unidade_do_condimento_na_marmita é a unidade dessa quantidade (ex: 'g')
        # condimento.unidade_medida_rendimento é a unidade em que o condimento rende (ex: 'kg')
        
        # Converter a quantidade do condimento usada na marmita para a unidade de rendimento do condimento
        quantidade_condimento_convertida_para_rendimento = converter_unidade(
            mc.quantidade_do_condimento,
            mc.unidade_do_condimento_na_marmita,
            condimento.unidade_medida_rendimento
        )
        if quantidade_condimento_convertida_para_rendimento is None:
            return False, f"Erro de conversão de unidade para o condimento '{condimento.nome}' na marmita."

        # Quantidade total do condimento necessária para TODAS as marmitas produzidas
        total_condimento_necessario_para_producao = quantidade_condimento_convertida_para_rendimento * quantidade_marmitas_produzidas

        # 2. Para cada ingrediente dentro deste condimento
        for ci in condimento.itens: # Para cada ingrediente no condimento
            ingrediente = ci.ingrediente
            if not ingrediente:
                print(f"Erro: Ingrediente associado ao condimento {condimento.nome} não encontrado.")
                return False, f"Ingrediente não encontrado para o condimento {condimento.nome}."

            # ci.quantidade_do_ingrediente é a quantidade numérica do ingrediente na receita do condimento
            # ci.unidade_do_ingrediente_na_receita é a unidade dessa quantidade (ex: 'g')
            # ingrediente.unidade_medida é a unidade em que o ingrediente foi comprado (ex: 'kg')

            # Calcular a proporção de cada ingrediente no condimento
            # Ex: se 1kg de condimento usa 0.8kg de frango, e precisamos de 0.5kg de condimento,
            # então precisamos de 0.8 * 0.5 = 0.4kg de frango.
            
            # Primeiro, converter a quantidade do ingrediente na receita do condimento para a unidade de rendimento do condimento
            # Isso nos dá a quantidade do ingrediente por unidade de rendimento do condimento.
            # Ex: 0.8kg de frango por 1kg de condimento.
            quantidade_ingrediente_por_unidade_condimento = converter_unidade(
                ci.quantidade_do_ingrediente,
                ci.unidade_do_ingrediente_na_receita,
                condimento.unidade_medida_rendimento # Unidade de rendimento do condimento
            )
            if quantidade_ingrediente_por_unidade_condimento is None:
                return False, f"Erro de conversão de unidade para o ingrediente '{ingrediente.nome}' no condimento '{condimento.nome}'."

            # Calcular a quantidade total deste ingrediente necessária para a produção
            # (quantidade_ingrediente_por_unidade_condimento * total_condimento_necessario_para_producao)
            total_ingrediente_necessario_para_producao = quantidade_ingrediente_por_unidade_condimento * total_condimento_necessario_para_producao

            # Converter a quantidade total do ingrediente necessária para a UNIDADE DE COMPRA do ingrediente
            # para que possamos comparar com ingrediente.quantidade_comprada
            quantidade_final_a_consumir = converter_unidade(
                total_ingrediente_necessario_para_producao,
                condimento.unidade_medida_rendimento, # A quantidade calculada está na unidade de rendimento do condimento
                ingrediente.unidade_medida # A unidade em que o ingrediente foi comprado/estocado
            )
            if quantidade_final_a_consumir is None:
                return False, f"Erro de conversão de unidade final para o ingrediente '{ingrediente.nome}'."

            # Acumular a quantidade total necessária de cada ingrediente
            # (em sua unidade de compra, para comparação com o estoque)
            ingredientes_necessarios_por_unidade[ingrediente.id] = \
                ingredientes_necessarios_por_unidade.get(ingrediente.id, 0.0) + quantidade_final_a_consumir

    # 3. Verificar estoque e consumir
    ingredientes_a_consumir = []
    for ingrediente_id, quantidade_necessaria in ingredientes_necessarios_por_unidade.items():
        ingrediente = db.session.get(Ingrediente, ingrediente_id)
        if not ingrediente:
            return False, f"Ingrediente (ID: {ingrediente_id}) não encontrado para consumo."

        print(f"DEBUG CONSUMO: {ingrediente.nome}: Necessário {quantidade_necessaria:.2f} {ingrediente.unidade_medida}, Estoque {ingrediente.quantidade_comprada:.2f} {ingrediente.unidade_medida}")

        if ingrediente.quantidade_comprada < quantidade_necessaria:
            return False, f"Estoque insuficiente de '{ingrediente.nome}'. Necessário: {quantidade_necessaria:.2f} {ingrediente.unidade_medida}, Disponível: {ingrediente.quantidade_comprada:.2f} {ingrediente.unidade_medida}."
        
        ingredientes_a_consumir.append((ingrediente, quantidade_necessaria))

    # Se tudo for suficiente, realizar o consumo
    for ingrediente, quantidade_necessaria in ingredientes_a_consumir:
        ingrediente.quantidade_comprada -= quantidade_necessaria
        db.session.add(ingrediente) # Adiciona ao session para salvar a alteração

    return True, "Ingredientes consumidos com sucesso."


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