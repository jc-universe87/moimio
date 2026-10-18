🌐 [English](07-check-in.md) · [Deutsch](07-check-in.de.md) · [한국어](07-check-in.ko.md) · [Español](07-check-in.es.md) · **Português (Brasil)** · [Français](07-check-in.fr.md)

# 07 — Check-in

A tela de check-in é o que a equipe usa no dia do evento para marcar quem chegou. É uma lista simples, com caixas de seleção grandes, pensada para funcionar bem em um tablet ou celular na mesa de recepção.

<p align="center">
  <img src="../assets/check-in.png" alt="Modo de check-in com a caixa de busca, a barra de progresso e as caixas de seleção" width="560">
  <br>
  <em>Modo de check-in</em>
</p>

---

## Como chegar ao check-in

O que você vê depende de quem você é.

**Administradores** (Superadministrador ou administrador do evento) clicam em **Abrir modo de check-in →** na página principal do evento. O botão aparece durante a fase de Evento, enquanto o evento está **Antes do início** ou **Em andamento** (não depois que ele fica **Concluído**). Ele abre uma tela cheia, sem barra lateral, que mostra só o nome do evento, um botão de tema e **Sair**. **← Voltar para Atribuição** retorna à área administrativa normal. Quando todos os tipos de grupo estiverem confirmados, o quadro de atribuição também oferece o atalho **Check-in pronto →**.

**Membros da equipe cuja única permissão é o check-in** vão direto para essa tela cheia quando abrem o evento durante a fase de Evento. Não há botão de saída: essa é a tela deles durante o turno.

**Membros da equipe com check-in e outras permissões** (por exemplo, check-in e Participantes) veem **Check-in** na barra lateral. Ele abre a mesma lista de check-in dentro do layout normal da área administrativa, para que possam alternar entre as tarefas.

Membros da equipe com **Acesso antes do início do evento** também podem abrir o check-in durante a fase de Inscrição (veja a [seção 11](11-staff-permissions.pt-BR.md)).

Seja qual for o caminho, os dados são os mesmos: uma marcação feita em um aparelho aparece em todas as outras telas em um ou dois segundos.

---

## A lista de check-in

Cada linha é um participante. Aparecem todos os inscritos, confirmados ou ainda pendentes; as inscrições canceladas não aparecem.

No topo:

- Uma **caixa de busca** (*"Pesquisar por nome, e-mail ou código de grupo..."*). Ela também encontra números de participante e nomes de marcações, e ignora acentos, hífens e variações de grafia, como Müller / Mueller.
- Uma barra de progresso com *"28 de 34 com check-in"*.
- Os filtros: **Todos**, **Check-in realizado**, **Sem check-in**.
- **Colunas**, para escolher quais colunas aparecem.
- **+ Criar coluna** (administradores e membros da equipe com **Acesso antes do início do evento**).

As colunas mostradas por padrão são:

- **Nº**: o número do participante neste evento.
- **Nome**, com os pontinhos das marcações da pessoa (clique neles para ver o que significam ou para atribuir marcações, se você tiver permissão).
- **Check-in**: a caixa principal, para "a pessoa chegou".
- **Horário de check-in**: quando a pessoa foi marcada.

Clique em **Colunas** para mostrar ou ocultar outras. A lista é dividida em **Acompanhamento de check-in** (as suas colunas de marcação personalizadas), **Campos de inscrição** (**Código de grupo**, **Gênero**, **Telefone**, **Igreja / Organização**, **País**, **Endereço**, **Data de nascimento**, **Mensagem**, **Inscrito em** e **Horário de check-in**), **Campos personalizados** do seu formulário de inscrição e **Outros** (**Notas**, que adiciona um botão para ler e escrever notas sobre aquela pessoa). Arraste o cabeçalho de uma coluna para os lados para reordenar e clique em um cabeçalho para ordenar por ele. As colunas escolhidas ficam salvas naquele aparelho.

No celular, cada pessoa é um cartão com o nome e as caixas de seleção; toque em **N detalhes** para ver as outras colunas.

---

## Colunas de check-in personalizadas

Além da marcação principal de **Check-in**, você pode adicionar colunas de marcação para qualquer coisa que queira controlar na porta: pagamento recebido, camiseta entregue, crachá entregue, termo assinado e assim por diante.

Para adicionar uma, clique em **+ Criar coluna**, digite um nome, como "Pagamento" ou "Camiseta", e clique em **Adicionar**. A nova coluna aparece com uma caixa vazia para cada participante.

Para excluir uma coluna personalizada, clique no pequeno ✕ ao lado do nome dela, no cabeçalho (administradores e membros da equipe com **Acesso antes do início do evento**). Uma confirmação (**Excluir coluna**) avisa que a coluna e todas as marcações dela serão removidas para todos. Não dá para desfazer.

Vale saber:

- **Várias pessoas da equipe podem trabalhar no mesmo participante ao mesmo tempo**; por exemplo, uma marca "Pagamento" enquanto outra marca "Camiseta".
- **Só a marcação principal de Check-in conta como chegada.** As colunas personalizadas são controladas à parte e não mudam os números de "com check-in".

---

## O que uma marcação faz

As marcações são salvas na hora; não há botão de salvar. Marcar a caixa principal de **Check-in** também registra o horário, mostrado na coluna **Horário de check-in**. Clique de novo na marcação para desfazê-la; o horário também é apagado.

---

## Sincronização em tempo real

Todas as telas de check-in ficam conectadas ao servidor. Quando alguém marca uma caixa (principal ou personalizada, em qualquer aparelho), todas as outras telas abertas se atualizam em um ou dois segundos. Não há botão de atualizar.

Na prática: um participante chega, a voluntária A faz o check-in dele no celular, e o voluntário B, na outra ponta da mesa, vê a linha mudar na hora. Duas pessoas marcando o mesmo participante ao mesmo tempo não é problema; o resultado é simplesmente "marcado".

A conexão é automática. Se o Wi-Fi cair por um instante, a tela se reconecta sozinha quando ele voltar.

---

## Perfil do participante

Clique no **ⓘ** ao lado de um nome (**Ver perfil**) para abrir o **Perfil do participante**: dados de contato, dados da inscrição, em quais grupos a pessoa está em cada tipo de grupo (útil para "em que quarto eu estou?"), as preferências de grupo, os campos personalizados e as notas. É o mesmo painel do quadro de atribuição. Para adicionar uma nota ou mudar as marcações, use a coluna **Notas** e os pontinhos de marcação na linha.

---

## Situações comuns

### "Ela está aqui, mas não consigo encontrá-la."

Busque por parte do nome, pelo e-mail ou pelo código de grupo. Se encontrar, faça o check-in. Se ela não estiver na lista, a inscrição pode ter sido cancelada, ou ela nunca se inscreveu. Peça a um administrador para verificar a página **Participantes**: uma inscrição cancelada pode voltar a ser confirmada, e aí ela aparece no check-in na hora.

### "Preciso desfazer uma marcação."

Clique de novo na marcação. Ela volta a ficar desmarcada e o horário de check-in é apagado.

### "Estamos em dois na mesma mesa. Não vamos atrapalhar um ao outro?"

Não. Cada um pode buscar e marcar no próprio aparelho, e as duas telas ficam sincronizadas.

### "Usamos nosso próprio sistema de pagamento ou de termos. Podemos só registrar as chegadas?"

Sim. Não crie colunas personalizadas; a marcação principal de **Check-in** funciona sozinha.

### "Como consigo uma lista de quem chegou?"

Há duas opções:

- Em **Participantes**, clique em **↓ Exportar ▾ ▸ Lista completa de participantes**. O CSV tem uma coluna **Checked In** (Yes / No) para todos.
- Em **Relatórios**, o bloco **Check-in** mostra o total atualizado durante a fase de Evento. Para ter uma cópia em papel na porta, imprima a lista **Presença** (veja a [seção 08](08-reports-and-pdf-exports.pt-BR.md)).

---

## Próximos passos

A [seção 08 — Relatórios e PDFs](08-reports-and-pdf-exports.pt-BR.md) trata da página Relatórios, das listas em PDF para imprimir em diferentes formatos e idiomas e do que as listas mostram sobre a sua atribuição.
