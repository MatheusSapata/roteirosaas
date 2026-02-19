# RoteiroSaaS – Plataforma full-stack para agências de viagens

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=white" alt="FastAPI Badge" />
  <img src="https://img.shields.io/badge/Vue.js-42b883?logo=vue.js&logoColor=white" alt="Vue 3 Badge" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-0ea5e9?logo=tailwindcss&logoColor=white" alt="Tailwind Badge" />
  <img src="https://img.shields.io/badge/Stripe-6772E5?logo=stripe&logoColor=white" alt="Stripe Badge" />
  <img src="https://img.shields.io/badge/Mercado%20Pago-009ee3?logo=mercadopago&logoColor=white" alt="Mercado Pago Badge" />
</p>

> SaaS para criação e gestão de páginas de viagem com editor visual, integrações de pagamento e monitoramento em tempo real.

- :rocket: **Backend FastAPI** com autenticação JWT, fila de expiração de planos e Alembic para versionamento do banco.
- :art: **Frontend Vue 3 + Vite** para o painel administrativo e páginas públicas responsivas com Tailwind.
- :money_with_wings: **Assinaturas e checkout** via Stripe e Mercado Pago.
- :bar_chart: **Métricas e rastreamento** de visitas/cliques armazenados em `stats`.
- :shield: **Testes automatizados** com `pytest` cobrindo os fluxos críticos (login, recuperação de senha, stats).

![Visão Geral](https://img.shields.io/badge/Arquitetura-RoteiroSaaS-blue?style=for-the-badge)

```mermaid
graph LR
    subgraph Frontend [Frontend (Vue 3 + Vite + Pinia)]
        A[Admin Pages] -->|REST| API
        B[Public Landing Pages] -->|GET pages| API
    end
    subgraph Backend [Backend (FastAPI + SQLAlchemy)]
        API --> DB[(PostgreSQL/SQLite)]
        API --> Uploads[(Uploads estáticos)]
        API --> Stripe
        API --> MP[Mercado Pago]
    end
    Scheduler((Cron Job)) --> API
```

## Sumário
1. [Visão Geral](#visão-geral)
2. [Stack & Estrutura](#stack--estrutura)
3. [Variáveis de Ambiente](#variáveis-de-ambiente)
4. [Como rodar](#como-rodar)
5. [Scripts úteis](#scripts-úteis)
6. [Testes & Qualidade](#testes--qualidade)
7. [Endereços e rotas chave](#endereços-e-rotas-chave)
8. [Fluxo de deploy](#fluxo-de-deploy)
9. [Roadmap](#roadmap)

## Visão Geral
O RoteiroSaaS foi pensado para agências que precisam criar landing pages personalizadas de viagens e acompanhar desempenho. O sistema divide-se em:

- **Painel administrativo** (Vue 3) para montar seções (Hero, CTA, FAQ, Depoimentos etc.) usando formulários dinâmicos e upload de mídia.
- **API** (FastAPI) que centraliza cadastros, autenticação, templates e métricas. Todas as rotas privadas usam JWT com refresh automático.
- **Mecanismo de billing** para trocas de plano, faturas e notificações webhook (Stripe + Mercado Pago).
- **Camada de monitoramento** que salva stats de cada página (visitas, cliques) para serem exibidas no dashboard.

## Stack & Estrutura

```
.
├── backend/        # API FastAPI, Alembic e scripts utilitários
│   ├── app/        # Core da aplicação (models, schemas, routers)
│   ├── scripts/    # Automação de admins e tasks
│   ├── tests/      # Pytest cobrindo health/auth/stats
│   └── docker-compose.yml / Dockerfile
├── frontend/       # SPA Vue 3 (Vite + Tailwind)
│   ├── src/        # Componentes, stores Pinia, rotas, serviços
│   ├── postcss.config.cjs / tailwind.config.cjs
│   └── package.json
└── README.md       # Este documento
```

### Principais tecnologias
- **Backend:** FastAPI, SQLAlchemy, Alembic, Pydantic v2, JWT (`python-jose`), Mercado Pago SDK, Stripe SDK.
- **Frontend:** Vue 3 (Composition API), Pinia, Vue Router, Axios, Tailwind CSS, Vite.
- **Infra/DevX:** Docker Compose, pytest, scripts Bash/Python para automação.

## Variáveis de Ambiente

### Backend (`backend/.env`)
| Chave | Descrição |
| --- | --- |
| `ENV` | `dev`, `prod` ou `test` (controla jobs e logging). |
| `DATABASE_URL` | URL do banco (PostgreSQL em produção, SQLite durante dev/testes). |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Configuração de tokens. |
| `APP_NAME` | Nome exibido nas respostas FastAPI. |
| `MP_*` | Tokens e URLs de retorno do Mercado Pago. |
| `STRIPE_*` | Chaves e IDs de preço da Stripe. |
| `PASSWORD_RESET_TOKEN_MINUTES` | Expiração de tokens de redefinição. |

> Consulte `backend/.env.example` para valores base.

### Frontend (`frontend/.env`)
Crie um arquivo com as URLs necessárias:
```
VITE_API_URL=http://localhost:8000
VITE_PUBLIC_DOMAIN=https://app.seudominio.com
```
(adicione outras chaves conforme integrações futuras)

## Como rodar

### Pré-requisitos
- **Python 3.11+**
- **Node.js 20+** (ou 18 LTS)
- **npm** ou `pnpm`

### Backend (modo manual)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- A API ficará em `http://localhost:8000` e expõe `/docs` e `/redoc`.
- O diretório `uploads/` é criado automaticamente e servido em `/uploads`.

### Frontend
```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
npm run build          # gera /dist
npm run preview        # testa o build
```

### Docker Compose (opcional)
```bash
cd backend
docker-compose up --build
```
Esse compose sobe a API FastAPI e um banco PostgreSQL configurado via Alembic.

## Scripts úteis
- `python scripts/create_master_admin.py --email ...` – Cria/atualiza o superusuário que acessa `/admin/administracao`.
- `python scripts/create_master_admin.py --help` – Lista parâmetros disponíveis.
- `backend/test_login.sh` – Fluxo básico de login via `httpie`/`curl`.
- `npm run lint` (frontend) – placeholder para ferramentas futuras.

## Testes & Qualidade
```bash
cd backend
pytest
```
Os testes usam SQLite em memória e cobrem:
- `/health`
- Fluxo completo de autenticação (registro → login → recuperação).
- Regras de stats (somente páginas publicadas contam visitas/cliques).

Adicione novos testes em `backend/tests/` seguindo o padrão das fixtures em `tests/conftest.py`.

## Endereços e rotas chave
- **Saúde:** `GET /health`
- **Autenticação:** `POST /api/v1/auth/login`, `POST /api/v1/auth/register`, `POST /api/v1/auth/forgot-password`
- **Páginas e seções:** `GET/POST /api/v1/pages`, `GET /api/v1/templates`
- **Uploads:** `POST /api/v1/media`, arquivos servidos em `/uploads/<filename>`
- **Métricas:** `POST /api/v1/stats/visit`, `POST /api/v1/stats/click`
- **Painel público:** `GET /public/<slug>` (renderizado pelo frontend)

## Fluxo de deploy
1. Trabalhe na branch `developer`.
2. Abra PR → revise → faça merge em `main`.
3. **Backend:** `git pull origin main`, configure envs e `uvicorn`/`gunicorn` (ou use Docker). Rode migrações Alembic se necessário.
4. **Frontend:** `npm ci && npm run build` e publique o conteúdo de `frontend/dist` (S3, Vercel, servidor Nginx etc.).
5. Configure webhooks Stripe/Mercado Pago apontando para `/api/v1/billing/webhook`.

## Roadmap
- [ ] Implantar suíte de testes end-to-end (Cypress/Playwright) para o editor.
- [ ] Adicionar cobertura de integrações (webhooks Stripe/MP) no CI.
- [ ] Melhorar acessibilidade das páginas públicas.
- [ ] Automatizar deploy (GitHub Actions → Docker Registry/Server).

---
Feito com foco em agências que precisam de agilidade para lançar campanhas. Em caso de dúvidas ou sugestões, abra uma issue em [MatheusSapata/roteirosaas](https://github.com/MatheusSapata/roteirosaas). 🚀
