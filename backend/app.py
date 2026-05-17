import os
import sys
from datetime import datetime, date
from decimal import Decimal
import json

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'frontend', 'templates'),
            static_folder=os.path.join(base_dir, 'frontend', 'static'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-vendas-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///' + os.path.join(base_dir, 'database', 'vendas.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================================================
# MODELOS
# =============================================================================

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), default='admin')
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.String(300))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    vendas = db.relationship('Venda', backref='cliente', lazy='dynamic')

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    preco_custo = db.Column(db.Numeric(10, 2), nullable=False)
    preco_venda = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade_estoque = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(50))
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def lucro_unitario(self):
        return float(self.preco_venda) - float(self.preco_custo)

    @property
    def margem_lucro(self):
        if float(self.preco_custo) == 0:
            return 0
        return ((float(self.preco_venda) - float(self.preco_custo)) / float(self.preco_custo)) * 100

class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    data_venda = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(12, 2), default=0)
    lucro_total = db.Column(db.Numeric(12, 2), default=0)
    forma_pagamento = db.Column(db.String(30), default='dinheiro')
    status = db.Column(db.String(20), default='concluida')
    observacoes = db.Column(db.Text)

    itens = db.relationship('ItemVenda', backref='venda', lazy='dynamic', cascade='all, delete-orphan')

class ItemVenda(db.Model):
    __tablename__ = 'itens_venda'
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    custo_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    lucro_item = db.Column(db.Numeric(10, 2), nullable=False)

    produto = db.relationship('Produto')

class LogOperacao(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    acao = db.Column(db.String(50), nullable=False)
    tabela = db.Column(db.String(50))
    registro_id = db.Column(db.Integer)
    detalhes = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

# =============================================================================
# UTILITÁRIOS
# =============================================================================

def registrar_log(acao, tabela=None, registro_id=None, detalhes=None):
    """Registra uma operação no log de auditoria."""
    log = LogOperacao(
        usuario_id=session.get('usuario_id'),
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        detalhes=detalhes,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

def requer_login(f):
    """Decorator para rotas que exigem login."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            return jsonify({'erro': 'Autenticação necessária'}), 401
        return f(*args, **kwargs)
    return decorated

# =============================================================================
# ROTAS - AUTENTICAÇÃO
# =============================================================================

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/clientes')
def clientes_page():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    return render_template('clientes.html')

@app.route('/produtos')
def produtos_page():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    return render_template('produtos.html')

@app.route('/vendas')
def vendas_page():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    return render_template('vendas.html')

@app.route('/relatorios')
def relatorios_page():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    return render_template('relatorios.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '')

    if not email or not senha:
        return jsonify({'erro': 'Email e senha são obrigatórios'}), 400

    usuario = Usuario.query.filter_by(email=email, ativo=True).first()

    if not usuario or not check_password_hash(usuario.senha_hash, senha):
        return jsonify({'erro': 'Email ou senha incorretos'}), 401

    session['usuario_id'] = usuario.id
    session['usuario_nome'] = usuario.nome
    session['usuario_tipo'] = usuario.tipo

    registrar_log('login', 'usuarios', usuario.id, f'Login de {usuario.nome}')

    return jsonify({
        'sucesso': True,
        'usuario': {'id': usuario.id, 'nome': usuario.nome, 'email': usuario.email, 'tipo': usuario.tipo}
    }), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    if 'usuario_id' in session:
        registrar_log('logout', 'usuarios', session['usuario_id'])
        session.clear()
    return jsonify({'sucesso': True, 'mensagem': 'Logout realizado'}), 200

@app.route('/api/usuario/atual')
def usuario_atual():
    if 'usuario_id' not in session:
        return jsonify({'autenticado': False}), 200

    usuario = Usuario.query.get(session['usuario_id'])
    if not usuario:
        session.clear()
        return jsonify({'autenticado': False}), 200

    return jsonify({
        'autenticado': True,
        'usuario': {'id': usuario.id, 'nome': usuario.nome, 'email': usuario.email, 'tipo': usuario.tipo}
    }), 200

# =============================================================================
# ROTAS - CLIENTES
# =============================================================================

@app.route('/api/clientes', methods=['GET'])
@requer_login
def listar_clientes():
    try:
        busca = request.args.get('q', '').strip()
        query = Cliente.query

        if busca:
            query = query.filter(
                db.or_(
                    Cliente.nome.ilike(f'%{busca}%'),
                    Cliente.email.ilike(f'%{busca}%'),
                    Cliente.telefone.ilike(f'%{busca}%')
                )
            )

        clientes = query.order_by(Cliente.nome).all()

        resultado = []
        for c in clientes:
            # Calcular total gasto e lucro gerado pelo cliente
            total_gasto = db.session.query(db.func.sum(Venda.total)).filter(Venda.cliente_id == c.id).scalar() or 0
            total_lucro = db.session.query(db.func.sum(Venda.lucro_total)).filter(Venda.cliente_id == c.id).scalar() or 0
            num_vendas = Venda.query.filter_by(cliente_id=c.id).count()

            resultado.append({
                'id': c.id,
                'nome': c.nome,
                'email': c.email,
                'telefone': c.telefone,
                'endereco': c.endereco,
                'cidade': c.cidade,
                'estado': c.estado,
                'latitude': c.latitude,
                'longitude': c.longitude,
                'total_gasto': float(total_gasto),
                'total_lucro': float(total_lucro),
                'num_vendas': num_vendas,
                'criado_em': c.criado_em.isoformat() if c.criado_em else None
            })

        return jsonify({'sucesso': True, 'clientes': resultado}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/clientes', methods=['POST'])
@requer_login
def criar_cliente():
    try:
        data = request.get_json()

        if not data.get('nome'):
            return jsonify({'erro': 'Nome do cliente é obrigatório'}), 400

        cliente = Cliente(
            nome=data['nome'].strip(),
            email=data.get('email', '').strip().lower(),
            telefone=data.get('telefone', '').strip(),
            endereco=data.get('endereco', '').strip(),
            cidade=data.get('cidade', '').strip(),
            estado=data.get('estado', '').strip().upper()[:2],
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )

        db.session.add(cliente)
        db.session.commit()

        registrar_log('criar', 'clientes', cliente.id, f'Cliente {cliente.nome} criado')

        return jsonify({'sucesso': True, 'cliente': {'id': cliente.id, 'nome': cliente.nome}}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/clientes/<int:id>', methods=['PUT'])
@requer_login
def atualizar_cliente(id):
    try:
        cliente = Cliente.query.get_or_404(id)
        data = request.get_json()

        cliente.nome = data.get('nome', cliente.nome).strip()
        cliente.email = data.get('email', cliente.email).strip().lower()
        cliente.telefone = data.get('telefone', cliente.telefone).strip()
        cliente.endereco = data.get('endereco', cliente.endereco).strip()
        cliente.cidade = data.get('cidade', cliente.cidade).strip()
        cliente.estado = data.get('estado', cliente.estado).strip().upper()[:2]
        cliente.latitude = data.get('latitude', cliente.latitude)
        cliente.longitude = data.get('longitude', cliente.longitude)

        db.session.commit()

        registrar_log('atualizar', 'clientes', cliente.id, f'Cliente {cliente.nome} atualizado')

        return jsonify({'sucesso': True, 'mensagem': 'Cliente atualizado'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/clientes/<int:id>', methods=['DELETE'])
@requer_login
def excluir_cliente(id):
    try:
        cliente = Cliente.query.get_or_404(id)
        nome = cliente.nome

        # Verifica se há vendas associadas
        if Venda.query.filter_by(cliente_id=id).first():
            return jsonify({'erro': 'Não é possível excluir cliente com vendas registradas'}), 400

        db.session.delete(cliente)
        db.session.commit()

        registrar_log('excluir', 'clientes', id, f'Cliente {nome} excluído')

        return jsonify({'sucesso': True, 'mensagem': 'Cliente excluído'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/clientes/<int:id>')
@requer_login
def obter_cliente(id):
    try:
        cliente = Cliente.query.get_or_404(id)

        total_gasto = db.session.query(db.func.sum(Venda.total)).filter(Venda.cliente_id == id).scalar() or 0
        total_lucro = db.session.query(db.func.sum(Venda.lucro_total)).filter(Venda.cliente_id == id).scalar() or 0
        num_vendas = Venda.query.filter_by(cliente_id=id).count()

        return jsonify({
            'sucesso': True,
            'cliente': {
                'id': cliente.id,
                'nome': cliente.nome,
                'email': cliente.email,
                'telefone': cliente.telefone,
                'endereco': cliente.endereco,
                'cidade': cliente.cidade,
                'estado': cliente.estado,
                'latitude': cliente.latitude,
                'longitude': cliente.longitude,
                'total_gasto': float(total_gasto),
                'total_lucro': float(total_lucro),
                'num_vendas': num_vendas,
                'criado_em': cliente.criado_em.isoformat() if cliente.criado_em else None
            }
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# =============================================================================
# ROTAS - PRODUTOS
# =============================================================================

@app.route('/api/produtos', methods=['GET'])
@requer_login
def listar_produtos():
    try:
        busca = request.args.get('q', '').strip()
        categoria = request.args.get('categoria', '').strip()

        query = Produto.query.filter_by(ativo=True)

        if busca:
            query = query.filter(
                db.or_(
                    Produto.nome.ilike(f'%{busca}%'),
                    Produto.descricao.ilike(f'%{busca}%')
                )
            )

        if categoria:
            query = query.filter(Produto.categoria == categoria)

        produtos = query.order_by(Produto.nome).all()

        resultado = []
        for p in produtos:
            resultado.append({
                'id': p.id,
                'nome': p.nome,
                'descricao': p.descricao,
                'preco_custo': float(p.preco_custo),
                'preco_venda': float(p.preco_venda),
                'lucro_unitario': p.lucro_unitario,
                'margem_lucro': round(p.margem_lucro, 2),
                'quantidade_estoque': p.quantidade_estoque,
                'categoria': p.categoria,
                'ativo': p.ativo,
                'criado_em': p.criado_em.isoformat() if p.criado_em else None
            })

        return jsonify({'sucesso': True, 'produtos': resultado}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/produtos/categorias')
@requer_login
def listar_categorias():
    try:
        categorias = db.session.query(Produto.categoria).filter(
            Produto.categoria.isnot(None),
            Produto.ativo == True
        ).distinct().all()
        return jsonify({'sucesso': True, 'categorias': [c[0] for c in categorias if c[0]]}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/produtos', methods=['POST'])
@requer_login
def criar_produto():
    try:
        data = request.get_json()

        if not data.get('nome'):
            return jsonify({'erro': 'Nome do produto é obrigatório'}), 400
        if not data.get('preco_venda'):
            return jsonify({'erro': 'Preço de venda é obrigatório'}), 400

        produto = Produto(
            nome=data['nome'].strip(),
            descricao=data.get('descricao', '').strip(),
            preco_custo=Decimal(str(data.get('preco_custo', 0))),
            preco_venda=Decimal(str(data['preco_venda'])),
            quantidade_estoque=data.get('quantidade_estoque', 0),
            categoria=data.get('categoria', '').strip()
        )

        db.session.add(produto)
        db.session.commit()

        registrar_log('criar', 'produtos', produto.id, f'Produto {produto.nome} criado')

        return jsonify({'sucesso': True, 'produto': {'id': produto.id, 'nome': produto.nome}}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/produtos/<int:id>', methods=['PUT'])
@requer_login
def atualizar_produto(id):
    try:
        produto = Produto.query.get_or_404(id)
        data = request.get_json()

        produto.nome = data.get('nome', produto.nome).strip()
        produto.descricao = data.get('descricao', produto.descricao).strip()
        produto.preco_custo = Decimal(str(data.get('preco_custo', produto.preco_custo)))
        produto.preco_venda = Decimal(str(data.get('preco_venda', produto.preco_venda)))
        produto.quantidade_estoque = data.get('quantidade_estoque', produto.quantidade_estoque)
        produto.categoria = data.get('categoria', produto.categoria).strip()

        db.session.commit()

        registrar_log('atualizar', 'produtos', produto.id, f'Produto {produto.nome} atualizado')

        return jsonify({'sucesso': True, 'mensagem': 'Produto atualizado'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/produtos/<int:id>', methods=['DELETE'])
@requer_login
def excluir_produto(id):
    try:
        produto = Produto.query.get_or_404(id)
        nome = produto.nome

        # Soft delete
        produto.ativo = False
        db.session.commit()

        registrar_log('excluir', 'produtos', id, f'Produto {nome} inativado')

        return jsonify({'sucesso': True, 'mensagem': 'Produto inativado'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# =============================================================================
# ROTAS - VENDAS
# =============================================================================

@app.route('/api/vendas', methods=['GET'])
@requer_login
def listar_vendas():
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        cliente_id = request.args.get('cliente_id', type=int)

        query = Venda.query

        if data_inicio:
            query = query.filter(Venda.data_venda >= data_inicio)
        if data_fim:
            query = query.filter(Venda.data_venda <= data_fim + ' 23:59:59')
        if cliente_id:
            query = query.filter(Venda.cliente_id == cliente_id)

        vendas = query.order_by(Venda.data_venda.desc()).limit(100).all()

        resultado = []
        for v in vendas:
            cliente_nome = v.cliente.nome if v.cliente else 'Cliente removido'
            itens_list = []
            for item in v.itens:
                itens_list.append({
                    'id': item.id,
                    'produto_id': item.produto_id,
                    'produto_nome': item.produto.nome if item.produto else 'Produto removido',
                    'quantidade': item.quantidade,
                    'preco_unitario': float(item.preco_unitario),
                    'subtotal': float(item.subtotal)
                })

            resultado.append({
                'id': v.id,
                'cliente_id': v.cliente_id,
                'cliente_nome': cliente_nome,
                'data_venda': v.data_venda.isoformat() if v.data_venda else None,
                'total': float(v.total),
                'lucro_total': float(v.lucro_total),
                'forma_pagamento': v.forma_pagamento,
                'status': v.status,
                'observacoes': v.observacoes,
                'itens': itens_list
            })

        return jsonify({'sucesso': True, 'vendas': resultado}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/vendas', methods=['POST'])
@requer_login
def criar_venda():
    try:
        data = request.get_json()

        if not data.get('cliente_id'):
            return jsonify({'erro': 'Cliente é obrigatório'}), 400
        if not data.get('itens') or len(data['itens']) == 0:
            return jsonify({'erro': 'Adicione pelo menos um item à venda'}), 400

        cliente = Cliente.query.get(data['cliente_id'])
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        venda = Venda(
            cliente_id=data['cliente_id'],
            forma_pagamento=data.get('forma_pagamento', 'dinheiro'),
            observacoes=data.get('observacoes', '').strip(),
            status='concluida'
        )

        db.session.add(venda)
        db.session.flush()

        total_venda = Decimal('0')
        lucro_venda = Decimal('0')

        for item_data in data['itens']:
            produto = Produto.query.get(item_data['produto_id'])
            if not produto or not produto.ativo:
                db.session.rollback()
                return jsonify({'erro': f'Produto ID {item_data["produto_id"]} não encontrado'}), 404

            qtd = int(item_data['quantidade'])
            if qtd <= 0:
                db.session.rollback()
                return jsonify({'erro': 'Quantidade deve ser maior que zero'}), 400

            if produto.quantidade_estoque < qtd:
                db.session.rollback()
                return jsonify({'erro': f'Estoque insuficiente para {produto.nome} (disponível: {produto.quantidade_estoque})'}), 400

            preco_unit = Decimal(str(item_data.get('preco_unitario', produto.preco_venda)))
            custo_unit = produto.preco_custo
            subtotal = preco_unit * qtd
            lucro_item = (preco_unit - custo_unit) * qtd

            item = ItemVenda(
                venda_id=venda.id,
                produto_id=produto.id,
                quantidade=qtd,
                preco_unitario=preco_unit,
                custo_unitario=custo_unit,
                subtotal=subtotal,
                lucro_item=lucro_item
            )

            db.session.add(item)

            # Atualiza estoque
            produto.quantidade_estoque -= qtd

            total_venda += subtotal
            lucro_venda += lucro_item

        venda.total = total_venda
        venda.lucro_total = lucro_venda

        db.session.commit()

        registrar_log('criar', 'vendas', venda.id, f'Venda #{venda.id} - Total: R$ {float(total_venda):.2f}')

        return jsonify({
            'sucesso': True,
            'venda': {
                'id': venda.id,
                'total': float(venda.total),
                'lucro_total': float(venda.lucro_total)
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/vendas/<int:id>', methods=['DELETE'])
@requer_login
def excluir_venda(id):
    try:
        venda = Venda.query.get_or_404(id)

        # Devolve os itens ao estoque
        for item in venda.itens:
            produto = Produto.query.get(item.produto_id)
            if produto:
                produto.quantidade_estoque += item.quantidade

        db.session.delete(venda)
        db.session.commit()

        registrar_log('excluir', 'vendas', id, f'Venda #{id} excluída')

        return jsonify({'sucesso': True, 'mensagem': 'Venda excluída e estoque restaurado'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# =============================================================================
# ROTAS - DASHBOARD E RELATÓRIOS
# =============================================================================

@app.route('/api/dashboard')
@requer_login
def dashboard_dados():
    try:
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)

        # Vendas de hoje
        vendas_hoje = db.session.query(db.func.sum(Venda.total)).filter(
            db.func.date(Venda.data_venda) == hoje,
            Venda.status == 'concluida'
        ).scalar() or 0

        lucro_hoje = db.session.query(db.func.sum(Venda.lucro_total)).filter(
            db.func.date(Venda.data_venda) == hoje,
            Venda.status == 'concluida'
        ).scalar() or 0

        # Vendas do mês
        vendas_mes = db.session.query(db.func.sum(Venda.total)).filter(
            Venda.data_venda >= inicio_mes,
            Venda.status == 'concluida'
        ).scalar() or 0

        lucro_mes = db.session.query(db.func.sum(Venda.lucro_total)).filter(
            Venda.data_venda >= inicio_mes,
            Venda.status == 'concluida'
        ).scalar() or 0

        # Total de vendas
        num_vendas_hoje = Venda.query.filter(
            db.func.date(Venda.data_venda) == hoje,
            Venda.status == 'concluida'
        ).count()

        num_vendas_mes = Venda.query.filter(
            Venda.data_venda >= inicio_mes,
            Venda.status == 'concluida'
        ).count()

        # Total de clientes
        total_clientes = Cliente.query.count()
        total_produtos = Produto.query.filter_by(ativo=True).count()

        # Produtos com estoque baixo (menos de 10)
        estoque_baixo = Produto.query.filter(
            Produto.quantidade_estoque < 10,
            Produto.ativo == True
        ).count()

        # Top 5 clientes que mais geram lucro
        top_clientes = db.session.query(
            Cliente.id,
            Cliente.nome,
            db.func.sum(Venda.lucro_total).label('lucro_total'),
            db.func.sum(Venda.total).label('total_gasto')
        ).join(Venda).filter(Venda.status == 'concluida').group_by(
            Cliente.id, Cliente.nome
        ).order_by(db.desc('lucro_total')).limit(5).all()

        top_clientes_list = []
        for c in top_clientes:
            top_clientes_list.append({
                'id': c.id,
                'nome': c.nome,
                'lucro_total': float(c.lucro_total) if c.lucro_total else 0,
                'total_gasto': float(c.total_gasto) if c.total_gasto else 0
            })

        # Top 5 produtos mais vendidos (por lucro)
        top_produtos = db.session.query(
            Produto.id,
            Produto.nome,
            db.func.sum(ItemVenda.lucro_item).label('lucro_total'),
            db.func.sum(ItemVenda.quantidade).label('qtd_vendida')
        ).join(ItemVenda).join(Venda).filter(
            Venda.status == 'concluida',
            Produto.ativo == True
        ).group_by(Produto.id, Produto.nome).order_by(
            db.desc('lucro_total')
        ).limit(5).all()

        top_produtos_list = []
        for p in top_produtos:
            top_produtos_list.append({
                'id': p.id,
                'nome': p.nome,
                'lucro_total': float(p.lucro_total) if p.lucro_total else 0,
                'qtd_vendida': int(p.qtd_vendida) if p.qtd_vendida else 0
            })

        # Vendas dos últimos 7 dias para gráfico
        vendas_7dias = []
        for i in range(6, -1, -1):
            dia = hoje - __import__('datetime').timedelta(days=i)
            total_dia = db.session.query(db.func.sum(Venda.total)).filter(
                db.func.date(Venda.data_venda) == dia,
                Venda.status == 'concluida'
            ).scalar() or 0
            lucro_dia = db.session.query(db.func.sum(Venda.lucro_total)).filter(
                db.func.date(Venda.data_venda) == dia,
                Venda.status == 'concluida'
            ).scalar() or 0
            vendas_7dias.append({
                'dia': dia.strftime('%d/%m'),
                'total': float(total_dia),
                'lucro': float(lucro_dia)
            })

        return jsonify({
            'sucesso': True,
            'resumo': {
                'vendas_hoje': float(vendas_hoje),
                'lucro_hoje': float(lucro_hoje),
                'num_vendas_hoje': num_vendas_hoje,
                'vendas_mes': float(vendas_mes),
                'lucro_mes': float(lucro_mes),
                'num_vendas_mes': num_vendas_mes,
                'total_clientes': total_clientes,
                'total_produtos': total_produtos,
                'estoque_baixo': estoque_baixo
            },
            'top_clientes': top_clientes_list,
            'top_produtos': top_produtos_list,
            'vendas_7dias': vendas_7dias
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/relatorios/lucratividade-clientes')
@requer_login
def relatorio_lucratividade_clientes():
    try:
        clientes = db.session.query(
            Cliente.id,
            Cliente.nome,
            Cliente.email,
            Cliente.cidade,
            db.func.count(Venda.id).label('num_vendas'),
            db.func.sum(Venda.total).label('total_gasto'),
            db.func.sum(Venda.lucro_total).label('lucro_total')
        ).outerjoin(Venda).filter(
            db.or_(Venda.status == 'concluida', Venda.status.is_(None))
        ).group_by(Cliente.id, Cliente.nome, Cliente.email, Cliente.cidade).order_by(
            db.desc('lucro_total')
        ).all()

        resultado = []
        for c in clientes:
            resultado.append({
                'id': c.id,
                'nome': c.nome,
                'email': c.email,
                'cidade': c.cidade,
                'num_vendas': int(c.num_vendas) if c.num_vendas else 0,
                'total_gasto': float(c.total_gasto) if c.total_gasto else 0,
                'lucro_total': float(c.lucro_total) if c.lucro_total else 0,
                'ticket_medio': float(c.total_gasto / c.num_vendas) if c.num_vendas and c.num_vendas > 0 else 0
            })

        return jsonify({'sucesso': True, 'clientes': resultado}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/relatorios/lucratividade-produtos')
@requer_login
def relatorio_lucratividade_produtos():
    try:
        produtos = db.session.query(
            Produto.id,
            Produto.nome,
            Produto.categoria,
            Produto.preco_custo,
            Produto.preco_venda,
            db.func.sum(ItemVenda.quantidade).label('qtd_vendida'),
            db.func.sum(ItemVenda.lucro_item).label('lucro_total')
        ).outerjoin(ItemVenda).outerjoin(Venda).filter(
            db.or_(Venda.status == 'concluida', Venda.status.is_(None)),
            Produto.ativo == True
        ).group_by(Produto.id, Produto.nome, Produto.categoria, 
                   Produto.preco_custo, Produto.preco_venda).order_by(
            db.desc('lucro_total')
        ).all()

        resultado = []
        for p in produtos:
            custo = float(p.preco_custo) if p.preco_custo else 0
            venda = float(p.preco_venda) if p.preco_venda else 0
            margem = ((venda - custo) / custo * 100) if custo > 0 else 0

            resultado.append({
                'id': p.id,
                'nome': p.nome,
                'categoria': p.categoria,
                'preco_custo': custo,
                'preco_venda': venda,
                'margem_lucro': round(margem, 2),
                'qtd_vendida': int(p.qtd_vendida) if p.qtd_vendida else 0,
                'lucro_total': float(p.lucro_total) if p.lucro_total else 0
            })

        return jsonify({'sucesso': True, 'produtos': resultado}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/relatorios/vendas-periodo')
@requer_login
def relatorio_vendas_periodo():
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        if not data_inicio or not data_fim:
            return jsonify({'erro': 'Período obrigatório'}), 400

        query = Venda.query.filter(
            Venda.data_venda >= data_inicio,
            Venda.data_venda <= data_fim + ' 23:59:59',
            Venda.status == 'concluida'
        )

        total_vendas = db.session.query(db.func.sum(Venda.total)).filter(
            Venda.data_venda >= data_inicio,
            Venda.data_venda <= data_fim + ' 23:59:59',
            Venda.status == 'concluida'
        ).scalar() or 0

        total_lucro = db.session.query(db.func.sum(Venda.lucro_total)).filter(
            Venda.data_venda >= data_inicio,
            Venda.data_venda <= data_fim + ' 23:59:59',
            Venda.status == 'concluida'
        ).scalar() or 0

        num_vendas = query.count()

        # Por forma de pagamento
        por_pagamento = db.session.query(
            Venda.forma_pagamento,
            db.func.count(Venda.id).label('qtd'),
            db.func.sum(Venda.total).label('total')
        ).filter(
            Venda.data_venda >= data_inicio,
            Venda.data_venda <= data_fim + ' 23:59:59',
            Venda.status == 'concluida'
        ).group_by(Venda.forma_pagamento).all()

        pagamento_list = []
        for p in por_pagamento:
            pagamento_list.append({
                'forma': p.forma_pagamento,
                'quantidade': int(p.qtd),
                'total': float(p.total) if p.total else 0
            })

        return jsonify({
            'sucesso': True,
            'resumo': {
                'periodo': f'{data_inicio} a {data_fim}',
                'total_vendas': float(total_vendas),
                'total_lucro': float(total_lucro),
                'num_vendas': num_vendas,
                'ticket_medio': float(total_vendas / num_vendas) if num_vendas > 0 else 0
            },
            'por_pagamento': pagamento_list
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# =============================================================================
# INICIALIZAÇÃO COM DADOS DE EXEMPLO
# =============================================================================

def criar_dados_exemplo():
    """Cria dados de exemplo se o banco estiver vazio."""
    if Usuario.query.first():
        return

    # Usuário admin
    admin = Usuario(
        nome='Administrador',
        email='admin@vendas.com',
        senha_hash=generate_password_hash('admin123'),
        tipo='admin'
    )
    db.session.add(admin)

    # Clientes de exemplo
    clientes_exemplo = [
        Cliente(nome='João Silva', email='joao@email.com', telefone='(11) 98765-4321', 
                cidade='São Paulo', estado='SP', latitude=-23.5505, longitude=-46.6333),
        Cliente(nome='Maria Santos', email='maria@email.com', telefone='(11) 98765-4322',
                cidade='São Paulo', estado='SP', latitude=-23.5505, longitude=-46.6333),
        Cliente(nome='Pedro Oliveira', email='pedro@email.com', telefone='(21) 98765-4323',
                cidade='Rio de Janeiro', estado='RJ', latitude=-22.9068, longitude=-43.1729),
        Cliente(nome='Ana Costa', email='ana@email.com', telefone='(31) 98765-4324',
                cidade='Belo Horizonte', estado='MG', latitude=-19.9167, longitude=-43.9345),
        Cliente(nome='Carlos Ferreira', email='carlos@email.com', telefone='(41) 98765-4325',
                cidade='Curitiba', estado='PR', latitude=-25.4284, longitude=-49.2733),
        Cliente(nome='Fernanda Lima', email='fernanda@email.com', telefone='(51) 98765-4326',
                cidade='Porto Alegre', estado='RS', latitude=-30.0346, longitude=-51.2177),
        Cliente(nome='Ricardo Mendes', email='ricardo@email.com', telefone='(71) 98765-4327',
                cidade='Salvador', estado='BA', latitude=-12.9714, longitude=-38.5014),
        Cliente(nome='Patrícia Souza', email='patricia@email.com', telefone='(81) 98765-4328',
                cidade='Recife', estado='PE', latitude=-8.0476, longitude=-34.8770),
    ]
    db.session.add_all(clientes_exemplo)
    db.session.flush()

    # Produtos de exemplo
    produtos_exemplo = [
        Produto(nome='Notebook Dell', descricao='Notebook i5 8GB RAM 256GB SSD', 
                preco_custo=2500, preco_venda=3200, quantidade_estoque=15, categoria='Eletrônicos'),
        Produto(nome='Mouse Logitech', descricao='Mouse sem fio ergonômico',
                preco_custo=80, preco_venda=150, quantidade_estoque=50, categoria='Eletrônicos'),
        Produto(nome='Teclado Mecânico', descricao='Teclado RGB switches red',
                preco_custo=200, preco_venda=350, quantidade_estoque=20, categoria='Eletrônicos'),
        Produto(nome='Monitor 24"', descricao='Monitor Full HD 144Hz',
                preco_custo=800, preco_venda=1200, quantidade_estoque=10, categoria='Eletrônicos'),
        Produto(nome='Cadeira Gamer', descricao='Cadeira ergonômica reclinável',
                preco_custo=600, preco_venda=950, quantidade_estoque=8, categoria='Móveis'),
        Produto(nome='Mesa Escritório', descricao='Mesa 120cm com gavetas',
                preco_custo=400, preco_venda=650, quantidade_estoque=5, categoria='Móveis'),
        Produto(nome='Webcam HD', descricao='Webcam 1080p com microfone',
                preco_custo=120, preco_venda=220, quantidade_estoque=30, categoria='Eletrônicos'),
        Produto(nome='Headset Gamer', descricao='Headset 7.1 surround',
                preco_custo=180, preco_venda=320, quantidade_estoque=25, categoria='Eletrônicos'),
        Produto(nome='Impressora Laser', descricao='Impressora laser monocromática',
                preco_custo=900, preco_venda=1400, quantidade_estoque=7, categoria='Eletrônicos'),
        Produto(nome='Roteador WiFi 6', descricao='Roteador mesh dual band',
                preco_custo=300, preco_venda=500, quantidade_estoque=12, categoria='Eletrônicos'),
    ]
    db.session.add_all(produtos_exemplo)
    db.session.flush()

    # Vendas de exemplo (últimos 30 dias)
    from datetime import timedelta
    import random

    formas_pagamento = ['dinheiro', 'cartao_credito', 'cartao_debito', 'pix', 'boleto']

    for i in range(50):
        dias_atras = random.randint(0, 30)
        data_venda = datetime.utcnow() - timedelta(days=dias_atras, hours=random.randint(0, 23))

        cliente = random.choice(clientes_exemplo)
        num_itens = random.randint(1, 4)

        venda = Venda(
            cliente_id=cliente.id,
            data_venda=data_venda,
            forma_pagamento=random.choice(formas_pagamento),
            status='concluida'
        )
        db.session.add(venda)
        db.session.flush()

        total = Decimal('0')
        lucro = Decimal('0')

        produtos_usados = random.sample(produtos_exemplo, min(num_itens, len(produtos_exemplo)))

        for produto in produtos_usados:
            qtd = random.randint(1, 3)
            preco = produto.preco_venda
            custo = produto.preco_custo
            subtotal = preco * qtd
            lucro_item = (preco - custo) * qtd

            item = ItemVenda(
                venda_id=venda.id,
                produto_id=produto.id,
                quantidade=qtd,
                preco_unitario=preco,
                custo_unitario=custo,
                subtotal=subtotal,
                lucro_item=lucro_item
            )
            db.session.add(item)

            total += subtotal
            lucro += lucro_item

            # Atualiza estoque
            produto.quantidade_estoque -= qtd

        venda.total = total
        venda.lucro_total = lucro

    db.session.commit()
    print('✅ Dados de exemplo criados com sucesso!')

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_dados_exemplo()
    app.run(debug=True, host='0.0.0.0', port=5000)
