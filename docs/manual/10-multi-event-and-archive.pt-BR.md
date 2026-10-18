🌐 [English](10-multi-event-and-archive.md) · [Deutsch](10-multi-event-and-archive.de.md) · [한국어](10-multi-event-and-archive.ko.md) · [Español](10-multi-event-and-archive.es.md) · **Português (Brasil)** · [Français](10-multi-event-and-archive.fr.md)

# 10 — Vários eventos e arquivo

O Moimio parte do princípio de que uma organização realiza mais de um evento. Depois que você configura um formulário de inscrição, tipos de grupo e uma equipe, muitas vezes vai querer reaproveitar essa configuração. Esta seção explica como organizar vários eventos em um mesmo Moimio, como funciona o arquivamento e como criar um evento novo a partir de um anterior.

<p align="center">
  <img src="../assets/events-list.png" alt="A lista de eventos com as abas Ativos, Passados e Arquivados, cartões de evento com etiquetas de fase e os botões + Novo evento e De backup" width="720">
  <br>
  <em>A lista de eventos</em>
</p>

---

## A lista de eventos

Barra lateral ▸ **Eventos**. Quando você está dentro de um evento, use **Todos os eventos**, no topo da barra lateral, para voltar para cá.

No topo há uma caixa de busca e, em seguida, três abas, cada uma com uma contagem:

- **Ativos**: eventos que não estão arquivados e ainda não terminaram (incluindo eventos sem datas definidas). Os eventos fixados aparecem primeiro.
- **Passados**: eventos cuja data de término já passou.
- **Arquivados**: eventos que foram arquivados (veja abaixo). Superadministradores sempre veem esta aba; os demais só a veem quando há algo nela.

Cada cartão mostra o nome do evento, uma etiqueta indicando em que ponto ele está (**Configuração**, **Inscrição**, **Evento**, **Passado** ou **Arquivado**), as datas e o local, e um número de destaque, como quantas pessoas estão inscritas. Os Superadministradores também têm um menu **⋯** em cada cartão, com **Fixar no topo** / **Desafixar**, **Arquivar** / **Desarquivar** e **Excluir evento**.

O botão **+ Novo evento** cria um evento do zero. **↑ De backup** leva você à página Backup, para restaurar um evento a partir de um arquivo de backup (veja a [§09](09-data-export-gdpr.pt-BR.md#backups)). Os dois botões aparecem para Superadministradores e para membros da equipe que receberam **Pode criar novos eventos**.

---

## Fechar as inscrições x arquivar

São duas coisas diferentes, que muita gente confunde:

- **Fechar as inscrições** faz parte da vida normal de um evento: Configuração → Inscrição → Evento. Fechar impede novas inscrições e leva o evento para a fase de Evento, em que você faz a atribuição e o check-in. Veja a [§02](02-events-and-registration.pt-BR.md).
- **Arquivar** guarda o evento. Ele fica somente para leitura e vai para a aba **Arquivados**, mas todos os dados são mantidos.

Um evento pode ser arquivado a qualquer momento: um rascunho que você abandonou ou (o caso mais comum) um evento que já acabou e que você quer guardar. O arquivamento é **reversível**.

---

## Como arquivar um evento

### Onde fica o botão

O arquivamento é para **Superadministradores**. Qualquer um destes caminhos funciona:

- Lista de eventos ▸ **⋯** no cartão do evento ▸ **Arquivar**
- **Painel de configuração ▸ Zona de perigo ▸ Arquivar** (enquanto o evento ainda está na Configuração)
- **Detalhes do evento ▸ Zona de perigo ▸ Arquivar**

A Zona de perigo vem recolhida para evitar cliques acidentais; clique no título dela para abri-la. Confirme com **Arquivar** na janela **Arquivar este evento?**.

### O que acontece quando você arquiva

- O evento vai para a aba **Arquivados** da lista de eventos.
- O evento fica **somente para leitura para todos, inclusive Superadministradores**. Para mudar qualquer coisa, desarquive primeiro.
- O formulário público de inscrição recusa novas inscrições.
- Os dados existentes (participantes, atribuições, check-ins, notas) continuam intactos.
- Um aviso **Arquivado** aparece no topo das páginas do evento.

### Como desarquivar

Nos mesmos lugares: **⋯ ▸ Desarquivar** no cartão, ou **Zona de perigo ▸ Desarquivar**. O evento volta a poder ser editado e reaparece em **Ativos** ou **Passados**, conforme as datas. As inscrições e o check-in continuam de onde pararam.

---

## Como criar um evento novo a partir de um anterior

Quando você realiza um evento que se repete (mesmo formulário de inscrição, quartos parecidos, a mesma equipe), copiar a configuração da última vez poupa muito trabalho.

### Como fazer

1. Lista de eventos ▸ **+ Novo evento**.
2. Digite o nome do novo evento.
3. Marque **Usar configurações de outro evento** e escolha o evento de onde copiar.
4. Em **O que copiar**, desmarque o que não quiser. Os cinco vêm marcados:
   - **Marcações**: as definições das marcações (nome, cor etc.), não quem as tinha.
   - **Formulário de inscrição**: quais campos padrão aparecem e quais são obrigatórios.
   - **Campos personalizados**: as suas próprias perguntas.
   - **Tipos de grupo**: todos os tipos de grupo, com seus grupos, capacidades e configurações de gênero. Os grupos restritos a uma marcação são ligados à cópia daquela marcação no novo evento; se você não copiar as marcações, essas restrições são descartadas.
   - **Membros da equipe**: todos da equipe do evento anterior, com a mesma função e as mesmas permissões.
5. Clique em **Criar evento**.

O novo evento começa na Configuração, pronto para você adicionar as datas e abrir as inscrições. **Nenhum dado de participante é copiado, nunca**: nem participantes, nem atribuições, nem check-ins, nem notas.

Você só pode copiar de eventos aos quais tem acesso.

### Como copiar entre instalações

Para levar a configuração para outro Moimio, ou para um evento que já existe, exporte as partes como arquivos: **Exportar tipos de grupo** / **Importar tipos de grupo**, do lado da atribuição (veja a [§05](05-group-types-and-units.pt-BR.md)), e **Exportar formulário** / **Importar formulário**, para o formulário de inscrição (veja a [§02](02-events-and-registration.pt-BR.md)). Esses arquivos contêm só configuração, nunca dados pessoais.

### E os backups?

Os backups (veja a [§09](09-data-export-gdpr.pt-BR.md#backups)) são o outro caminho: um backup completo guarda tudo, inclusive os participantes. **Copie as configurações ao começar uma nova edição; use um backup como cópia de segurança ou para levar um evento para outro Moimio.** Um backup **Apenas estrutura (compatível com GDPR)** é um modelo que pode ser compartilhado, sem nenhum dado pessoal.

---

## Vários eventos ao mesmo tempo

Nada no Moimio impede isso. Cada evento é um mundo à parte: participantes próprios, tipos de grupo próprios, equipe própria. Uma mesma pessoa que se inscreve em dois eventos é tratada como duas inscrições separadas, uma por evento.

Na prática, vale saber:

- **Trocar de evento.** Use **Todos os eventos**, no topo da barra lateral, e escolha outro evento. Todas as funções veem esse link.
- **O acesso da equipe é por evento.** Um membro da equipe no Evento A não ganha acesso automático ao Evento B. Adicione a pessoa a cada evento (ou copie os **Membros da equipe** ao criar o novo).
- **Os campos personalizados são por evento.** A pergunta "Tamanho da camiseta" do Evento A é separada da do Evento B, mesmo que o texto seja igual.
- **Os tipos de grupo são por evento.** A "Atribuição de quartos" do Evento A não tem nada a ver com a "Atribuição de quartos" do Evento B.

Essa separação é proposital. Você pode realizar um retiro de mulheres e uma conferência de homens no mesmo Moimio sem que nenhum dado se misture.

---

## Próximos passos

A [seção 11 — Equipe e permissões](11-staff-permissions.pt-BR.md) trata das contas de usuário, da equipe de cada evento e das permissões para Participantes, Atribuição, Check-in, Relatórios e Marcações.
