# Checklist de Desenvolvimento – Projeto SGC (Expandido)

## Informações do Aluno
- **Nome:** Richard Raupp Odi
- **Turma:** TIN19
- **Data de início:** 08/10/2026

---

## Fase 1: Setup e Ambiente
- [ ] Criar estrutura do projeto (`app.py`, `templates/`)
- [ ] Inicializar Git e configurar `.gitignore`
- [ ] Configurar `requirements.txt` (Flask, Flask-SQLAlchemy, etc.)
- [ ] Criar template base com Bootstrap 5 e barra de navegação responsiva
- [ ] **COMMIT:** "Setup inicial do projeto SGC"

---

## Fase 2: Módulo de Usuários e Autenticação
- [ ] Modelar classe `Usuario` (`id`, `username`, `email`, `senha_hash`)
- [ ] Criar rota e formulário de Registro de Usuários com hashing de senha
- [ ] Criar rota e tela de Login validando hash
- [ ] Criar rota de Logout limpando a sessão
- [ ] Implementar controle de acesso (bloquear páginas do sistema para não autenticados)
- [ ] **COMMIT:** "Implementa sistema de autenticação e sessões"

---

## Fase 3: CRUD de Clientes
- [ ] Modelar classe `Cliente` (`id`, `nome`, `email`, `telefone`, `cpf_cnpj`, `data_cadastro`)
- [ ] Rota `GET /clientes` com listagem em tabela
- [ ] Rotas `GET` e `POST /cliente/novo` para cadastro
- [ ] Rotas `GET` e `POST /cliente/editar/<id>` para edição
- [ ] Rota `POST /cliente/excluir/<id>` com confirmação
- [ ] Validações de duplicidade de e-mail/documento
- [ ] **COMMIT:** "Implementa CRUD completo de clientes"

---

## Fase 4: CRUD de Produtos
- [ ] Modelar classe `Produto` (`id`, `nome`, `preco`, `estoque`, `categoria`, `descricao`)
- [ ] Implementar Listagem com tabela estilizada
- [ ] Implementar Criação, Edição e Exclusão
- [ ] Validação de dados numéricos (preço e estoque >= 0)
- [ ] **COMMIT:** "Implementa CRUD completo de produtos"

---

## Fase 5: Usabilidade, Segurança e Filtros
- [ ] Campo de busca ou filtro (por nome em Produtos e Clientes)
- [ ] Exibição dinâmica da barra de navegação (exibir nome do usuário logado)
- [ ] Tratamento de erros de banco com `db.session.rollback()`
- [ ] Páginas personalizadas de erro 404 e 403 (Acesso Negado)
- [ ] Mensagens de feedback (`flash`) em todas as operações
- [ ] **COMMIT:** "Aprimora segurança, feedbacks e filtros de busca"

---

## Fase 6: Documentação e Entrega
- [ ] Documentar endpoints e funções com docstrings
- [ ] Criar `README.md` completo com guia de instalação, informações do projeto e tecnologias utilizadas
- [ ] Limpar código, imports não utilizados e prints
- [ ] **COMMIT FINAL:** "Entrega da versão final do SGC"