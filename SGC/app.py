import os
import re
from datetime import datetime
from decimal import Decimal
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Chave secreta: lida de variável de ambiente.
# O valor padrão serve apenas para desenvolvimento local.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "chave-apenas-para-desenvolvimento")

# Banco SQLite salvo na pasta "instance" (sgc.db)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sgc.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# O cookie de sessão não é enviado em requisições vindas de outros sites
# (protege os formulários POST contra ataques CSRF simples).
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
class Usuario(db.Model):
    """Usuário do sistema. A senha nunca é guardada: apenas o hash."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        """Texto que identifica o usuário ao depurar."""
        return f"<Usuario {self.username}>"


class Cliente(db.Model):
    """Cliente cadastrado. Telefone e CPF/CNPJ são guardados só com números."""

    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefone = db.Column(db.String(11))
    cpf_cnpj = db.Column(db.String(14), unique=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        """Texto que identifica o cliente ao depurar."""
        return f"<Cliente {self.nome}>"


class Produto(db.Model):
    """Produto do catálogo. O preço é guardado em reais, com 2 casas decimais."""

    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=0)
    categoria = db.Column(db.String(50))
    descricao = db.Column(db.Text)

    def __repr__(self):
        """Texto que identifica o produto ao depurar."""
        return f"<Produto {self.nome}>"


# Cria as tabelas que ainda não existem (não apaga dados já existentes).
with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------
def login_obrigatorio(view):
    """Decorador que só deixa o usuário autenticado acessar a rota.

    Verifica a sessão e também se o usuário ainda existe no banco.
    Quem tenta abrir uma página (GET) é enviado ao login; quem tenta enviar
    um formulário (POST) sem estar autenticado recebe o erro 403.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        """Executa a rota somente se houver um usuário autenticado."""
        usuario_id = session.get("usuario_id")
        if usuario_id is None or db.session.get(Usuario, usuario_id) is None:
            session.clear()
            if request.method not in ("GET", "HEAD"):
                abort(403)
            flash("Faça login para acessar esta página.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapper


def validar_registro(username, email, senha, confirmacao):
    """Valida os dados do registro e devolve uma lista de mensagens de erro."""
    erros = []

    if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username):
        erros.append("O nome de usuário deve ter de 3 a 30 caracteres, "
                     "usando apenas letras, números e sublinhado (_).")

    if len(email) > 120 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("Informe um e-mail válido.")

    if len(senha) < 6:
        erros.append("A senha deve ter pelo menos 6 caracteres.")
    elif len(senha) > 128:
        erros.append("A senha deve ter no máximo 128 caracteres.")
    elif senha != confirmacao:
        erros.append("A confirmação de senha não confere.")

    # Só consulta o banco se o formato básico estiver correto
    if not erros:
        if Usuario.query.filter(func.lower(Usuario.username) == username.lower()).first():
            erros.append("Este nome de usuário já está em uso.")
        if Usuario.query.filter(func.lower(Usuario.email) == email).first():
            erros.append("Este e-mail já está cadastrado.")

    return erros


@app.route("/registro", methods=["GET", "POST"])
def registro():
    """Cadastra um novo usuário (GET mostra o formulário, POST grava)."""
    if "usuario_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmacao = request.form.get("confirmacao", "")

        erros = validar_registro(username, email, senha, confirmacao)
        if erros:
            for erro in erros:
                flash(erro, "danger")
            return render_template("registro.html", username=username, email=email)

        novo = Usuario(
            username=username,
            email=email,
            senha_hash=generate_password_hash(senha),
        )
        try:
            db.session.add(novo)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Não foi possível concluir o cadastro. Tente novamente.", "danger")
            return render_template("registro.html", username=username, email=email)

        flash("Cadastro realizado com sucesso! Faça login para continuar.", "success")
        return redirect(url_for("login"))

    return render_template("registro.html", username="", email="")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Autentica o usuário comparando a senha com o hash armazenado."""
    if "usuario_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        senha = request.form.get("senha", "")

        usuario = Usuario.query.filter(
            func.lower(Usuario.username) == username.lower()
        ).first()

        if usuario and check_password_hash(usuario.senha_hash, senha):
            session.clear()  # descarta qualquer sessão anterior
            session["usuario_id"] = usuario.id
            session["username"] = usuario.username
            flash(f"Bem-vindo, {usuario.username}!", "success")
            return redirect(url_for("index"))

        # Mensagem genérica: não revela se o usuário existe ou não
        flash("Usuário ou senha inválidos.", "danger")
        return render_template("login.html", username=username)

    return render_template("login.html", username="")


@app.route("/logout", methods=["POST"])
def logout():
    """Encerra a sessão do usuário."""
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------
@app.route("/")
@login_obrigatorio
def index():
    """Página inicial (exige login)."""
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Busca (usada nas listas de clientes e de produtos)
# ---------------------------------------------------------------------------
def ler_busca():
    """Lê o termo digitado na busca (?busca=...), limitado a 100 caracteres."""
    return request.args.get("busca", "").strip()[:100]


def filtro_nome(coluna, busca):
    """Cria a condição "o nome contém o texto buscado", sem diferenciar
    maiúsculas de minúsculas. Os símbolos % e _ são tratados como texto comum.
    """
    texto = busca.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return coluna.ilike(f"%{texto}%", escape="\\")


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------
def somente_digitos(texto):
    """Remove tudo que não for número (usado em telefone e CPF/CNPJ)."""
    return re.sub(r"\D", "", texto)


@app.template_filter("documento")
def formatar_documento(valor):
    """Mostra um CPF (000.000.000-00) ou CNPJ (00.000.000/0000-00)."""
    if valor and len(valor) == 11:
        return f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"
    if valor and len(valor) == 14:
        return f"{valor[:2]}.{valor[2:5]}.{valor[5:8]}/{valor[8:12]}-{valor[12:]}"
    return valor or ""


@app.template_filter("telefone")
def formatar_telefone(valor):
    """Mostra o telefone como (00) 00000-0000 ou (00) 0000-0000."""
    if valor and len(valor) == 11:
        return f"({valor[:2]}) {valor[2:7]}-{valor[7:]}"
    if valor and len(valor) == 10:
        return f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
    return valor or ""


def ler_formulario_cliente():
    """Lê os campos do formulário de cliente, já sem espaços nas pontas."""
    return {
        "nome": request.form.get("nome", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "telefone": request.form.get("telefone", "").strip(),
        "cpf_cnpj": request.form.get("cpf_cnpj", "").strip(),
    }


def validar_cliente(form, cliente_id=None):
    """Valida os dados de um cliente.

    Devolve (erros, dados): a lista de mensagens de erro e um dicionário com
    os valores prontos para gravar (telefone e CPF/CNPJ só com números).
    Na edição, informe cliente_id para que o próprio cliente não seja
    considerado duplicado.
    """
    erros = []
    nome = form["nome"]
    email = form["email"]
    telefone = form["telefone"]
    documento = form["cpf_cnpj"]
    telefone_numeros = somente_digitos(telefone)
    documento_numeros = somente_digitos(documento)

    if not nome:
        erros.append("O nome é obrigatório.")
    elif len(nome) > 100:
        erros.append("O nome deve ter no máximo 100 caracteres.")

    email_ok = False
    if not email:
        erros.append("O e-mail é obrigatório.")
    elif len(email) > 120 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("Informe um e-mail válido.")
    else:
        email_ok = True

    # Telefone é opcional, mas, se vier preenchido, precisa ser válido
    if telefone and (not re.fullmatch(r"[\d\s()+-]+", telefone)
                     or len(telefone_numeros) not in (10, 11)):
        erros.append("Informe o telefone com DDD. Exemplo: (11) 98765-4321.")

    documento_ok = False
    if not documento:
        erros.append("O CPF/CNPJ é obrigatório.")
    elif (not re.fullmatch(r"[\d.\-/\s]+", documento)
          or len(documento_numeros) not in (11, 14)):
        erros.append("Informe um CPF (11 números) ou um CNPJ (14 números).")
    else:
        documento_ok = True

    # Duplicidade: ignora o próprio cliente quando estiver editando
    if email_ok:
        consulta = Cliente.query.filter(func.lower(Cliente.email) == email)
        if cliente_id is not None:
            consulta = consulta.filter(Cliente.id != cliente_id)
        if consulta.first():
            erros.append("Já existe um cliente com este e-mail.")

    if documento_ok:
        consulta = Cliente.query.filter(Cliente.cpf_cnpj == documento_numeros)
        if cliente_id is not None:
            consulta = consulta.filter(Cliente.id != cliente_id)
        if consulta.first():
            erros.append("Já existe um cliente com este CPF/CNPJ.")

    dados = {
        "nome": nome,
        "email": email,
        "telefone": telefone_numeros or None,
        "cpf_cnpj": documento_numeros,
    }
    return erros, dados


@app.route("/clientes")
@login_obrigatorio
def clientes():
    """Lista os clientes em uma tabela, com busca opcional por nome (?busca=)."""
    busca = ler_busca()
    consulta = Cliente.query
    if busca:
        consulta = consulta.filter(filtro_nome(Cliente.nome, busca))
    lista = consulta.order_by(func.lower(Cliente.nome), Cliente.id).all()
    return render_template("clientes.html", clientes=lista, busca=busca)


@app.route("/cliente/novo", methods=["GET", "POST"])
@login_obrigatorio
def cliente_novo():
    """Mostra o formulário (GET) e cadastra o cliente (POST)."""
    form = {"nome": "", "email": "", "telefone": "", "cpf_cnpj": ""}

    if request.method == "POST":
        form = ler_formulario_cliente()
        erros, dados = validar_cliente(form)
        if erros:
            for erro in erros:
                flash(erro, "danger")
            return render_template("cliente_form.html", form=form, cliente_id=None)

        try:
            db.session.add(Cliente(**dados))
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Não foi possível salvar o cliente. Confira se o e-mail e o "
                  "CPF/CNPJ já não estão cadastrados.", "danger")
            return render_template("cliente_form.html", form=form, cliente_id=None)

        flash(f"Cliente {dados['nome']} cadastrado com sucesso!", "success")
        return redirect(url_for("clientes"))

    return render_template("cliente_form.html", form=form, cliente_id=None)


@app.route("/cliente/editar/<int:cliente_id>", methods=["GET", "POST"])
@login_obrigatorio
def cliente_editar(cliente_id):
    """Mostra o formulário preenchido (GET) e atualiza o cliente (POST)."""
    cliente = db.session.get(Cliente, cliente_id)
    if cliente is None:
        flash("Cliente não encontrado.", "warning")
        return redirect(url_for("clientes"))

    if request.method == "POST":
        form = ler_formulario_cliente()
        erros, dados = validar_cliente(form, cliente_id=cliente.id)
        if erros:
            for erro in erros:
                flash(erro, "danger")
            return render_template("cliente_form.html", form=form, cliente_id=cliente.id)

        try:
            cliente.nome = dados["nome"]
            cliente.email = dados["email"]
            cliente.telefone = dados["telefone"]
            cliente.cpf_cnpj = dados["cpf_cnpj"]
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Não foi possível atualizar o cliente. Confira se o e-mail e o "
                  "CPF/CNPJ já não estão cadastrados.", "danger")
            return render_template("cliente_form.html", form=form, cliente_id=cliente_id)

        flash(f"Cliente {dados['nome']} atualizado com sucesso!", "success")
        return redirect(url_for("clientes"))

    form = {
        "nome": cliente.nome,
        "email": cliente.email,
        "telefone": formatar_telefone(cliente.telefone),
        "cpf_cnpj": formatar_documento(cliente.cpf_cnpj),
    }
    return render_template("cliente_form.html", form=form, cliente_id=cliente.id)


@app.route("/cliente/excluir/<int:cliente_id>", methods=["POST"])
@login_obrigatorio
def cliente_excluir(cliente_id):
    """Exclui o cliente (somente por POST, após confirmação na tela)."""
    cliente = db.session.get(Cliente, cliente_id)
    if cliente is None:
        flash("Cliente não encontrado.", "warning")
        return redirect(url_for("clientes"))

    nome = cliente.nome
    try:
        db.session.delete(cliente)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Não foi possível excluir o cliente. Tente novamente.", "danger")
        return redirect(url_for("clientes"))

    flash(f"Cliente {nome} excluído com sucesso.", "success")
    return redirect(url_for("clientes"))


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------
PRECO_MAXIMO = Decimal("99999999.99")
ESTOQUE_MAXIMO = 999999999


@app.template_filter("moeda")
def formatar_moeda(valor):
    """Mostra um número como valor em reais. Exemplo: R$ 1.234,50."""
    if valor is None:
        return ""
    texto = f"{valor:,.2f}"  # exemplo: 1,234.50
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def ler_formulario_produto():
    """Lê os campos do formulário de produto, já sem espaços nas pontas."""
    return {
        "nome": request.form.get("nome", "").strip(),
        "preco": request.form.get("preco", "").strip(),
        "estoque": request.form.get("estoque", "").strip(),
        "categoria": request.form.get("categoria", "").strip(),
        "descricao": request.form.get("descricao", "").strip(),
    }


def validar_produto(form):
    """Valida os dados de um produto.

    Devolve (erros, dados): a lista de mensagens de erro e um dicionário com
    os valores já convertidos (preço em float, estoque em int) para gravar.
    """
    erros = []
    nome = form["nome"]
    categoria = form["categoria"]
    descricao = form["descricao"]

    if not nome:
        erros.append("O nome do produto é obrigatório.")
    elif len(nome) > 100:
        erros.append("O nome do produto deve ter no máximo 100 caracteres.")

    # Preço: número >= 0, com vírgula ou ponto e até 2 casas decimais
    preco = None
    if not form["preco"]:
        erros.append("O preço é obrigatório.")
    elif not re.fullmatch(r"\d+([.,]\d{1,2})?", form["preco"], re.ASCII):
        erros.append("O preço deve ser um número maior ou igual a zero, com até "
                     "2 casas decimais. Exemplo: 19,90.")
    else:
        valor = Decimal(form["preco"].replace(",", "."))
        if valor > PRECO_MAXIMO:
            erros.append("O preço máximo permitido é R$ 99.999.999,99.")
        else:
            preco = float(valor)

    # Estoque: número inteiro >= 0
    estoque = None
    if not form["estoque"]:
        erros.append("O estoque é obrigatório.")
    elif not re.fullmatch(r"\d+", form["estoque"], re.ASCII):
        erros.append("O estoque deve ser um número inteiro maior ou igual a zero.")
    else:
        digitos = form["estoque"].lstrip("0") or "0"
        if len(digitos) > len(str(ESTOQUE_MAXIMO)) or int(digitos) > ESTOQUE_MAXIMO:
            erros.append("O estoque máximo permitido é 999.999.999 unidades.")
        else:
            estoque = int(digitos)

    if len(categoria) > 50:
        erros.append("A categoria deve ter no máximo 50 caracteres.")
    if len(descricao) > 1000:
        erros.append("A descrição deve ter no máximo 1000 caracteres.")

    dados = {
        "nome": nome,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria or None,
        "descricao": descricao or None,
    }
    return erros, dados


@app.route("/produtos")
@login_obrigatorio
def produtos():
    """Lista os produtos em uma tabela, com busca opcional por nome (?busca=)."""
    busca = ler_busca()
    consulta = Produto.query
    if busca:
        consulta = consulta.filter(filtro_nome(Produto.nome, busca))
    lista = consulta.order_by(func.lower(Produto.nome), Produto.id).all()
    return render_template("produtos.html", produtos=lista, busca=busca)


@app.route("/produto/novo", methods=["GET", "POST"])
@login_obrigatorio
def produto_novo():
    """Mostra o formulário (GET) e cadastra o produto (POST)."""
    form = {"nome": "", "preco": "", "estoque": "0", "categoria": "", "descricao": ""}

    if request.method == "POST":
        form = ler_formulario_produto()
        erros, dados = validar_produto(form)
        if erros:
            for erro in erros:
                flash(erro, "danger")
            return render_template("produto_form.html", form=form, produto_id=None)

        try:
            db.session.add(Produto(**dados))
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Não foi possível salvar o produto. Tente novamente.", "danger")
            return render_template("produto_form.html", form=form, produto_id=None)

        flash(f"Produto {dados['nome']} cadastrado com sucesso!", "success")
        return redirect(url_for("produtos"))

    return render_template("produto_form.html", form=form, produto_id=None)


@app.route("/produto/editar/<int:produto_id>", methods=["GET", "POST"])
@login_obrigatorio
def produto_editar(produto_id):
    """Mostra o formulário preenchido (GET) e atualiza o produto (POST)."""
    produto = db.session.get(Produto, produto_id)
    if produto is None:
        flash("Produto não encontrado.", "warning")
        return redirect(url_for("produtos"))

    if request.method == "POST":
        form = ler_formulario_produto()
        erros, dados = validar_produto(form)
        if erros:
            for erro in erros:
                flash(erro, "danger")
            return render_template("produto_form.html", form=form, produto_id=produto_id)

        try:
            produto.nome = dados["nome"]
            produto.preco = dados["preco"]
            produto.estoque = dados["estoque"]
            produto.categoria = dados["categoria"]
            produto.descricao = dados["descricao"]
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Não foi possível atualizar o produto. Tente novamente.", "danger")
            return render_template("produto_form.html", form=form, produto_id=produto_id)

        flash(f"Produto {dados['nome']} atualizado com sucesso!", "success")
        return redirect(url_for("produtos"))

    form = {
        "nome": produto.nome,
        "preco": f"{produto.preco:.2f}".replace(".", ","),
        "estoque": str(produto.estoque),
        "categoria": produto.categoria or "",
        "descricao": produto.descricao or "",
    }
    return render_template("produto_form.html", form=form, produto_id=produto_id)


@app.route("/produto/excluir/<int:produto_id>", methods=["POST"])
@login_obrigatorio
def produto_excluir(produto_id):
    """Exclui o produto (somente por POST, após confirmação na tela)."""
    produto = db.session.get(Produto, produto_id)
    if produto is None:
        flash("Produto não encontrado.", "warning")
        return redirect(url_for("produtos"))

    nome = produto.nome
    try:
        db.session.delete(produto)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Não foi possível excluir o produto. Tente novamente.", "danger")
        return redirect(url_for("produtos"))

    flash(f"Produto {nome} excluído com sucesso.", "success")
    return redirect(url_for("produtos"))


# ---------------------------------------------------------------------------
# Páginas de erro
# ---------------------------------------------------------------------------
@app.errorhandler(403)
def acesso_negado(erro):
    """Mostra a página personalizada de acesso negado (erro 403)."""
    return render_template("403.html"), 403


@app.errorhandler(404)
def nao_encontrado(erro):
    """Mostra a página personalizada de página não encontrada (erro 404)."""
    return render_template("404.html"), 404


if __name__ == "__main__":
    # O modo de depuração fica desligado por padrão, pois expõe detalhes
    # internos. Para ligá-lo no seu computador: defina FLASK_DEBUG=1.
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
