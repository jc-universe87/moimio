🌐 [English](quick-guide.md) · [Deutsch](quick-guide.de.md) · [한국어](quick-guide.ko.md) · [Español](quick-guide.es.md) · **Português (Brasil)** · [Français](quick-guide.fr.md)

# Guia de instalação rápida

Para quem se sente à vontade com terminal, Docker e um pouco de administração de sistemas. Se não for o seu caso, o [Guia para iniciantes](beginner.pt-BR.md) trata dos mesmos assuntos com mais calma e mais explicações.

Tempo necessário: **30 a 60 minutos**, de um servidor novo até um administrador logado. A maior parte disso é o primeiro `docker compose up --build`, que monta as duas imagens do Moimio a partir do código-fonte, na sua máquina.

---

## Pré-requisitos

- Um servidor Linux (qualquer distribuição moderna: Ubuntu 22.04+, Debian 12+, Fedora, qualquer uma com systemd).
- **Docker Engine 24+** e **Docker Compose v2** (o subcomando `docker compose`, e não o antigo `docker-compose` avulso).
- **Git** (para clonar), ou simplesmente baixe e descompacte o tarball do código-fonte.
- **Portas:** `6120` (frontend; ele também repassa `/api` e `/health` para o backend, então os navegadores só precisam desta). O Compose também publica `6121` (backend, para acesso direto à API durante a depuração) e `6122` (PostgreSQL). Nenhuma das duas precisa ser pública; veja "Como mudar as portas" abaixo para vinculá-las ao localhost.
- Permissão de `sudo` para o `upgrade.sh`, que chama `sudo docker compose`.
- Cerca de **2 GB de RAM** e **5 GB de disco** para uma instalação do tamanho de uma igreja pequena.

Para verificar se o Docker está pronto:

```bash
docker --version          # → Docker version 24.0+ ...
docker compose version    # → Docker Compose version v2.x.x
```

Se `docker compose version` falhar, você está com o Compose antigo e avulso. Instale o plugin v2: `apt install docker-compose-plugin` (Ubuntu/Debian) ou siga as [instruções oficiais do Docker](https://docs.docker.com/compose/install/).

---

## 1. Clone e configure

```bash
git clone https://github.com/jc-universe87/moimio.git
cd moimio
cp .env.example .env
```

Abra o `.env` e edite pelo menos as duas primeiras destas variáveis:

| Variável | O que definir |
|---|---|
| `SECRET_KEY` | Uma sequência aleatória de **pelo menos 64 caracteres**. Gere uma com `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` ou `openssl rand -hex 64`. **Não deixe o valor provisório `change-me-...` em produção.** |
| `POSTGRES_PASSWORD` | Uma senha aleatória para o usuário do banco de dados. Mesmo método de geração. |
| `DATABASE_URL` | Opcional. O `docker-compose.yml` monta a `DATABASE_URL` do backend a partir de `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB`, então a linha do `.env` não é a que o contêiner usa. Atualize a parte da senha mesmo assim, se quiser manter o arquivo coerente. |

Defina a `POSTGRES_PASSWORD` **antes da primeira inicialização.** O Postgres só a aplica quando o volume `pgdata` é criado pela primeira vez; alterá-la depois causa `password authentication failed` até que você a altere também dentro do banco de dados.

Deixe `LOG_LEVEL=INFO` (o padrão). Veja "Reforço de segurança para produção" para entender o porquê.

Se quiser e-mail funcionando desde o início, defina também o bloco SMTP; veja a tabela de SMTP no fim deste guia. Pular o SMTP não tem problema; o aplicativo funciona sem ele (os e-mails de confirmação de inscrição simplesmente não são enviados, e os administradores podem confirmar as inscrições manualmente).

### Como mudar as portas

Os padrões são 6120 (frontend), 6121 (backend) e 6122 (Postgres). Se alguma delas já estiver em uso no seu servidor, sobrescreva no `.env`:

```
FRONTEND_PORT=7120
BACKEND_PORT=7121
DB_PORT=7122
```

O `docker-compose.yml` lê esses valores com `${FRONTEND_PORT:-6120}` etc., então os valores do env passam adiante sem outras edições. Aí você abriria `http://localhost:7120`.

Os valores vão direto para o mapeamento `ports:` do Compose, então você também pode informar um endereço. Isto vincula a porta apenas à interface de loopback do servidor:

```
BACKEND_PORT=127.0.0.1:6121
DB_PORT=127.0.0.1:6122
# Only when your reverse proxy or tunnel runs on this same host:
FRONTEND_PORT=127.0.0.1:6120
```

O navegador fala com o backend pelo proxy `/api` do frontend, então mudar a `BACKEND_PORT` não exige mais nada. (Arquivos `.env` mais antigos ainda podem ter `VITE_API_URL`; nada lê essa variável, então você pode apagar a linha.)

---

## 2. Suba os contêineres

![Saída do terminal durante o docker compose up --build](../assets/install-docker-build.png)

```bash
docker compose up -d --build
```

A primeira execução baixa imagens e monta tudo; conte com 3 a 5 minutos em uma conexão razoável. As montagens seguintes são mais rápidas.

Acompanhe o backend subindo:

```bash
docker compose logs -f backend
```

Você está procurando duas linhas de log, nesta ordem:

```
INFO  [alembic.runtime.migration] Running upgrade ... -> <latest migration>
INFO  Application startup complete.
```

A primeira significa que o esquema do banco de dados foi criado/migrado com sucesso. A segunda significa que o uvicorn está servindo a API. Se você vir a segunda sem a primeira, as migrações já estavam em dia, e isso também está certo. **Pressione Ctrl-C para parar de acompanhar o log; os contêineres continuam rodando.**

Faça um teste rápido da API (o mesmo endpoint também pode ser acessado pelo frontend em `http://localhost:6120/health`):

```bash
curl http://localhost:6121/health
# → {"status":"ok","database":"healthy","version":"1.0.6"}
```

### Sobre as migrações do Alembic

O Alembic é uma ferramenta de migração de banco de dados que acompanha o SQLAlchemy. Ele cuida da evolução do esquema: cada arquivo de migração é um conjunto de alterações versionado que sabe como levar o banco de dados adiante (e, quando possível, para trás).

Duas coisas que vale saber:

- **As migrações rodam automaticamente toda vez que o contêiner do backend inicia.** O CMD do Dockerfile é `alembic upgrade head && uvicorn ...`: o Alembic verifica a revisão atual do banco de dados, aplica as migrações mais novas que encontrar e depois passa a vez para o uvicorn.
- **As migrações não apagam os seus dados.** Cada migração é incremental: "adicionar esta coluna", "criar esta tabela", "renomear este índice". Elas nunca recriam o banco de dados do zero. Desde que você não rode `docker compose down -v` (a opção `-v` apaga os volumes nomeados, incluindo `moimio_pgdata`), os dados dos participantes, os eventos e as atribuições são preservados nas atualizações.

Se algum dia você precisar zerar o banco de dados, o comando é `docker compose down -v` (ele remove o volume `pgdata`, chamado `<project>_pgdata`, por exemplo `moimio_pgdata`). Faça isso só em uma instalação sem dados reais.

---

## 3. Crie o primeiro administrador

![Assistente de configuração inicial para a primeira conta de Superadministrador](../assets/first-time-setup.png)

O Moimio não vem com um administrador padrão. Abra `http://localhost:6120` (ou a porta que você configurou) no navegador. Você vai cair automaticamente em uma **tela de configuração inicial**: o Moimio percebe que não existe nenhum usuário e oferece o assistente.

Preencha:

- **Nome completo**: o nome exibido na área administrativa.
- **E-mail**: o seu login.
- **Senha** e **Confirmar senha**: no mínimo 8 caracteres. Use um bom gerenciador de senhas.

A tela também tem um seletor de idioma e um botão de modo claro/escuro. Clique em **Criar superadministrador**. A conta é criada com a função de **Superadministrador**, e você é levado à página de login para entrar com ela. A tela de configuração nunca mais aparece depois que existe algum usuário.

**Alternativa: criação pela linha de comando.** Para instalações sem interface ou provisionamento automatizado, a mesma operação está disponível na linha de comando:

```bash
docker compose exec backend python -m app.cli.create_admin
```

Ele pede e-mail, nome completo e senha e cria um Superadministrador. Pela tela é a opção recomendada para quem hospeda por conta própria. A linha de comando também é o caminho de volta se você perder a senha do único Superadministrador e não tiver SMTP para redefini-la: crie um segundo Superadministrador com outro e-mail.

---

## 4. Entre (depois da configuração)

Entre em `http://localhost:6120/login` com a conta que você acabou de criar.

Sem nenhum evento ainda, você cai na tela **Bem-vindo ao Moimio**; clique em **Criar seu primeiro evento**. Depois que houver eventos, a lista de eventos tem um botão **+ Novo evento**.

Como Superadministrador, abra também **Workspace** na barra lateral e defina a sua **URL do aviso de privacidade**. O formulário público de inscrição tem um link para ela logo após a frase de consentimento; se deixar em branco, nenhum link aparece.

---

## 5. Reforço de segurança para produção

Antes de expor o Moimio à internet:

- Coloque um proxy reverso com terminação TLS na frente da porta 6120. Caddy, Traefik ou um Cloudflare Tunnel no servidor funcionam bem; Nginx + Let's Encrypt é a opção clássica.
- O HTTPS também é o que faz os recursos do aplicativo funcionarem. Os navegadores só registram o service worker com HTTPS ou em `localhost`, então uma instalação aberta por um endereço de rede local em HTTP simples, como `http://192.168.1.20:6120`, fica sem cache offline, sem o aviso de "nova versão disponível" e sem nada para o botão "Limpar cache e recarregar" limpar, e nenhum erro em lugar nenhum explica o motivo.
- Mantenha a porta do backend (6121) e a do banco de dados (6122) fora da internet pública. Vincule-as ao localhost no `.env` (veja "Como mudar as portas"). Uma regra de firewall no servidor não basta: as portas publicadas pelo Docker são abertas no iptables pelo próprio Docker e passam por cima das regras do `ufw`/`firewalld`.
- Leia o [`SECURITY.md`](../../SECURITY.md) (em inglês): a seção "Hardening recommendations for self-hosters" trata do resto (SECRET_KEY forte, troca periódica da senha do banco de dados, atualizações do servidor Docker, cuidado com as credenciais SMTP).
- Deixe `LOG_LEVEL=INFO` em qualquer instalação com participantes reais. `LOG_LEVEL=DEBUG` grava nomes, endereços e datas de nascimento dos participantes no log do contêiner a cada requisição; para depurar, use uma cópia com dados inventados.

---

## 6. Atualização

Na raiz do repositório do seu clone git:

```bash
./upgrade.sh                # latest commit on your current branch
./upgrade.sh v1.0.6         # a specific release tag (see CHANGELOG.md)
./upgrade.sh v1.0.6 --yes   # skip the confirmation prompt
./upgrade.sh --dry-run      # show what would happen, change nothing
```

O script primeiro faz verificações (`.env` presente, árvore de trabalho limpa, contêiner `db` rodando), mostra os commits que vai aplicar, faz backup do `.env` em `.env.pre-upgrade-<timestamp>.bak` e do banco de dados em `../pgdata-pre-upgrade-<timestamp>.sql.gz`, depois faz checkout da versão de destino e roda `docker compose down`, `build --no-cache` e `up -d`. No fim, ele mostra os comandos exatos para voltar atrás. Guarde os backups até ter certeza de que está tudo bem com a nova versão. Fazer checkout de uma tag deixa o clone em um HEAD destacado (detached HEAD); então, depois de fixar uma versão, informe a próxima explicitamente também (`./upgrade.sh v1.0.7`), em vez de rodar o script sem argumentos.

Depois de reiniciar, o script espera até 90 segundos para o contêiner do backend ficar "healthy". O healthcheck do backend no `docker-compose.yml` chama `/health` a cada 10 segundos, depois de um período inicial de 30 segundos. Se a espera terminar com um aviso de "did not become healthy" (por exemplo, por causa de uma migração demorada), confira `curl http://localhost:6121/health` e o log do backend antes de voltar atrás.

O equivalente manual, se preferir:

```bash
git pull            # or: git fetch --tags && git checkout v1.0.6
docker compose build --no-cache
docker compose up -d --force-recreate
```

O `--no-cache` importa quando o Dockerfile muda (novas dependências, instalação de fontes etc.). Se você pular essa opção, pode acabar rodando código novo sobre uma camada de imagem antiga e dar de cara com falhas confusas.

As migrações rodam automaticamente na inicialização do backend; não é preciso rodar `alembic upgrade head` manualmente. Os seus dados são preservados nas atualizações (o volume `pgdata` não é tocado). Mesmo assim, faça um backup antes, como em qualquer atualização.

O `deploy.sh`, na raiz do repositório, é outra ferramenta: ele substitui a instalação a partir de um pacote `../moimio-ce-<tag>.zip` e é destinado a instalações que não foram feitas com `git clone`. Se você clonou o repositório, use o `upgrade.sh`.

### Imagens de contêiner

Este guia monta as imagens a partir do código-fonte. Cada versão também é publicada como `ghcr.io/jc-universe87/moimio-backend:<tag>` e `ghcr.io/jc-universe87/moimio-frontend:<tag>` (por exemplo, `v1.0.6`). Se você usá-las, sempre fixe uma tag de versão: `:latest` está congelada na v1.0.6, não é mais atualizada e não tem suporte. O `backend/deploy/production.yml` é o modelo do serviço hospedado, não um arquivo compose para hospedagem própria; use o `docker-compose.yml` da raiz.

---

## 7. Backups

O backup mais simples é um `pg_dump` do Postgres:

```bash
docker compose exec -T db pg_dump -U moimio moimio | gzip > moimio-backup-$(date +%F).sql.gz
```

Agende isso no cron. Guarde os dumps em algum lugar fora do servidor.

Para restaurar, carregue o dump em um banco de dados vazio (um dump simples enviado para um banco já populado falha nas tabelas e linhas existentes):

```bash
docker compose stop backend
docker compose exec -T db dropdb -U moimio moimio
docker compose exec -T db createdb -U moimio moimio
gunzip -c moimio-backup-2026-10-01.sql.gz | docker compose exec -T db psql -U moimio moimio
docker compose start backend
```

(Troque pelo seu `POSTGRES_USER` / `POSTGRES_DB`, se você os alterou.)

O produto também traz um backup por evento dentro do aplicativo: a página **Backup**, na barra lateral, baixa um ZIP por evento (completo, ou só a estrutura, sem dados pessoais), e **Restaurar a partir de backup** traz um evento de volta como um novo rascunho, nesta ou em outra instalação. Os membros da equipe e as funções deles não vão no backup; convide a equipe de novo no servidor de destino. Veja [`docs/manual/09-data-export-gdpr.pt-BR.md`](../manual/09-data-export-gdpr.pt-BR.md), no manual do usuário.

Para um arquivo do workspace inteiro pela linha de comando: `docker compose exec backend python -m app.cli.export_all --out /tmp/moimio-export.zip`.

Para trazer um workspace inteiro para este servidor, com todos os eventos de uma vez, veja [Moving a workspace to your own Moimio](../moving-a-workspace.md) (em inglês).

---

## Referência de SMTP (opcional)

Se você quer e-mails de confirmação de inscrição e redefinição de senha, preencha o bloco SMTP no `.env`:

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=events@yourchurch.org
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=events@yourchurch.org
SMTP_FROM_NAME=Your Church Events
SMTP_TLS=true
SMTP_SSL=false
```

`SMTP_TLS=true` é STARTTLS (porta 587). Para TLS implícito na porta 465, defina `SMTP_PORT=465`, `SMTP_SSL=true` e `SMTP_TLS=false`. O e-mail só é ativado quando `SMTP_HOST` e `SMTP_USER` estão definidos. Reinicie o backend depois de mudar qualquer um deles (`docker compose up -d backend`).

Provedores comuns e as configurações típicas deles (confira na documentação atual do provedor, porque elas mudam de vez em quando):

| Provedor | Host típico | Porta típica | Observações |
|---|---|---|---|
| Zoho Mail | `smtp.zoho.eu` / `smtp.zoho.com` | 587 | Gere uma senha de app em Account → Security |
| Gmail / Google Workspace | `smtp.gmail.com` | 587 | Exige verificação em duas etapas + senha de app |
| Brevo (antigo Sendinblue) | `smtp-relay.brevo.com` | 587 | O plano gratuito cobre o volume da maioria das igrejas pequenas |
| SMTP2GO | `mail.smtp2go.com` | 587 | Pagamento por uso, com plano gratuito |
| Mailgun | `smtp.mailgun.org` | 587 | Exige verificação de domínio |

**Sempre confira a documentação de SMTP atual do seu provedor** antes de configurar: configurações, números de porta e requisitos de autenticação mudam. A fonte de verdade é a página do provedor, não esta tabela.

Teste pela interface depois de criar um evento: abra as configurações do formulário de inscrição do evento (**Configuração ▸ Inscrição** enquanto o evento está na configuração, **Mais ▸ Formulário de inscrição** depois que as inscrições abrirem) e depois **Confirmação por e-mail ▸ Enviar e-mail de teste**. O e-mail de teste vai para o seu próprio endereço de login e informa qual nome de remetente (`From`), qual `Reply-To` e qual servidor SMTP foram usados; muito útil para investigar casos de "o e-mail nunca chegou".

Se o SMTP ficar em branco, o aplicativo não envia nada e registra `email_skipped` para cada envio que seria feito. Útil para desenvolvimento.

---

## Referência de configurações opcionais

Todas estas variáveis são lidas do `.env` e repassadas pelo `docker-compose.yml`. Reinicie com `docker compose up -d` depois de alterá-las.

| Variável | Padrão | O que faz |
|---|---|---|
| `LOG_LEVEL` | `INFO` | `DEBUG` registra todas as consultas ao banco de dados com os valores, ou seja, dados de participantes. |
| `RATE_LIMIT_REGISTRATION` | `60` | Inscrições por minuto a partir de um mesmo endereço. Cada familiar a mais no formulário conta. Aumente se uma congregação inteira se inscrever ao mesmo tempo pelo mesmo Wi-Fi; `0` desativa o limite. Atrás do seu próprio proxy reverso ou Cloudflare Tunnel, é usado o endereço real do visitante, desde que esse proxy chegue ao Moimio a partir de um endereço privado ou de loopback e envie `X-Forwarded-For`. |
| `FEATURE_ALLOCATION` | `true` | `false` desativa o motor de atribuição, para uma instalação só de inscrições. |
| `FEATURE_OUTBOUND_WEBHOOKS` | `true` | `false` oculta a página Webhooks e desativa o envio. Veja [webhooks](../webhooks.md) (em inglês). |
| `WEBHOOK_ALLOW_PRIVATE_TARGETS` | `false` | URLs de webhook em endereços privados, de loopback ou link-local (`10.x`, `192.168.x`, `localhost`…) são recusadas, a menos que isto seja `true`. Ative só se o seu receptor estiver na sua própria rede. Não está no `.env.example`; adicione a linha você mesmo. |
| `WEBHOOK_DELIVERY_RETENTION_DAYS` | `30` | Por quanto tempo o histórico de envios de webhooks é mantido. |

As demais variáveis do `.env.example` e do `docker-compose.yml` (`FEATURE_CREATE_EVENT_CONFIRMATION`, `EVENT_CHARGE_*`, `BILLING_CARD_LAST4`, `FEATURE_ACCOUNT_PORTAL`, `ACCOUNT_URL`, `FEATURE_DEMO_NOTICE`, `MOIMIO_DEMO_MAIL_URL`, `MOIMIO_TENANT_ID`, `MOIMIO_WEBHOOK_URL`, `MOIMIO_WEBHOOK_SECRET`) existem para o serviço hospedado e os workspaces de demonstração. Deixe-as com os valores padrão em uma instalação própria normal. `APP_URL` não é mais usada: os links dos e-mails usam o endereço da própria requisição.

---

## Solução de problemas

**`docker compose up` sai na hora, sem logs.**
Veja o erro real: `docker compose ps` e depois `docker compose logs <service>`. A causa mais comum é conflito de portas: outra coisa no servidor já está usando 6120, 6121 ou 6122. Pare o serviço que está em conflito ou mude a porta (veja "Como mudar as portas" acima).

**Os logs do backend mostram `connection refused` para `db:5432`.**
O backend iniciou antes de o Postgres estar pronto. A cláusula `depends_on: condition: service_healthy` normalmente evita isso; se está acontecendo, a sua versão do Docker pode ser antiga demais. Atualize o Docker ou simplesmente rode `docker compose restart backend`.

**Os logs do backend mostram `relation "users" does not exist`.**
As migrações do Alembic não rodaram. Procure em `docker compose logs backend` um erro do Alembic mais acima no log. A solução costuma ser `docker compose down && docker compose up -d --force-recreate`.

**A página diz "Não foi possível conectar ao servidor", ou o login falha com erro de rede.**
O contêiner do frontend serve a página e repassa `/api/*` para o contêiner do backend. Verifique se o backend está no ar (`docker compose ps` e depois `docker compose logs backend`) e se `curl http://localhost:6120/health` responde. Se você colocou o seu próprio proxy reverso na frente, confira se ele encaminha todos os caminhos para a porta 6120, e não só `/`.

**Os logs do backend mostram `password authentication failed for user "moimio"`.**
A `POSTGRES_PASSWORD` foi alterada depois que o volume do banco de dados foi criado; o Postgres mantém a senha original. Coloque a senha antiga de volta no `.env` ou altere-a dentro do banco de dados (`docker compose exec db psql -U moimio -c "ALTER USER moimio PASSWORD '<new>'"`) e reinicie.

**Qualquer outra coisa.**
Abra um [relatório de bug](https://github.com/jc-universe87/moimio/issues/new?template=bug_report.md) com os logs relevantes (oculte antes qualquer dado de participante).

---

Pronto para usar o Moimio? Comece pelo [Manual do usuário](../manual/README.pt-BR.md) para ver o fluxo de organização de eventos.
