# Backend – Guia de Testes

Para garantir que os fluxos críticos do SaaS continuem funcionando (login, redefinição de senha e rastreamento público), adicionamos uma suíte mínima de testes com `pytest`.

## Requisitos

1. Ative o ambiente virtual (`.venv`) se ainda não estiver ativo.
2. Instale as dependências (incluindo `pytest`):
   ```bash
   pip install -r requirements.txt
   ```

## Executando os testes

Na pasta `backend/`, rode:

```bash
pytest
```

Isso prepara um banco SQLite em memória, executa os testes em `backend/tests/` e limpa o ambiente automaticamente.

Os testes atuais cobrem:

- `/health` – disponibilidade básica da API.
- Fluxo completo de autenticação: registro, login, recuperação e redefinição de senha.
- Regras das métricas públicas (stats) garantindo que apenas páginas publicadas registrem visitas/cliques.

Adicione novos testes seguindo o mesmo padrão (FastAPI `TestClient` + fixtures em `tests/conftest.py`).

## Criando o Admin Master

Para garantir que apenas você tenha acesso ao painel master, execute o script abaixo (com o ambiente configurado):

```bash
python scripts/create_master_admin.py --email seu-email@empresa.com --password SenhaForte123 --name "Seu Nome" --whatsapp 55999999999
```

O script cria/atualiza o usuário informado, define `is_superuser=True` e mantém o plano Infinity. Use essas credenciais para acessar `/admin/administracao`.

## Etiquetas automáticas do período trial

O backend agenda, no startup do FastAPI, uma rotina diária que roda no horário configurado (padrão `08:00` em `America/Sao_Paulo`) para verificar usuários em período de teste. Quando encontra usuários faltando 5, 3 ou 1 dia, ou completando 1 dia de atraso após o vencimento, o serviço adiciona etiquetas específicas no ViajeChat. Para habilitar essa automação defina no `.env`:

- `VIAJECHAT_API_KEY` (pode e deve ser a mesma chave usada no `notifyViajeChat` do front) e, opcionalmente, `VIAJECHAT_API_BASE_URL` caso a URL mude.
- Os IDs das etiquetas para cada estágio (`VIAJECHAT_TAG_TRIAL_5DAYS`, `VIAJECHAT_TAG_TRIAL_3DAYS`, `VIAJECHAT_TAG_TRIAL_1DAY`, `VIAJECHAT_TAG_TRIAL_OVERDUE_1DAY`).
- Ajuste de horário/minuto/timezone via `TRIAL_TAG_JOB_HOUR`, `TRIAL_TAG_JOB_MINUTE` e `TRIAL_TAG_JOB_TIMEZONE` (por exemplo, 15:30 em `America/Sao_Paulo`).

Se nenhuma etiqueta ou chave estiver configurada, o job é ignorado automaticamente.
