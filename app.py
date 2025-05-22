from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
from models import db, Usuario, Marmita, Venda, VendaItem
from flask_migrate import Migrate
from functools import wraps
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # 🔒 Chave secreta mais segura

# 🔗 Configuração do Banco com controle de conexões
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://avnadmin:AVNS_BcfQql_OZUE_EXMLhp9@marmitas-db-marmitas.h.aivencloud.com:15576/defaultdb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 🔧 Limitar conexões no banco
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,       # 🔥 até 10 conexões no pool
    'max_overflow': 0,     # 🔥 não permite conexões além do pool
    'pool_timeout': 30,    # tempo máximo de espera por conexão
    'pool_recycle': 1800   # recicla conexões a cada 30 minutos
}

db.init_app(app)
migrate = Migrate(app, db)


# 🔸 Context processor para injetar usuário logado nos templates
@app.context_processor
def inject_usuario_logado():
    if 'usuario_id' in session:
        usuario = db.session.get(Usuario, session['usuario_id'])
        return dict(usuario_logado=usuario)
    return dict(usuario_logado=None)


# 🔸 Função para acessar o carrinho na sessão
def get_carrinho():
    if 'carrinho' not in session:
        session['carrinho'] = {}
    return session['carrinho']


# 🔸 Decorador para verificar admin
def login_admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            abort(403)
        return f(*args, **kwargs)
    return wrapper


# 🔸 Página inicial
@app.route('/')
def index():
    marmitas = Marmita.query.filter(Marmita.quantidade > 0).all()
    carrinho = get_carrinho()
    usuario = None
    if 'usuario_id' in session:
        usuario = db.session.get(Usuario, session['usuario_id'])
    return render_template('index.html', marmitas=marmitas, carrinho=carrinho, usuario_logado=usuario)


# 🔸 Registro de usuários
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        endereco = request.form['endereco']

        if Usuario.query.filter_by(email=email).first():
            return render_template('registro.html', erro="Email já cadastrado.")

        usuario = Usuario(nome=nome, email=email, endereco=endereco)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()

        session['usuario_id'] = usuario.id
        session['admin'] = usuario.administrador

        return redirect(url_for('index'))

    return render_template('registro.html')


# 🔸 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.verificar_senha(senha):
            session['usuario_id'] = usuario.id
            session['admin'] = usuario.administrador

            if usuario.administrador:
                return redirect(url_for('painel_admin'))
            else:
                return redirect(url_for('index'))
        else:
            return render_template('login.html', erro='Login inválido.')
    return render_template('login.html')


# 🔸 Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# 🔸 Painel admin
@app.route('/admin', methods=['GET', 'POST'])
@login_admin_required
def painel_admin():
    if request.method == 'POST':
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

    marmitas = Marmita.query.all()
    return render_template('admin.html', marmitas=marmitas)


# 🔸 Deletar marmita
@app.route('/admin/deletar/<int:id>')
@login_admin_required
def deletar_marmita(id):
    marmita = db.session.get(Marmita, id)
    if marmita:
        db.session.delete(marmita)
        db.session.commit()
    return redirect(url_for('painel_admin'))


# 🔸 Atualizar estoque
@app.route('/admin/atualizar_estoque/<int:id>', methods=['POST'])
@login_admin_required
def atualizar_estoque(id):
    marmita = db.session.get(Marmita, id)
    try:
        adicional = int(request.form['quantidade_adicional'])
        if adicional > 0:
            marmita.quantidade += adicional
            db.session.commit()
    except ValueError:
        pass
    return redirect(url_for('painel_admin'))


# 🔸 Adicionar item ao carrinho
@app.route('/adicionar/<int:id>')
def adicionar(id):
    marmita = db.session.get(Marmita, id)
    carrinho = get_carrinho()
    atual = carrinho.get(str(id), 0)

    if marmita and atual < marmita.quantidade:
        carrinho[str(id)] = atual + 1
        session.modified = True
    return redirect(url_for('index'))


# 🔸 Aumentar item no carrinho
@app.route('/aumentar/<int:id>', methods=['POST'])
def aumentar(id):
    marmita = db.session.get(Marmita, id)
    carrinho = get_carrinho()
    atual = carrinho.get(str(id), 0)

    if marmita and atual < marmita.quantidade:
        carrinho[str(id)] = atual + 1
        session.modified = True
        return jsonify({'success': True, 'nova_quantidade': carrinho[str(id)]})
    else:
        return jsonify({'success': False, 'mensagem': 'Estoque insuficiente.'}), 400


# 🔸 Diminuir item do carrinho
@app.route('/diminuir/<int:id>', methods=['POST'])
def diminuir(id):
    carrinho = get_carrinho()
    id_str = str(id)
    if id_str in carrinho:
        carrinho[id_str] = max(0, carrinho[id_str] - 1)
        if carrinho[id_str] == 0:
            del carrinho[id_str]
        session.modified = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'mensagem': 'Item não encontrado no carrinho.'}), 404


# 🔸 Ver carrinho
@app.route('/carrinho')
def ver_carrinho():
    carrinho = get_carrinho()
    itens = []
    total = 0
    for id_str, quantidade in carrinho.items():
        marmita = db.session.get(Marmita, int(id_str))
        if marmita:
            subtotal = marmita.preco * quantidade
            total += subtotal
            itens.append({'marmita': marmita, 'quantidade': quantidade, 'subtotal': subtotal})
    return render_template('carrinho.html', itens=itens, total=total)


# 🔸 Checkout
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    usuario = None
    if 'usuario_id' in session:
        usuario = db.session.get(Usuario, session['usuario_id'])

    carrinho = get_carrinho()
    itens = []
    total = 0

    for id_str, quantidade in carrinho.items():
        marmita = db.session.get(Marmita, int(id_str))
        if marmita:
            subtotal = marmita.preco * quantidade
            total += subtotal
            itens.append({'marmita': marmita, 'quantidade': quantidade, 'subtotal': subtotal})

    if request.method == 'POST':
        if not carrinho:
            return render_template('checkout.html', erro="Carrinho vazio.", itens=itens, total=total)

        endereco = request.form['endereco']
        forma_pagamento = request.form['pagamento']
        troco = request.form.get('troco', '')

        # 🚨 Checar estoque antes de finalizar
        for item in itens:
            if item['marmita'].quantidade < item['quantidade']:
                return f"Estoque insuficiente para {item['marmita'].nome}."

        venda = Venda(
            usuario_id=usuario.id if usuario else None,
            total=total
        )
        db.session.add(venda)
        db.session.commit()

        for item in itens:
            venda_item = VendaItem(
                venda_id=venda.id,
                marmita_id=item['marmita'].id,
                quantidade=item['quantidade']
            )
            db.session.add(venda_item)

            item['marmita'].quantidade -= item['quantidade']

        db.session.commit()
        session.pop('carrinho', None)

        return f'✅ Pedido realizado com sucesso! ID: {venda.id} - Endereço: {endereco} - Pagamento: {forma_pagamento}' + (f" - Troco: {troco}" if troco else "")

    return render_template(
        'checkout.html',
        endereco=(usuario.endereco if usuario else ""),
        itens=itens,
        total=total
    )


if __name__ == '__main__':
    app.run(debug=True)
