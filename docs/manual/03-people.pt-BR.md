# 03 — Participantes

A tabela Participantes é onde você vai passar a maior parte do tempo durante a fase de Inscrição. É uma lista de todos os inscritos no seu evento, com ferramentas para ver, editar, confirmar, marcar e agrupar as pessoas.


<p align="center">
  <img src="../assets/people-table.png" alt="Tabela Participantes com a caixa de busca, os filtros de status, os botões Colunas, Exportar e Importar CSV e as ações de cada linha" width="560">
  <br>
  <em>Tabela Participantes com a caixa de busca, os filtros de status, os botões Colunas, Exportar e Importar CSV e as ações de cada linha</em>
</p>


---

## A tabela Participantes

Abra **Participantes** na barra lateral. Você verá uma tabela com uma linha por inscrição. As colunas mostradas por padrão são:

- **Nº**: o número sequencial do participante no evento (por exemplo, `#1`, `#12`). Uma identificação simples e fácil de usar. Sempre aparece, sempre em primeiro lugar.
- **Nome**: o nome completo como foi inscrito, seguido dos pontinhos coloridos das marcações do participante (veja [Marcações](04-marks.pt-BR.md)). Sempre aparece.
- **E-mail**.
- **Código de grupo**: o código usado na inscrição ou o que o Moimio gerou. Passe o mouse sobre ele (ou mantenha pressionado no celular) para ver quem mais compartilha aquele código.
- **Status**: Pendente / Confirmado / Cancelado (em cores diferentes).
- **Inscrito em**: data e hora da inscrição.
- **Notas**: abre as notas daquele participante; um pequeno número mostra quantas notas existem.
- **Ações**: os controles de cada linha: **✉ Reenviar** (manda de novo o e-mail de inscrição; não aparece para participantes cancelados), **↓ Exportar dados** (a exportação completa dos dados do participante, conforme a LGPD/GDPR, em JSON) e **Remover** (remove o participante sem apagá-lo do banco de dados). Exportar dados e Remover são exclusivos dos administradores do evento.

Clique em **Colunas** para mostrar ou ocultar outras colunas: **Gênero**, **Data de nascimento**, **Telefone**, **Endereço**, **País**, **Igreja / Organização** e **Mensagem** (estas aparecem na lista quando pelo menos um participante as preencheu), **Com check-in** e todos os campos personalizados do seu formulário de inscrição (em **Campos personalizados**). Você também pode arrastar o cabeçalho de uma coluna (pela alça ⠿) para mudar a ordem das colunas.

A tabela permite:

- **Filtrar por status.** Botões no topo: **Todos**, **Pendente**, **Confirmado**, **Cancelado**. Em **Todos**, as pessoas canceladas vão para o fim da lista, com o nome riscado.
- **Ordenar**: clique no cabeçalho de qualquer coluna; clique de novo para inverter.
- **Buscar**: procura por nome, e-mail, código de grupo, telefone, igreja/organização e nomes de marcações. A busca é tolerante com acentos, hífens, apóstrofos e grafias de trema (buscar "Mueller" encontra "Müller").

Acima da tabela, um contador mostra quantos participantes correspondem à sua busca e ao filtro (por exemplo, "12 de 80 participantes").

O Moimio lembra, para cada usuário e neste navegador, as colunas escolhidas, a ordem das colunas e a ordenação, para que a tabela apareça igual da próxima vez. (Ordenar por um campo personalizado funciona, mas não fica salvo.)

Não há seleção de várias linhas na tabela Participantes; as ações (editar, marcar, exportar, remover) são feitas uma linha de cada vez.

### Layout no celular e em tela larga

No celular ou em um tablet estreito, cada participante aparece como um cartão com número, nome, marcações, status, e-mail e código de grupo. Toque em **▸ N detalhes** (ou **▸ Mais**) para expandir o cartão e ver as outras colunas que você ativou, além de **Reenviar**, **Exportar dados** e **Remover**. Em telas mais largas, você vê a tabela completa, com todas as colunas lado a lado. Os recursos são os mesmos; só o layout muda.

---

## Como editar campos direto na tabela

Você precisa de permissão para editar participantes (administradores do evento ou membros da equipe com permissão de edição em Participantes). Passe o mouse sobre um valor: se aparecer um sublinhado, você pode clicar nele.

**Nome e e-mail**: clique no valor. O Moimio primeiro pede uma confirmação (**Editar o nome?** / **Editar o endereço de e-mail?**), porque você está alterando dados pessoais. Clique em **Editar**, altere o valor e pressione Enter ou clique em ✓. Nenhum e-mail é enviado.

**Código de grupo**: clique no código (ou em **+ Adicionar**, se não houver), digite e pressione Enter ou clique em ✓. É salvo na hora.

**Status**: clique no indicador de status. Aparecem três opções (Pendente / Confirmado / Cancelado); clique na que você quer. ✕ fecha sem alterar nada. Veja [Status das inscrições](#status-das-inscrições) abaixo.

**Gênero, data de nascimento, telefone, endereço, país, igreja/organização**: clique no valor, altere e pressione Enter (ou clique em ✓). Uma janela **Confirmar alteração** mostra o valor antigo → o valor novo. Clique em **Confirmar alteração** para salvar; **Cancelar** descarta.

**Campos personalizados** funcionam do mesmo jeito (com a janela de confirmação). O campo de entrada segue o tipo do campo: caixa de texto para texto, caixa numérica para números, lista suspensa para campos de escolha, lista suspensa ✓ / ✕ para campos Sim/Não e seletor de datas para datas.

**A mensagem é somente leitura**: é a mensagem do participante para os organizadores, e não algo para os organizadores sobrescreverem. Clique em **Ver** para lê-la por inteiro.

**Nº**, **Inscrito em** e **Com check-in** são definidos pelo Moimio e não podem ser editados aqui.

---

## Status das inscrições

Todo participante tem um status. O status determina quase tudo o que vem depois: pessoas canceladas ficam fora da atribuição, do check-in e da maioria das contagens.

| Status | Significado | Como o participante chega a ele |
|---|---|---|
| **Pendente** | Inscrito, mas ainda não clicou no link de confirmação do e-mail. | Só acontece quando **Exigir confirmação por e-mail para inscrições** está ativado (Mais ▸ Formulário de inscrição). |
| **Confirmado** | A inscrição está completa. | Logo após a inscrição, quando a confirmação por e-mail está desativada (o padrão); depois de clicar no link do e-mail; depois de uma importação de CSV; ou quando um administrador define manualmente. |
| **Cancelado** | O participante desistiu, ou você cancelou em nome dele. | Definido por um administrador. Cancelar tira a pessoa de todos os grupos em que ela estava. |

Por padrão, o motor de atribuição também distribui participantes pendentes (a opção **Incluir participantes não confirmados**; veja a [seção 6](06-allocation-engine.pt-BR.md)).

Você pode mudar o status pela linha quando:

- Um e-mail nunca chegou (caiu no spam; endereço antigo). Mude o status para **Confirmado** manualmente.
- Alguém liga para cancelar. Mude o status para **Cancelado**.
- Alguém se inscreveu duas vezes. Cancele uma das inscrições.

Você pode alternar entre os status à vontade.

---

## Códigos de grupo

Os códigos de grupo ligam inscrições relacionadas, para que o motor de atribuição as trate como um cluster.

### Como os participantes definem o código de grupo

O formulário de inscrição tem um campo opcional de **código de grupo**. A convenção é `STEM-NNN` (por exemplo, `SMITH-742`). Uma família de quatro pessoas que se inscreve junta digitaria `SMITH-742` em todas as inscrições. O motor então tenta mantê-las juntas ao atribuir quartos (ou qualquer outro tipo de grupo).

Se a pessoa não informar um código, o Moimio cria uma base a partir do sobrenome e acrescenta um número único, normalmente de três dígitos (por exemplo, `SMITH-742`), passando para quatro ou cinco só se aquele sobrenome já tiver muitos clusters no evento, e inclui o resultado no e-mail de inscrição, para que a pessoa possa compartilhá-lo com quem quiser ficar junto.

Se a pessoa digitar só a base (por exemplo, `SMITH`, sem número), vale a mesma lógica: um número único é acrescentado antes de salvar. Isso evita colisões: duas famílias sem relação entre si que digitam `SMITH` acabam com códigos diferentes, então não são agrupadas por engano. Para entrar de propósito em um cluster existente, a pessoa digita o código completo (`SMITH-742`), que é salvo exatamente como foi digitado. Os códigos são armazenados em letras maiúsculas.

### Como os administradores gerenciam os códigos de grupo

Na tabela Participantes, você pode:

- **Definir ou alterar** o código de grupo de um participante clicando no valor (ou em **+ Adicionar**). Útil quando alguém se inscreveu sem código e você percebe que a pessoa está com uma família. Digite o código completo da outra pessoa para colocá-las no mesmo cluster.
- **Ver quem está em um cluster** passando o mouse sobre um código. A janelinha lista todos os outros com o mesmo código, ou avisa que mais ninguém o tem.

### Por que um "cluster de uma pessoa só" não conta

Se o código de grupo de um participante não é compartilhado com mais ninguém, ele é um "cluster de uma pessoa só". O motor o trata como qualquer outra pessoa individual. O código de grupo é mantido (você o vê na interface e nos relatórios), mas não ativa nenhum comportamento de agrupamento.

---

## Notas

Clique em **Notas** em uma linha para abrir as notas daquele participante. Digite em **Escreva uma nota...** e clique em **Adicionar nota**.

- Uma nota é **Privado** por padrão: só você a vê. Marque **Compartilhar com a equipe** antes de adicioná-la para que ela seja uma nota de **Equipe**, visível para os outros membros da equipe do evento.
- Cada nota mostra quem a escreveu e quando. Se a conta do autor tiver sido excluída depois, aparece **[usuário removido]**.
- Você pode excluir notas pelo ícone de lixeira. Só o autor (ou um Superadministrador) pode de fato excluir uma nota.

As mesmas notas aparecem no painel de perfil do participante, no quadro de Atribuição e no Check-in.

### Histórico

O histórico de atribuição de um participante (quem o colocou onde, movimentações, remoções, exclusões e se foi uma pessoa ou o motor) não fica na tabela Participantes. Abra o perfil dele (**Ver perfil**, o ícone ⓘ) no quadro de Atribuição ou no Check-in para vê-lo. Veja a [seção 6](06-allocation-engine.pt-BR.md).

---

## Inscrição em lote (importação de CSV)

Em eventos em que os participantes não usam o formulário público (por exemplo, um retiro fechado com participantes pré-selecionados, em que você já tem uma planilha com a lista), você pode importá-los diretamente.

No topo da tabela Participantes, clique em **↑ Importar CSV**. A janela **Importar participantes** se abre:

1. Clique em **Baixar modelo** para obter um CSV com os cabeçalhos de coluna corretos (incluindo seus campos personalizados).
2. Preencha seus dados e salve como CSV.
3. Em **Formato de data no seu arquivo**, escolha **Europeu (DD.MM.AAAA)** ou **ISO / Coreano (AAAA.MM.DD)**, para que as datas de nascimento sejam lidas corretamente.
4. Arraste o arquivo para a janela (ou clique para escolhê-lo). O Moimio mostra uma prévia: linhas 🟢 estão certas, linhas 🟡 têm um aviso, linhas 🔴 têm um erro (nome, sobrenome ou e-mail faltando, e-mail inválido, e-mail repetido no arquivo, gênero inválido, data ambígua, um valor que não está entre as opções de um campo de escolha e assim por diante).
5. Clique em **Importar N linhas válidas**. Linhas com erro são ignoradas; linhas só com avisos são importadas.

Os participantes importados entram com o status **Confirmado** e recebem um número de participante e (se necessário) um código de grupo gerado. Nenhum e-mail é enviado: o administrador que faz a importação está garantindo que os endereços estão corretos.

Fique de olho nos avisos amarelos:

- **Já registrado**: aquele endereço de e-mail já está no evento. A linha é importada mesmo assim, então você ficaria com dois registros da mesma pessoa. Tire a linha do arquivo se não for isso o que você quer.
- **Sem consentimento GDPR**: a linha não tem `true`/`yes` na coluna de consentimento.
- Se todas as linhas tiverem o mesmo gênero, o Moimio avisa: programas de planilha às vezes preenchem automaticamente um valor na coluna inteira.

O formato CSV é tolerante:

- A ordem das colunas não importa, e as grafias mais comuns dos cabeçalhos em inglês são reconhecidas ("First Name", "Surname", "E-mail", "DOB", "Mobile", "Church" e assim por diante).
- As colunas da exportação de Participantes `No.`, `Status`, `Checked In`, `Registered`, `Marks` e `Message` são ignoradas silenciosamente, então você pode reimportar uma exportação.
- Outras colunas não reconhecidas aparecem em um aviso amarelo na prévia. Na importação, cada uma vira um novo campo personalizado (oculto no formulário público de inscrição), e a coluna correspondente já aparece ativada na tabela Participantes. As colunas que só existem na exportação do próprio Moimio (**No.**, **Status**, **Checked In**, **Marks**, **Registered**, **Message**, **Excluded From**) são ignoradas sem aviso, para que você possa reimportar uma exportação do jeito que ela está.
- Colunas opcionais ausentes ficam vazias.
- **Marcações e exclusões não são importadas.** Atribua as marcações depois da importação, na tabela Participantes ou no quadro de Atribuição.

Para importações muito grandes (mais de 1.000 linhas), divida o arquivo em lotes de algumas centenas para manter a prévia rápida.

---

## Exportação

Há duas opções de exportação em CSV no topo da tabela Participantes, no botão **↓ Exportar ▾**:

- **Lista completa de participantes**: todos os participantes do evento (exceto os removidos), independentemente da busca ou do filtro de status que estiver na tela. Colunas (com os cabeçalhos em inglês): First Name, Last Name, Email, Gender, Date of Birth, Phone, Address, Country, Church/Organisation, Group Code, GDPR Consent, No., Status, Checked In, **Marks** (nomes das marcações separados por vírgula), **Excluded From** (os tipos de grupo dos quais a pessoa foi deixada de fora), uma coluna por campo personalizado e Message. As atribuições ficam de fora deste CSV de propósito: para um retrato das atribuições, use as listas em PDF em Relatórios ou o backup.
- **Apenas nomes + e-mails**: um CSV de duas colunas (nome, e-mail), pronto para colar em uma ferramenta de lista de e-mails.

Há também a ação **↓ Exportar dados** em cada linha (na coluna Ações), que baixa a **exportação de dados LGPD/GDPR** de um participante em JSON; veja a [seção 9](09-data-export-gdpr.pt-BR.md).

---

## Situações comuns

### "O e-mail nunca chegou"

Na tabela Participantes, clique no indicador de status **Pendente** do participante e escolha **Confirmado**. Pronto.

Se quiser que ele receba o e-mail mesmo assim, clique em **✉ Reenviar** na linha dele. Um participante pendente recebe o link de confirmação de novo; um participante confirmado recebe o e-mail de inscrição com o código de grupo.

### "Duas inscrições são da mesma pessoa"

Na tabela Participantes, encontre as duas linhas (busque pelo nome ou e-mail). Escolha qual manter (normalmente a que foi confirmada primeiro ou a que tem informações mais completas). Mude a outra para **Cancelado**. Se a cancelada já estava em algum grupo, essas vagas são liberadas automaticamente.

### "Quero marcar todos os líderes"

Crie uma marcação em **Mais ▸ Marcações**, na barra lateral (ou no cartão **Marcas** do painel de configuração). Dê um nome, por exemplo "Líder", escolha uma cor bem diferente e confira se **Tabela de pessoas** está marcado em **Visível em**.
Depois, na tabela Participantes, encontre cada líder. Ao lado do nome há um pequeno botão ● (um círculo vazio quando a pessoa ainda não tem marcações). Clique nele e clique em **Atribuir** ao lado de "Líder".

### "Exportar todo mundo para uma lista de e-mails"

Use **↓ Exportar ▾ → Apenas nomes + e-mails**. É um CSV de duas colunas; cole direto na sua ferramenta de e-mails.

---

## Quando o participante cancela depois

Há duas opções:

- **Cancelar** (status → **Cancelado**): o registro continua visível na tabela Participantes (riscado, no fim de **Todos**, ou no filtro **Cancelado**), mas fica fora da atribuição, do check-in e da maioria das contagens. As vagas em grupos são liberadas. Você pode voltar a pessoa para Pendente ou Confirmado a qualquer momento; útil para quem sai da lista de espera.
- **Remover** (a ação **Remover** na coluna Ações da linha, só para administradores do evento): depois que você confirma em **Remover participante**, a pessoa some de todas as listas, atribuições e contagens. O registro é mantido no banco de dados para fins de registro (a exportação de dados LGPD/GDPR ainda o inclui; veja a [seção 9](09-data-export-gdpr.pt-BR.md)), mas não há botão para trazê-lo de volta; restaurá-lo exige alguém com acesso ao banco de dados.

A exclusão física completa do registro (para os raros casos em que a legislação exige) também é, por enquanto, uma operação manual no banco de dados; veja a [seção 9](09-data-export-gdpr.pt-BR.md) para entender o motivo.

---

## Próximos passos

A [seção 04 — Marcações](04-marks.pt-BR.md) trata do sistema de marcações: como definir etiquetas coloridas, atribuí-las aos participantes e configurar como elas influenciam o motor de atribuição.
