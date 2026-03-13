# Dominios personalizados por agencia

## Visao geral

- Cada agencia pode cadastrar diversos hosts proprios (raiz ou subdominio) em **Admin → Dominios**.
- A URL padrao `roteiroonline.com/{agencia}/{roteiro}` continua funcionando como fallback.
- Quando um host customizado ficar **verificado e ativo**, as paginas publicas passam a responder em `https://host-customizado/{roteiro}`.
- O backend identifica automaticamente o modo correto: hosts internos usam o slug no caminho; hosts customizados ativos usam apenas o `route_slug`.

## Fluxo de DNS e SSL

1. **Cadastro** gera um token (`ro_verify_xxxxx`) e instrucoes de DNS.
2. **Verificacao** confere:
   - Registro TXT `_roteiroonline-verification.<subdominio?>` contendo o token.
   - Registro principal:
     - Subdominio → `CNAME` apontando para `CUSTOM_DOMAIN_CNAME_TARGET`.
     - Dominio raiz → `A` apontando para `CUSTOM_DOMAIN_APEX_IP`.
3. Ao confirmar a verificacao, o backend marca `is_verified` e inicia o fluxo de SSL (`ssl_status` = `pending/requested`). O `DomainSslService` ainda e um stub pronto para integrar com Certbot/Cloudflare mais adiante.
4. **Ativacao** so libera trafego quando o dominio foi verificado e o SSL esta disponivel (ou quando nao existe provider configurado, aceitando ativacao manual).

## Configuracao DNS

| Cenario                | Registro TXT                                   | Registro Principal                       |
|------------------------|------------------------------------------------|------------------------------------------|
| `www.suaagencia.com`   | Host: `_roteiroonline-verification.www`        | Tipo: `CNAME`, Host: `www`, Valor: `roteiroonline.com` |
| `roteiros.suaagencia.com` | Host: `_roteiroonline-verification.roteiros` | Tipo: `CNAME`, Host: `roteiros`, Valor: `roteiroonline.com` |
| `suaagencia.com`       | Host: `_roteiroonline-verification`            | Tipo: `A`, Host: `@`, Valor: `CUSTOM_DOMAIN_APEX_IP` |

> Preferimos subdominio (CNAME) porque facilita migracoes e evita depender de IP fixo.

## Resolucao publica

- `PublicPageResolverService` recebe `host`, `path` e a sessao do banco:
  - Hosts presentes em `PLATFORM_DOMAINS` → mantem o acesso `/{agency_slug}/{route_slug}`.
  - Hosts salvos em `agency_domains` com `is_active=true` e `is_verified=true` → localizam a agencia apenas pelo host e usam `/{route_slug}`.
- O HTML final usa canonical/OG `url` com o host correto, respeitando `X-Forwarded-Proto` (padrao `https` quando o header nao existir).

## Ajustes no Nginx / proxy

1. Encaminhar todos os hosts customizados para o backend FastAPI (mesmo upstream).
2. Preservar `Host` original e `X-Forwarded-Proto`.
3. Manter excecoes para `/api`, `/admin`, `/assets`, `/uploads` etc (arquivos estaticos continuam onde ja estavam).
4. Instalar certificados SSL validos para cada host customizado (hoje emissao manual/externa).
5. Garantir que os registros DNS CNAME ou A apontem para `CUSTOM_DOMAIN_CNAME_TARGET` ou `CUSTOM_DOMAIN_APEX_IP`.

## Limitacoes atuais

- O fluxo de SSL ainda depende de integracao com emissor externo.
- O backend nao revalida DNS continuamente; eh preciso clicar em "Verificar" apos ajustar registros.
- Dominio apex em TLDs incomuns podem exigir ajustar a dependencia `publicsuffix2`.

## Variaveis de ambiente

| Variavel                       | Descricao                                                              |
|--------------------------------|------------------------------------------------------------------------|
| `PLATFORM_DOMAINS`             | Lista separada por virgula dos hosts oficiais da plataforma.           |
| `FORBIDDEN_CUSTOM_HOSTS`       | Hosts proibidos para cadastro (ex.: dominio oficial, localhost).       |
| `PLATFORM_PRIMARY_DOMAIN`      | Dominio usado para canonicos no modo padrao.                           |
| `CUSTOM_DOMAIN_CNAME_TARGET`   | Destino CNAME para subdominios.                                        |
| `CUSTOM_DOMAIN_APEX_IP`        | IP publico para registros A do dominio raiz.                           |
| `DOMAIN_VERIFICATION_PREFIX`   | Prefixo aplicado no host do registro TXT de verificacao.               |
| `CUSTOM_DOMAIN_SSL_PROVIDER`   | Nome/identificador do emissor de SSL (vazio = emissao manual).         |
| `CUSTOM_DOMAIN_SSL_SCRIPT_PATH` | Caminho absoluto do script que emite certificados (quando `CUSTOM_DOMAIN_SSL_PROVIDER=certbot`). |

## Como a tela do painel funciona

- `AgencyDomainsView.vue` consome `/api/v1/agencies/me/domains`.
- Cada dominio mostra instrucoes TXT/CNAME/A, status (pendente, verificado, SSL, ativo, primario) e acoes:
  - Verificar dominio
  - Ativar / Desativar
  - Tornar primario
  - Excluir (apenas quando inativo)
- O formulario valida hosts sem protocolo/path e permite marcar como primario no cadastro.

## Automatizando SSL com Certbot (VPS Hostinger)

1. **Instale o Certbot** no VPS (Ubuntu/Debian):
   ```bash
   sudo apt update && sudo apt install -y certbot python3-certbot-nginx
   ```
2. **Crie uma pasta webroot** compartilhada com o Nginx que responde pelos domínios customizados:
   ```bash
   sudo mkdir -p /var/www/roteiroonline/.well-known/acme-challenge
   sudo chown -R www-data:www-data /var/www/roteiroonline
   ```
3. **Inclua no Nginx** (server block que atende os hosts customizados) para servir o webroot:
   ```nginx
   location /.well-known/acme-challenge/ {
       root /var/www/roteiroonline;
   }
   ```
4. **Copie o script** `backend/scripts/issue_custom_domain_cert.sh` para o VPS (ex.: `/opt/roteiroonline/issue_custom_domain_cert.sh`) e torne-o executável:
   ```bash
   sudo mkdir -p /opt/roteiroonline
   sudo cp backend/scripts/issue_custom_domain_cert.sh /opt/roteiroonline/
   sudo chmod +x /opt/roteiroonline/issue_custom_domain_cert.sh
   ```
5. **Exponha o script no container** (se estiver usando Docker) montando `/opt/roteiroonline` dentro do serviço `api`.
6. **Configure o `.env` do backend**:
   ```
   CUSTOM_DOMAIN_SSL_PROVIDER=certbot
   CUSTOM_DOMAIN_SSL_SCRIPT_PATH=/opt/roteiroonline/issue_custom_domain_cert.sh
   CERTBOT_WEBROOT=/var/www/roteiroonline
   CERTBOT_EMAIL=suporte@suaempresa.com.br
   ```
7. **Recrie o container** (`docker compose up -d --build api`). A partir de agora, quando um domínio for verificado o serviço chamará o script, rodará `certbot` e atualizará automaticamente `ssl_status=issued`. A cada emissão o `deploy-hook` incluso no script recarrega o Nginx para passar a servir o novo certificado.
