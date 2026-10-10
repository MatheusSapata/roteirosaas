# Roteiro SaaS — instruções para o Claude

Vale para qualquer pessoa que use o Claude neste repositório (Matheus ou colegas).
Fale sempre em português do Brasil.

## Deploy em produção (VPS)

**Quando o usuário disser "pode fazer o deploy", "faz o deploy", "sobe para produção" ou algo equivalente, execute o workflow do n8n abaixo. Não faça deploy manual por SSH e não rode os scripts na mão.**

| | |
|---|---|
| Workflow | **Deploy VPS - Roteirosaas** |
| ID | `DsqpHGyfqB7fzJy4` |
| URL | https://n8n.viajeon.com/workflow/DsqpHGyfqB7fzJy4 |
| Credencial SSH (no n8n) | `VPS Deploy` (usuário `deploy`, na pasta `/opt/roteirosaas`) |

### Como executar

1. Confirme que o que deve ir para produção **já está na `main`** (PR com merge feito). O deploy faz `git pull` da `main`; se o código não estiver lá, o pull não traz nada.
2. Use o MCP do n8n: `execute_workflow` com `workflowId = DsqpHGyfqB7fzJy4` e `executionMode = manual`.
3. O deploy leva alguns minutos (build do frontend e recriação dos containers). Acompanhe com `get_workflow_execution` (use `includeData` com `nodeNames` para não estourar o limite de tokens) ou peça ao usuário para avisar quando terminar.
4. Informe o resultado em poucas palavras: passou ou onde parou, o commit que ficou na VPS e o estado dos containers.

### O que o workflow faz (em ordem, parando no primeiro erro)

1. `git pull --ff-only origin main` em `/opt/roteirosaas`
2. `bash scripts/deploy-admin.sh`
3. `bash scripts/deploy-public.sh`
4. Mostra o último commit e o `docker ps`

Se um passo falha, a execução termina como **erro** no n8n com o código e a mensagem. Leia a mensagem, conte ao usuário e corrija a causa antes de tentar de novo. Não repita às cegas.

### Regras de segurança (produção com clientes reais)

- **Nunca** use `git reset --hard`, `git clean`, `docker compose down -v`, `docker volume rm` nem `docker system prune --volumes`.
- Os dados (Postgres, Redis, Evolution, pgAdmin) ficam em **volumes nomeados do Docker**, fora do projeto. O deploy só recria os containers `api-admin` e `api-public`.
- A VPS tem **alterações locais que devem ser mantidas** (não estão no GitHub): `backend/docker-compose.admin.yml`, `backend/docker-compose.base.yml`, `backend/docker-compose.public.yml`, `backend/scripts/issue_custom_domain_cert.sh` e a migração `backend/alembic/versions/0010_merge_0004_0009.py`. O `git pull --ff-only` preserva essas alterações e só falha se o GitHub mudar os mesmos arquivos; nesse caso pare e avise o usuário.
- **Não rode deploy manual como root.** Arquivos criados pelo root dentro de `/opt/roteirosaas` fazem o `npm ci` falhar com `EACCES`. Se acontecer, o usuário corrige no Web console da Hostinger com `chown -R deploy:deploy /opt/roteirosaas`.
- Neste projeto, "fazer o deploy" significa este workflow na VPS. Não use o `deploy_project` da Lovable, a não ser que o usuário peça isso explicitamente.

## Backup do banco

É um workflow **separado**, que **não** faz parte do deploy:

| | |
|---|---|
| Workflow | **Backup diario do banco (3h)** |
| ID | `hT5AuhEQqf7PGLm9` |
| Quando roda | Todo dia às 3h (America/Sao_Paulo) |
| Onde salva | `/opt/roteirosaas/backups/diario-*.sql.gz` na VPS |
| Retenção | Só os 2 mais recentes |

- O backup **não inclui os dados** de `whatsapp_messages` (só a estrutura), porque o `pg_dump` dessa tabela falhou com `missing chunk number 0 for toast value`. As mensagens do WhatsApp, portanto, **não têm backup**.
- Para pedir um backup agora, execute esse workflow do mesmo jeito (`execute_workflow`, modo `manual`).
