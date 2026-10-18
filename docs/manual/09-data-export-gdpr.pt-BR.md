# 09 — Exportação de dados e LGPD/GDPR

O Moimio foi feito para que quem organiza um evento possa cumprir as suas obrigações de controlador de dados, segundo o GDPR (e de forma muito parecida com a LGPD), sem sair do aplicativo. As peças envolvidas são: exportação de dados por participante (artigos 15 e 20), edição direta (artigo 16), remoção (artigo 17), backup por evento e tratamento claro dos participantes cancelados.

Esta seção é prática: o que fazer e quando. Para a postura técnica e jurídica, veja [GDPR compliance](../gdpr-compliance.md) (em inglês).

<p align="center">
  <img src="../assets/insight-panel-export.png" alt="O painel de perfil com os dados de um participante e o botão Exportar dados no topo" width="560">
  <br>
  <em>O painel de perfil, com o botão Exportar dados no topo</em>
</p>

---

## Exportação por participante: quando alguém pede os próprios dados

O artigo 15 (direito de acesso) e o artigo 20 (portabilidade dos dados) aparecem juntos aqui: um participante manda um e-mail dizendo "me envie tudo o que vocês têm sobre mim".

### Como fazer

As exportações de dados pessoais são para os **Administradores do evento** daquele evento e para os **Superadministradores**. Há dois pontos de partida:

- **Pela tabela Participantes.** Encontre a linha da pessoa e clique em **↓ Exportar dados** na coluna Ações. (Recomendado para pedidos rotineiros: é o caminho mais rápido.)
- **Pelo painel de perfil.** No quadro de atribuição ou no Check-in, clique no pequeno ícone **ⓘ** (**Ver perfil**) ao lado do nome do participante e depois em **↓ Exportar dados**, no topo do painel. Mesmo arquivo, mesmo conteúdo. Prático quando você já está olhando para a pessoa e chega um pedido.

Nos dois casos:

1. O seu navegador baixa um único arquivo: `participant-export-{participant number}-{date}.json`.
2. Envie o arquivo ao participante pelo mesmo canal que ele usou para pedir.

Participantes cancelados podem ser exportados do mesmo jeito: eles continuam na tabela Participantes, em cinza.

### O que há no arquivo

Um único documento JSON (um formato padrão, legível por máquina) com estas seções:

- **`export_metadata`**: versão do formato, quando o arquivo foi gerado e uma nota curta sobre o que ficou de fora.
- **`event`**: o evento em que a pessoa se inscreveu: nome, descrição, local, fuso horário e datas. Nada sobre outros participantes nem sobre o resto da sua configuração.
- **`participant`**: o registro da inscrição: nome, e-mail, gênero, data de nascimento, telefone, endereço, país, igreja/organização, mensagem, código de grupo, status, consentimento, situação do check-in, idioma e quando o registro foi criado, alterado ou removido.
- **`custom_fields`**: todas as respostas às suas perguntas personalizadas, com o nome de cada pergunta.
- **`marks`**: todas as marcações que a pessoa tem, com nome, cor e data em que foram atribuídas.
- **`preference_requests`**: os pedidos "quero ficar no grupo de…" que a pessoa fez e os pedidos de outras pessoas que a mencionam.
- **`allocations`**: em qual grupo ela está, em cada tipo de grupo.
- **`exclusions`**: os tipos de grupo dos quais você a deixou de fora.
- **`allocation_history`**: o histórico de entradas, mudanças e saídas de grupos.
- **`notes`**: apenas as notas publicadas escritas sobre este participante.
- **`checkin_values`**: todas as marcações nas suas colunas de check-in.

### O que fica de fora, e por quê

- **Notas não publicadas (rascunhos).** Os rascunhos são anotações de trabalho de um membro da equipe, não comunicações publicadas.
- **Quem da sua equipe moveu a pessoa.** O histórico diz o que aconteceu e quando, não qual membro da equipe fez a mudança.
- **Dados de outros participantes**, mesmo de pessoas com o mesmo código de grupo ou no mesmo quarto. Cada pessoa recebe só os próprios dados.

Toda exportação também fica registrada no log do servidor (`data_export_generated`), com o evento, o participante e quem fez o download.

---

## Artigo 16: retificação (o participante diz "corrija isto")

Se o participante disser que um dado está errado, abra **Participantes** e clique no valor para editá-lo ali mesmo. Nome, e-mail, gênero, data de nascimento, telefone, endereço, país, igreja/organização, código de grupo, status e respostas a campos personalizados podem ser editados assim; veja a [§03](03-people.pt-BR.md). A mensagem que o próprio participante escreveu para você é somente leitura, para nunca ser sobrescrita por engano.

---

## Artigo 17: apagamento ("direito ao esquecimento")

Duas operações, com duas intenções diferentes:

### Remover (o caso do dia a dia)

Na tabela Participantes, clique em **Remover** na coluna Ações do participante e depois em **Remover participante** para confirmar. Só Administradores do evento e Superadministradores veem esse botão.

O participante some do uso diário: Participantes, quadro de atribuição, Check-in, relatórios, exportações e a atribuição. Ele também fica de fora de qualquer backup feito depois. O registro em si é mantido no banco de dados para fins de registro. Não há botão para trazer a pessoa de volta; quem cuida do seu servidor pode restaurá-la no banco de dados, se necessário.

Este é o caminho certo para *"mudei de ideia, não vou mais"* ou *"por favor, me tirem das suas listas"*.

### Apagamento permanente (o caso raro)

Nesta versão não há um botão que apague permanentemente uma única pessoa: um "excluir para sempre" irreversível é fácil demais de clicar por engano. As suas opções:

- **Excluir o evento inteiro** (Superadministrador: **Zona de perigo ▸ Excluir evento**, no painel de configuração ou na página Detalhes do evento) depois que ele acabar e você não precisar mais dele. Isso apaga permanentemente todos os inscritos. Baixe um backup antes, se você puder precisar dos registros.
- **Para uma única pessoa**, peça a quem cuida do seu servidor Moimio para remover o registro do banco de dados. Veja [GDPR compliance](../gdpr-compliance.md) para entender o contexto.

---

## Link do aviso de privacidade no formulário de inscrição

Se a sua organização tem um aviso de privacidade próprio, coloque o endereço dele em **Workspace ▸ Aviso de privacidade ▸ URL do aviso de privacidade** (Superadministrador) e clique em **Salvar**. O formulário público de inscrição passa a mostrar um link **Aviso de privacidade** logo após a frase de consentimento. Se deixar em branco, nenhum link aparece.

---

## Backups

Além das exportações por participante, o Moimio pode fazer backup de eventos inteiros.

### Onde encontrar

Barra lateral ▸ **Backup** (em **Gerenciar**, só para Superadministradores). A página tem o título **Exportar**.

### Como fazer um backup

1. Marque um ou mais eventos em **Baixar backups de eventos** (ou **Selecionar tudo**).
2. Em **Conteúdo do backup**, escolha:
   - **Backup completo**: o evento inteiro: participantes, respostas, grupos e atribuições, exclusões, marcações, preferências, notas, colunas e marcações de check-in, histórico, suas configurações e regras e as datas originais. Use como cópia de segurança, antes de uma grande mudança ou para levar um evento para outro Moimio.
   - **Apenas estrutura (compatível com GDPR)**: a estrutura do evento sem nenhum dado pessoal: formulário de inscrição, perguntas personalizadas, tipos de grupo e seus grupos, marcações, colunas de check-in e configurações. Sem participantes, sem notas e sem os dados do remetente dos seus e-mails. Pode ser compartilhado com outra organização como modelo, sem riscos.
3. Clique em **Baixar {n} backup(s)**. Cada evento é baixado como um arquivo `.zip` separado (os arquivos só de estrutura têm `-structure` no nome).

Algumas coisas que vale saber:

- **Notas:** um backup completo contém todas as notas publicadas, mais os *seus próprios* rascunhos. Os rascunhos de outros membros da equipe nunca entram.
- **Participantes removidos** não entram nos backups.
- **Os membros da equipe e as funções deles nunca fazem parte de um backup.** Convide a sua equipe de novo depois de restaurar.

### Como restaurar

Na página Backup, clique em **↑ Restaurar a partir de backup** (o botão **↑ De backup** na lista de eventos leva ao mesmo lugar). Envie o `.zip`; o Moimio mostra uma prévia (nome do evento, quando foi exportado, quantos participantes e atribuições) e depois você clica em **Restaurar evento**.

- É criado um evento **novo**, chamado `{original name} (Restored)` e colocado de volta na fase de Configuração. O original não é alterado.
- Ele mantém as datas originais, então fica na lista de eventos no mesmo lugar que o original. Clique em **Abrir o evento restaurado** para ir direto a ele.
- Se parte do arquivo estiver danificada, o Moimio deixa de fora só as linhas que não consegue ler e segue em frente. O resultado informa quantas linhas ficaram de fora, quantas entradas precisaram ser encurtadas e quantos valores voltaram para a configuração padrão.
- Arquivos de backup mais antigos continuam podendo ser restaurados.

A restauração é exclusiva dos Superadministradores.

### Como mudar o workspace inteiro de lugar

A página Backup trabalha com um evento de cada vez. Para levar todos os eventos de uma vez para um Moimio que você mesmo mantém, existe uma exportação do workspace inteiro e um único comando que a restaura (com um modo de teste que não altera nada). Veja [Moving a workspace to your own Moimio](../moving-a-workspace.md) (em inglês).

---

## Participantes cancelados

Cancelar não é excluir: é uma mudança de status. Os participantes cancelados continuam na tabela Participantes, em cinza, para que você tenha um registro claro. Os dados deles continuam lá e a exportação por participante continua funcionando. Para tirá-los das suas listas, use **Remover** (veja acima).

Em relação ao artigo 18 (limitação do tratamento), o status cancelado funciona como uma limitação leve: os participantes cancelados ficam fora da atribuição, do Check-in, das listas e da maioria dos relatórios. Os dados deles não estão sendo usados para o evento; apenas ficam guardados.

---

## Próximos passos

A [seção 10 — Vários eventos e arquivo](10-multi-event-and-archive.pt-BR.md) trata de como organizar vários eventos na mesma instalação do Moimio, arquivar eventos passados sem excluí-los, o que muda quando um evento é arquivado e como reaproveitar a configuração de um evento anterior.
