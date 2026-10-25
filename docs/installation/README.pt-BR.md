🌐 [English](README.md) · [Deutsch](README.de.md) · [한국어](README.ko.md) · [Español](README.es.md) · **Português (Brasil)** · [Français](README.fr.md)

# Instalação

Este guia trata da instalação do **Moimio CE (Community Edition)**, a versão de código aberto que você pode hospedar por conta própria. (Para o produto hospedado, basta se cadastrar em [moimio.app](https://moimio.app), sem precisar instalar nada.)

O Moimio CE roda em três contêineres Docker (um backend, um frontend e um banco de dados), orquestrados pelo Docker Compose. A instalação consiste basicamente em: clonar, configurar, rodar `docker compose up --build` (que monta as imagens do Moimio a partir do código-fonte, na sua máquina) e depois criar o primeiro administrador pela tela de configuração.

Há dois guias nesta pasta, conforme a sua experiência. Escolha um.

---

## Qual guia devo seguir?

### → [Guia de instalação rápida](quick-guide.pt-BR.md)

Use este se você já sabe:

- O que é Docker e como rodar comandos `docker compose`.
- Como entrar em um servidor por SSH, editar um arquivo e ler logs.
- Como configurar um proxy reverso com terminação TLS (Caddy, Nginx, Traefik ou um Cloudflare Tunnel).

Tempo necessário: **30 a 60 minutos**, do clone até um administrador logado.

### → [Guia para iniciantes](beginner.pt-BR.md)

Use este se alguma das coisas acima parecer desconhecida. O guia para iniciantes:

- Apresenta as **duas principais opções de hospedagem**: um VPS alugado (servidor na nuvem) ou o seu próprio computador/mini-PC em casa ou no escritório, com Cloudflare Tunnel para o acesso público.
- Ensina do zero a trabalhar com SSH, incluindo a geração de chaves.
- Instala o Docker com o comando oficial de uma linha, sem pressupor nada.
- Configura o Moimio passo a passo, explicando para que serve cada parte.
- Trata de nomes de domínio e de HTTPS com Caddy ou Cloudflare.

Tempo necessário: **cerca de 2 horas** na primeira vez, a maior parte esperando.

Você não precisa ser programador para segui-lo. Precisa estar disposto a copiar os comandos com cuidado e a pedir ajuda quando algo não funcionar.

---

## Quanto vai custar

O custo de hospedagem depende inteiramente de onde você colocar o Moimio.

| Onde | Custo | Ideal para |
|---|---|---|
| Seu próprio notebook / computador (para testar) | Grátis | Experimentar o Moimio e aprender o fluxo. Não serve para eventos reais, porque o notebook precisa ficar ligado. |
| Um mini-PC da igreja, no escritório | Hardware, pagamento único (€150–300) | Uma igreja pequena que realiza alguns eventos por ano. Funciona desde que o escritório tenha energia e internet estáveis. |
| Um VPS alugado em qualquer provedor de nuvem | ~€4–10 por mês | A maioria dos usuários. Sempre ligado, fácil de ampliar. Há opções hospedadas na UE para quem se preocupa com o GDPR. |

Você também vai querer um **nome de domínio** (€10–15 por ano) para ter links de inscrição de verdade; o guia para iniciantes mostra como fazer isso.

---

## Requisitos de hardware

O Moimio é leve. Números de referência:

- **CPU:** qualquer processador x86_64 ou ARM64 moderno. Dois núcleos bastam.
- **RAM:** **mínimo de 2 GB**, 4 GB com folga. O uso de memória cresce pouco conforme aumentam as inscrições simultâneas.
- **Disco:** **5 GB** para as imagens do aplicativo e o banco de dados; o banco em si cresce devagar (o Moimio não armazena arquivos enviados).
- **Rede:** um IP público (ou um túnel como o Cloudflare Tunnel) é necessário para que os participantes acessem o formulário de inscrição. Portas de entrada 80/443 (ou 6120, se você dispensar o TLS para testes). Para eventos reais, planeje usar HTTPS: alguns recursos do aplicativo (cache offline, o aviso de "nova versão disponível") só funcionam com HTTPS ou em `localhost`.

Para verificar se a máquina que você está considerando atende a esses requisitos:

- **CPU + arquitetura:** `uname -m` (Linux/macOS) ou veja "Tipo de sistema" em Sobre (Windows). Qualquer resultado `x86_64`, `aarch64` ou `arm64` serve.
- **RAM:** `free -h` (Linux), Monitor de Atividade (macOS), Gerenciador de Tarefas → Desempenho (Windows).
- **Espaço livre em disco:** `df -h` (Linux/macOS), Explorador de Arquivos → Este Computador (Windows).
- **Acesso público:** se for um VPS, o provedor informa o IP público; se for o seu próprio computador, veja a seção sobre Cloudflare Tunnel no guia para iniciantes.

Um VPS pequeno com 2 vCPU e 2 GB de RAM (normalmente por volta de €4–5/mês em provedores europeus) aguenta um evento de 150 pessoas sem esforço. Um **Raspberry Pi 4 (4 GB)** também funciona para eventos pequenos, rodando no escritório da igreja. Os dois são apenas exemplos: o Moimio não exige nenhum hardware ou provedor de hospedagem específico.

---

## Sistema operacional

Qualquer lugar onde o Docker rode:

- **Linux** (Ubuntu 22.04+, Debian 12+, Fedora, Arch, ...): recomendado para produção.
- **macOS** com Docker Desktop: bom para desenvolvimento; não recomendado para eventos reais, com inscrições de verdade (notebooks não são servidores).
- **Windows** com Docker Desktop e WSL2: mesma ressalva.

---

## Depois da instalação

Quando o Moimio estiver rodando, o seu navegador vai abrir automaticamente a tela de **Configuração inicial**. Preencha seu nome completo, seu e-mail e uma senha (duas vezes), clique em **Criar superadministrador** e depois entre com a conta que acabou de criar. Como ainda não há eventos, você verá a tela **Bem-vindo ao Moimio**, com um botão **Criar seu primeiro evento**.

Duas coisas que vale fazer logo:

- **Defina o link do aviso de privacidade.** Como Superadministrador, abra **Workspace** na barra lateral e informe o endereço do aviso de privacidade da sua organização. O formulário público de inscrição passa a ter um link para ele logo após a frase de consentimento.
- **Planeje atualizações e backups.** Os dois guias têm uma seção curta sobre cada assunto. Em resumo: `./upgrade.sh` atualiza uma instalação feita com git e faz um backup do banco de dados antes; a página **Backup** do aplicativo baixa backups por evento.

Está vindo do serviço hospedado ou de outro servidor? Veja [Moving a workspace to your own Moimio](../moving-a-workspace.md) (em inglês).

A partir daí, o [Manual do usuário](../manual/README.pt-BR.md) mostra como organizar um evento na prática: criar eventos, configurar as inscrições, rodar o motor de atribuição, fazer o check-in, exportar listas.

Se você tiver problemas na instalação, as seções de solução de problemas no fim de cada guia tratam das falhas mais comuns. Para qualquer coisa mais estranha que isso, [abra um relatório de bug](https://github.com/pistio/moimio/issues/new?template=bug_report.md).
