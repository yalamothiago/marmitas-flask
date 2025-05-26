# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from models import db, Marmita, Usuario, Ingrediente, Condimento, CondimentoItem, MarmitaCondimento, ProducaoMarmita
from forms import IngredienteForm, CondimentoForm, MarmitaForm # Importe os novos formulários
from utilities import calcular_custo_unitario_ingrediente, calcular_custo_condimento, calcular_custo_marmita # Importe as funções de cálculo
from functools import wraps # Para o decorador login_admin_required

admin_bp = Blueprint('admin', __name__)

def login_admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            flash('Você não tem permissão para acessar esta página.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return wrapper

@admin_bp.route('/', methods=['GET']) # Painel Admin é apenas GET
@login_admin_required
def painel_admin():
    marmitas = Marmita.query.all()
    ingredientes = Ingrediente.query.all()
    condimentos = Condimento.query.all()
    return render_template('admin/admin.html',
                           marmitas=marmitas,
                           ingredientes=ingredientes,
                           condimentos=condimentos)

# --- Rotas para Gerenciar Ingredientes ---

@admin_bp.route('/ingredientes', methods=['GET'])
@login_admin_required
def gerenciar_ingredientes():
    ingredientes = Ingrediente.query.all()
    return render_template('admin/gerenciar_ingredientes.html', ingredientes=ingredientes)

@admin_bp.route('/ingredientes/adicionar', methods=['GET', 'POST'])
@login_admin_required
def adicionar_ingrediente():
    form = IngredienteForm()
    if form.validate_on_submit():
        novo_ingrediente = Ingrediente(
            nome=form.nome.data,
            quantidade=form.quantidade_comprada.data,
            total_pago=form.total_pago.data,
            unidade_medida=form.unidade_medida.data
        )
        db.session.add(novo_ingrediente)
        db.session.commit() # Commit inicial para ter ID
        
        calcular_custo_unitario_ingrediente(novo_ingrediente) # Calcula e salva o custo unitário
        
        flash('Ingrediente adicionado com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_ingredientes'))
    return render_template('admin/adicionar_ingrediente.html', form=form)

# Implemente rotas para atualizar/deletar ingrediente similarmente ao marmita

# --- Rotas para Gerenciar Condimentos ---

@admin_bp.route('/condimentos', methods=['GET'])
@login_admin_required
def gerenciar_condimentos():
    condimentos = Condimento.query.all()
    return render_template('admin/gerenciar_condimentos.html', condimentos=condimentos)

@admin_bp.route('/condimentos/adicionar', methods=['GET', 'POST'])
@login_admin_required
def adicionar_condimento():
    form = CondimentoForm()
    if form.validate_on_submit():
        novo_condimento = Condimento(
            nome=form.nome.data,
            rendimento=form.rendimento.data,
            unidade_medida=form.unidade_medida_rendimento.data
        )
        db.session.add(novo_condimento)
        db.session.commit() # Commit inicial para ter ID

        # POR SIMPLICIDADE PARA HOJE: não vamos adicionar ingredientes ao condimento AGORA na mesma tela.
        # Isso exigiria um formulário dinâmico no front-end ou uma tela de edição separada.
        # Você pode adicionar manualmente depois ou simplificar para um condimento sem ingredientes por enquanto.
        flash('Condimento adicionado com sucesso! Adicione os ingredientes depois.', 'success')
        return redirect(url_for('admin.gerenciar_condimentos')) # Redireciona para gerenciar condimentos
    return render_template('admin/adicionar_condimento.html', form=form)

# --- Rotas para Gerenciar Marmitas (NOVA LÓGICA) ---

@admin_bp.route('/marmitas/adicionar', methods=['GET', 'POST'])
@login_admin_required
def adicionar_marmita():
    form = MarmitaForm()
    if form.validate_on_submit():
        nova_marmita = Marmita(
            nome=form.nome.data,
            preco=form.preco.data,
            quantidade=0, # Estoque inicial é zero, pois é produzido
            descricao=form.descricao.data,
            unidade_medida=form.unidade_medida.data,
            margem_lucro_percentual=form.margem_lucro_percentual.data
        )
        db.session.add(nova_marmita)
        db.session.commit() # Commit inicial para ter ID

        # O custo de produção da marmita será calculado após a associação de condimentos.
        flash('Marmita adicionada com sucesso! Agora associe os condimentos a ela.', 'success')
        return redirect(url_for('admin.painel_admin')) # Redireciona para o painel principal
    return render_template('admin/adicionar_marmita.html', form=form)

# Rota para Atualizar Estoque (Produzir Marmitas)
@admin_bp.route('/admin/atualizar_estoque/<int:id>', methods=['POST'])
@login_admin_required
def atualizar_estoque(id): # Esta rota é para PRODUZIR marmitas, não só adicionar.
    marmita = db.session.get(Marmita, id)
    if not marmita:
        flash('Marmita não encontrada.', 'warning')
        return redirect(url_for('admin.painel_admin'))

    try:
        quantidade_produzida = int(request.form['quantidade_adicional'])
        if quantidade_produzida > 0:
            marmita.quantidade += quantidade_produzida
            
            # Opcional: Registrar a produção
            producao = ProducaoMarmita(
                marmita_id=marmita.id,
                quantidade_produzida=quantidade_produzida,
                custo_producao_total=marmita.custo_producao_base * quantidade_produzida if marmita.custo_producao_base else 0.0
            )
            db.session.add(producao)

            db.session.commit()
            flash(f'Estoque de {marmita.nome} atualizado em {quantidade_produzida} unidades. Total: {marmita.quantidade}.', 'success')
        else:
            flash('Quantidade produzida deve ser maior que zero.', 'warning')
    except ValueError:
        flash('Quantidade produzida inválida.', 'danger')
    return redirect(url_for('admin.painel_admin'))

# --- Rota para Deletar Marmita (Continua a mesma) ---
@admin_bp.route('/admin/deletar/<int:id>')
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

# --- Rotas para Associar Ingredientes/Condimentos (Essas são mais complexas para fazer para amanhã, mas ideais) ---

# Exemplo de como seria a rota para adicionar ingrediente a um condimento
@admin_bp.route('/condimento/<int:condimento_id>/adicionar_ingrediente', methods=['GET', 'POST'])
@login_admin_required
def adicionar_ingrediente_a_condimento(condimento_id):
    condimento = db.session.get(Condimento, condimento_id)
    if not condimento:
        flash("Condimento não encontrado.", "danger")
        return redirect(url_for('admin.gerenciar_condimentos'))

    # Para amanhã, você pode simplificar isso: talvez um formulário simples.
    # Em um sistema real, seria um formulário com SelectField para escolher Ingrediente e FloatField para quantidade.
    if request.method == 'POST':
        ingrediente_id = request.form.get('ingrediente_id', type=int)
        quantidade = request.form.get('quantidade', type=float)

        ingrediente = db.session.get(Ingrediente, ingrediente_id)
        if not ingrediente or not quantidade:
            flash("Dados inválidos para adicionar ingrediente.", "danger")
            return redirect(url_for('admin.adicionar_ingrediente_a_condimento', condimento_id=condimento_id))

        condimento_item = CondimentoItem(
            condimento_id=condimento.id,
            ingrediente_id=ingrediente.id,
            quantidade=quantidade
        )
        db.session.add(condimento_item)
        db.session.commit()
        calcular_custo_condimento(condimento) # Recalcula o custo do condimento

        flash(f'Ingrediente {ingrediente.nome} adicionado ao condimento {condimento.nome}.', 'success')
        return redirect(url_for('admin.adicionar_ingrediente_a_condimento', condimento_id=condimento_id))
    
    ingredientes_disponiveis = Ingrediente.query.all()
    condimento_itens_existentes = CondimentoItem.query.filter_by(condimento_id=condimento.id).all()
    
    return render_template('admin/adicionar_ingrediente_a_condimento.html',
                           condimento=condimento,
                           ingredientes_disponiveis=ingredientes_disponiveis,
                           condimento_itens_existentes=condimento_itens_existentes)