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

## Integração com Cakto (checkout e criação automática de usuários)

1. **Preencha as variáveis de ambiente** no `.env`:
   - `CAKTO_WEBHOOK_SECRET`: token simples para proteger o endpoint (adicione `?token=...` na URL do webhook).
   - `CAKTO_PASSWORD_TOKEN_MINUTES`: tempo de expiração dos links da tela `create-password`.
   - `CAKTO_OFFER_*` ou `CAKTO_PRODUCT_*`: informe os IDs das ofertas/produtos da Cakto para cada plano (`essencial`, `growth`, `infinity`) e ciclo (`monthly`, `annual`). Basta preencher um dos dois IDs por combinação; o serviço tenta casar primeiro pelo `offer_id` e depois pelo `product_id`.
2. **Configure o webhook no painel Cakto** apontando para `https://SEU_DOMÍNIO/api/cakto/webhook?token=...` e marque os eventos `purchase_approved`, `subscription_created`, `subscription_renewed`, `subscription_canceled` e `subscription_renewal_refused`.
3. **Página de obrigado/upsell**: direcione para `https://SEU_DOMÍNIO/create-password?order={order_id}` (ou use o `refId`). A tela chama `GET /api/cakto/onboarding/session` passando `order_id` ou `ref_id` e só exibe o formulário quando o webhook já criou usuário/assinatura.
4. **Criação da senha**: o formulário envia `POST /api/cakto/onboarding/session/password` com o mesmo identificador e a nova senha. O backend valida força, salva e libera o login imediatamente.

Sempre que um pagamento aprovado chega pelo webhook, o backend:
- Localiza o plano a partir do `offer_id`/`product_id`.
- Cria/atualiza o usuário, assinatura (`provider=cakto`) e encerra qualquer trial.
- Gera um token de onboarding (vinculado ao `order_id`/`refId`) que o front usa para liberar a tela `create-password`.

Eventos de cancelamento ou renovação atualizam o status da assinatura automaticamente. Se faltar algum campo no payload, verifique os IDs configurados nas variáveis `CAKTO_*`.
