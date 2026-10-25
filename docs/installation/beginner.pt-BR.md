🌐 [English](beginner.md) · [Deutsch](beginner.de.md) · [한국어](beginner.ko.md) · [Español](beginner.es.md) · **Português (Brasil)** · [Français](beginner.fr.md)

# Guia de instalação para iniciantes

Este guia é para quem nunca abriu um terminal, mas precisa do Moimio funcionando para um evento de verdade. Vamos com calma.

Se você já se sente à vontade com Docker e servidores Linux, o [Guia de instalação rápida](quick-guide.pt-BR.md) trata dos mesmos assuntos em 30 minutos.

Você não precisa ser programador. Precisa estar disposto a copiar os comandos com cuidado e a pedir ajuda quando algo não funcionar.

---

## Uma palavra sincera antes de começar

Instalar o Moimio dá mais trabalho do que instalar um programa no computador. Ainda não existe a experiência "clique no botão, espere, pronto". Se você esbarrar em algo que o guia não cobre, pedir ajuda a um amigo com mais conhecimento técnico ou colar o erro em um assistente de IA costuma resolver em poucos minutos.

Na primeira vez, reserve **cerca de duas horas**. A maior parte disso é espera por downloads. Na segunda vez, é bem mais rápido.

---

## Vale a pena hospedar por conta própria? Um choque de realidade

A instalação é a parte fácil. A pergunta mais difícil é como vai ser manter um servidor em produção nos meses seguintes, principalmente durante um evento ao vivo, quando algo quebra e você precisa de tudo funcionando de novo em vinte minutos.

Um Moimio auto-hospedado é um pequeno servidor Linux pelo qual você passa a ser responsável. Na prática, isso significa:

- **O servidor precisa ficar ligado.** Se o escritório ficar sem energia, o Wi-Fi do local cair ou o provedor do VPS tiver uma pane, as inscrições ficam fora do ar até você colocá-las de volta.
- **É preciso aplicar atualizações.** Novas versões do Moimio (um comando; veja [Como atualizar o Moimio](#como-atualizar-o-moimio)), correções de segurança do Ubuntu, atualizações ocasionais do Docker. Não é toda semana, mas também não é nunca.
- **As coisas vão falhar nas horas mais inconvenientes.** A renovação do certificado SSL pode falhar; uma migração do banco de dados pode se recusar a rodar depois de uma atualização; o contêiner do banco de dados pode se recusar a reiniciar. A solução normalmente é um ou dois comandos, *se você souber quais*.
- **Os backups são problema seu.** O Moimio tem um recurso de backup, mas usá-lo de fato antes de uma grande mudança, e guardar o resultado em um lugar seguro, fica por sua conta.
- **DNS, certificados e túneis são frágeis na operação.** Um domínio expira, um IP muda, um token da Cloudflare é trocado, e o formulário de inscrição passa a dar erro 404.

**Uma autoavaliação.** Antes de continuar, responda com sinceridade:

- [ ] Você se sente à vontade rodando comandos no terminal e lendo mensagens de erro.
- [ ] Se um serviço não inicia, você sabe encontrar e ler os logs dele.
- [ ] Se o endereço IP do servidor mudar, você sabe atualizar o DNS.
- [ ] Se algo quebrar às 23h durante o evento, você tem alguém (ou o conhecimento) para consertar.
- [ ] Você tem uma estratégia de backup, e não só a intenção de ter uma.

**Se alguma resposta for *não*, considere o [moimio.app](https://moimio.app), a versão hospedada e gerenciada do mesmo produto.** Ele roda o mesmo código, o mesmo motor de atribuição, o mesmo fluxo de inscrição. Hospedagem, backups, atualizações e SSL ficam por conta do serviço. Os preços atuais estão no site.

Se você quiser hospedar por conta própria, este guia continua mostrando o caminho. O custo de hospedar por conta própria não são os poucos euros por mês de um VPS: é ficar de plantão durante um evento ao vivo. Tome a decisão de olhos abertos.

---

## Escolha onde hospedar

Há duas formas razoáveis de rodar o Moimio. Escolha a que combina com a sua situação:

### → Caminho A — Alugue um servidor pequeno (um "VPS")

Um VPS é um pequeno computador que fica em um data center, que você aluga por mês e acessa remotamente. Custa de €4 a €10 por mês. Sempre ligado, sempre acessível, sem nenhum equipamento para manter do seu lado.

**Ideal se:** você quer pouca manutenção, vai abrir as inscrições com meses de antecedência ou não quer um computador em casa ocupado rodando o Moimio.

Continue em [Caminho A — Configuração do VPS](#caminho-a--alugue-um-vps), abaixo.

### → Caminho B — Hospede no seu próprio computador ou mini-PC

Rode o Moimio em um computador que você já tem e exponha-o à internet por meio de um serviço gratuito chamado Cloudflare Tunnel. Nenhum custo de hospedagem.

**Ideal se:** a soberania dos dados é uma exigência rígida (você precisa especificamente que os dados dos participantes fiquem em um equipamento seu) e você tem alguém capaz de resolver problemas em uma máquina Linux durante um evento.

Um servidor em casa ou no escritório é bem menos confiável do que um VPS. A energia, a internet, o conector cloudflared e o próprio sistema operacional podem falhar; o formulário de inscrição fica fora do ar até alguém chegar à máquina e consertar. Se a soberania dos dados não for uma exigência rígida, o Caminho A (VPS) ou o [moimio.app](https://moimio.app) são opções mais simples.

Continue em [Caminho B — Hospedagem própria com Cloudflare Tunnel](#caminho-b--hospede-por-conta-própria-com-cloudflare-tunnel), abaixo.

Os dois caminhos se encontram no **[Passo 4 — Instale o Moimio](#passo-4--instale-o-moimio)**, que é igual independentemente de onde o Moimio vai rodar.

---

## Caminho A — Alugue um VPS

Um provedor de VPS oferece um pequeno computador em um data center. Existem muitos: Hetzner, OVH, Scaleway, DigitalOcean, Linode, Vultr, Contabo e vários provedores regionais. A maioria cobra de €4 a €10/mês pelo que o Moimio precisa.

Para igrejas e organizações missionárias europeias, provedores com data centers na Europa costumam ser preferíveis por causa do GDPR (os dados dos participantes ficam na UE). Hetzner Cloud (na Alemanha / Finlândia) e OVH (na França / Alemanha) são escolhas comuns. Para organizadores no Brasil, na Coreia, no Japão, nos EUA ou em outros lugares, o provedor de nuvem local costuma servir bem; se você estiver no Brasil, vale escolher pensando também na LGPD. O Moimio não se importa com qual você escolher.

> **Não recomendamos um provedor específico.** Este guia usa o Hetzner Cloud como *exemplo* por ser bem documentado e barato, e não como recomendação. Escolha o provedor em que você confia. A configuração é parecida em todos.

### Passo 1 — Cadastre-se e crie o servidor

Cada provedor de VPS tem o seu próprio processo de cadastro e criação de servidor. Em vez de documentar aqui um passo a passo que fica desatualizado toda vez que o provedor muda o painel, siga a documentação de primeiros passos do seu próprio provedor.

Para o Hetzner Cloud especificamente: <https://docs.hetzner.com/cloud/servers/getting-started/creating-a-server/>

Ao criar o servidor, as escolhas que importam para o Moimio são:

- **Sistema operacional:** **Ubuntu 24.04** (ou 22.04): são os mais fáceis de conseguir ajuda se algo der errado.
- **Tamanho do servidor:** cerca de **2 vCPU + 2 GB de RAM + 40 GB de disco** é mais do que suficiente para um evento de 150 pessoas. A maioria dos provedores chama isso de plano "pequeno" e cobra €4–5/mês.
- **Chave SSH:** adicione a sua chave SSH durante a criação (para poder se conectar sem senha). Se você ainda não tem uma, vá para o [Passo 2 — Gere uma chave SSH](#passo-2--gere-uma-chave-ssh) antes de criar o servidor e depois volte aqui.
- **Localização:** escolha um data center perto de onde estão os seus participantes. Data centers na UE costumam ser preferíveis para eventos europeus; para eventos em outros lugares, escolha o que for adequado geográfica e juridicamente.

Depois que o servidor for criado, o provedor informa um **endereço IP público** (algo como `203.0.113.42`). **Anote esse endereço IP**: você vai precisar dele para se conectar.

### Passo 2 — Gere uma chave SSH

Uma chave SSH são dois arquivos que formam um par: uma **chave pública** (que você entrega ao provedor do VPS) e uma **chave privada** (que fica no seu notebook, como uma chave de casa digital). Juntas, elas permitem que o seu notebook entre no servidor sem senha.

No seu notebook, abra um terminal:

- **macOS:** Spotlight → "Terminal".
- **Linux:** qualquer aplicativo de terminal.
- **Windows:** instale o [Windows Terminal](https://aka.ms/terminal) pela Microsoft Store ou use o PowerShell, que já vem instalado.

Depois digite:

```bash
ssh-keygen -t ed25519 -C "you@your-email.com"
```

(O e-mail é só um rótulo. Nenhum e-mail é enviado.) Quando o programa perguntar:

- Pressione Enter para aceitar o local padrão do arquivo.
- Digite uma frase secreta (passphrase) de que você vá se lembrar (ela protege a chave se o notebook for roubado). Pressione Enter.
- Digite a frase secreta de novo. Pressione Enter.

Leia a chave pública:

```bash
cat ~/.ssh/id_ed25519.pub
```

Isso mostra uma linha comprida começando com `ssh-ed25519 AAAA...`. Copie a linha inteira. Adicione-a na configuração de chaves SSH do seu provedor de VPS (todo provedor tem uma seção para isso no painel). Agora o seu servidor (quando você o criar, ou depois de reinstalá-lo) aceita logins vindos do seu notebook.

Se você travar neste passo, pesquise "[seu provedor de VPS] adicionar chave SSH": todo provedor tem documentação sobre isso.

### Passo 3 — Conecte-se ao servidor

Abra um terminal no seu notebook:

```bash
ssh root@203.0.113.42
```

(Troque `203.0.113.42` pelo endereço IP do seu servidor.)

Na primeira vez, aparece uma pergunta sobre se você confia no servidor. Digite `yes` e pressione Enter. Digite a frase secreta da sua chave SSH, se for pedida. Você deve ver algo assim:

```
Welcome to Ubuntu 24.04.x LTS ...
root@your-server:~#
```

Esse é o prompt do terminal do **servidor**. Tudo o que você digitar agora roda no servidor, não no seu notebook. **Você entrou.**

Se aparecer `Permission denied (publickey)`, a sua chave SSH não está associada ao servidor. Confira de novo a configuração de chaves SSH do seu provedor.

Agora vá para o [Passo 4 — Instale o Moimio](#passo-4--instale-o-moimio).

---

## Caminho B — Hospede por conta própria com Cloudflare Tunnel

Neste caminho, você precisa de um computador que possa ficar ligado o tempo todo: um desktop, um mini-PC, um notebook antigo que você não usa mais ou um Raspberry Pi 4 (4 GB ou 8 GB). Também precisa de uma conexão de internet estável no lugar onde esse computador fica.

### Passo 1 — Prepare o seu computador

Instale o **Linux**, se ainda não tiver:

- **Notebook ou desktop antigo:** o Ubuntu Desktop 24.04 LTS é a opção mais amigável. Baixe em <https://ubuntu.com/download/desktop> e siga o guia de instalação deles.
- **Raspberry Pi:** use o Raspberry Pi OS ou o Ubuntu Server para ARM. A documentação de cada um explica a configuração.
- **Mini-PC comprado especialmente para isso:** a maioria vem com Windows, mas o Ubuntu se instala sem problemas. O Raspberry Pi Imager e o instalador do Ubuntu são bem documentados.

Você não é *obrigado* a usar Linux (o Moimio também roda no macOS com Docker Desktop e no Windows com Docker Desktop e WSL2), mas, para um servidor que vai ficar ligado por meses, o Linux é a escolha mais previsível.

### Passo 2 — Instale o Docker

Abra um terminal no computador (não por SSH de outro lugar: direto na máquina, ou por SSH a partir de um notebook na mesma rede, se você tiver ativado isso). Depois:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Saia da sessão e entre de novo (ou reinicie) para que a nova permissão de grupo passe a valer. Depois verifique:

```bash
docker --version
docker run --rm hello-world
```

Se aparecer "Hello from Docker!", o Docker está funcionando.

### Passo 3 — Configure o Cloudflare Tunnel

Um **Cloudflare Tunnel** é um serviço gratuito que dá ao computador de casa ou do escritório um endereço público, sem que você precise abrir portas no roteador nem saber o IP da sua casa. O tráfego passa pela rede da Cloudflare, que cuida do TLS para você.

1. Cadastre-se em <https://dash.cloudflare.com/sign-up>, se ainda não tiver uma conta na Cloudflare. O plano gratuito é suficiente.
2. Adicione o seu domínio à Cloudflare (você vai precisar de um nome de domínio; veja [a seção sobre domínios](#como-conseguir-um-nome-de-domínio) abaixo, se ainda não tiver um).
3. Vá para **Zero Trust → Networks → Tunnels** no painel da Cloudflare. Clique em **Create a tunnel**, dê um nome (por exemplo, "moimio-home") e siga as instruções da Cloudflare para instalar o conector na sua máquina Linux. O assistente da Cloudflare fornece o comando exato de instalação do `cloudflared` para o seu sistema.
4. Na seção **Public hostnames** do túnel, adicione um nome como `events.yourchurch.org` e defina o **Service** como `HTTP://localhost:6120`.
5. Salve. A Cloudflare obtém e renova automaticamente um certificado TLS.

Acesse `https://events.yourchurch.org` em qualquer navegador: quando o Moimio estiver rodando, no próximo passo, você vai chegar a ele pelo túnel, já com HTTPS configurado.

Para instruções atualizadas: <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/>

### Quando a hospedagem própria dá errado

O que costuma dar errado em instalações próprias durante um evento de verdade, mais ou menos em ordem de probabilidade:

- **Falta de energia** no local do evento ou no escritório derruba o servidor. Reduza o risco com um nobreak (~€80) para o computador e o roteador.
- **Queda de internet** no local do evento ou no escritório derruba o endereço público. Reduza o risco deixando a internet do celular (roteamento) pronta para assumir, ou aceite o risco de ficar fora do ar.
- **O conector cloudflared para.** Uma atualização do sistema, um pico de memória ou uma versão desatualizada do conector pode desconectar o túnel sem aviso. A solução normalmente é `sudo systemctl restart cloudflared` no servidor: fácil, *se* você conseguir chegar ao servidor e souber o comando.
- **O próprio sistema operacional para de responder.** É menos provável em uma instalação nova do Ubuntu e mais provável em um Raspberry Pi rodando outras coisas ou em uma máquina que não é reiniciada há meses. Recuperar normalmente exige acesso físico.

Nada disso é exótico: são as falhas normais de quem roda um servidor fora de um data center. A pergunta é se você tem alguém capaz de resolvê-las na hora do evento. Se sim, hospedar por conta própria é uma troca razoável para manter os dados fisicamente nas suas instalações. Se não, o [moimio.app](https://moimio.app) absorve esses quatro tipos de falha.

Agora vá para o [Passo 4 — Instale o Moimio](#passo-4--instale-o-moimio).

---

## Passo 4 — Instale o Moimio

Este passo é igual, seja no VPS ou na hospedagem própria. O terminal em que você está é um VPS acessado por SSH (Caminho A) ou a sua própria máquina (Caminho B). Daqui em diante, **"o servidor"** significa o computador em que o Moimio vai rodar, seja ele qual for.

### 4.1 Baixe o código

```bash
git clone https://github.com/pistio/moimio.git
cd moimio
```

O `git` já vem instalado no Ubuntu. O clone leva alguns segundos.

O prompt agora mostra que você está dentro da pasta `moimio`.

### 4.2 Configure o Moimio

```bash
cp .env.example .env
nano .env
```

O `nano` é um editor de texto simples. Use as setas do teclado para navegar. Encontre estas linhas e edite-as:

**`SECRET_KEY`**: troque o valor provisório por uma sequência aleatória de verdade. Para gerar uma, abra um **segundo terminal** no seu notebook e rode:

```bash
openssl rand -hex 64
```

Copie o resultado. Cole como o novo valor de `SECRET_KEY` no `nano`.

**`POSTGRES_PASSWORD`**: troque `moimio_dev` por outra sequência aleatória (rode `openssl rand -hex 32` para uma mais curta). Faça isso agora, antes da primeira inicialização: o banco de dados guarda a senha com que foi iniciado pela primeira vez.

**`DATABASE_URL`**: você pode deixar esta linha como está; o Moimio monta o endereço real do banco de dados a partir da `POSTGRES_PASSWORD`. Se você gosta de tudo organizado, troque também o `moimio_dev` dela pela nova senha.

**`LOG_LEVEL`**: deixe como `INFO`. A opção `DEBUG` grava nomes, endereços e datas de nascimento dos participantes nos arquivos de log do servidor, então ela serve só para investigar problemas com dados inventados.

Para salvar: **Ctrl-O** e depois **Enter**. Para sair: **Ctrl-X**.

Por enquanto, você não precisa mexer em mais nada neste arquivo. As configurações de e-mail são opcionais e estão explicadas em [Envio de e-mail (opcional)](#envio-de-e-mail-opcional), abaixo.

### 4.3 Inicie o Moimio

```bash
docker compose up -d --build
```

O Docker baixa as imagens base, monta as imagens do Moimio e inicia três contêineres (banco de dados, backend, frontend). A primeira execução leva de **5 a 10 minutos**.

Quando terminar:

```bash
docker compose logs --tail=30 backend
```

Procure por:

```
INFO  [alembic.runtime.migration] Running upgrade ... -> <latest migration>
INFO  Application startup complete.
```

Se você vir essas linhas, o Moimio está no ar. (A primeira linha só aparece quando o banco de dados precisou ser criado ou atualizado, então não tem problema se você vir só a segunda.) **Não continue se aparecerem linhas de erro**: veja a seção de solução de problemas no fim deste guia.

### 4.4 Configuração inicial (crie a sua conta de administrador)

<p align="center">
  <img src="../assets/first-time-setup.png" alt="Assistente de configuração inicial para a primeira conta de Superadministrador" width="420">
  <br>
  <em>Assistente de configuração inicial para a primeira conta de Superadministrador</em>
</p>

Abra um navegador:

- **Caminho A (VPS):** acesse `http://YOUR_SERVER_IP:6120` (por exemplo, `http://203.0.113.42:6120`).
- **Caminho B (hospedagem própria):** acesse `http://localhost:6120`, se estiver na mesma máquina, ou `https://events.yourchurch.org`, se o seu Cloudflare Tunnel estiver configurado.

Você vai cair automaticamente na tela de **Configuração inicial**. O Moimio só a mostra enquanto ainda não existe nenhuma conta. Preencha:

- **Nome completo**: como o seu nome vai aparecer no Moimio.
- **E-mail**: o que você vai usar para entrar.
- **Senha** e **Confirmar senha**: pelo menos 8 caracteres. Um gerenciador de senhas é um grande aliado aqui.

Você pode trocar o idioma da tela no seletor logo abaixo. Clique em **Criar superadministrador**. O Moimio então mostra a página de login: entre com o e-mail e a senha que você acabou de escolher. Essa primeira conta é a de **Superadministrador**, a única conta que pode fazer tudo.

🎉 **Você instalou o Moimio.**

<p align="center">
  <img src="../assets/welcome-splash.png" alt="A tela Bem-vindo ao Moimio, exibida quando ainda não há eventos" width="560">
  <br>
  <em>A tela Bem-vindo ao Moimio</em>
</p>

Como ainda não há eventos, você verá a tela **Bem-vindo ao Moimio**, que explica as três fases de um evento (Configuração, Inscrição, Evento). Clique em **Criar seu primeiro evento** para começar.

Mais uma coisa que vale fazer agora: clique em **Workspace** no menu da esquerda e cole o endereço do **aviso de privacidade** da sua organização, se houver um. Quem preencher o seu formulário de inscrição vai ver um link para ele logo ao lado da caixa de consentimento.

---

## Passo 5 — Torne o Moimio acessível em um domínio de verdade (opcional, recomendado)

Acessar o Moimio em `http://203.0.113.42:6120` funciona para você, mas não é o endereço que você mandaria aos participantes. Para inscrições de verdade, você quer algo como `https://events.yourchurch.org`. O HTTPS também ativa algumas facilidades que os navegadores só permitem em sites seguros, como o aviso de "nova versão disponível" e o cache offline.

Se você seguiu o **Caminho B (hospedagem própria com Cloudflare Tunnel)**, já fez isso: o endereço do seu túnel é o endereço público. Pule esta seção.

Se você seguiu o **Caminho A (VPS)**, continue:

### Como conseguir um nome de domínio

Se você ainda não tem um, compre em qualquer registrador de domínios (Namecheap, Porkbun, INWX, Cloudflare Registrar, OVH, Registro.br: todos servem). Um domínio `.org` custa cerca de €10–15 por ano.

Você não precisa de um domínio separado: um subdomínio de um domínio que você já tem funciona muito bem. Se a sua igreja está em `yourchurch.org`, um subdomínio como `events.yourchurch.org` é mais limpo do que um domínio totalmente novo.

Se registro de domínio e DNS parecerem assustadores, este é um bom momento para pedir ajuda a um amigo com mais conhecimento técnico ou descrever a sua situação para um assistente de IA: ele pode explicar o processo do seu registrador em poucos minutos.

### Como apontar o domínio para o servidor (caminho do VPS)

Nas configurações de DNS do seu registrador, adicione um **registro A**:

| Nome | Tipo | Valor |
|---|---|---|
| `events` (ou o subdomínio que quiser) | A | `203.0.113.42` (o IP do seu servidor) |

Salve. O DNS se propaga em poucos minutos (às vezes leva até uma hora). Teste:

```bash
ping events.yourchurch.org
```

Se vierem respostas do IP do seu servidor, o DNS está funcionando.

### Como adicionar HTTPS (TLS)

Você tem duas opções limpas. As duas funcionam; escolha a que combina com o seu nível de conforto.

#### Opção 1 — Cloudflare na frente

A mais simples se TLS é novidade para você: use a Cloudflare como proxy reverso.

1. Adicione o seu domínio a uma conta (gratuita) da Cloudflare.
2. Configure um Cloudflare Tunnel no seu VPS, exatamente como no [Caminho B, Passo 3](#passo-3--configure-o-cloudflare-tunnel), apontando para `HTTP://localhost:6120`. (Com um túnel, você não precisa do registro A acima; a Cloudflare cria a entrada de DNS para você.)
3. A Cloudflare cuida do HTTPS automaticamente: você acessa `https://events.yourchurch.org` e o túnel leva o tráfego até o Moimio.

Um registro A simples, só com o proxy da Cloudflare, não basta: a Cloudflare encaminharia os visitantes para as portas web padrão (80/443), e o Moimio escuta na 6120. O túnel evita isso, e você não precisa abrir nenhuma porta.

É o que muita gente que hospeda por conta própria acaba fazendo, porque na prática é "configure e esqueça".

#### Opção 2 — Caddy no servidor

Instale o Caddy junto com o Moimio, no mesmo servidor. O Caddy obtém um certificado Let's Encrypt automaticamente.

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

Edite o `/etc/caddy/Caddyfile`:

```bash
sudo nano /etc/caddy/Caddyfile
```

Substitua o conteúdo por:

```
events.yourchurch.org {
    reverse_proxy localhost:6120
}
```

(Troque pelo seu domínio de verdade.) Salve (Ctrl-O, Enter) e saia (Ctrl-X). Recarregue o Caddy:

```bash
sudo systemctl reload caddy
```

O Caddy obtém um certificado TLS do Let's Encrypt automaticamente (de 30 a 60 segundos na primeira vez). Acesse `https://events.yourchurch.org`.

Agora você pode (e deve) fechar a porta 6120 para a internet, porque só o Caddy, no mesmo servidor, precisa falar com ela. A forma confiável é dizer ao Docker para escutar apenas no próprio servidor. Abra o `.env` de novo (`nano .env`) e defina:

```
FRONTEND_PORT=127.0.0.1:6120
BACKEND_PORT=127.0.0.1:6121
DB_PORT=127.0.0.1:6122
```

Salve e aplique com `docker compose up -d`. (Uma regra do `ufw` sozinha não resolve: o Docker abre as portas diretamente e passa por cima do `ufw`.) O firewall do próprio provedor, no painel web dele, é uma boa segunda camada: libere só as portas 22, 80 e 443.

---

## Envio de e-mail (opcional)

O Moimio funciona sem e-mail. Com ele, as pessoas recebem um e-mail de confirmação ao se inscrever, e você consegue redefinir uma senha esquecida. Para ativar, você precisa dos dados de uma conta de e-mail que permita envio por "SMTP" (é esse o nome que as páginas de ajuda do seu provedor de e-mail vão usar). Abra o `.env` e preencha o bloco que começa com `SMTP_`:

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=events@yourchurch.org
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=events@yourchurch.org
SMTP_FROM_NAME=Your Church Events
```

Salve e rode `docker compose up -d` para aplicar. Para conferir se funciona, abra as configurações do formulário de inscrição de um evento e clique em **Enviar e-mail de teste**, em **Confirmação por e-mail**: uma mensagem de teste chega na sua própria caixa de entrada. O [Guia de instalação rápida](quick-guide.pt-BR.md#referência-de-smtp-opcional) tem as configurações dos provedores mais comuns.

---

## Como atualizar o Moimio

Quando sair uma versão nova, rode no servidor:

```bash
cd ~/moimio
./upgrade.sh
```

O script mostra o que vai mudar e pergunta **Proceed with upgrade? [y/N]**. Digite `y`. Em seguida ele:

- salva uma cópia do seu arquivo de configurações `.env`,
- salva um backup do banco de dados ao lado da pasta `moimio` (um arquivo chamado `pgdata-pre-upgrade-<date-and-time>.sql.gz`),
- baixa a nova versão, monta o Moimio de novo e o reinicia,
- mostra os comandos exatos para voltar à versão antiga, se você precisar.

Ele pode pedir a sua senha, porque usa `sudo`. Para ir para uma versão específica em vez da mais nova, informe o nome dela, por exemplo `./upgrade.sh v1.0.6` (os nomes das versões estão no changelog). Para ver o que ele faria sem mudar nada, rode `./upgrade.sh --dry-run`.

No fim, o script espera até 90 segundos para o Moimio informar que está saudável. Se ele mostrar "backend did not become healthy", abra o Moimio no navegador antes de seguir as instruções para voltar atrás: se a página carregar e você conseguir entrar, o mais provável é que a atualização só tenha precisado de mais tempo para iniciar.

As atualizações costumam levar de 3 a 5 minutos. O site fica fora do ar por parte desse tempo, enquanto o Moimio é montado de novo e reiniciado. Se houver um evento em andamento, faça isso fora do horário do evento.

Os dados dos participantes são mantidos nas atualizações; as mudanças no banco de dados de que uma nova versão precisa são aplicadas automaticamente quando ela inicia. Guarde os arquivos de backup até ter certeza de que está tudo bem com a nova versão e depois apague-os.

---

## Backups

O backup mais simples é um dump do banco de dados. No servidor:

```bash
cd ~/moimio
docker compose exec -T db pg_dump -U moimio moimio | gzip > ~/moimio-backup-$(date +%F).sql.gz
```

Isso cria um arquivo de backup com a data no nome, na sua pasta pessoal. Copie-o regularmente para o seu notebook ou para um armazenamento na nuvem.

Restaurar substitui tudo o que há no banco de dados pelo conteúdo do backup, então só faça isso quando for realmente a intenção. O banco de dados precisa ser esvaziado antes, e é isso que as linhas `dropdb` e `createdb` fazem:

```bash
cd ~/moimio
docker compose stop backend
docker compose exec -T db dropdb -U moimio moimio
docker compose exec -T db createdb -U moimio moimio
gunzip -c ~/moimio-backup-2026-04-28.sql.gz | docker compose exec -T db psql -U moimio moimio
docker compose start backend
```

(Use o nome do seu próprio arquivo de backup.)

Em instalações de produção de verdade, automatize o backup com o `cron` e mande o arquivo para fora do servidor. Se isso estiver além do seu conforto, peça ajuda a um amigo com conhecimento técnico ou abra uma issue no GitHub pedindo um guia de "backup agendado".

**Backups dentro do Moimio.** Os administradores também têm uma página **Backup** no menu da esquerda. Ela baixa um arquivo ZIP por evento, e o botão **Restaurar a partir de backup** traz um evento de volta como um novo rascunho. Isso é útil antes de uma grande mudança em um evento ou para copiar um evento para outro Moimio. As contas dos membros da equipe não vão junto, então você precisaria convidá-los de novo em um servidor novo.

**Vai levar tudo para um servidor novo**, ou trazer os seus eventos do serviço hospedado? Veja [Moving a workspace to your own Moimio](../moving-a-workspace.md) (em inglês).

---

## Solução de problemas

**`docker compose up` falha com "permission denied".**
Você não está no grupo `docker`. Saia da sessão e entre de novo (a instalação adiciona o seu usuário ao grupo, mas isso só vale depois de um novo login) ou use `sudo docker compose up -d --build`.

**O navegador mostra "não é possível acessar este site".**
Três verificações, nesta ordem:
1. O servidor está realmente ligado? Em um VPS, confira no painel do provedor. Na hospedagem própria, o computador precisa estar ligado e conectado.
2. O Moimio está realmente rodando? No servidor: `docker compose ps`. As três linhas (db, backend, frontend) devem mostrar `Up`. Se não, `docker compose logs <service>` mostra o motivo.
3. O firewall está bloqueando? Os provedores de VPS muitas vezes têm uma camada de firewall separada; confira se a porta de que você precisa está aberta.

**O navegador abre a página, mas não consigo entrar (e não aparece a tela de configuração inicial).**
Já existe uma conta. A tela de configuração só aparece quando não existe nenhuma conta. Use o formulário de login. Se você esqueceu a senha e o e-mail não está configurado, pode criar uma segunda conta de Superadministrador pelo servidor (use outro endereço de e-mail), entrar com ela e seguir em frente:

```bash
docker compose exec backend python -m app.cli.create_admin
```

**A página só diz "Não foi possível conectar ao servidor".**
A parte do site do Moimio está rodando, mas a parte que fica por trás dela não está respondendo. Rode `docker compose ps` e confira se a linha `backend` mostra `Up`; se não mostrar, `docker compose logs --tail=50 backend` normalmente diz o motivo.

**O log do backend mostra `password authentication failed`.**
A senha do banco de dados no `.env` foi alterada depois que o Moimio foi iniciado pela primeira vez; o banco de dados continua esperando a original. Coloque a senha original de volta no `.env` e rode `docker compose up -d`.

**O Cloudflare Tunnel não chega ao Moimio.**
No servidor: `sudo systemctl status cloudflared` mostra se o conector está rodando, e `sudo journalctl -u cloudflared -f` mostra o log ao vivo (pressione Ctrl-C para parar de acompanhar). Causa comum: o túnel aponta para `localhost:80`, mas o Moimio está em `localhost:6120`. Atualize a configuração do nome público (public hostname) do túnel.

**Erros de HTTPS depois de configurar o domínio (caminho do Caddy).**
O DNS pode ainda não ter se propagado. Espere 5 minutos e tente de novo. Ou o Caddy ainda não obteve o certificado: `sudo systemctl status caddy` mostra o que ele está fazendo. Os logs ficam em `journalctl -u caddy`.

**Qualquer coisa mais estranha que isso.**
Abra um [relatório de bug](https://github.com/pistio/moimio/issues/new?template=bug_report.md). Inclua:
- O que você estava tentando fazer.
- O que de fato apareceu (a mensagem de erro exata).
- O que `docker compose logs --tail=50 backend` mostra.
- Oculte qualquer dado de participante antes de colar.

---

## Próximos passos

Você instalou o Moimio. Para organizar um evento de fato, o [Manual do usuário](../manual/README.pt-BR.md) mostra como criar um evento, configurar as inscrições, rodar o motor de atribuição, fazer o check-in e exportar as listas.

Se você chegou até aqui sem a ajuda de um programador, fez algo que a maioria das pessoas diria que é "técnico demais para mim". Bem-vindo ao mundo do software auto-hospedado.
