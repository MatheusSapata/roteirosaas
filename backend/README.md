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
