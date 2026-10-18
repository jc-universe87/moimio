🌐 [English](05-group-types-and-units.md) · [Deutsch](05-group-types-and-units.de.md) · [한국어](05-group-types-and-units.ko.md) · [Español](05-group-types-and-units.es.md) · **Português (Brasil)** · [Français](05-group-types-and-units.fr.md)

# 05 — Tipos de grupo e grupos

O motor de atribuição coloca os participantes em **grupos** (os quartos, grupos, mesas ou oficinas individuais), que são organizados em **tipos de grupo**. Esta seção explica os dois: o que são, como configurá-los e as escolhas que definem o comportamento mais tarde.

Durante a Configuração, é no cartão **Tipos de grupo** do painel de configuração que você cria e edita os tipos de grupo (é preciso ter pelo menos um para abrir as inscrições). Depois, e também para adicionar os quartos e grupos propriamente ditos, use a página **Atribuição**.

---

## O modelo em um parágrafo

Um **tipo de grupo** é uma forma de atribuição. Ele contém **grupos**: os quartos, grupos, oficinas ou equipes específicos dentro dele. Assim, "Atribuição de quartos" é um tipo de grupo; "Suíte Vista do Lago" é um grupo dentro dele. Um participante é colocado em um grupo, ou em vários, dependendo da regra do tipo de grupo. No aplicativo, os grupos são chamados pelo rótulo que o próprio tipo de grupo define ("Quarto", "Grupo", "Mesa"…), então você vai ver botões como **+ Adicionar Quarto**.

---

## Com o que você começa

Todo evento novo é criado com dois tipos de grupo já prontos:

- **Atribuição de quartos**: um quarto por pessoa, ainda sem nenhum quarto dentro.
- **Grupos pequenos**: um grupo por pessoa, ainda sem nenhum grupo dentro.

Esses dois tipos de grupo padrão acompanham o idioma em que cada organizador está trabalhando (por exemplo, "Zimmerbelegung" e "Kleingruppen" em alemão), e as listas impressas usam o idioma do PDF. Assim que você renomeia um deles, o nome que você deu fica valendo em todos os idiomas. Se você digitar de volta um nome padrão (por exemplo, "Atribuição de quartos"), ele volta a ser traduzido.

Você pode renomeá-los, excluí-los ou criar outros tipos de grupo ao lado deles. Se você criar um evento copiando a configuração de um evento anterior, recebe os tipos de grupo daquele evento no lugar.

---

## Como criar e editar tipos de grupo

Na página **Atribuição**, clique em **+ Adicionar tipo de grupo**. (No painel de configuração, abra o cartão **Tipos de grupo** e clique em **+ Adicionar tipo de grupo** ali.) Você define:

### Nome do tipo de grupo

Como o tipo de grupo se chama (por exemplo, "Quartos", "Grupos pequenos", "Mesas"). Aparece na página Atribuição e nos relatórios. Use as palavras que a sua equipe usaria.

### Nome

A palavra para **um** grupo deste tipo, por exemplo "Quarto", "Equipe" ou "Sessão". Ela é usada em botões e rótulos ("+ Adicionar Quarto", "4 × Quarto"). Se você deixar em branco, o Moimio simplesmente usa "Grupo".

### Uma pessoa pode estar em mais de um?

- **Não, apenas um** (por exemplo, quartos): um participante pertence a **um** grupo deste tipo. Quartos são o exemplo clássico: você dorme em um quarto, não em três. O mesmo vale para mesas, equipes de trabalho e grupos pequenos.
- **Sim, vários**: um participante pode pertencer a **vários** grupos deste tipo. Oficinas são o exemplo clássico: alguém pode participar de várias ao longo do evento. O mesmo vale para sessões, turnos e atividades opcionais.

Se estiver em dúvida, pergunte: "Essa pessoa poderia, legitimamente, estar em dois destes ao mesmo tempo?" Se sim, escolha **Sim, vários**.

Clique em **Criar**. O tipo de grupo aparece como um cartão na página Atribuição, mostrando quantos grupos ele tem e quantas pessoas estão atribuídas, sem atribuição e não incluídas.

Para alterar um tipo de grupo depois, use os controles do cartão:

- **Clique no título** para renomeá-lo ali mesmo (Enter salva, Esc cancela).
- **Ícone de lápis**: abre o editor com os mesmos três campos.
- **↑ ↓** (ou arraste o cartão, no computador): muda a ordem dos tipos de grupo.
- **Ícone vermelho de lixeira**: exclui o tipo de grupo. O aviso é bem direto: o tipo de grupo, tudo o que há nele e todas as atribuições de participantes dentro dele são removidos permanentemente. Não dá para desfazer.

### Como exportar e importar uma estrutura

O menu **⋯** ao lado de **+ Adicionar tipo de grupo** tem **Exportar tipos de grupo** e **Importar tipos de grupo**. A exportação salva todos os tipos de grupo do evento, com seus grupos, capacidades, regras de gênero, restrições por marcação e configurações do motor, em um arquivo JSON. Importe esse arquivo em outro evento (até mesmo em outro servidor Moimio) para reaproveitar a estrutura. O arquivo contém só a configuração, nunca dados de participantes.

Bom saber:

- A importação **adiciona** os tipos de grupo do arquivo; ela nunca sobrescreve nem mescla com o que já existe. Importar em um evento novo dá a você os tipos de grupo do arquivo *mais* os dois padrão, então exclua o que não precisar. Importar o mesmo arquivo duas vezes gera duplicatas.
- As restrições e as prioridades de marcações são associadas pelo nome da marcação. Se o evento de destino tiver uma marcação com o mesmo nome, elas se conectam; se não tiver, são descartadas.
- As descrições e as notas dos grupos não são incluídas.

### Configurações do motor

Cada tipo de grupo tem as suas próprias configurações do motor, abertas pelo ícone ⚙ **Configurações do motor**, ao lado do botão **Atribuir automaticamente**, dentro do tipo de grupo. Elas aparecem na ordem em que o motor as aplica:

- **Incluir participantes não confirmados** (padrão: ativado)
- **Manter códigos de grupo juntos** (padrão: ativado)
- **Dividir códigos de grupo se necessário** (padrão: ativado; fica cinza enquanto Manter códigos de grupo juntos estiver desativado)
- **Um código de grupo ocupa um grupo inteiro** (padrão: desativado)
- **Aplicar as marcações nesta ordem** (veja a [seção 4](04-marks.pt-BR.md))
- **Manter juntas as pessoas do mesmo gênero** (padrão: ativado)
- **Equilibrar o tamanho dos grupos** (padrão: ativado)

Você pode mudá-las a qualquer momento; rode Atribuir automaticamente de novo para aplicá-las. O que cada uma faz está explicado na [seção 6](06-allocation-engine.pt-BR.md).

### Como confirmar um tipo de grupo

Quando estiver satisfeito com a atribuição de um tipo de grupo, clique em **Confirmar tipo de grupo** no cartão dele (ou em **Confirmar este tipo de grupo →**, dentro dele, quando todos estiverem atribuídos). O indicador de status muda para **Confirmado** para toda a equipe. Isso é um sinal, não um bloqueio: qualquer edição posterior o reabre automaticamente, e **Reabrir para editar** faz isso manualmente. Veja a [seção 6](06-allocation-engine.pt-BR.md).

---

## Grupos dentro de um tipo de grupo

Depois que o tipo de grupo existe, adicione os grupos dele. Na página **Atribuição**, clique no cartão do tipo de grupo para abri-lo e depois em **+ Adicionar Quarto** (ou o que estiver no seu rótulo **Nome**).

Para cada grupo, você define:

### Nome

Como o grupo se chama. Use nomes que façam sentido para os participantes: "Suíte Vista do Lago" em vez de "Quarto 3", "Equipe Vermelha" em vez de "Equipe A", "Oficina de Cerâmica" em vez de "Oficina 2". Os nomes saem nas listas e nas folhas de presença. Você também pode clicar no nome de um grupo, no cartão, para renomeá-lo ali mesmo.

### Descrição

Uma linha curta e opcional para a sua equipe, por exemplo "Tem beliches" ou "Acessível para cadeira de rodas". Ela não sai nas listas impressas.

### Capacidade

O número máximo de pessoas. Digite um número ou deixe em branco: um campo vazio marca **Sem limite de capacidade**, e aquele grupo aceita qualquer número de pessoas. Digitar um número desmarca a opção; marcá-la apaga o número.

Os grupos com capacidade mostram a ocupação, por exemplo `5/6`; os grupos sem limite mostram só a contagem. O motor nunca enche um grupo além da capacidade. Quando você coloca alguém manualmente em um grupo cheio, o Moimio pergunta antes de exceder a capacidade, e um grupo lotado além do limite aparece marcado como **acima da capacidade**.

### Gênero

Todo grupo tem a sua própria configuração de gênero, em qualquer tipo de grupo:

- **Misto** (padrão): qualquer pessoa pode ser colocada aqui.
- **Apenas homens**: só participantes do gênero masculino.
- **Apenas mulheres**: só participantes do gênero feminino.

Participantes sem gênero informado (nem todo evento pergunta isso) **não podem** ser colocados em um grupo só para homens ou só para mulheres. É uma regra rígida, tanto para o motor quanto para a atribuição manual: o motor prefere deixá-los sem atribuição a quebrar a regra.

As restrições de gênero importam principalmente nos quartos de dormir. Para oficinas, equipes e a maioria dos outros tipos de grupo, deixe como **Misto**.

### Restrição por marcação

Cada cartão de grupo tem um botão ● de marcações. Atribua uma marcação ali para reservar o grupo para quem tem aquela marcação (o cartão passa a mostrar "Somente *{marcação}*"). Clique em **Remover** para tirar a restrição. Veja a [seção 4](04-marks.pt-BR.md).

### Notas

Cada cartão de grupo tem um ícone de notas. As notas de grupo funcionam como as notas de participante: são privadas, a menos que você marque **Compartilhar com a equipe**. Elas aparecem no quadro, não nas listas impressas.

Os grupos podem ser reordenados com as setas ↑ ↓ nos cartões (ou arrastando, no computador), editados com o ícone de lápis e excluídos com o ícone vermelho de lixeira. Excluir um grupo o remove permanentemente, junto com todas as atribuições de participantes nele; esses participantes voltam para a lista de quem está sem atribuição.

---

## Como deixar alguém de fora de um tipo de grupo

Às vezes uma pessoa deve entrar na distribuição de quartos, mas não em um grupo pequeno (um palestrante que só vem por um dia, por exemplo). Em vez de cancelar a inscrição, **não inclua** essa pessoa apenas naquele tipo de grupo. Dentro do tipo de grupo, no quadro de Atribuição, você pode:

- passar o mouse sobre a pessoa e clicar no ícone de exclusão (**Não incluir na atribuição**),
- arrastá-la para a lista **Não incluídos**, abaixo do painel de quem está sem atribuição, ou
- selecionar várias pessoas e clicar em **Não incluir** na barra inferior.

As pessoas não incluídas saem de qualquer grupo daquele tipo, o motor não mexe nelas ali, e elas continuam normalmente em todos os outros tipos de grupo. A lista **Não incluídos (N)** mostra quem são; use o ícone de desfazer (**Incluir na atribuição**) para trazer alguém de volta. Se você atribuir manualmente uma pessoa não incluída a um grupo, o Moimio pergunta antes (**Atribuir mesmo assim**) e desfaz a exclusão.

As exclusões aparecem na exportação de Participantes (coluna **Excluded From**), no histórico e na exportação de dados do participante e em uma página separada da lista em PDF.

---

## O que pode ser alterado depois

| Propriedade | Pode ser alterada depois? |
|---|---|
| Nome do tipo de grupo e rótulo Nome | Sim, a qualquer momento. |
| Uma pessoa pode estar em mais de um? | Sim, mas mudar isso depois que as pessoas foram atribuídas pode deixar atribuições que já não combinam com a intenção da regra. Rode o motor de novo em seguida. |
| Configurações do motor | Sim, a qualquer momento. Rode o motor de novo para aplicar. |
| Nome e descrição do grupo | Sim, a qualquer momento. |
| Capacidade do grupo | Sim. Se você baixar a capacidade para menos do que o número de pessoas já no grupo, ninguém é movido; o grupo fica marcado como **acima da capacidade** até você resolver. |
| Restrição de gênero ou por marcação do grupo | Sim. Quem já estava atribuído não é movido automaticamente; rode o motor de novo ou mova as pessoas manualmente. |
| Adicionar novos grupos | Sim. Rode o motor de novo (por exemplo, com **Atribuir apenas novos participantes**) para preenchê-los. |
| Excluir grupos | Sim, após uma confirmação. Os participantes deles voltam a ficar sem atribuição. |
| Excluir um tipo de grupo | Sim, após uma confirmação. Tudo o que há nele é removido permanentemente. |

Mudar "Uma pessoa pode estar em mais de um?" é o tipo de alteração que pede um plano claro: passar de **Não, apenas um** para **Sim, vários** no meio do evento normalmente significa repensar a configuração, e não só trocar uma opção.

---

## Próximos passos

A [seção 06 — Motor de atribuição](06-allocation-engine.pt-BR.md) explica como o motor de fato coloca os participantes nos grupos que você configurou: a ordem em que ele trabalha, as configurações, os motivos pelos quais alguém pode ficar sem atribuição e como ler a proposta.
