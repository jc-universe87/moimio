🌐 [English](02-events-and-registration.md) · [Deutsch](02-events-and-registration.de.md) · [한국어](02-events-and-registration.ko.md) · [Español](02-events-and-registration.es.md) · **Português (Brasil)** · [Français](02-events-and-registration.fr.md)

# 02 — Eventos e inscrições

Como criar um evento, preencher os detalhes, configurar o formulário de inscrição, abrir as inscrições e acompanhar as inscrições que chegam.

---

## Como criar um evento

Na lista de eventos, clique em **+ Novo evento**. O formulário **Criar evento** é propositalmente enxuto:

- **Nome do evento**: aparece no topo do formulário de inscrição e na sua lista de eventos. Use um nome que as pessoas entendam ("Retiro de Primavera 2026" em vez de "RP2026-EVENTO-001").
- **Usar configurações de outro evento** (opcional, aparece quando você já tem pelo menos um evento): marque a opção, escolha o evento de onde copiar e depois **O que copiar**: **Marcações**, **Formulário de inscrição**, **Campos personalizados**, **Tipos de grupo** (com seus quartos e grupos) e **Membros da equipe**. Os cinco vêm marcados; desmarque o que não quiser. Só a configuração é copiada: nunca participantes, atribuições, check-ins ou notas.

Clique em **Criar evento**. O evento é criado como rascunho e você cai no **painel de configuração**.

Se você começou do zero (sem copiar configurações), dois tipos de grupo já estão esperando por você: **Atribuição de quartos** e **Grupos pequenos**. (Eles aparecem no idioma da sua interface, e você pode renomeá-los ou excluí-los.) Se você copiou tipos de grupo de outro evento, recebe esses no lugar.

Todo o resto (datas, local, descrição, fuso horário, campos do formulário de inscrição, grupos, marcações, equipe) é configurado em seguida, no painel de configuração.

> **Restaurar em vez de criar.** Se você tem um arquivo de backup do Moimio de um evento anterior, o botão **↑ De backup**, ao lado de **+ Novo evento**, recria esse evento como um novo rascunho.

---

## O painel de configuração

<p align="center">
  <br>
  <img src="../assets/setup-hub.png" alt="Painel de configuração com os cinco cartões" width="560">
  <br>
  <em>Painel de configuração com os cinco cartões</em>
</p>

São cinco cartões, cada um uma área de configuração. Clique em um cartão para abri-lo.

| Cartão | O que abrange |
|---|---|
| **Detalhes** | Nome do evento, descrição, local, datas de início e término, fuso horário. |
| **Inscrição** | O formulário público de inscrição: quais campos padrão mostrar e os seus próprios campos personalizados. |
| **Tipos de grupo** | As formas de dividir as pessoas: quartos, grupos pequenos, oficinas (veja a [seção 5](05-group-types-and-units.pt-BR.md)). Já vem com **Atribuição de quartos** e **Grupos pequenos**. Os quartos e grupos de cada tipo são adicionados depois, em **Atribuição**, e não neste cartão. |
| **Marcações** | Opcional. Etiquetas coloridas como "Vegetariano" ou "Líder" (veja a [seção 4](04-marks.pt-BR.md)). |
| **Equipe** | Opcional. Adicione outros usuários ao evento e escolha o que cada um pode acessar (veja a [seção 11](11-staff-permissions.pt-BR.md)). |

Os cartões **Detalhes** e **Inscrição** têm, cada um, um botão **Salvar e confirmar** no fim. **Os dois precisam estar confirmados** para você abrir as inscrições. O cartão **Inscrição** só pode ser confirmado se o evento tiver pelo menos um tipo de grupo; como os dois tipos padrão já vêm prontos, isso só importa se você tiver excluído todos.

Confirmar não é um caminho sem volta: **Desmarcar** reabre um cartão para alterações, e você pode confirmá-lo de novo depois. Esse passo extra só existe para impedir que você abra as inscrições com a configuração pela metade.

> **Datas e horários.** As datas aparecem no formato escolhido em **Preferências**; o seletor de datas segue o seu navegador. Os horários são mostrados no formato 24 horas, no fuso horário do próprio evento.

---

## Como configurar o formulário de inscrição

Abra o cartão **Inscrição**.

### Campos padrão

**Nome**, **Sobrenome**, **E-mail** e a caixa de **consentimento** sempre fazem parte do formulário e não podem ser desativados. Em **Campos padrão** você pode adicionar outros, cada um com duas caixas de seleção:

- **Mostrar**: o campo aparece no formulário.
- **Obrigatório**: o campo precisa ser preenchido (só disponível quando **Mostrar** está marcado).

As alterações são salvas automaticamente.

| Campo | Observações |
|---|---|
| Gênero | A pessoa escolhe **Masculino** ou **Feminino**. O motor de atribuição usa isso nos grupos restritos a um único gênero. |
| Data de nascimento | Útil em retiros com grupos por faixa etária. |
| Telefone | |
| Endereço | |
| País | Útil em eventos internacionais. |
| Igreja / Organização | Útil quando os participantes vêm de várias igrejas ou organizações. |

Todo formulário também tem um campo opcional **Mensagem aos organizadores** (para restrições alimentares, acessibilidade e coisas do tipo) e uma caixa de consentimento. Se um Superadministrador tiver definido uma **URL do aviso de privacidade** em **Gerenciar ▸ Workspace**, um link **Aviso de privacidade** aparece logo após a frase de consentimento.

### Campos personalizados

Para o que os campos padrão não cobrem, clique em **+ Adicionar campo**, em **Campos personalizados**. Escolha:

- **Nome do campo**: o que a pessoa vê ("Tamanho da camiseta", "Você já veio antes?").
- **Tipo**: **Texto**, **Número**, **Lista suspensa**, **Sim/Não**, **Data** ou **Texto informativo**.
- **Obrigatório**: se o campo precisa ser preenchido.
- **Opções**: para **Lista suspensa**, as alternativas separadas por vírgula (por exemplo, `S, M, L, XL`).
- **Mostrar no formulário de registro**: desmarque para um campo que só a sua equipe preenche (ele continua aparecendo na tabela Participantes).

Clique em **Adicionar campo personalizado** para salvar.

Campos personalizados comuns:

- "Tamanho da camiseta" (Lista suspensa: PP, P, M, G, GG, XGG)
- "Você é líder de grupo pequeno?" (Sim/Não)
- "É sua primeira vez neste evento?" (Lista suspensa: Sim, Não, Já vim uma vez)
- "Restrições alimentares" (Texto ou Lista suspensa, dependendo de quão fixo é o cardápio)
- "Autorização de uso de imagem" (Sim/Não, para usar a imagem do participante nas fotos do evento)

Os campos personalizados pertencem a um único evento: adicionar "Tamanho da camiseta" aqui não o adiciona aos seus outros eventos. Você pode editar ou excluir um campo depois que as inscrições começaram, mas **excluir um campo também exclui todas as respostas já dadas a ele**.

> **Reaproveitar um formulário.** O menu **⋯** no topo do cartão tem **Exportar formulário** e **Importar formulário**, para você salvar um formulário em um arquivo e carregá-lo em outro evento (ou em outra instalação do Moimio). A importação nunca duplica campos que você já tem.

#### Textos informativos

Um **Texto informativo** é um aviso seu no formulário, como instruções de como chegar ou um lembrete. Ninguém preenche, então ele não tem a caixa **Obrigatório**. Dê a ele um título e o texto. As quebras de linha são mantidas. Para um link, cole o endereço da web ou escreva `[texto do link](https://example.org/formulario.pdf)` para mostrar suas próprias palavras. Os links abrem em uma nova aba.

#### Mostrar um campo só quando ele se aplica

Marque **Mostrar somente se…** em um campo para que ele apareça só quando uma resposta anterior combinar:

- um campo de **Sim/Não** acima dele tem a resposta que você escolher. Exemplo: "Monitor" é **Sim**, então aparece "Qual equipe?".
- um campo de **Lista suspensa** acima dele tem uma das opções que você marcar.
- a pessoa tem menos do que a idade que você definir, pela **Data de nascimento**. A idade é calculada na data de início do evento, ou no dia do registro se o evento não tiver data de início. A **Data de nascimento** precisa estar ativada nos campos padrão.

Um campo oculto nunca é obrigatório, e uma resposta digitada antes de o campo voltar a ficar oculto não é salva. Em uma inscrição familiar, cada pessoa adicional é verificada separadamente: uma jovem de 15 anos vê o aviso para menores de 18, o pai dela não.

Um **Texto informativo** com condição também ganha uma coluna em **Participantes** (marcada desde o início) e no **Check-in** (ative em **Colunas**). Ela mostra **Aplica-se** para todas as pessoas a quem o aviso se destinava, para a recepção ver quem precisa trazer, por exemplo, uma autorização assinada. Se você corrigir a data de nascimento de alguém ou mudar a data de início do evento, a coluna acompanha.

Use **↑** e **↓** para mudar a ordem dos seus campos personalizados. Um campo só pode depender de um campo acima dele, então uma mudança de ordem que quebraria isso é recusada com uma mensagem. Pelo mesmo motivo, um campo do qual outro depende só pode ser excluído depois que essa condição for removida.

### Códigos de grupo: famílias e amigos juntos

Todo formulário tem uma seção **Vem com família ou amigos?**. A pessoa escolhe uma destas opções:

- **Venho sozinho(a)**
- **Sou o primeiro do meu grupo a me registrar**: o Moimio cria um novo código de grupo para ela (com base no sobrenome, por exemplo `SMITH-742`) e o inclui no e-mail de confirmação, para que ela possa repassá-lo.
- **Tenho um código de grupo**: a pessoa digita o código que recebeu (por exemplo, `KIM-104`) e fica com aquele grupo.
- **Sim, mas não tenho o código, apenas o nome**: só aparece se você ativou **Permitir preferências de grupo** (veja abaixo). A pessoa digita um nome e alguns detalhes, e você junta as pessoas manualmente.

Todos que compartilham um código de grupo formam um grupo que o motor de atribuição tenta manter junto. Veja a [seção 5](05-group-types-and-units.pt-BR.md) para entender todo o funcionamento.

Os códigos de grupo têm o formato `STEM-NNN`: até oito letras do sobrenome (ou de um nome que a pessoa escolher), um hífen e um número. Os acentos são removidos, então Müller vira `MULLER` e García vira `GARCIA`; um sobrenome sem letras latinas (por exemplo, 김) recebe `GROUP`. Mesmo quem se inscreve sozinho recebe um código, normalmente com um número de três dígitos (mais longo só se muitas pessoas no evento tiverem o mesmo sobrenome). Ao inscrever várias pessoas de uma vez, cada pessoa a mais pode usar o mesmo código da primeira (recomendado para famílias), ficar sem código ou usar outro.

---

## Como abrir as inscrições

No fim do painel de configuração fica o quadro **Abrir inscrições**. Enquanto **Detalhes** e **Inscrição** não estiverem confirmados, ele mostra *"Confirme os Detalhes e a Inscrição para desbloquear."* e o botão fica cinza. Depois de confirmados, ele muda para **Pronto para abrir as inscrições →**. Clique nele.

O evento passa de rascunho para aberto, você está na fase de **Inscrição** e o formulário público de inscrição está no ar.

Para encontrar o link público, clique em **Compartilhar formulário**, no topo da página **Inscrição** (o primeiro item da barra lateral). Você verá:

- Um QR code para cartazes e boletins impressos.
- O **Link do formulário** (por exemplo, `https://events.yourchurch.org/register/abc-123-def`), com os botões **Copiar** e **Abrir ↗**.
- **Compartilhar…**, em celulares e tablets, para enviar direto a um aplicativo de mensagens.

Divulgue esse link do jeito que você costuma alcançar os participantes: e-mail, boletim da igreja, grupo de WhatsApp, site da igreja. Ele é o mesmo durante toda a vida do evento. Para incorporar o formulário no seu site, use o **Código de incorporação**, em **Mais ▸ Formulário de inscrição ▸ Compartilhar inscrição**.

### Configurações disponíveis depois da abertura

Com as inscrições abertas, **Mais ▸ Formulário de inscrição** reúne tudo o que havia no cartão Inscrição e mais alguns extras:

- **Permitir preferências de grupo**: permite que as pessoas indiquem com quem gostariam de ficar, mesmo sem um código de grupo. Você analisa esses pedidos antes de fazer a atribuição.
- **Personalizar aparência**: **Abrir personalizador** para mudar as cores, a fonte e o estilo dos cantos do formulário.
- **Confirmação por e-mail**: **Exigir confirmação por e-mail para inscrições** (desativado por padrão), o **Nome do remetente**, o **E-mail de resposta (Reply-To)** e **Enviar e-mail de teste**, para verificar se o e-mail funciona. Clique em **Salvar configurações de e-mail** depois de alterar.

Se você quer a confirmação por e-mail, ative-a logo depois de abrir as inscrições, antes de divulgar o link.

### Acompanhando as inscrições

A página **Inscrição** mostra quantas pessoas estão **Inscritos**, com os números de **Confirmados**, **Pendentes** e **Cancelados**, um gráfico das inscrições nos **Últimos 7 dias**, **Últimos 30 dias** ou **Desde a abertura**, um quadro **Requer atenção** (por exemplo, pessoas que ainda não confirmaram o e-mail) e uma lista de **Inscrições recentes**. Ela se atualiza sozinha conforme as pessoas se inscrevem, sem precisar recarregar. **Ver todos os participantes** leva você à tabela Participantes ([seção 03](03-people.pt-BR.md)).

---

## O que os participantes veem ao se inscrever

<p align="center">
  <img src="../assets/public-registration-form.png" alt="Formulário público de inscrição" width="420">
  <br>
  <em>Formulário público de inscrição</em>
</p>

Os participantes chegam a um formulário limpo, com o nome, a descrição, o local e a data do seu evento. Eles:

1. Escolhem o idioma no seletor 🌐, no pé da página, se precisarem (o formulário está disponível nos mesmos seis idiomas da área administrativa).
2. Preenchem os campos que você configurou e escolhem uma opção em **Vem com família ou amigos?**.
3. Marcam a caixa de consentimento (e podem abrir o seu **Aviso de privacidade**, se você tiver definido um).
4. Clicam em **Inscrever-se**.

Para inscrever várias pessoas de uma vez (uma família, um grupo de jovens), eles clicam em **+ Registrar outra pessoa**. Cada pessoa a mais ganha o seu próprio cartão, com o atalho **Copiar dados de …**, e o botão passa a ser **Registrar 2 pessoas** (3, 4, …).

Se algo estiver faltando ou errado, o formulário avisa no idioma da própria pessoa, ao lado do campo que precisa ser corrigido.

O que acontece depois depende da sua configuração de **Confirmação por e-mail**:

- **Desativada (o padrão).** A inscrição é **confirmada** na hora. A pessoa vê **Inscrição concluída** e recebe um e-mail com o código de grupo (se o seu servidor puder enviar e-mails).
- **Ativada.** A inscrição começa como **pendente**. A pessoa vê **Verifique seu e-mail** e recebe um e-mail com um link de confirmação. Quando ela clica, a inscrição passa a **confirmada**, ela vê **Confirmado!** e recebe um segundo e-mail com o código de grupo.

Se o seu servidor não estiver configurado para enviar e-mails (SMTP) e a confirmação estiver ativada, os e-mails simplesmente não são enviados e essas inscrições continuam **pendentes**, porque ninguém consegue clicar em um link que nunca recebeu. Confirme essas pessoas manualmente na página Participantes ou ative **Incluir participantes não confirmados** nas configurações do motor de atribuição. Se o e-mail de alguém se perdeu, a página Participantes também tem um botão **Reenviar**, que manda o e-mail de inscrição de novo.

---

## Como fechar as inscrições

As inscrições **não fecham automaticamente** quando a data de início chega. É sempre você quem fecha.

- **Durante a fase de Inscrição:** clique em **Fechar inscrições →** na página **Inscrição**.
- **Depois que o evento começou:** um aviso **As inscrições ainda estão abertas** aparece no topo de **Atribuição** (*"As pessoas ainda podem se inscrever enquanto o evento está acontecendo."*), com um botão **Fechar inscrições**.

Depois de fechar, o aviso no topo de **Atribuição** passa a mostrar **As inscrições estão fechadas**, com um botão **Reabrir inscrições**. Você pode reabrir a qualquer momento, mesmo depois que o evento começou; é útil para quem chega atrasado ou para visitantes de um dia que se inscrevem na porta.

Enquanto as inscrições estão fechadas, quem tentar enviar o formulário vê a mensagem *"As inscrições não estão abertas para este evento."*

---

## Erros comuns nesta fase

- **Esquecer de confirmar o cartão Detalhes.** A pessoa configura o formulário de inscrição, clica em **Salvar e confirmar** e não entende por que o botão de abrir as inscrições continua cinza. **Detalhes** e **Inscrição** precisam estar confirmados.
- **Adicionar campos personalizados obrigatórios depois que as inscrições abriram.** Quem já se inscreveu não terá respondido a eles. As novas inscrições funcionam normalmente, mas você vai precisar correr atrás das informações que faltam nas anteriores.
- **Não testar o envio de e-mails.** Antes de divulgar o link amplamente, use **Mais ▸ Formulário de inscrição ▸ Confirmação por e-mail ▸ Enviar e-mail de teste** para verificar se o e-mail funciona e depois preencha o seu próprio formulário para um teste completo, do início ao fim.

---

## Próximos passos

A [seção 03 — Participantes](03-people.pt-BR.md) mostra o que fazer com as inscrições depois que elas começam a chegar: a tabela Participantes, os status, as edições, as confirmações manuais e os códigos de grupo do lado da administração.
