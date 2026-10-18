🌐 [English](08-reports-and-pdf-exports.md) · [Deutsch](08-reports-and-pdf-exports.de.md) · [한국어](08-reports-and-pdf-exports.ko.md) · [Español](08-reports-and-pdf-exports.es.md) · **Português (Brasil)** · [Français](08-reports-and-pdf-exports.fr.md)

# 08 — Relatórios e PDFs

A página **Relatórios** mostra de relance os principais números do seu evento e é onde você baixa as listas para imprimir: alguns blocos de resumo no topo e, abaixo, as listas em PDF de cada tipo de grupo.

<p align="center">
  <img src="../assets/reports.png" alt="Página Relatórios com os blocos de resumo, o seletor de idioma do PDF e os downloads de listas" width="560">
  <br>
  <em>Página Relatórios: blocos de resumo e downloads de listas</em>
</p>

---

## Onde encontrar Relatórios

**Relatórios**, na barra lateral, durante as fases de Inscrição e Evento. Administradores e Superadministradores sempre a veem; membros da equipe a veem se as permissões deles incluírem relatórios.

A página tem duas partes:

- **Em cima: os blocos de resumo**, para inscrição, atribuição e (durante a fase de Evento) check-in.
- **Embaixo: Downloads de listas**, uma linha por tipo de grupo, com os botões **Compacto** e **Presença**.

---

## Os blocos de resumo

### Inscrição

- **Destaque:** o número de inscrições ativas (confirmadas mais pendentes; as canceladas não entram na conta).
- **Abaixo:** o detalhamento, por exemplo `26 confirmados · 5 pendentes · 2 cancelados`.

De relance: as pessoas estão se inscrevendo, e as pendentes estão confirmando?

### Atribuição

- **Destaque:** a proporção de participantes ativos que estão em pelo menos um grupo, por exemplo `87%`.
- **Abaixo:** `27 de 31 participantes alocados em grupos`.

Isto conta pessoas, não vagas. 100% significa que todos os participantes ativos estão em pelo menos um dos seus tipos de grupo. Quem está em um quarto e também em um grupo pequeno conta uma vez só.

### Check-in *(só na fase de Evento)*

- **Destaque:** a proporção de participantes ativos que já fizeram check-in, por exemplo `82%`.
- **Abaixo:** `28 de 34 com check-in`.

Este bloco só aparece na fase de Evento; antes disso, não há check-in a fazer.

---

## Downloads de listas

Acima da lista de tipos de grupo há duas opções que valem para todos os downloads da página:

- **Idioma do PDF**: o idioma em que o PDF é impresso, seja qual for o idioma em que você usa o Moimio. Escolha entre English, Deutsch, 한국어, Español, Português (BR) e Français. Ele começa igual ao idioma da sua interface, e assim um organizador alemão pode imprimir uma lista em inglês para uma equipe internacional.
- **Incluir capa**: adiciona uma primeira página com o nome do evento, as datas, o local e os números da atribuição. Vem desativado para economizar papel; é útil ao entregar uma lista a um coordenador ou guardar uma cópia para registro.

Cada linha de tipo de grupo mostra o nome e um resumo como `5 grupos · 87% dos participantes`, com dois botões:

- **Compacto**: nomes agrupados por grupo, para pranchetas e portas. A4 retrato.
- **Presença**: uma folha com caixa de seleção, linha de assinatura e coluna de observações para cada pessoa, para a equipe do check-in. A4 paisagem.

### A lista detalhada

Um terceiro formato, a lista **Detalhada**, traz os dados de contato completos (nome, gênero, data de nascimento, telefone, e-mail, código de grupo). Como ela contém dados pessoais, não fica na página Relatórios. Baixe-a pelo quadro de atribuição: **Atribuição ▸** abra um tipo de grupo **▸ ⋯ ▸ Lista detalhada (com dados pessoais)** ou **Detalhado + capa**. O seletor de idioma **PDF**, logo acima dessas duas opções, define o idioma. Administradores sempre podem baixá-la; membros da equipe precisam de permissão para ver Participantes.

---

## O que há em cada PDF

Toda página tem um cabeçalho com o nome do evento, o tipo de grupo e o formato, além de uma faixa colorida para facilitar a organização de folhas soltas. O rodapé mostra o nome e as datas do evento e *"Página 2 de 5"*.

### Compacto

Para cada grupo:

- Uma barra de título com o nome do grupo, quantas pessoas há nele em relação à capacidade (com uma pequena barra de ocupação) e a restrição de gênero, se houver.
- Uma lista com marcadores dos membros, em ordem de sobrenome. Cada linha mostra o nome, os pontinhos das marcações, a inicial do gênero e o código de grupo.
- Grupos com mais de 6 pessoas são impressos em duas colunas para economizar papel.

### Presença

A4 paisagem, com as linhas **RECEPÇÃO** e **DATA** em branco no topo. Para cada grupo, uma barra de título e depois uma linha por pessoa: caixa de seleção, nome (com os pontinhos das marcações), código de grupo, telefone, linha de assinatura e espaço para observações. Feita para ser impressa, entregue a alguém com uma prancheta e marcada à mão conforme as pessoas chegam.

### Detalhada

A4 paisagem. Para cada grupo, uma barra de título e uma tabela com nome (com os pontinhos das marcações), gênero, data de nascimento, telefone, e-mail e código de grupo. Use quando alguém precisar dos dados de contato completos, por exemplo um líder de grupo ou um parceiro externo.

### A página "Não alocados"

Se alguém deste tipo de grupo não estiver em nenhum grupo, todos os formatos (Compacto, Presença e Detalhado) terminam com uma página **NÃO ALOCADOS**, que lista essas pessoas com telefone e e-mail, em dois blocos:

- **EXCLUÍDOS**: pessoas que você deixou de fora deste tipo de grupo de propósito (veja a [seção 06](06-allocation-engine.pt-BR.md#como-deixar-alguém-de-fora-de-um-tipo-de-grupo)).
- **SEM VAGA**: pessoas que simplesmente ainda não foram colocadas em um grupo.

Um bloco é omitido quando estaria vazio, e a página inteira é omitida quando todos estão atribuídos. Inscrições canceladas nunca aparecem.

### Capa

Quando **Incluir capa** está marcado, o PDF começa com uma capa que mostra o nome, as datas e o local do evento, o tipo de grupo e o formato, três números (**TOTAL**, **ALOCADOS** e **NÃO ALOCADOS**, este último destacado quando não é zero) e quando e por quem o PDF foi gerado.

---

## Marcações nos PDFs

As marcações visíveis em **Atribuição** aparecem como pequenos pontinhos coloridos logo depois do nome de cada pessoa, nos três formatos. Uma legenda **Marcações** no fim da lista mostra qual cor corresponde a qual marcação, listando só as marcações que de fato aparecem naquele PDF.

Se alguém tiver mais marcações do que cabem (4 pontinhos no Compacto e no Detalhado, 3 na folha de Presença), as que sobram ficam de fora. As marcações aparecem em ordem alfabética, para que todas as impressões fiquem iguais.

---

## Uma visualização rápida para imprimir

No quadro de atribuição, **⋯ ▸ ↗ Abrir visão geral** abre uma visualização somente leitura do tipo de grupo em uma nova aba, com um botão **🖨 Imprimir**. É útil para imprimir rapidamente a situação atual sem baixar um PDF.

---

## E o CSV?

As exportações em planilha ficam na página **Participantes**, não em Relatórios. Clique em **↓ Exportar ▾** e escolha **Lista completa de participantes** (todos os campos, incluindo as colunas **Status**, **Checked In**, **Marks** e **Excluded From**) ou **Apenas nomes + e-mails** (para uma ferramenta de lista de e-mails). O CSV de Participantes não mostra quem está em qual grupo; para isso, use as listas em PDF ou um backup.

---

## Quando a página está vazia

Se ainda não houver inscrições nem tipos de grupo, a página mostra apenas *"Abra as inscrições para começar a coletar dados. Os relatórios serão preenchidos automaticamente a partir disso."* Se não houver tipos de grupo, a seção de listas mostra *"Ainda não há tipos de grupo."* Tudo vai sendo preenchido conforme chegam as inscrições e as atribuições.

---

## Próximos passos

A [seção 09 — Exportação de dados e LGPD/GDPR](09-data-export-gdpr.pt-BR.md) trata das exportações de dados por participante (o caminho dos artigos 15 e 20), dos backups por evento e de como o Moimio lida com exclusão e apagamento de dados.
