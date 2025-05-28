from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from models import db, Marmita, Usuario, Ingrediente, Condimento, CondimentoItem, MarmitaCondimento, ProducaoMarmita, Precificacao, Estoque, Pedido # Importe todos os modelos
from forms import IngredienteForm, CondimentoForm, MarmitaForm, CondimentoItemForm, MarmitaCondimentoForm, PrecificacaoForm, EstoqueForm, PedidoForm # Importe todos os formulários
from utilities import calcular_custo_unitario_ingrediente, calcular_custo_condimento, calcular_custo_unitario_marmita_receita, calcular_precificacao, atualizar_estoque_apos_producao, processar_pedido # Importe as funções de cálculo atualizadas
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def login_admin_required(f):
    """
    Decorador para rotas que exigem que o usuário seja um administrador.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            flash('Você não tem permissão para acessar esta página.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return wrapper

@admin_bp.route('/', methods=['GET'])
@login_admin_required
def painel_admin():
    """
    Exibe o painel administrativo com listas de marmitas (receitas), ingredientes, condimentos,
    precificações, estoques e pedidos.
    """
    marmitas = Marmita.query.all()
    ingredientes = Ingrediente.query.all()
    condimentos = Condimento.query.all()
    precificacoes = Precificacao.query.all()
    estoques = Estoque.query.all()
    pedidos = Pedido.query.all()

    return render_template('admin/admin.html',
                           marmitas=marmitas,
                           ingredientes=ingredientes,
                           condimentos=condimentos,
                           precificacoes=precificacoes,
                           estoques=estoques,
                           pedidos=pedidos)

# --- Rotas para Gerenciar Ingredientes ---

@admin_bp.route('/ingredientes', methods=['GET'])
@login_admin_required
def gerenciar_ingredientes():
    """
    Exibe a lista de ingredientes.
    """
    ingredientes = Ingrediente.query.all()
    return render_template('admin/gerenciar_ingredientes.html', ingredientes=ingredientes)

@admin_bp.route('/ingredientes/adicionar', methods=['GET', 'POST'])
@login_admin_required
def adicionar_ingrediente():
    """
    Permite adicionar um novo ingrediente e calcula seu custo unitário.
    """
    form = IngredienteForm()
    if form.validate_on_submit():
        novo_ingrediente = Ingrediente(
            nome=form.nome.data,
            quantidade_comprada=form.quantidade_comprada.data,
            total_pago=form.total_pago.data,
            unidade_medida=form.unidade_medida.data
        )
        db.session.add(novo_ingrediente)
        db.session.commit() # Commit inicial para que o ingrediente tenha um ID

        calcular_custo_unitario_ingrediente(novo_ingrediente) # Calcula e atualiza o custo unitário
        db.session.commit() # Salva o custo unitário no banco de dados

        flash('Ingrediente adicionado com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_ingredientes'))
    return render_template('admin/adicionar_ingrediente.html', form=form)

@admin_bp.route('/ingredientes/editar/<int:ingrediente_id>', methods=['GET', 'POST'])
@login_admin_required
def editar_ingrediente(ingrediente_id):
    """
    Permite editar um ingrediente existente.
    """
    ingrediente = db.session.get(Ingrediente, ingrediente_id)
    if not ingrediente:
        flash('Ingrediente não encontrado.', 'warning')
        return redirect(url_for('admin.gerenciar_ingredientes'))

    form = IngredienteForm(obj=ingrediente)
    if form.validate_on_submit():
        form.populate_obj(ingrediente)
        calcular_custo_unitario_ingrediente(ingrediente) # Recalcula o custo unitário
        db.session.commit()
        flash('Ingrediente atualizado com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_ingredientes'))
    return render_template('admin/editar_ingrediente.html', form=form, ingrediente=ingrediente)

@admin_bp.route('/ingredientes/deletar/<int:ingrediente_id>', methods=['POST'])
@login_admin_required
def deletar_ingrediente(ingrediente_id):
    """
    Permite deletar um ingrediente.
    """
    ingrediente = db.session.get(Ingrediente, ingrediente_id)
    if ingrediente:
        db.session.delete(ingrediente)
        db.session.commit()
        flash('Ingrediente deletado com sucesso!', 'success')
    else:
        flash('Ingrediente não encontrado.', 'warning')
    return redirect(url_for('admin.gerenciar_ingredientes'))


# --- Rotas para Gerenciar Condimentos ---

@admin_bp.route('/condimentos', methods=['GET'])
@login_admin_required
def gerenciar_condimentos():
    """
    Exibe a lista de condimentos.
    """
    condimentos = Condimento.query.all()
    return render_template('admin/gerenciar_condimentos.html', condimentos=condimentos)

@admin_bp.route('/condimentos/adicionar', methods=['GET', 'POST'])
@login_admin_required
def adicionar_condimento():
    """
    Permite adicionar um novo condimento. Após a adição, redireciona para a associação de ingredientes.
    """
    form = CondimentoForm()
    if form.validate_on_submit():
        novo_condimento = Condimento(
            nome=form.nome.data,
            rendimento=form.rendimento.data,
            unidade_medida_rendimento=form.unidade_medida_rendimento.data
        )
        db.session.add(novo_condimento)
        db.session.commit() # Commit inicial para ter ID

        flash('Condimento adicionado com sucesso! Agora adicione os ingredientes a ele.', 'info')
        return redirect(url_for('admin.adicionar_ingrediente_a_condimento', condimento_id=novo_condimento.id))
    return render_template('admin/adicionar_condimento.html', form=form)

@admin_bp.route('/condimento/<int:condimento_id>/adicionar_ingrediente', methods=['GET', 'POST'])
@login_admin_required
def adicionar_ingrediente_a_condimento(condimento_id):
    """
    Permite adicionar ingredientes a um condimento específico.
    """
    condimento = db.session.get(Condimento, condimento_id)
    if not condimento:
        flash("Condimento não encontrado.", "danger")
        return redirect(url_for('admin.gerenciar_condimentos'))

    form = CondimentoItemForm()
    # Popula as opções do SelectField de ingredientes
    form.ingrediente_id.choices = [(i.id, i.nome) for i in Ingrediente.query.all()]

    if form.validate_on_submit():
        ingrediente_id = form.ingrediente_id.data
        quantidade_do_ingrediente = form.quantidade_do_ingrediente.data

        ingrediente = db.session.get(Ingrediente, ingrediente_id)
        if not ingrediente:
            flash("Ingrediente selecionado não encontrado.", "danger")
            return redirect(url_for('admin.adicionar_ingrediente_a_condimento', condimento_id=condimento_id))

        # Verifica se já existe um CondimentoItem para evitar duplicatas
        condimento_item_existente = CondimentoItem.query.filter_by(
            condimento_id=condimento.id, ingrediente_id=ingrediente.id).first()

        if condimento_item_existente:
            flash(f'Ingrediente {ingrediente.nome} já adicionado a este condimento. Edite-o se precisar alterar a quantidade.', 'warning')
        else:
            condimento_item = CondimentoItem(
                condimento_id=condimento.id,
                ingrediente_id=ingrediente.id,
                quantidade_do_ingrediente=quantidade_do_ingrediente
            )
            db.session.add(condimento_item)
            db.session.commit() # Commit para salvar o CondimentoItem

            # Recalcula o custo total e unitário do condimento
            calcular_custo_condimento(condimento)
            db.session.commit() # Salva os custos atualizados do condimento

            flash(f'Ingrediente {ingrediente.nome} adicionado ao condimento {condimento.nome}.', 'success')

        return redirect(url_for('admin.adicionar_ingrediente_a_condimento', condimento_id=condimento_id))

    condimento_itens_existentes = CondimentoItem.query.filter_by(condimento_id=condimento.id).all()

    return render_template('admin/adicionar_ingrediente_a_condimento.html',
                           condimento=condimento,
                           form=form,
                           condimento_itens_existentes=condimento_itens_existentes)

@admin_bp.route('/condimento/<int:condimento_id>/editar_ingrediente/<int:item_id>', methods=['GET', 'POST'])
@login_admin_required
def editar_ingrediente_condimento(condimento_id, item_id):
    """
    Permite editar a quantidade de um ingrediente em um condimento.
    """
    condimento = db.session.get(Condimento, condimento_id)
    condimento_item = db.session.get(CondimentoItem, item_id)

    if not condimento or not condimento_item or condimento_item.condimento_id != condimento.id:
        flash('Item de condimento não encontrado.', 'warning')
        return redirect(url_for('admin.adicionar_ingrediente_a_condimento', condimento_id=condimento_id))

    form = CondimentoItemForm(obj=condimento_item)
    form.ingrediente_id.choices = [(condimento_item.ingrediente.id, condimento_item.ingrediente.nome)] # Apenas o ingrediente atual
    form.ingrediente_id.render_kw = {'disabled': 'disabled'} # Desabilita o campo no HTML

    if form.validate_on_submit():
        condimento_item.quantidade_do_ingrediente = form.quantidade_do_ingrediente.data
        db.session.commit()

        calcular_custo_condimento(condimento) # Recalcula o custo do condimento
        db.session.commit()

        flash('Quantidade do ingrediente atualizada com sucesso!', 'success')
        return redirect(url_for('admin.adicionar_ingrediente_a_condimento', condimento_id=condimento_id))

    return render_template('admin/editar_ingrediente_condimento.html', form=form, condimento=condimento, condimento_item=condimento_item)

@admin_bp.route('/condimento/<int:condimento_id>/deletar_ingrediente/<int:item_id>', methods=['POST'])
@login_admin_required
def deletar_ingrediente_condimento(condimento_id, item_id):
    """
    Permite deletar um ingrediente de um condimento.
    """
    condimento = db.session.get(Condimento, condimento_id)
    condimento_item = db.session.get(CondimentoItem, item_id)

    if not condimento or not condimento_item or condimento_item.condimento_id != condimento.id:
        flash('Item de condimento não encontrado.', 'warning')
        return redirect(url_for('admin.adicionar_ingrediente_a_condimento', condimento_id=condimento_id))

    db.session.delete(condimento_item)
    db.session.commit()

    calcular_custo_condimento(condimento) # Recalcula o custo do condimento
    db.session.commit()

    flash('Ingrediente removido do condimento com sucesso!', 'success')
    return redirect(url_for('admin.adicionar_ingrediente_a_condimento', condimento_id=condimento_id))

@admin_bp.route('/condimentos/editar/<int:condimento_id>', methods=['GET', 'POST'])
@login_admin_required
def editar_condimento(condimento_id):
    """
    Permite editar um condimento existente.
    """
    condimento = db.session.get(Condimento, condimento_id)
    if not condimento:
        flash('Condimento não encontrado.', 'warning')
        return redirect(url_for('admin.gerenciar_condimentos'))

    form = CondimentoForm(obj=condimento)
    if form.validate_on_submit():
        form.populate_obj(condimento)
        db.session.commit()
        calcular_custo_condimento(condimento) # Recalcula o custo do condimento, caso rendimento mude
        db.session.commit()
        flash('Condimento atualizado com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_condimentos'))
    return render_template('admin/editar_condimento.html', form=form, condimento=condimento)

@admin_bp.route('/condimentos/deletar/<int:condimento_id>', methods=['POST'])
@login_admin_required
def deletar_condimento(condimento_id):
    """
    Permite deletar um condimento.
    """
    condimento = db.session.get(Condimento, condimento_id)
    if condimento:
        db.session.delete(condimento)
        db.session.commit()
        flash('Condimento deletado com sucesso!', 'success')
    else:
        flash('Condimento não encontrado.', 'warning')
    return redirect(url_for('admin.gerenciar_condimentos'))

# --- Rotas para Gerenciar Marmitas (Receitas) ---

@admin_bp.route('/marmitas', methods=['GET'])
@login_admin_required
def gerenciar_marmitas():
    """
    Exibe a lista de marmitas (receitas).
    """
    marmitas = Marmita.query.all()
    return render_template('admin/gerenciar_marmitas.html', marmitas=marmitas)


@admin_bp.route('/marmitas/adicionar', methods=['GET', 'POST'])
@login_admin_required
def adicionar_marmita():
    """
    Permite adicionar uma nova marmita (receita).
    """
    form = MarmitaForm()
    if form.validate_on_submit():
        nova_marmita = Marmita(
            nome=form.nome.data,
            descricao=form.descricao.data,
            rendimento_receita=form.rendimento_receita.data
        )
        db.session.add(nova_marmita)
        db.session.commit() # Commit inicial para ter ID

        flash('Marmita adicionada com sucesso! Agora associe os condimentos a ela.', 'info')
        return redirect(url_for('admin.associar_condimento_a_marmita', marmita_id=nova_marmita.id))
    return render_template('admin/adicionar_marmita.html', form=form)


@admin_bp.route('/marmita/<int:marmita_id>/associar_condimento', methods=['GET', 'POST'])
@login_admin_required
def associar_condimento_a_marmita(marmita_id):
    """
    Permite associar condimentos a uma marmita específica.
    """
    marmita = db.session.get(Marmita, marmita_id)
    if not marmita:
        flash("Marmita não encontrada.", "danger")
        return redirect(url_for('admin.gerenciar_marmitas'))

    form = MarmitaCondimentoForm()
    # Popula as opções do SelectField de condimentos
    form.condimento_id.choices = [(c.id, c.nome) for c in Condimento.query.all()]

    if form.validate_on_submit():
        condimento_id = form.condimento_id.data
        quantidade_do_condimento = form.quantidade_do_condimento.data

        condimento = db.session.get(Condimento, condimento_id)
        if not condimento:
            flash("Condimento selecionado não encontrado.", "danger")
            return redirect(url_for('admin.associar_condimento_a_marmita', marmita_id=marmita_id))

        # Verifica se já existe um MarmitaCondimento para evitar duplicatas
        marmita_condimento_existente = MarmitaCondimento.query.filter_by(
            marmita_id=marmita.id, condimento_id=condimento.id).first()

        if marmita_condimento_existente:
            flash(f'Condimento {condimento.nome} já associado a esta marmita. Edite-o se precisar alterar a quantidade.', 'warning')
        else:
            marmita_condimento = MarmitaCondimento(
                marmita_id=marmita.id,
                condimento_id=condimento.id,
                quantidade_do_condimento=quantidade_do_condimento
            )
            db.session.add(marmita_condimento)
            db.session.commit() # Commit para salvar o MarmitaCondimento

            # Recalcula o custo unitário da marmita
            calcular_custo_unitario_marmita_receita(marmita)
            db.session.commit() # Salva o custo unitário atualizado da marmita

            flash(f'Condimento {condimento.nome} associado à marmita {marmita.nome}.', 'success')

        return redirect(url_for('admin.associar_condimento_a_marmita', marmita_id=marmita_id))

    marmita_condimentos_existentes = MarmitaCondimento.query.filter_by(marmita_id=marmita.id).all()

    return render_template('admin/associar_condimento_a_marmita.html',
                           marmita=marmita,
                           form=form,
                           marmita_condimentos_existentes=marmita_condimentos_existentes)

@admin_bp.route('/marmita/<int:marmita_id>/editar_condimento/<int:item_id>', methods=['GET', 'POST'])
@login_admin_required
def editar_condimento_marmita(marmita_id, item_id):
    """
    Permite editar a quantidade de um condimento em uma marmita.
    """
    marmita = db.session.get(Marmita, marmita_id)
    marmita_condimento = db.session.get(MarmitaCondimento, item_id)

    if not marmita or not marmita_condimento or marmita_condimento.marmita_id != marmita.id:
        flash('Item de condimento da marmita não encontrado.', 'warning')
        return redirect(url_for('admin.associar_condimento_a_marmita', marmita_id=marmita_id))

    form = MarmitaCondimentoForm(obj=marmita_condimento)
    form.condimento_id.choices = [(marmita_condimento.condimento.id, marmita_condimento.condimento.nome)] # Apenas o condimento atual
    form.condimento_id.render_kw = {'disabled': 'disabled'} # Desabilita o campo no HTML

    if form.validate_on_submit():
        marmita_condimento.quantidade_do_condimento = form.quantidade_do_condimento.data
        db.session.commit()

        calcular_custo_unitario_marmita_receita(marmita) # Recalcula o custo da marmita
        db.session.commit()

        flash('Quantidade do condimento na marmita atualizada com sucesso!', 'success')
        return redirect(url_for('admin.associar_condimento_a_marmita', marmita_id=marmita_id))

    return render_template('admin/editar_condimento_marmita.html', form=form, marmita=marmita, marmita_condimento=marmita_condimento)

@admin_bp.route('/marmita/<int:marmita_id>/deletar_condimento/<int:item_id>', methods=['POST'])
@login_admin_required
def deletar_condimento_marmita(marmita_id, item_id):
    """
    Permite deletar um condimento de uma marmita.
    """
    marmita = db.session.get(Marmita, marmita_id)
    marmita_condimento = db.session.get(MarmitaCondimento, item_id)

    if not marmita or not marmita_condimento or marmita_condimento.marmita_id != marmita.id:
        flash('Item de condimento da marmita não encontrado.', 'warning')
        return redirect(url_for('admin.associar_condimento_a_marmita', marmita_id=marmita_id))

    db.session.delete(marmita_condimento)
    db.session.commit()

    calcular_custo_unitario_marmita_receita(marmita) # Recalcula o custo da marmita
    db.session.commit()

    flash('Condimento removido da marmita com sucesso!', 'success')
    return redirect(url_for('admin.associar_condimento_a_marmita', marmita_id=marmita_id))

@admin_bp.route('/marmitas/editar/<int:marmita_id>', methods=['GET', 'POST'])
@login_admin_required
def editar_marmita(marmita_id):
    """
    Permite editar uma marmita (receita) existente.
    """
    marmita = db.session.get(Marmita, marmita_id)
    if not marmita:
        flash('Marmita não encontrada.', 'warning')
        return redirect(url_for('admin.gerenciar_marmitas'))

    form = MarmitaForm(obj=marmita)
    if form.validate_on_submit():
        form.populate_obj(marmita)
        db.session.commit()
        calcular_custo_unitario_marmita_receita(marmita) # Recalcula o custo, caso rendimento mude
        db.session.commit()
        flash('Marmita atualizada com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_marmitas'))
    return render_template('admin/editar_marmita.html', form=form, marmita=marmita)

@admin_bp.route('/marmitas/deletar/<int:marmita_id>', methods=['POST'])
@login_admin_required
def deletar_marmita(marmita_id):
    """
    Permite deletar uma marmita.
    """
    marmita = db.session.get(Marmita, marmita_id)
    if marmita:
        db.session.delete(marmita)
        db.session.commit()
        flash('Marmita deletada com sucesso!', 'success')
    else:
        flash('Marmita não encontrada.', 'warning')
    return redirect(url_for('admin.gerenciar_marmitas'))

# --- Rotas para Gerenciar Precificação ---

@admin_bp.route('/precificacoes', methods=['GET'])
@login_admin_required
def gerenciar_precificacoes():
    """
    Exibe a lista de precificações existentes.
    """
    precificacoes = Precificacao.query.all()
    return render_template('admin/gerenciar_precificacoes.html', precificacoes=precificacoes)

@admin_bp.route('/precificacoes/adicionar', methods=['GET', 'POST'])
@login_admin_required
def adicionar_precificacao():
    """
    Permite adicionar uma nova precificação para uma marmita.
    """
    form = PrecificacaoForm()
    # Popula as opções do SelectField com marmitas que AINDA NÃO possuem precificação
    marmitas_sem_precificacao = Marmita.query.filter(~Marmita.precificacao.has()).all()
    form.marmita_id.choices = [(m.id, m.nome) for m in marmitas_sem_precificacao]

    if form.validate_on_submit():
        marmita_id = form.marmita_id.data
        valor_de_venda = form.valor_de_venda.data

        marmita = db.session.get(Marmita, marmita_id)
        if not marmita:
            flash("Marmita não encontrada para precificação.", "danger")
            return redirect(url_for('admin.adicionar_precificacao'))

        if marmita.custo_unitario_producao is None or marmita.custo_unitario_producao == 0:
            flash(f"O custo de produção da marmita '{marmita.nome}' não está definido. Por favor, associe condimentos e calcule o custo antes de precificar.", "warning")
            return redirect(url_for('admin.adicionar_precificacao'))

        nova_precificacao = Precificacao(
            marmita_id=marmita.id,
            valor_de_venda=valor_de_venda
        )
        db.session.add(nova_precificacao)
        db.session.commit() # Commit inicial para ter ID

        calcular_precificacao(nova_precificacao) # Calcula margem e lucro
        db.session.commit() # Salva os valores calculados

        flash(f'Precificação para {marmita.nome} adicionada com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_precificacoes'))
    return render_template('admin/adicionar_precificacao.html', form=form)

@admin_bp.route('/precificacoes/editar/<int:precificacao_id>', methods=['GET', 'POST'])
@login_admin_required
def editar_precificacao(precificacao_id):
    """
    Permite editar uma precificação existente.
    """
    precificacao = db.session.get(Precificacao, precificacao_id)
    if not precificacao:
        flash('Precificação não encontrada.', 'warning')
        return redirect(url_for('admin.gerenciar_precificacoes'))

    form = PrecificacaoForm(obj=precificacao)
    # A marmita_id não deve ser alterável para uma precificação existente
    form.marmita_id.choices = [(precificacao.marmita.id, precificacao.marmita.nome)]
    form.marmita_id.render_kw = {'disabled': 'disabled'} # Desabilita o campo no HTML

    if form.validate_on_submit():
        precificacao.valor_de_venda = form.valor_de_venda.data
        db.session.commit()

        calcular_precificacao(precificacao) # Recalcula margem e lucro
        db.session.commit()

        flash('Precificação atualizada com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_precificacoes'))
    return render_template('admin/editar_precificacao.html', form=form, precificacao=precificacao)

@admin_bp.route('/precificacoes/deletar/<int:precificacao_id>', methods=['POST'])
@login_admin_required
def deletar_precificacao(precificacao_id):
    """
    Permite deletar uma precificação.
    """
    precificacao = db.session.get(Precificacao, precificacao_id)
    if precificacao:
        db.session.delete(precificacao)
        db.session.commit()
        flash('Precificação deletada com sucesso!', 'success')
    else:
        flash('Precificação não encontrada.', 'warning')
    return redirect(url_for('admin.gerenciar_precificacoes'))

# --- Rotas para Gerenciar Estoque ---

@admin_bp.route('/estoque', methods=['GET'])
@login_admin_required
def gerenciar_estoque():
    """
    Exibe a lista de itens em estoque.
    """
    estoques = Estoque.query.all()
    return render_template('admin/gerenciar_estoque.html', estoques=estoques)

@admin_bp.route('/estoque/produzir', methods=['GET', 'POST'])
@login_admin_required
def produzir_marmitas_estoque():
    """
    Permite produzir marmitas e adicionar ao estoque.
    """
    form = EstoqueForm()
    # Popula as opções do SelectField com marmitas que possuem precificação
    # Agora usamos precificacao.id e precificacao.marmita.nome
    marmitas_precificadas = Precificacao.query.all()
    form.precificacao_id.choices = [(p.id, f"{p.marmita.nome} (Custo: R${p.custo_marmita:.2f}, Venda: R${p.valor_de_venda:.2f})") for p in marmitas_precificadas if p.marmita]

    if form.validate_on_submit():
        precificacao_id = form.precificacao_id.data
        quantidade_produzida = form.quantidade.data

        precificacao = db.session.get(Precificacao, precificacao_id)
        if not precificacao:
            flash("Precificação não encontrada.", "danger")
            return redirect(url_for('admin.produzir_marmitas_estoque'))

        # Atualizar o estoque existente ou criar um novo registro de estoque
        estoque_item = Estoque.query.filter_by(precificacao_id=precificacao_id).first()

        if estoque_item:
            # Se o item de estoque já existe, apenas atualiza a quantidade
            atualizar_estoque_apos_producao(estoque_item, quantidade_produzida)
            flash(f'Estoque de {precificacao.marmita.nome} atualizado. Quantidade: {estoque_item.quantidade}.', 'success')
        else:
            # Se o item de estoque não existe, cria um novo
            novo_estoque = Estoque(
                precificacao_id=precificacao_id,
                quantidade=0 # Inicializa com 0, a função de atualização vai adicionar
            )
            db.session.add(novo_estoque)
            db.session.commit() # Commit para ter ID

            atualizar_estoque_apos_producao(novo_estoque, quantidade_produzida)
            flash(f'Estoque inicial para {precificacao.marmita.nome} criado. Quantidade: {novo_estoque.quantidade}.', 'success')

        db.session.commit() # Salva as alterações no estoque

        # Opcional: Registrar a produção na tabela ProducaoMarmita
        producao = ProducaoMarmita(
            marmita_id=precificacao.marmita.id, # Usa o ID da marmita da precificação
            quantidade_produzida=quantidade_produzida,
            # Custo de produção total = custo unitário da receita * quantidade produzida
            custo_producao_total=precificacao.marmita.custo_unitario_producao * quantidade_produzida
        )
        db.session.add(producao)
        db.session.commit()

        return redirect(url_for('admin.gerenciar_estoque'))
    return render_template('admin/produzir_marmitas_estoque.html', form=form)

@admin_bp.route('/estoque/ajustar/<int:estoque_id>', methods=['GET', 'POST'])
@login_admin_required
def ajustar_estoque(estoque_id):
    """
    Permite ajustar a quantidade de um item em estoque.
    """
    estoque_item = db.session.get(Estoque, estoque_id)
    if not estoque_item:
        flash('Item de estoque não encontrado.', 'warning')
        return redirect(url_for('admin.gerenciar_estoque'))

    form = EstoqueForm(obj=estoque_item)
    # A precificacao_id não deve ser alterável para um item de estoque existente
    form.precificacao_id.choices = [(estoque_item.precificacao_referencia.id, estoque_item.precificacao_referencia.marmita.nome)]
    form.precificacao_id.render_kw = {'disabled': 'disabled'} # Desabilita o campo no HTML
    form.quantidade.label = 'Nova Quantidade em Estoque' # Altera o rótulo para indicar ajuste

    if form.validate_on_submit():
        nova_quantidade = form.quantidade.data
        if nova_quantidade < 0:
            flash('A quantidade em estoque não pode ser negativa.', 'danger')
            return redirect(url_for('admin.ajustar_estoque', estoque_id=estoque_id))

        estoque_item.quantidade = nova_quantidade
        db.session.commit()
        flash(f'Estoque de {estoque_item.precificacao_referencia.marmita.nome} ajustado para {nova_quantidade} unidades.', 'success')
        return redirect(url_for('admin.gerenciar_estoque'))
    return render_template('admin/ajustar_estoque.html', form=form, estoque_item=estoque_item)

@admin_bp.route('/estoque/deletar/<int:estoque_id>', methods=['POST'])
@login_admin_required
def deletar_estoque(estoque_id):
    """
    Permite deletar um registro de estoque.
    """
    estoque_item = db.session.get(Estoque, estoque_id)
    if estoque_item:
        db.session.delete(estoque_item)
        db.session.commit()
        flash('Registro de estoque deletado com sucesso!', 'success')
    else:
        flash('Registro de estoque não encontrado.', 'warning')
    return redirect(url_for('admin.gerenciar_estoque'))


# --- Rotas para Gerenciar Pedidos ---

@admin_bp.route('/pedidos', methods=['GET'])
@login_admin_required
def gerenciar_pedidos():
    """
    Exibe a lista de pedidos.
    """
    pedidos = Pedido.query.all()
    return render_template('admin/gerenciar_pedidos.html', pedidos=pedidos)

@admin_bp.route('/pedidos/adicionar', methods=['GET', 'POST'])
@login_admin_required
def adicionar_pedido():
    """
    Permite adicionar um novo pedido.
    """
    form = PedidoForm()
    # Popula as opções do SelectField com ITENS EM ESTOQUE (quantidade > 0)
    # Agora usamos estoque_item.id e o nome da marmita via precificacao
    estoques_disponiveis = Estoque.query.filter(Estoque.quantidade > 0).all()
    form.estoque_id.choices = [(e.id, f"{e.precificacao_referencia.marmita.nome} (Estoque: {e.quantidade})") for e in estoques_disponiveis if e.precificacao_referencia and e.precificacao_referencia.marmita]

    if form.validate_on_submit():
        estoque_id_selecionado = form.estoque_id.data
        quantidade_marmita_id = form.quantidade_marmita_id.data

        estoque_item = db.session.get(Estoque, estoque_id_selecionado)
        if not estoque_item or estoque_item.quantidade < quantidade_marmita_id:
            flash("Quantidade de marmitas em estoque insuficiente ou item de estoque não encontrado.", "danger")
            return redirect(url_for('admin.adicionar_pedido'))

        novo_pedido = Pedido(
            nome_cliente=form.nome_cliente.data,
            email_cliente=form.email_cliente.data,
            contato_cliente=form.contato_cliente.data,
            estoque_id=estoque_id_selecionado, # Usamos estoque_id agora
            quantidade_marmita_id=quantidade_marmita_id
        )
        db.session.add(novo_pedido)
        db.session.commit() # Commit inicial para ter ID

        # Processa o pedido (calcula total e atualiza estoque)
        if processar_pedido(novo_pedido): # A função processar_pedido já faz a validação de estoque
            db.session.commit() # Salva as alterações do pedido e do estoque
            flash('Pedido adicionado com sucesso e estoque atualizado!', 'success')
        else:
            flash('Não foi possível processar o pedido devido a estoque insuficiente ou outro erro.', 'danger')
            db.session.rollback() # Desfaz as alterações se houver erro
            return redirect(url_for('admin.adicionar_pedido'))

        return redirect(url_for('admin.gerenciar_pedidos'))
    return render_template('admin/adicionar_pedido.html', form=form)

@admin_bp.route('/pedidos/editar/<int:pedido_id>', methods=['GET', 'POST'])
@login_admin_required
def editar_pedido(pedido_id):
    """
    Permite editar um pedido existente.
    NOTA: Editar pedidos pode ser complexo devido ao impacto no estoque.
    Considere se é melhor permitir apenas a adição e o status (concluído/cancelado).
    """
    pedido = db.session.get(Pedido, pedido_id)
    if not pedido:
        flash('Pedido não encontrado.', 'warning')
        return redirect(url_for('admin.gerenciar_pedidos'))

    form = PedidoForm(obj=pedido)
    # Desabilita os campos de marmita e quantidade para evitar complexidade de estoque na edição simples
    # Agora acessamos o nome da marmita via estoque_item_pedido -> precificacao_referencia -> marmita
    form.estoque_id.choices = [(pedido.estoque_id, f"{pedido.estoque_item_pedido.precificacao_referencia.marmita.nome} (Estoque: {pedido.estoque_item_pedido.quantidade})")]
    form.estoque_id.render_kw = {'disabled': 'disabled'}
    form.quantidade_marmita_id.render_kw = {'disabled': 'disabled'}

    if form.validate_on_submit():
        form.populate_obj(pedido)
        db.session.commit()
        flash('Pedido atualizado com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_pedidos'))
    return render_template('admin/editar_pedido.html', form=form, pedido=pedido)

@admin_bp.route('/pedidos/deletar/<int:pedido_id>', methods=['POST'])
@login_admin_required
def deletar_pedido(pedido_id):
    """
    Permite deletar um pedido.
    NOTA: Ao deletar um pedido, você pode querer reverter o estoque.
    """
    pedido = db.session.get(Pedido, pedido_id)
    if pedido:
        # Opcional: Reverter o estoque ao deletar o pedido
        estoque_item = Estoque.query.filter_by(id=pedido.estoque_id).first()
        if estoque_item:
            estoque_item.quantidade += pedido.quantidade_marmita_id
            db.session.add(estoque_item) # Adiciona ao session para salvar

        db.session.delete(pedido)
        db.session.commit()
        flash('Pedido deletado com sucesso!', 'success')
    else:
        flash('Pedido não encontrado.', 'warning')
    return redirect(url_for('admin.gerenciar_pedidos'))