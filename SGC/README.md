# SGC - Sistema de Gestão de Catálogo

Aplicação web para cadastrar e gerenciar **clientes** e **produtos**, com
autenticação de usuários. Projeto desenvolvido em Python e Flask.

- **Aluno:** Richard Raupp Odi
- **Turma:** TIN19
- **Início do projeto:** 08/10/2026

## Funcionalidades

- **Usuários:** registro, login e logout, com senha guardada apenas como hash.
- **Proteção de acesso:** todas as páginas de clientes e produtos exigem login.
  Quem não está autenticado é levado ao login; um envio de formulário sem
  login recebe a página de "Acesso negado" (403).
- **Clientes:** listar, cadastrar, editar e excluir (nome, e-mail, telefone,
  CPF/CNPJ e data de cadastro), com checagem de e-mail e CPF/CNPJ duplicados.
- **Produtos:** listar, cadastrar, editar e excluir (nome, preço, estoque,
  categoria e descrição).
- **Busca por nome** nas listas de clientes e de produtos.
- **Confirmação antes de excluir**, mensagens de sucesso e de erro em todas as
  operações e páginas personalizadas para os erros 403 e 404.

## Tecnologias

- Python 3.11 ou superior (testado com Python 3.13)
- Flask e Flask-SQLAlchemy
- SQLite (banco de dados em arquivo, sem instalação extra)
- HTML, CSS, Jinja2 e Bootstrap 5 (carregado por CDN, então é preciso internet
  para o visual aparecer corretamente)
- Git e GitHub

## Estrutura do projeto

```
SGC/
├── app.py                 # modelos, rotas e configuração
├── requirements.txt       # dependências
├── .gitignore
├── README.md
├── templates/
│   ├── base.html          # layout, navbar e mensagens
│   ├── index.html
│   ├── login.html
│   ├── registro.html
│   ├── clientes.html
│   ├── cliente_form.html
│   ├── produtos.html
│   ├── produto_form.html
│   ├── 403.html
│   └── 404.html
├── static/
│   └── css/style.css
└── instance/
    └── sgc.db             # criado automaticamente (não vai para o Git)
```

## Instalação

### 1. Instalar o Python

1. Baixe o Python em <https://www.python.org/downloads/>.
2. **No Windows**, marque a opção **"Add python.exe to PATH"** durante a
   instalação.
3. Confira a instalação em um terminal:

```
python --version
```

No Linux e no macOS o comando pode ser `python3` em vez de `python`.

### 2. Obter o projeto

Baixe os arquivos ou clone o repositório e abra a pasta `SGC` no Visual Studio
Code. Os comandos abaixo devem ser executados no terminal **dentro da pasta
`SGC`** (no VS Code: menu Terminal > Novo Terminal).

### 3. Criar e ativar o ambiente virtual

O ambiente virtual isola as bibliotecas do projeto.

**Windows (PowerShell):**

```
python -m venv venv
venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, execute antes (vale só para esse terminal):

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Windows (Prompt de Comando):**

```
python -m venv venv
venv\Scripts\activate.bat
```

**Linux e macOS:**

```
python3 -m venv venv
source venv/bin/activate
```

Quando o ambiente está ativo, o terminal mostra `(venv)` no início da linha.

### 4. Instalar as dependências

```
pip install -r requirements.txt
```

## Configuração

A aplicação funciona sem configurar nada, mas há duas variáveis de ambiente:

| Variável | Para que serve | Padrão |
|---|---|---|
| `SECRET_KEY` | Chave que protege as sessões. **Defina um valor próprio e secreto se a aplicação for usada fora do seu computador.** | valor fixo, só para desenvolvimento |
| `FLASK_DEBUG` | Com valor `1`, liga o modo de depuração (reinício automático e erros detalhados). | desligado |

Para gerar uma chave aleatória:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

Exemplos de como definir as variáveis antes de executar:

```
# PowerShell
$env:SECRET_KEY = "cole-a-chave-aqui"
$env:FLASK_DEBUG = "1"

# Prompt de Comando
set SECRET_KEY=cole-a-chave-aqui
set FLASK_DEBUG=1

# Linux / macOS
export SECRET_KEY="cole-a-chave-aqui"
export FLASK_DEBUG=1
```

Nunca coloque chaves ou senhas reais no código nem nos commits.

## Executando

Com o ambiente virtual ativo:

```
python app.py
```

Abra <http://127.0.0.1:5000> no navegador. Para parar o servidor, use
`Ctrl + C` no terminal.

## Banco de dados

- O banco é um arquivo SQLite: `instance/sgc.db`.
- Ele é **criado automaticamente** na primeira execução. Ao iniciar, a
  aplicação roda `db.create_all()`, que cria as tabelas `usuarios`, `clientes`
  e `produtos` quando elas ainda não existem e **não apaga dados existentes**.
- Para começar do zero, pare o servidor e apague o arquivo `instance/sgc.db`.
  Ele será recriado vazio na próxima execução (todos os dados e usuários serão
  perdidos).
- O arquivo do banco fica fora do Git, pelo `.gitignore`.

## Como usar

1. Abra a aplicação. Como você ainda não está logado, será levado à tela de
   login.
2. Clique em **Registrar** e crie sua conta: usuário (3 a 30 caracteres, com
   letras, números e `_`), e-mail e senha (mínimo de 6 caracteres).
3. Entre com o usuário e a senha. Seu nome aparece na barra de navegação.
4. Use **Clientes** e **Produtos** no menu para cadastrar, editar e excluir.
   A caixa de busca filtra a lista pelo nome.
5. Clique em **Sair** para encerrar a sessão.

### Regras de validação

| Campo | Regra |
|---|---|
| Cliente: nome | obrigatório, até 100 caracteres |
| Cliente: e-mail | obrigatório, formato válido, único |
| Cliente: telefone | opcional; se informado, DDD + 8 ou 9 dígitos |
| Cliente: CPF/CNPJ | obrigatório, 11 ou 14 números (com ou sem pontuação), único |
| Produto: nome | obrigatório, até 100 caracteres |
| Produto: preço | número maior ou igual a zero, até 2 casas decimais (ex.: `19,90`) |
| Produto: estoque | número inteiro maior ou igual a zero |
| Produto: categoria / descrição | opcionais, até 50 / 1000 caracteres |

Dados inválidos não são gravados no banco.

## Rotas

| Método | Rota | O que faz | Exige login |
|---|---|---|---|
| GET | `/` | Página inicial | sim |
| GET, POST | `/registro` | Cria um usuário | não |
| GET, POST | `/login` | Faz login | não |
| POST | `/logout` | Encerra a sessão | não |
| GET | `/clientes` | Lista clientes (`?busca=texto` filtra por nome) | sim |
| GET, POST | `/cliente/novo` | Formulário e cadastro de cliente | sim |
| GET, POST | `/cliente/editar/<id>` | Formulário e atualização de cliente | sim |
| POST | `/cliente/excluir/<id>` | Exclui um cliente | sim |
| GET | `/produtos` | Lista produtos (`?busca=texto` filtra por nome) | sim |
| GET, POST | `/produto/novo` | Formulário e cadastro de produto | sim |
| GET, POST | `/produto/editar/<id>` | Formulário e atualização de produto | sim |
| POST | `/produto/excluir/<id>` | Exclui um produto | sim |

Sem login, um acesso por `GET` redireciona para `/login` e um envio por `POST`
retorna a página 403. Registros inexistentes mostram o aviso "não encontrado" e
voltam para a lista; endereços inexistentes mostram a página 404.

## Segurança

- Senhas são guardadas apenas como hash (`generate_password_hash`, do
  Werkzeug) e conferidas com `check_password_hash`. A senha nunca vai para a
  sessão.
- As consultas ao banco usam o SQLAlchemy, que envia os valores como parâmetros
  (sem montar SQL com texto digitado). Na busca, `%` e `_` são tratados como
  texto comum.
- O Jinja escapa o HTML do que é exibido nas páginas.
- A verificação de login é feita **nas rotas**, não apenas escondendo links.
- O login mostra a mesma mensagem para usuário inexistente e senha errada.
- Exclusões e logout só funcionam por `POST`.
- O cookie de sessão usa `HttpOnly` e `SameSite=Lax`.
- Erros do banco desfazem a operação (`rollback`) e mostram uma mensagem sem
  detalhes internos.

### Limitações conhecidas

- Os formulários **não têm token CSRF** (o projeto não usa Flask-WTF). O
  `SameSite=Lax` reduz o risco, mas não o substitui.
- Não há recuperação de senha, confirmação de e-mail nem limite de tentativas
  de login.
- O CPF/CNPJ é validado só pela quantidade de números, sem calcular os dígitos
  verificadores.
- No SQLite, a busca ignora maiúsculas e minúsculas apenas para letras sem
  acento (`mar` encontra `Maria`, mas `JOÃO` não encontra `João`).
- O servidor do `python app.py` é de desenvolvimento e não deve ser usado em
  produção.

## Solução de problemas

| Problema | O que fazer |
|---|---|
| `python` não é reconhecido | Reinstale o Python marcando "Add to PATH" ou use `python3` |
| `No module named flask` | Ative o ambiente virtual e rode `pip install -r requirements.txt` |
| A página abre sem estilo | O Bootstrap vem de CDN: confira a conexão com a internet |
| `Address already in use` | Outro programa usa a porta 5000: feche-o ou pare o servidor anterior |
| Quero apagar todos os dados | Pare o servidor e apague `instance/sgc.db` |

## Histórico por fases

| Fase | Conteúdo | Mensagem do commit |
|---|---|---|
| 1 | Setup e ambiente | `Setup inicial do projeto SGC` |
| 2 | Usuários e autenticação | `Implementa sistema de autenticação e sessões` |
| 3 | CRUD de clientes | `Implementa CRUD completo de clientes` |
| 4 | CRUD de produtos | `Implementa CRUD completo de produtos` |
| 5 | Usabilidade, segurança e filtros | `Aprimora segurança, feedbacks e filtros de busca` |
| 6 | Documentação e entrega | `Entrega da versão final do SGC` |
