🌐 [English](04-marks.md) · [Deutsch](04-marks.de.md) · [한국어](04-marks.ko.md) · [Español](04-marks.es.md) · **Português (Brasil)** · [Français](04-marks.fr.md)

# 04 — Marcações

Uma **marcação** é uma etiqueta colorida que você atribui a um participante. As marcações aparecem para a equipe na área administrativa, mas os participantes não as veem. Elas servem para duas coisas:

1. **Identificação visual.** "Esta pessoa é líder." "Esta pessoa precisa ficar no térreo." "Esta pessoa vai levar violão." Com uma olhada, a equipe sabe o que precisa saber.
2. **Comportamento na atribuição.** As marcações podem influenciar o motor de atribuição: manter juntas as pessoas com a mesma marcação, distribuí-las por igual ou não ter efeito nenhum. Elas também podem reservar um quarto ou grupo para quem as tem.

Esta seção explica como definir marcações, atribuí-las e configurar o comportamento delas.

---

## Onde fica o editor de marcações

O editor de marcações pode ser aberto de alguns lugares, dependendo do seu acesso e da fase do evento:

- **Fase de Configuração:** o cartão **Marcas** no painel de configuração.
- **Fases de Inscrição e Evento**, para administradores do evento e Superadministradores: **Mais ▸ Marcações**, na barra lateral.
- Para membros da equipe com permissão de edição em marcações (mas sem direitos de administrador): **Marcações** aparece como um item próprio na barra lateral.

Todos os caminhos abrem o mesmo editor para o evento atual.

---

## O editor de marcações

O editor lista todas as marcações definidas para este evento. Cada marcação mostra sua cor, seu nome, onde ela aparece, quem a criou ("Criado por …") e quantas pessoas a têm (**N pessoas**; passe o mouse para ver os nomes).

Para criar uma marcação, clique em **+ Adicionar marcação** e preencha:

- **Nome da marcação**: como ela se chama ("Líder", "Primeira vez").
- **Cor**: escolha na paleta rápida (vermelho, laranja, amarelo, verde, verde-azulado, azul, roxo, rosa, cinza) ou use o seletor de cores para digitar um valor Hex ou RGB.
- **Visível em**: caixas de seleção para os três lugares onde a marcação pode aparecer como um pontinho colorido ao lado do nome do participante: **Tabela de pessoas**, **Atribuição**, **Check-in**. As três vêm marcadas por padrão. Uma marcação sem nenhuma delas marcada aparece como "Oculto em todos os lugares".

Depois clique em **Criar marcação**. Para alterar uma marcação, clique no ícone cinza de lápis; para excluí-la, clique no ícone vermelho de lixeira.

Excluir uma marcação a remove de todos os participantes que a têm. A janela de exclusão mostra quantas pessoas têm a marcação no momento (e alguns dos nomes), e você precisa digitar o nome da marcação para confirmar.

Os administradores do evento também veem **Importar de outro evento**, que copia as definições das marcações (nomes, cores, visibilidade; não quem as tem) de um evento anterior.

Membros da equipe com permissão de edição em marcações podem criar marcações, mas só podem editar ou excluir as que eles mesmos criaram. Membros com acesso somente leitura veem a lista sem os botões de edição.

### Como planejar o seu conjunto de marcações

Alguns princípios que deixam as marcações mais úteis:

- **Use poucas.** De cinco a dez marcações por evento é o ideal. Mais do que isso, a poluição visual atrapalha mais do que ajuda.
- **Use cores bem diferentes.** Dois verdes parecidos não servem para nada. A paleta rápida tem cores bem distintas; fique perto dela.
- **Use nomes curtos.** "Líder", e não "Líder designado de grupo pequeno (inscrito como tal)". O nome aparece em muitos lugares, e etiquetas curtas são mais fáceis de ler.

Alguns conjuntos de marcações que costumam funcionar bem:

- **Retiro:** Líder (verde), Primeira vez (amarelo), Vegetariano (roxo), Alergia a castanhas (vermelho), Precisa de térreo (azul).
- **Conferência:** Palestrante (laranja), Voluntário (verde-azulado), VIP (roxo), Imprensa (vermelho).
- **Acampamento de jovens:** Líder de chalé (verde), Júnior (amarelo), Sênior (azul), Necessidades especiais (rosa).

---

## Como atribuir marcações aos participantes

Você pode atribuir marcações na tabela **Participantes**, no quadro de **Atribuição** e no **Check-in**. Clique no pequeno botão ● (ou em qualquer pontinho colorido) ao lado do nome do participante. Abre-se uma janela com a lista de marcações; clique em **Atribuir** para adicionar uma ou em **Remover** para tirá-la. Cada marcação atribuída mostra quem a atribuiu e quando.

A janela só lista as marcações visíveis no lugar de onde você a abriu. Se uma marcação estiver faltando, confira as opções de **Visível em** dela.

Um participante pode ter quantas marcações forem necessárias: alguém pode ser Líder, Vegetariano e Precisa de térreo ao mesmo tempo.

Sem permissão para alterar marcações, a janela abre só para visualização, para que você ainda possa ver o que significam os pontinhos.

---

## Prioridade das marcações: definida por tipo de grupo

As marcações só afetam o motor nos tipos de grupo em que você as ativou, e cada tipo de grupo tem a sua própria lista.

Abra o tipo de grupo na página **Atribuição** e clique no ícone ⚙ **Configurações do motor**, ao lado do botão **Atribuir automaticamente**. Em **Aplicar as marcações nesta ordem** você verá:

- as marcações ativas neste tipo de grupo, numeradas, cada uma com uma lista suspensa: **Sem efeito**, **Manter juntos** ou **Distribuir uniformemente**;
- abaixo delas, as outras marcações, com **+ Adicionar** para ativá-las.

Arraste as marcações ativas (ou use as setas ↑ ↓) para mudar a ordem; ✕ tira uma marcação da lista. A marcação do topo é aplicada primeiro.

A mesma marcação pode fazer coisas diferentes em tipos de grupo diferentes. Uma marcação "Líder" pode estar como **Distribuir uniformemente** em Grupos pequenos (um líder por grupo) e nem estar na lista em Atribuição de quartos.

Quando um participante tem várias marcações, **apenas uma delas comanda o motor** em um determinado tipo de grupo: a que estiver mais alta na lista e configurada como Manter juntos ou Distribuir uniformemente. As outras continuam aparecendo como pontinhos, só não afetam a distribuição ali. Os códigos de grupo vêm primeiro: alguém colocado junto com o seu código de grupo não é movido por causa de uma marcação.

Uma ordem típica:

1. Marcações que devem ter mais peso na distribuição (Líder, Palestrante).
2. Outras marcações com algum efeito (Júnior, Primeira vez).
3. Marcações só informativas (Vegetariano, Alergia, Térreo): deixe-as fora da lista ou configure como **Sem efeito**. Elas nunca são consultadas.

---

## Como reservar um grupo para uma marcação

No quadro de Atribuição, cada cartão de quarto ou grupo tem o seu próprio botão ● de marcações. Use-o para **Atribuir** uma marcação àquele grupo: ele passa a ser "Somente *{marcação}*", e o motor só coloca ali pessoas que têm aquela marcação. É útil para um quarto de líderes ou um quarto silencioso. Quem tem a marcação é levado primeiro para o quarto reservado. Veja a [seção 5](05-group-types-and-units.pt-BR.md).

---

## Quando as marcações mudam depois que o motor já rodou

Adicionar, excluir ou atribuir uma marcação, ou mudar o comportamento ou a prioridade de uma marcação, não roda o motor de novo. A atribuição atual continua como estava.

Para aplicar as mudanças nas marcações, vá para **Atribuição**, abra o tipo de grupo e rode **Atribuir automaticamente** de novo. O motor é determinístico: os mesmos participantes, grupos, configurações e marcações sempre produzem a mesma atribuição, então rodar de novo dá a você uma proposta atualizada e limpa para revisar antes que qualquer coisa mude.

Se você só quer uma pequena mudança, também pode arrastar participantes manualmente no quadro.

---

## Marcações nos relatórios e exportações

- **As listas em PDF** mostram as marcações como pontinhos coloridos ao lado do nome de cada participante, com uma legenda. Só as marcações visíveis em **Atribuição** são impressas.
- **A exportação CSV de Participantes** (Lista completa de participantes) tem uma coluna **Marks** com os nomes das marcações separados por vírgula.
- **A exportação de dados LGPD/GDPR de um participante** lista as marcações dele.

---

## Erros comuns

- **Usar marcações demais.** Vinte marcações em um evento são impossíveis de administrar. Revise e corte à medida que o evento se aproxima.
- **Esperar que uma marcação mude a atribuição sozinha.** Uma marcação não faz nada no motor até estar na lista **Aplicar as marcações nesta ordem** de um tipo de grupo, como Manter juntos ou Distribuir uniformemente.
- **Ocultar uma marcação em uma tela e depois procurá-la ali.** A janela de atribuição só lista as marcações visíveis naquela tela.

---

## Próximos passos

A [seção 05 — Tipos de grupo e grupos](05-group-types-and-units.pt-BR.md) trata dos tipos de grupo e dos quartos ou grupos dentro deles, onde o motor de fato coloca os participantes, com capacidades e restrições de gênero.
