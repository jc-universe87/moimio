🌐 [English](01-getting-started.md) · [Deutsch](01-getting-started.de.md) · [한국어](01-getting-started.ko.md) · [Español](01-getting-started.es.md) · **Português (Brasil)** · [Français](01-getting-started.fr.md)

# 01 — Primeiros passos

Esta seção trata das partes do Moimio que você vai usar na primeira sessão: a configuração inicial, o layout da área administrativa, a lista de eventos, o modelo de fases que comanda todo o resto e o básico do gerenciamento de usuários.

---

## Configuração inicial (ainda sem usuários)

<p align="center">
  <img src="../assets/first-time-setup.png" alt="Tela de configuração inicial para a primeira conta de Superadministrador" width="420">
  <br>
  <em>Tela de configuração inicial para a primeira conta de Superadministrador</em>
</p>

Quando você acessa um Moimio recém-instalado, ainda não há nenhum usuário no sistema. Ao abrir o endereço, você vai direto para a tela de **Configuração inicial**. Antes de começar, você pode trocar o idioma no seletor 🌐 abaixo do formulário.

Preencha:

- **Nome completo**: o nome que aparece na área administrativa.
- **E-mail**: o seu login.
- **Senha** e **Confirmar senha**: no mínimo 8 caracteres. Use um bom gerenciador de senhas.

Clique em **Criar superadministrador**. Sua conta é criada com a função de **Superadministrador** e acesso total, e você já entra no sistema.

A tela de configuração aparece uma única vez. Assim que existe algum usuário, essa etapa é desativada e o endereço passa a mostrar a página de login normal.

> **Alternativa: configuração pela linha de comando.** Se você preferir criar o primeiro administrador pelo terminal (por exemplo, em instalações automatizadas ou sem interface), o projeto também traz uma ferramenta de linha de comando: `docker compose exec backend python -m app.cli.create_admin`. Os dois caminhos levam ao mesmo resultado; a configuração pela tela é a opção recomendada.

---

## Como entrar (depois da configuração inicial)

A página de login fica em `/login` (por exemplo, `https://events.yourchurch.org/login`). Digite seu e-mail e sua senha e clique em **Entrar**. O seletor 🌐 abaixo do formulário muda o idioma; o botão de sol/lua no canto superior direito alterna entre o modo claro e o escuro.

Se você esqueceu a senha, clique em **Esqueceu sua senha?**, digite seu e-mail e clique em **Enviar link de redefinição**. O link do e-mail expira em 30 minutos. Isso só funciona se o seu servidor tiver e-mail (SMTP) configurado. Se não tiver, não existe no aplicativo um botão para os administradores redefinirem a senha: um Superadministrador pode excluir sua conta e criá-la de novo (aí você precisará ser adicionado outra vez aos seus eventos), ou você pode pedir ajuda a quem cuida do servidor.

---

## O layout da área administrativa

Depois do login, a área administrativa tem duas partes:

- **Barra lateral** (à esquerda): toda a navegação fica aqui. O conteúdo muda conforme o evento em que você está, a fase desse evento e o que você tem permissão para fazer.
- **Área principal**: o que você tiver aberto.

**Não há barra superior.** No celular ou em uma janela estreita, a barra lateral se recolhe; toque no botão **≡** no canto superior esquerdo para abri-la de novo (no computador, o **◀** no topo da barra lateral a recolhe).

De cima para baixo, a barra lateral tem:

1. **Navegação.** Na lista de eventos, aparece apenas **Eventos**. Dentro de um evento, você tem o link **Todos os eventos**, que volta para a lista, e depois os itens do próprio evento (veja "As três fases" abaixo).
2. **Gerenciar**: ferramentas do workspace, visíveis só para quem pode usá-las:
   - **Usuários**: criar e gerenciar as contas da equipe (Superadministradores e membros da equipe com permissão para gerenciar usuários).
   - **Backup**: baixar backups de eventos ou restaurar um (Superadministradores).
   - **Webhooks**: enviar atualizações de atribuição para outro sistema que você mantém (Superadministradores, apenas na versão auto-hospedada).
   - **Workspace**: configurações de todo o workspace (Superadministradores). É aqui que você informa a **URL do aviso de privacidade** da sua organização: depois de preenchida, o formulário público de inscrição mostra um link **Aviso de privacidade** logo após a frase de consentimento. Se deixar em branco, nenhum link aparece.
3. **Seu nome e sua função** (por exemplo, *Superadministrador*).
4. **Ver tour de boas-vindas**: abre de novo a apresentação "Bem-vindo ao Moimio".
5. **Preferências**: abre um pequeno painel com **Idioma**, **Formato de data** e **Fuso horário**. Clique em **Salvar** para guardar. O formato de data vale para todas as datas da área administrativa (são seis formatos, como DD/MM/AAAA ou AAAA-MM-DD); o seu fuso horário passa a ser o padrão dos novos eventos que você criar.
6. **Sair**.
7. **Versão e informação legal** (por exemplo, `v1.0.6 · © Pistio`) e o botão de **modo claro/escuro**. Clicar na linha da versão abre o **Aviso legal**, que mostra os termos da licença do software e um botão **Limpar cache e recarregar** (veja abaixo).

### Como manter o aplicativo atualizado

Quando o seu servidor é atualizado, o Moimio mostra no canto da tela um cartão **Atualização disponível** ("Uma nova versão do Moimio está pronta."). Clique em **Atualizar** para carregar a nova versão. Se algo parecer travado ou desatualizado e esse cartão nunca aparecer, abra o **Aviso legal** (clicando na linha da versão, no pé da barra lateral) e clique em **Limpar cache e recarregar**.

Em celulares e tablets, também pode aparecer um aviso **Instalar Moimio**, oferecendo adicionar o aplicativo à tela inicial. Isso é opcional; **Agora não** fecha o aviso.

---

## As três fases

Todo evento está sempre em uma de três fases. A fase define o que a barra lateral mostra e quais ações estão disponíveis. Uma faixa colorida no topo do painel de configuração mostra em que ponto o evento está.

### Fase de Configuração

O evento é um **rascunho**. Você está configurando os detalhes do evento, o formulário de inscrição, os tipos de grupo, as marcações e a lista da equipe. O formulário público de inscrição **ainda não** aceita inscrições.

Barra lateral na Configuração: apenas **Configuração**, que abre o painel de configuração com seus cinco cartões.

### Fase de Inscrição

As inscrições estão **abertas** e a data de início ainda não chegou. O formulário público de inscrição está no ar; os participantes se inscrevem e você acompanha os números crescerem.

Barra lateral na Inscrição: **Inscrição** (a página de visão geral, com os números de inscrições e o botão **Compartilhar formulário**), **Atribuição**, **Participantes**, **Relatórios** e um menu **Mais** para o que se usa de vez em quando: **Detalhes do evento**, **Formulário de inscrição**, **Marcações** e **Equipe e permissões** (este último só se você puder gerenciar usuários).

### Fase de Evento

As inscrições estão **fechadas**, ou ainda estão abertas mas a data de início já chegou. O foco deixa de ser receber inscrições e passa a ser realizar o evento.

A fase de Evento tem três subestados, calculados automaticamente a partir das datas:

- **Antes do início**: as inscrições estão fechadas e a data de início ainda não chegou. É aqui que se fazem os últimos ajustes na atribuição.
- **Em andamento**: hoje está entre a data de início e a data de término (inclusive). O foco é o check-in.
- **Concluído**: a data de término já passou. Relatórios, exportações, arquivamento.

Barra lateral na fase de Evento: **Atribuição**, **Participantes**, **Relatórios** e o mesmo menu **Mais**. O check-in é aberto pelo botão **Abrir modo de check-in →** no topo de **Atribuição** (visível para administradores até o evento ser concluído).

Membros da equipe que não são administradores do evento veem uma barra lateral mais simples, só com as áreas a que têm acesso: **Participantes**, **Atribuição**, **Check-in**, **Relatórios** e/ou **Marcações**. Veja a [seção 11](11-staff-permissions.pt-BR.md).

### Como as mudanças de fase funcionam

A fase vem do status do evento combinado com o calendário:

- Rascunho → fase de Configuração.
- Aberto, data de início no futuro → fase de Inscrição.
- Aberto, data de início hoje ou antes → fase de Evento (automático, sem precisar clicar).
- Fechado → fase de Evento.

O status em si só muda quando você age:

- **Rascunho → aberto** acontece quando você clica em **Pronto para abrir as inscrições →**, no fim do painel de configuração. O botão só fica disponível depois que os cartões **Detalhes** e **Inscrição** estiverem confirmados.
- **Aberto → fechado** acontece quando você clica em **Fechar inscrições**: na página de visão geral **Inscrição**, durante a fase de Inscrição, ou no aviso **As inscrições ainda estão abertas**, no topo de **Atribuição**, depois que o evento começou.
- **Fechado → aberto** é possível a qualquer momento com **Reabrir inscrições**, no aviso **As inscrições estão fechadas** no topo de **Atribuição**.
- **Não** há como voltar para rascunho depois que as inscrições foram abertas.

**Arquivar não tem nada a ver com o status.** Eventos nunca são arquivados automaticamente. Um Superadministrador arquiva um evento pelo menu **⋯** na lista de eventos ou em **Mais ▸ Detalhes do evento ▸ Zona de perigo ▸ Arquivar** (na fase de Configuração, a mesma **Zona de perigo** fica no fim do painel de configuração). Um evento arquivado fica somente para leitura para todos, inclusive Superadministradores, não recebe novas inscrições e vai para a aba **Arquivados**. Dá para desfazer: **Desarquivar**, nos mesmos lugares.

---

## Gerenciamento de usuários

O resto da sua equipe (organizadores, voluntários, pessoal da porta) é adicionado na página **Usuários**, em **Gerenciar**, na barra lateral. A sua primeira conta de Superadministrador sempre tem acesso a ela.

Na página Usuários você pode:

- **Criar usuários**: clique em **+ Novo usuário**, preencha **Nome completo**, **E-mail**, **Senha** (pelo menos 8 caracteres) e **Função** e clique em **Criar usuário**. Passe a senha para a pessoa você mesmo; o Moimio não a envia por e-mail.
- **Editar usuários**: o ícone de lápis permite mudar nome, função e permissões extras. (O endereço de e-mail não pode ser alterado aqui.)
- **Desativar / Reativar**: um usuário desativado não consegue entrar, mas a conta e os dados dele são mantidos. Use quando alguém vai se afastar por um tempo.
- **Excluir**: o ícone vermelho de lixeira remove permanentemente a conta e todas as atribuições dessa pessoa em eventos. Não dá para desfazer. As notas que ela compartilhou com a equipe permanecem, identificadas como escritas por um usuário removido.

Há duas funções:

- **Superadministrador**: acesso total a todos os eventos, todos os usuários e todas as configurações.
- **Equipe**: vê apenas os eventos para os quais foi designado, com o acesso que recebeu em cada um.

Um usuário da Equipe também pode receber duas permissões extras, independentes entre si:

- **Permitir que este administrador gerencie usuários**: dá acesso à página **Usuários**.
- **Pode criar novos eventos**: dá acesso ao botão **+ Novo evento**. Quem cria um evento se torna automaticamente **Administrador do evento** (acesso total) daquele evento.

Depois que a conta existe, você adiciona a pessoa a um evento específico de dentro desse evento: pelo cartão **Equipe** no painel de configuração ou, mais tarde, em **Mais ▸ Equipe e permissões**. Ali você escolhe se ela será **Administrador do evento** (acesso total àquele evento) ou **Equipe**, com acesso a áreas específicas. Veja a [seção 11](11-staff-permissions.pt-BR.md) para o modelo completo de permissões.

Um usuário da Equipe que ainda não foi adicionado a nenhum evento vê, depois de entrar, a página **Aguardando sua primeira atribuição**, com um botão **Atualizar**.

---

## A lista de eventos

<p align="center">
  <br>
  <img src="../assets/events-list.png" alt="Lista de eventos com as abas Ativos / Passados / Arquivados" width="560">
  <br>
  <em>Lista de eventos com as abas Ativos / Passados / Arquivados</em>
</p>

Depois do login, a primeira página é a lista de eventos. Superadministradores veem todos os eventos; os demais veem apenas os eventos para os quais foram designados ou que criaram.

Cada cartão de evento mostra:

- O nome do evento, as datas e o local.
- Uma etiqueta colorida com a fase: **Configuração**, **Inscrição**, **Evento**, **Passado** ou **Arquivado**.
- Uma etiqueta **Admin** se você for o Administrador do evento.
- Um número de destaque conforme a fase: cartões confirmados (Configuração, por exemplo "1 / 2"), pessoas inscritas (Inscrição), pessoas com check-in feito (Evento) ou participantes presentes, nos eventos passados.

Clique em um cartão para abrir o evento. A barra lateral passa a mostrar os itens daquele evento.

Você também pode:

- **Criar um novo evento** com **+ Novo evento** (Superadministradores e membros da equipe que podem criar eventos).
- **Restaurar um evento a partir de um backup** com **↑ De backup**, ao lado.
- **Buscar** eventos pelo nome.
- **Alternar entre as abas** **Ativos**, **Passados** (a data de término já passou) e **Arquivados**.
- Usar o menu **⋯** de um cartão (Superadministradores) para **Fixar no topo**, **Arquivar** / **Desarquivar** ou **Excluir evento**. Os eventos fixados ficam no topo da aba Ativos.

Para reaproveitar a configuração de um evento anterior, marque **Usar configurações de outro evento** ao criar o novo; veja a [seção 02](02-events-and-registration.pt-BR.md).

---

## Sua primeira sessão: o que fazer

<p align="center">
  <img src="../assets/welcome-splash.png" alt="Cartão Bem-vindo ao Moimio, exibido enquanto ainda não há eventos" width="560">
  <br>
  <em>Cartão Bem-vindo ao Moimio, exibido enquanto ainda não há eventos</em>
</p>

Enquanto não há nenhum evento, a lista de eventos mostra um cartão **Bem-vindo ao Moimio** que explica as três fases, com um botão **Criar seu primeiro evento**. Você pode abri-lo de novo quando quiser com **Ver tour de boas-vindas**, na barra lateral.

Depois:

1. **Defina idioma, formato de data e fuso horário** em **Preferências**, no pé da barra lateral, e clique em **Salvar**.
2. **(Superadministradores)** Adicione o link do aviso de privacidade da sua organização em **Gerenciar ▸ Workspace ▸ URL do aviso de privacidade**, para que ele apareça em todos os formulários de inscrição.
3. **Crie seu primeiro evento** para explorar o painel de configuração. Você sempre pode excluí-lo depois.
4. **(Opcional)** Crie contas para o resto da equipe na página **Usuários**.

A próxima seção ([Eventos e inscrições](02-events-and-registration.pt-BR.md)) mostra em detalhes como criar um evento.

---

## Dois termos que você vai ver em todo lugar

**Participante** e **usuário** são coisas diferentes no Moimio.

- Um **participante** é alguém inscrito em um evento. Ele não tem login: existe como uma linha na sua tabela Participantes. Ele preenche o formulário de inscrição, recebe e-mails e faz check-in. Nunca vê a área administrativa.
- Um **usuário** é alguém que tem login: você e o resto da equipe organizadora. Todo usuário tem uma função (**Superadministrador** ou **Equipe**). Dentro de um evento específico, um usuário da Equipe é **Administrador do evento** (acesso total àquele evento) ou **Equipe**, com acesso a áreas selecionadas. Veja a [seção 11](11-staff-permissions.pt-BR.md) para o modelo completo.

Não confunda os dois ao ler o resto do manual. Participantes = as pessoas que vêm ao evento. Usuários = as pessoas que organizam o evento.
