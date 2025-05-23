from flask import (
    Flask, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    session, 
    abort, 
    jsonify,
    flash # <--- Adicione 'flash' aqui
)
from models import db, Usuario, Marmita, Venda, VendaItem
from flask_migrate import Migrate
from functools import wraps
import secrets

# --- Configuração da Aplicação Flask ---

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Variável de ambiente é ideal para credenciais em produção
DATABASE_URI = 'postgresql://avnadmin:AVNS_BcfQql_OZUE_EXMLhp9@marmitas-db-marmitas.h.aivencloud.com:15576/defaultdb?sslmode=require'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração do pool de conexões do banco de dados
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'max_overflow': 0,
    'pool_timeout': 30,
    'pool_recycle': 1800
}

db.init_app(app)
migrate = Migrate(app, db)

# --- Context Processors e Funções Auxiliares ---

@app.context_processor
def inject_usuario_logado():
    """Injeta o objeto do usuário logado em todos os templates."""
    if 'usuario_id' in session:
        usuario = db.session.get(Usuario, session['usuario_id'])
        return dict(usuario_logado=usuario)
    return dict(usuario_logado=None)

def get_carrinho():
    """Retorna o dicionário do carrinho da sessão, inicializando-o se necessário."""
    if 'carrinho' not in session:
        session['carrinho'] = {}
    return session['carrinho']

def login_admin_required(f):
    """
    Decorador para rotas que exigem que o usuário seja administrador.
    Redireciona para 403 Forbidden se não for admin.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            abort(403)  # Acesso negado
        return f(*args, **kwargs)
    return wrapper

def obter_carrinho_detalhes():
    """
    Processa os itens do carrinho da sessão, retornando uma lista de dicionários
    com detalhes da marmita, quantidade e subtotal, além do total geral.
    """
    carrinho = get_carrinho()
    itens_detalhes = []
    total_carrinho = 0

    for id_str, quantidade in carrinho.items():
        marmita = db.session.get(Marmita, int(id_str))
        if marmita:
            subtotal = marmita.preco * quantidade
            total_carrinho += subtotal
            itens_detalhes.append({
                'marmita': marmita, 
                'quantidade': quantidade, 
                'subtotal': subtotal
            })
    return itens_detalhes, total_carrinho

# --- Rotas da Aplicação ---

@app.route('/')
def index():
    """Página inicial que exibe as marmitas disponíveis."""
    marmitas = Marmita.query.filter(Marmita.quantidade > 0).all()
    # O context processor já injeta 'usuario_logado'

    mensagem = request.args.get('mensagem')

    return render_template('index.html', marmitas=marmitas, carrinho=get_carrinho(), mensagem=mensagem)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Rota para registro de novos usuários."""
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        # Campos de endereço
        estado = request.form.get('estado', '')
        cidade = request.form.get('cidade', '')
        bairro = request.form.get('bairro', '')
        rua = request.form.get('rua', '')
        numero = request.form.get('numero', '')
        complemento = request.form.get('complemento', '')
        cep = request.form.get('cep')

        if Usuario.query.filter_by(email=email).first():
            return render_template('registro.html', erro="Email já cadastrado.")

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            estado=estado,
            cidade=cidade,
            bairro=bairro,
            rua=rua,
            numero=numero,
            complemento=complemento,
            cep=cep
        )
        novo_usuario.set_senha(senha)
        db.session.add(novo_usuario)
        db.session.commit()

        session['usuario_id'] = novo_usuario.id
        session['admin'] = novo_usuario.administrador

        return redirect(url_for('index'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de usuários."""
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.verificar_senha(senha):
            session['usuario_id'] = usuario.id
            session['admin'] = usuario.administrador
            return redirect(url_for('painel_admin') if usuario.administrador else url_for('index'))
        else:
            return render_template('login.html', erro='Login inválido. Verifique seu e-mail e senha.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Rota para logout do usuário."""
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@login_admin_required
def painel_admin():
    """Painel administrativo para gerenciar marmitas."""
    if request.method == 'POST':
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
            return redirect(url_for('painel_admin'))
        except ValueError:
            # Lidar com erro de conversão (e.g., preço não numérico)
            return render_template('admin.html', marmitas=Marmita.query.all(), erro="Dados inválidos para a marmita.")

    marmitas = Marmita.query.all()
    return render_template('admin.html', marmitas=marmitas)

@app.route('/admin/deletar/<int:id>')
@login_admin_required
def deletar_marmita(id):
    """Deleta uma marmita do banco de dados."""
    marmita = db.session.get(Marmita, id)
    if marmita:
        db.session.delete(marmita)
        db.session.commit()
    return redirect(url_for('painel_admin'))

@app.route('/admin/atualizar_estoque/<int:id>', methods=['POST'])
@login_admin_required
def atualizar_estoque(id):
    """Atualiza o estoque de uma marmita existente."""
    marmita = db.session.get(Marmita, id)
    if not marmita:
        return redirect(url_for('painel_admin')) # Ou retornar um erro 404

    try:
        adicional = int(request.form['quantidade_adicional'])
        if adicional > 0:
            marmita.quantidade += adicional
            db.session.commit()
    except ValueError:
        pass # Ignora se a quantidade não for um número válido
    return redirect(url_for('painel_admin'))

@app.route('/adicionar/<int:id>')
def adicionar(id):
    """Adiciona uma unidade de uma marmita ao carrinho (chamada da página inicial)."""
    marmita = db.session.get(Marmita, id)
    carrinho = get_carrinho()
    quantidade_no_carrinho = carrinho.get(str(id), 0)

    if marmita and quantidade_no_carrinho < marmita.quantidade:
        carrinho[str(id)] = quantidade_no_carrinho + 1
        session.modified = True
    else:
        # Opcional: Adicionar uma mensagem de erro para o usuário
        # flash("Estoque insuficiente para adicionar mais deste item.")
        pass 
    return redirect(url_for('index'))

@app.route('/aumentar/<int:id>', methods=['POST'])
def aumentar(id):
    """Aumenta a quantidade de um item no carrinho (via AJAX no carrinho)."""
    marmita = db.session.get(Marmita, id)
    carrinho = get_carrinho()
    quantidade_no_carrinho = carrinho.get(str(id), 0)

    if marmita and quantidade_no_carrinho < marmita.quantidade:
        carrinho[str(id)] = quantidade_no_carrinho + 1
        session.modified = True
        return jsonify({'success': True, 'nova_quantidade': carrinho[str(id)]})
    else:
        return jsonify({'success': False, 'mensagem': 'Estoque insuficiente ou item não encontrado.'}), 400

@app.route('/diminuir/<int:id>', methods=['POST'])
def diminuir(id):
    """Diminui a quantidade de um item no carrinho (via AJAX no carrinho)."""
    carrinho = get_carrinho()
    id_str = str(id)

    if id_str in carrinho:
        carrinho[id_str] = max(0, carrinho[id_str] - 1)
        if carrinho[id_str] == 0:
            del carrinho[id_str] # Remove o item se a quantidade chegar a zero
        session.modified = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'mensagem': 'Item não encontrado no carrinho.'}), 404


@app.route('/remover_item_completo/<int:item_id>', methods=['POST'])
#@login_required # Garante que apenas usuários logados possam usar essa rota - Mantenha se quiser
def remover_item_completo(item_id):
    carrinho = get_carrinho() # Use get_carrinho() para garantir que é um dicionário
    item_id_str = str(item_id) # Converte o ID para string para corresponder à chave do dicionário

    if item_id_str in carrinho:
        del carrinho[item_id_str] # Remove a entrada completa do dicionário
        session.modified = True # Importante para garantir que a sessão seja salva
        flash(f'Todos os itens do produto foram removidos do carrinho.', 'info')
    else:
        flash(f'O produto não foi encontrado no carrinho.', 'warning')
        
    return jsonify({'success': True}) # Retorne JSON para a chamada AJAX
    # return redirect(url_for('ver_carrinho')) # Você pode manter o redirect se preferir não usar AJAX para isso
                                         


@app.route('/carrinho')
def ver_carrinho():
    """Exibe a página do carrinho com os itens e o total."""
    itens, total = obter_carrinho_detalhes()
    return render_template('carrinho.html', itens=itens, total=total)


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Processa o checkout do pedido."""
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para finalizar a compra.", "info") # Mensagem flash
        return redirect(url_for('login'))


    usuario = db.session.get(Usuario, session['usuario_id'])
    
    itens, total = obter_carrinho_detalhes()

    if request.method == 'POST':
        if not itens:
            return render_template(
                'checkout.html', 
                erro="Carrinho vazio. Adicione itens antes de finalizar a compra.", 
                itens=itens, 
                total=total,
                endereco=usuario.endereco_completo() # Simplificado
            )

        endereco_entrega = request.form.get('endereco')
        forma_pagamento = request.form.get('pagamento')
        troco_para = request.form.get('troco', '')

        # Validação de campos obrigatórios
        if not endereco_entrega or not forma_pagamento:
            return render_template(
                'checkout.html', 
                erro="Endereço de entrega e forma de pagamento são obrigatórios.", 
                itens=itens, 
                total=total, 
                endereco=usuario.endereco_completo() # Simplificado
            )

        # Checar estoque final antes de finalizar
        for item in itens:
            # Re-fetch da marmita para garantir que o estoque está atualizado
            marmita_atualizada = db.session.get(Marmita, item['marmita'].id)
            if not marmita_atualizada or marmita_atualizada.quantidade < item['quantidade']:
                return render_template(
                    'checkout.html', 
                    erro=f"Estoque insuficiente para {item['marmita'].nome}. Por favor, ajuste a quantidade.", 
                    itens=itens, 
                    total=total,
                    endereco=usuario.endereco_completo() # Simplificado
                )

        try:
            # Inicia uma transação para garantir a atomicidade
            with db.session.begin_nested():
                nova_venda = Venda(
                    usuario_id=usuario.id, # Simplificado (agora temos certeza que usuario.id existe)
                    total=total,
                    endereco_entrega=endereco_entrega, 
                    forma_pagamento=forma_pagamento,
                    troco_para=troco_para if troco_para else None
                )
                db.session.add(nova_venda)
                db.session.flush()

                for item in itens:
                    venda_item = VendaItem(
                        venda_id=nova_venda.id,
                        marmita_id=item['marmita'].id,
                        quantidade=item['quantidade'],
                        preco_unitario=item['marmita'].preco
                    )
                    db.session.add(venda_item)

                    # Subtrai do estoque
                    marmita_no_estoque = db.session.get(Marmita, item['marmita'].id)
                    marmita_no_estoque.quantidade -= item['quantidade']

                db.session.commit() # Confirma todas as operações da transação
                session.pop('carrinho', None) # Limpa o carrinho após a compra

            mensagem_sucesso = f'✅ Pedido realizado com sucesso! ID: {nova_venda.id} - Endereço: {endereco_entrega} - Pagamento: {forma_pagamento}'
            if troco_para:
                mensagem_sucesso += f' - Troco para: R$ {float(troco_para):.2f}'
            
            return redirect(url_for('index', mensagem=mensagem_sucesso))

        except Exception as e:
            db.session.rollback() # Reverte a transação em caso de erro
            print(f"Erro ao finalizar compra: {e}")
            return render_template(
                'checkout.html', 
                erro="Ocorreu um erro ao finalizar o pedido. Tente novamente.", 
                itens=itens, 
                total=total,
                endereco=usuario.endereco_completo() # Simplificado
            )

    return render_template(
        'checkout.html',
        endereco=usuario.endereco_completo(), # Simplificado
        itens=itens,
        total=total
    )

# --- Execução da Aplicação ---
if __name__ == '__main__':
    app.run(debug=True)