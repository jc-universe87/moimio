# Manual do usuário

Este manual explica como usar o Moimio para organizar um evento do início ao fim. Ele parte do princípio de que você já instalou o Moimio e fez login. Se ainda não fez isso, comece pelo [Guia de instalação](../installation/README.pt-BR.md).

> Este manual trata do **Moimio CE (Community Edition)**, a versão de código aberto que você pode hospedar por conta própria. O mesmo fluxo vale para o produto hospedado em [moimio.app](https://moimio.app): as duas edições usam o mesmo código.

---

## Como ler este manual

Você provavelmente não precisa ler tudo de uma vez. Há dois caminhos recomendados:

### → Se você quer organizar um evento até amanhã

Leia o **[Guia rápido](quick-guide.pt-BR.md)** (uns 10 minutos). Ele mostra um evento completo, da criação à exportação em PDF, sem entrar em detalhes nem em casos especiais. Você vai saber o suficiente para começar.

### → Se você quer entender o produto inteiro

Leia as seções numeradas em ordem. Cada uma trata de uma área do aplicativo. São cerca de 30 minutos no total.

---

## Seções

| # | Seção | O que tem nela |
|---|---|---|
| | [Guia rápido](quick-guide.pt-BR.md) | Um evento, do começo ao fim, em dez minutos de leitura. |
| 01 | [Primeiros passos](01-getting-started.pt-BR.md) | Configuração inicial e login. O layout da área administrativa, as três fases do evento (Configuração, Inscrição, Evento), contas de usuário, a lista de eventos, sua primeira sessão. |
| 02 | [Eventos e inscrições](02-events-and-registration.pt-BR.md) | Como criar eventos. O painel de configuração. Como configurar o formulário de inscrição, os campos personalizados e os códigos de grupo. Abrir e fechar as inscrições. E-mails de confirmação. |
| 03 | [Participantes](03-people.pt-BR.md) | A tabela Participantes. Status (pendente / confirmado / cancelado). Edição direto na tabela, códigos de grupo, notas, importação de CSV, exportações. |
| 04 | [Marcações](04-marks.pt-BR.md) | Etiquetas coloridas para identificar participantes. O editor de marcações. Prioridade das marcações em cada tipo de grupo. Reservar um grupo para uma marcação. |
| 05 | [Tipos de grupo e grupos](05-group-types-and-units.pt-BR.md) | Tipos de grupo (Atribuição de quartos, Grupos pequenos e outros que você criar) e os grupos dentro deles. Capacidade, gênero, restrições por marcação. Deixar alguém de fora de um tipo de grupo. Exportar e importar uma estrutura. |
| 06 | [Motor de atribuição](06-allocation-engine.pt-BR.md) | O que o motor faz, em linguagem simples. Configurações do motor. Revisar uma proposta, bloquear grupos, rodar de novo, ajustes manuais, histórico e motivos. |
| 07 | [Check-in](07-check-in.pt-BR.md) | A lista de check-in. Colunas de check-in personalizadas. Sincronização em tempo real entre tablets e celulares. |
| 08 | [Relatórios e PDFs](08-reports-and-pdf-exports.pt-BR.md) | Os blocos do painel. Listas em PDF nos formatos Compacto, Presença e Detalhado. Marcações nos PDFs. Exportações em CSV. |
| 09 | [Exportação de dados e LGPD/GDPR](09-data-export-gdpr.pt-BR.md) | A exportação dos dados pessoais de um participante. Editar, remover e apagar. Link para o aviso de privacidade. Backups completos ou só da estrutura, restauração, mudança de workspace. |
| 10 | [Vários eventos e arquivo](10-multi-event-and-archive.pt-BR.md) | A lista de eventos. Arquivar e desarquivar. Criar um novo evento a partir das configurações de um anterior. Vários eventos ao mesmo tempo. |
| 11 | [Equipe e permissões](11-staff-permissions.pt-BR.md) | Contas de usuário (Superadministrador, Equipe) e exclusão de usuários. A equipe de cada evento: Administrador do evento ou Equipe. As cinco configurações de permissão. |

---

## Convenções usadas

- Texto em **negrito** indica um elemento da tela em que você pode clicar: um botão, uma aba, um item de menu.
- Texto em `monoespaçado` indica um valor, uma chave de configuração ou um conceito técnico.
- O sinal ▸ indica uma sequência de cliques, por exemplo **Usuários ▸ + Novo usuário ▸ Criar usuário**.
- Há capturas de tela onde elas ajudam a se localizar na interface; algumas seções usam mais texto quando o layout é simples ou muda com frequência. Com o tempo, as capturas podem ficar um pouco diferentes da versão atual.

---

## Quando o manual não responde à sua dúvida

Três lugares para procurar:

- **[Perguntas frequentes](../faq.md)** (em inglês): dúvidas comuns sobre escopo, hospedagem, escala, LGPD/GDPR.
- **[Glossário](../glossary.md)** (em inglês): definições dos termos próprios do Moimio (cluster, marcação, código de grupo etc.).
- **A documentação da API gerada automaticamente** em `http://localhost:6121/docs` (ou onde estiver o seu backend): para quem desenvolve integrações com a API.

Se nada disso ajudar, [abra uma issue](https://github.com/jc-universe87/moimio/issues/new?template=feature_request.md). "O manual não explicou X" é um pedido de melhoria perfeitamente válido, e é justamente o tipo de retorno que deixa a documentação melhor.
