# 📚 Bookstore API

Backend completo para livraria e-commerce construído com **FastAPI**, **SQLAlchemy (async)** e **PostgreSQL**.

---

## Stack

| Tecnologia | Versão |
|---|---|
| Python | 3.11 |
| FastAPI | 0.115.12 |
| SQLAlchemy (async) | 2.0.40 |
| asyncpg | 0.30.0 |
| Alembic | 1.15.2 |
| Pydantic v2 | 2.11.3 |
| python-jose | 3.3.0 |
| passlib[bcrypt] | 1.7.4 |

---

## Estrutura do projeto

```
bookstore/
├── app/
│   ├── main.py            # Entrypoint FastAPI
│   ├── config.py          # Settings via pydantic-settings
│   ├── database.py        # Engine e sessão async
│   ├── deps.py            # Dependências (get_db, get_current_user, require_admin)
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic v2 schemas
│   ├── routers/           # FastAPI routers (endpoints)
│   └── services/          # Lógica de negócio
├── alembic/               # Migrações de banco
├── tests/                 # Suite de testes pytest-asyncio
├── alembic.ini
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Pré-requisitos

- Python 3.11+
- PostgreSQL 14+

---

## Setup

### 1. Clone e crie o ambiente virtual

```bash
git clone <repo-url>
cd bookstore
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais reais
```

Variáveis obrigatórias em `.env`:

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL asyncpg do PostgreSQL |
| `SECRET_KEY` | Chave secreta JWT (mín. 32 chars) |
| `ALGORITHM` | Algoritmo JWT (padrão: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do token (padrão: `30`) |

### 3. Crie o banco de dados no PostgreSQL

```sql
CREATE USER bookstore_user WITH PASSWORD 'changeme';
CREATE DATABASE bookstore_db OWNER bookstore_user;
```

### 4. Execute as migrações

```bash
alembic upgrade head
```

### 5. Inicie o servidor

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

A API estará disponível em `http://127.0.0.1:8000`.

Documentação interativa:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## Endpoints principais

### Autenticação

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/register` | Registrar usuário |
| `POST` | `/auth/login` | Login (retorna JWT) |
| `GET` | `/auth/me` | Perfil do usuário autenticado |
| `PATCH` | `/auth/me` | Atualizar perfil |

### Livros

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/books/` | Listar livros (filtros: `category_id`, `author_id`) |
| `GET` | `/books/{id}` | Detalhe do livro |
| `POST` | `/books/` | Criar livro *(admin)* |
| `PUT` | `/books/{id}` | Atualizar livro *(admin)* |
| `DELETE` | `/books/{id}` | Remover livro *(admin)* |

### Categorias

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/categories/` | Listar categorias |
| `GET` | `/categories/{id}` | Detalhe |
| `POST` | `/categories/` | Criar *(admin)* |
| `PUT` | `/categories/{id}` | Atualizar *(admin)* |
| `DELETE` | `/categories/{id}` | Remover *(admin)* |

### Autores

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/authors/` | Listar autores |
| `GET` | `/authors/{id}` | Detalhe |
| `POST` | `/authors/` | Criar *(admin)* |
| `PUT` | `/authors/{id}` | Atualizar *(admin)* |
| `DELETE` | `/authors/{id}` | Remover *(admin)* |

### Carrinho *(autenticado)*

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/cart/` | Ver carrinho |
| `POST` | `/cart/items` | Adicionar item |
| `PUT` | `/cart/items/{id}` | Atualizar quantidade |
| `DELETE` | `/cart/items/{id}` | Remover item |
| `DELETE` | `/cart/` | Limpar carrinho |

### Pedidos *(autenticado)*

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/orders/` | Listar pedidos |
| `POST` | `/orders/` | Criar pedido (do carrinho) |
| `GET` | `/orders/{id}` | Detalhe do pedido |
| `POST` | `/orders/{id}/cancel` | Cancelar pedido |

### Avaliações

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/reviews/books/{book_id}` | Listar avaliações do livro |
| `POST` | `/reviews/` | Criar avaliação *(autenticado)* |
| `DELETE` | `/reviews/{id}` | Remover avaliação *(autor)* |

---

## Testes

Os testes usam SQLite em memória via `aiosqlite` (sem necessidade de PostgreSQL).

```bash
# Instale dependências extras de teste
pip install aiosqlite

# Execute os testes
pytest tests/ -v
```

---

## Criando um usuário admin

Após registrar um usuário comum, atualize manualmente o campo `role` no banco:

```sql
UPDATE users SET role = 'admin' WHERE email = 'seu@email.com';
```

---

## Gerando uma nova migração

```bash
alembic revision --autogenerate -m "descrição da mudança"
alembic upgrade head
```

---

## Segurança

- Senhas hasheadas com **bcrypt**
- JWT com expiração configurável
- Variáveis sensíveis carregadas de `.env` (nunca commitadas)
- Servidor binding em `127.0.0.1`
- SQL via ORM (sem raw queries concatenadas)
- Logs estruturados sem dados sensíveis
