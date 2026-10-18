# 11 — Equipe e permissões

O Moimio tem dois tipos de conta de usuário e uma equipe para cada evento. Esta seção trata das duas coisas: quem é Superadministrador, quem é Equipe e como dar a alguém acesso a um evento específico, com as permissões certas.

<p align="center">
  <img src="../assets/staff-permissions.png" alt="O formulário Atribuir usuário ao evento, com o seletor Usuário, a lista suspensa Função, Copiar permissões de e as cinco configurações de permissão" width="560">
  <br>
  <em>Adicionando alguém à equipe de um evento</em>
</p>

---

## Contas de usuário

As contas são gerenciadas em Barra lateral ▸ **Usuários** (em **Gerenciar**), na página **Gerenciamento de usuários**.

### Superadministrador

O primeiro Superadministrador é criado durante a configuração inicial. Outros podem ser adicionados em **Gerenciamento de usuários**; só um Superadministrador pode tornar outra pessoa Superadministrador. Os Superadministradores:

- Têm acesso total a todos os eventos.
- Podem criar eventos e gerenciar usuários.
- São os únicos que podem arquivar, desarquivar, excluir ou fixar eventos e restaurar backups.
- São os únicos que veem **Backup**, **Workspace** e **Webhooks** na barra lateral.

Os Superadministradores não precisam ser adicionados à equipe de um evento: eles já têm acesso a tudo.

### Equipe

Uma conta de **Equipe** é só um login. **Sozinha, uma conta de Equipe não dá acesso a nenhum evento.** O acesso vem de ser adicionado à equipe de um evento, com uma função e permissões para aquele evento. Um usuário da Equipe que ainda não está em nenhuma equipe vê a tela **Aguardando sua primeira atribuição** ao entrar.

Dois recursos extras podem ser marcados para qualquer usuário da Equipe:

- **Permitir que este administrador gerencie usuários**: a pessoa pode abrir **Gerenciamento de usuários** e criar, editar, desativar e excluir contas de Equipe (mas não de Superadministradores).
- **Pode criar novos eventos**: a pessoa ganha o botão **+ Novo evento**. Quem cria um evento se torna automaticamente o Administrador do evento.

### Como adicionar, editar e remover contas

- **+ Novo usuário** abre o formulário: **Nome completo**, **E-mail**, **Senha**, **Função** e os dois recursos extras. Clique em **Criar usuário**.
- Na lista, o lápis cinza edita o nome, a função e os recursos extras de um usuário.
- **Desativar** impede alguém de entrar, sem excluir nada. **Reativar** devolve o acesso.
- O ícone vermelho de lixeira exclui a conta de vez (**Excluir permanentemente**). Você não pode excluir a si mesmo.

**Excluir um usuário sempre funciona, não importa o que ele tenha feito no Moimio.** Os lugares dele nas equipes dos eventos vão junto, assim como as notas não publicadas (rascunhos). As notas que ele publicou permanecem e aparecem como escritas por **[usuário removido]**. As entradas dele no histórico de atribuição também permanecem, igualmente como **[usuário removido]**.

Desativar é a opção mais suave se você estiver em dúvida: pode ser desfeita; a exclusão, não.

---

## A equipe de cada evento

Todo evento tem a sua própria lista de membros da equipe. Cada um tem:

- **Uma função neste evento:** **Administrador do evento** ou **Equipe**.
- **Permissões** (usadas só quando a função é Equipe).

Gerencie a equipe pelo cartão **Painel de configuração ▸ Colaboradores** durante a fase de Configuração, ou por **Mais ▸ Equipe e permissões** depois que as inscrições abrirem. Os dois abrem o mesmo painel **Equipe e permissões**.

Para adicionar pessoas, você precisa ser Superadministrador ou ter **Permitir que este administrador gerencie usuários**: a lista de pessoas para escolher vem do Gerenciamento de usuários. A pessoa precisa ter uma conta antes de ser adicionada.

### Função Administrador do evento

**Administrador do evento** dá acesso total a *este evento*. Ele pode:

- Editar os detalhes do evento, o formulário de inscrição e os tipos de grupo.
- Abrir e fechar as inscrições.
- Rodar a atribuição, confirmar os resultados e deixar pessoas de fora de um tipo de grupo.
- Usar o check-in, inclusive prepará-lo antes do evento.
- Criar, editar e excluir marcações.
- Baixar relatórios e exportações, incluindo a exportação de dados pessoais de um participante.
- Remover participantes.
- Gerenciar a equipe do evento (com o recurso de gerenciamento de usuários; veja acima).

Arquivar, excluir e restaurar eventos continuam sendo tarefas dos Superadministradores. Para Administradores do evento, as configurações de permissão são ignoradas: o acesso total já está implícito.

### Função Equipe

Quem é **Equipe** em um evento só pode fazer o que as suas permissões permitem. As cinco configurações de permissão estão descritas abaixo.

---

## As cinco configurações de permissão

Cada configuração é independente. Um membro da equipe pode ter qualquer combinação: por exemplo, Participantes em somente leitura mais Marcações, ou só Relatórios.

### Acesso a participantes (Sem acesso / Somente leitura / Leitura e escrita)

A tabela Participantes e os dados das inscrições.

- **Somente leitura**: vê a lista de participantes; pode buscar, filtrar e ver detalhes.
- **Leitura e escrita**: também pode editar dados, mudar status e códigos de grupo, inscrever pessoas e atribuir marcações.
- **Sem acesso**: o item Participantes fica oculto.

Remover participantes e exportar dados pessoais são tarefas exclusivas dos Administradores do evento.

### Acesso à atribuição (Sem acesso / Somente leitura / Leitura e escrita)

O quadro de atribuição.

- **Somente leitura**: vê quem está em qual grupo, em todos os tipos de grupo.
- **Leitura e escrita**: pode arrastar pessoas entre os grupos e adicionar, editar ou remover grupos.
- **Sem acesso**: o item Atribuição fica oculto.

Rodar a atribuição, confirmá-la, mudar as configurações dos tipos de grupo e deixar pessoas de fora de um tipo de grupo são tarefas dos Administradores do evento.

### Acesso ao check-in (caixa de seleção + opção extra)

A caixa principal permite que o membro da equipe veja a lista de check-in e marque as pessoas quando o evento começar.

Quando ela está marcada, aparece uma segunda opção: **Acesso antes do início do evento**. Com ela, a pessoa pode abrir o check-in durante a fase de Inscrição e adicionar ou excluir colunas de check-in antes das chegadas. É útil quando um coordenador designado, que nem sempre é Administrador do evento, prepara o check-in. Sem essa opção, a equipe do check-in pode marcar as caixas, mas não mudar as colunas.

Não existe check-in somente leitura: marcar as pessoas é justamente o objetivo. A opção extra controla *quando* a pessoa tem acesso, não quanto.

Superadministradores e Administradores do evento sempre têm acesso total ao check-in, inclusive antes do evento.

### Acesso a relatórios (caixa de seleção)

A página Relatórios.

- **Marcada**: vê os relatórios e pode baixar as listas em PDF Compacto e Presença.
- **Desmarcada**: o item Relatórios fica oculto.

A lista **Detalhada** e a planilha de participantes contêm dados pessoais, então também exigem **Acesso a participantes**; só o acesso a relatórios não basta.

### Acesso a marcações (caixa de seleção)

- **Marcada**: vê o item Marcações na barra lateral; pode criar marcações, editar ou excluir as marcações que *ela mesma* criou (não as de outras pessoas) e atribuir marcações aos participantes.
- **Desmarcada**: sem o item Marcações.

**Todos com acesso ao evento podem ver as marcações.** Quem pode ver os participantes pode clicar em uma marcação para ver o que ela significa. O acesso a marcações diz respeito a criá-las e atribuí-las. (**Leitura e escrita** em Participantes também permite atribuir marcações.)

---

## Como adicionar alguém a um evento

No cartão **Colaboradores** ou em **Equipe e permissões**:

1. Clique em **+ Atribuir usuário**.
2. Em **Usuário**, escolha alguém (**Selecione um usuário**). A lista mostra as contas ativas que ainda não estão neste evento.
3. Escolha uma **Função**: **Equipe** ou **Administrador do evento**.
4. Para Equipe, defina as cinco permissões.
5. Clique em **Atribuir usuário**.

### Copiar permissões de

Quando o evento já tem membros da Equipe, **Copiar permissões de** permite preencher o formulário com as configurações de outra pessoa (**Selecione um membro da equipe**). Ajuste o que quiser antes de salvar.

Dica: ao criar o evento do ano que vem, você pode copiar a equipe inteira; veja a [§10](10-multi-event-and-archive.pt-BR.md#como-criar-um-evento-novo-a-partir-de-um-anterior).

---

## Como editar ou remover alguém de um evento

A linha de cada membro da equipe tem um lápis cinza e um ícone vermelho de lixeira.

- **Editar** (lápis): o mesmo formulário, preenchido com a função e as permissões atuais. Clique em **Salvar**.
- **Remover** (lixeira): confirme em **Remover usuário do evento?**. O acesso da pessoa a este evento termina. A conta não é alterada: ela continua com os outros eventos.

Se a pessoa estiver com o evento aberto quando for removida, o próximo clique dela mostra uma tela de "sem acesso".

---

## Desativar um usuário x removê-lo de um evento

São dois alcances diferentes:

- **Remover de um evento** → encerra o acesso a *um* evento. A pessoa mantém o login e os outros eventos.
- **Desativar um usuário** (em Gerenciamento de usuários) → a pessoa não consegue mais entrar. Os lugares dela nas equipes continuam registrados, mas não podem ser usados.

Desative quando alguém sair da organização. Remova de um evento quando "ela terminou este evento, mas continua na equipe do ano que vem".

---

## Como acompanhar o que acontece

O histórico no painel de perfil de cada participante (o ícone **ⓘ Ver perfil**) mostra quem colocou ou moveu a pessoa, e quando. As principais ações administrativas (criar, arquivar e excluir eventos, remover participantes, exportar dados pessoais) também ficam registradas no log do servidor (`docker compose logs backend` em uma instalação auto-hospedada).

A exportação de dados do próprio participante não mostra qual membro da equipe fez cada movimentação (veja a [§09](09-data-export-gdpr.pt-BR.md)).

---

## Próximos passos

Este é o fim do manual do usuário. Para saber mais (conteúdo em inglês):

- [Glossary](../glossary.md): termos próprios do Moimio.
- [FAQ](../faq.md): perguntas frequentes.
- [GDPR compliance](../gdpr-compliance.md): postura de privacidade e detalhes técnicos.
- [Moving a workspace to your own Moimio](../moving-a-workspace.md): como levar todos os eventos para um servidor que você mantém.
- [Data model](../data-model.md): referência do esquema de dados para desenvolvedores e integradores.
