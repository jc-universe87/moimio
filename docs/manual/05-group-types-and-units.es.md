🌐 [English](05-group-types-and-units.md) · [Deutsch](05-group-types-and-units.de.md) · [한국어](05-group-types-and-units.ko.md) · **Español** · [Português (Brasil)](05-group-types-and-units.pt-BR.md) · [Français](05-group-types-and-units.fr.md)

# 05 — Tipos de grupo y unidades

El motor de asignación coloca a los participantes en **unidades** (cada habitación, grupo, mesa o taller concreto), que se organizan en **tipos de grupo**. Esta sección explica ambos conceptos: qué son, cómo prepararlos y qué decisiones determinan después su comportamiento.

Durante la Configuración, la tarjeta **Tipos de grupo** del centro de configuración es donde creas y editas los tipos de grupo (necesitas al menos uno para poder abrir las inscripciones). Más adelante, y para añadir las habitaciones y los grupos en sí, usa la página **Asignación**.

---

## El modelo en un párrafo

Un **tipo de grupo** es una forma de asignación. Contiene **unidades**: las habitaciones, grupos, talleres o equipos concretos que lo componen. Así, «Asignación de habitaciones» es un tipo de grupo y «Suite Vista al Lago» es una unidad dentro de él. Un participante se coloca en una unidad, o en varias, según la regla del tipo de grupo. En la aplicación, las unidades se llaman con la etiqueta propia del tipo de grupo («Habitación», «Grupo», «Mesa»…), así que verás botones como **+ Añadir Habitación**.

---

## Con qué empiezas

Cada evento nuevo se crea con dos tipos de grupo ya preparados:

- **Asignación de habitaciones**: una habitación por persona, todavía sin habitaciones dentro.
- **Grupos pequeños**: un grupo por persona, todavía sin grupos dentro.

Estos dos tipos de grupo predefinidos aparecen en el idioma en que trabaja cada organizador (por ejemplo, «Zimmerbelegung» y «Kleingruppen» en alemán), y las listas impresas usan el idioma del PDF. En cuanto renombras uno, tu nombre se mantiene en todos los idiomas. Si vuelves a escribir un nombre predefinido (por ejemplo, «Asignación de habitaciones»), vuelve a traducirse.

Puedes renombrarlos, eliminarlos o añadir más tipos de grupo junto a ellos. Si creas un evento copiando la configuración de uno anterior, tendrás los tipos de grupo de ese evento en su lugar.

---

## Crear y editar tipos de grupo

En la página **Asignación**, haz clic en **+ Añadir tipo de grupo**. (En el centro de configuración, abre la tarjeta **Tipos de grupo** y haz clic allí en **+ Añadir tipo de grupo**). Defines:

### Nombre del tipo de grupo

Cómo se llama el tipo de grupo (p. ej. «Habitaciones», «Grupos pequeños», «Mesas»). Aparece en la página Asignación y en los informes. Usa las palabras que usaría tu equipo.

### Nombre

La palabra para **una** unidad de este tipo de grupo, p. ej. «Habitación», «Equipo» o «Sesión». Se usa en botones y etiquetas («+ Añadir Habitación», «4 × Habitación»). Si lo dejas vacío, Moimio dice simplemente «Grupo».

### ¿Puede una persona estar en más de uno?

- **No, solo uno** (p. ej. habitaciones): un participante pertenece a **una** sola unidad de este tipo de grupo. Las habitaciones son el ejemplo clásico: duermes en una habitación, no en tres. Lo mismo ocurre con las mesas, los equipos de trabajo y los grupos pequeños.
- **Sí, varios**: un participante puede pertenecer a **varias** unidades de este tipo de grupo. Los talleres son el ejemplo clásico: alguien puede asistir a varios a lo largo de un evento. Lo mismo ocurre con las sesiones, los turnos y las actividades opcionales.

Si no lo tienes claro, pregúntate: «¿Podría esta persona estar legítimamente en dos de estos a la vez?». Si la respuesta es sí, elige **Sí, varios**.

Haz clic en **Crear**. El tipo de grupo aparece como una tarjeta en la página Asignación, que muestra cuántas unidades tiene y cuántas personas están asignadas, sin asignar y excluidas.

Para cambiar un tipo de grupo más adelante, usa los controles de su tarjeta:

- **Haz clic en el título** para renombrarlo directamente (Intro guarda, Esc cancela).
- **Icono del lápiz**: abre el editor con los mismos tres campos.
- **↑ ↓** (o arrastra la tarjeta en un ordenador): cambia el orden de los tipos de grupo.
- **Icono rojo de la papelera**: lo elimina. El aviso lo dice claramente: el tipo de grupo, todo su contenido y todas las asignaciones de participantes se eliminan permanentemente. No se puede deshacer.

### Exportar e importar una estructura

El menú **⋯** junto a **+ Añadir tipo de grupo** tiene **Exportar tipos de grupo** e **Importar tipos de grupo**. Al exportar se guardan todos los tipos de grupo del evento (con sus unidades, capacidades, reglas de género, restricciones por marca y configuración del motor) en un archivo JSON. Importa ese archivo en otro evento (incluso en otro servidor de Moimio) para reutilizar la estructura. El archivo solo contiene configuración, nunca datos de participantes.

Conviene saber:

- Al importar se **añaden** los tipos de grupo del archivo; nunca se sobrescribe ni se fusiona con lo que ya hay. Si importas en un evento nuevo, tendrás los tipos de grupo del archivo *más* los dos predefinidos, así que elimina los que no necesites. Si importas dos veces el mismo archivo, tendrás duplicados.
- Las restricciones y prioridades de las marcas se transfieren por el nombre de la marca. Si el evento de destino tiene una marca con el mismo nombre, se vinculan; si no, se descartan.
- Las descripciones y las notas de las unidades no se incluyen.

### Configuración del motor

Cada tipo de grupo tiene su propia configuración del motor, que se abre con el icono ⚙ **Configuración del motor**, junto al botón **Asignación automática** dentro del tipo de grupo. Los ajustes aparecen en el orden en que los aplica el motor:

- **Incluir participantes sin confirmar** (por defecto: activado)
- **Mantener juntos los códigos de grupo** (por defecto: activado)
- **Dividir códigos de grupo si es necesario** (por defecto: activado; en gris mientras Mantener juntos los códigos de grupo está desactivado)
- **Un código de grupo ocupa un grupo entero** (por defecto: desactivado)
- **Aplicar las marcas en este orden** (ver la [sección 4](04-marks.es.md))
- **Mantener juntas a las personas del mismo género** (por defecto: activado)
- **Equilibrar el tamaño de los grupos** (por defecto: activado)

Puedes cambiarlos en cualquier momento; vuelve a pulsar Asignación automática para aplicarlos. Qué hace cada uno se explica en la [sección 6](06-allocation-engine.es.md).

### Confirmar un tipo de grupo

Cuando estés conforme con la asignación de un tipo de grupo, haz clic en **Confirmar tipo de grupo** en su tarjeta (o en **Confirmar este tipo de grupo →** dentro de él, cuando todos estén asignados). La etiqueta de estado cambia a **Confirmado** para todo el equipo. Es una señal, no un bloqueo: cualquier cambio posterior lo reabre automáticamente, y **Reabrir para editar** lo hace a mano. Consulta la [sección 6](06-allocation-engine.es.md).

---

## Unidades dentro de un tipo de grupo

Una vez creado el tipo de grupo, añade sus unidades. En la página **Asignación**, haz clic en la tarjeta del tipo de grupo para abrirlo y luego en **+ Añadir Habitación** (o lo que hayas puesto en **Nombre**).

Para cada unidad defines:

### Nombre

Cómo se llama la unidad. Usa nombres que signifiquen algo para los participantes: «Suite Vista al Lago» mejor que «Habitación 3», «Equipo Rojo» mejor que «Equipo A», «Taller de cerámica» mejor que «Taller 2». Los nombres se imprimen en las listas y las hojas de registro. También puedes hacer clic en el nombre de una unidad en su tarjeta para renombrarla directamente.

### Descripción

Una línea breve y opcional para tu equipo, p. ej. «Tiene literas» o «Accesible en silla de ruedas». No se imprime en las listas.

### Capacidad

El número máximo de personas. Escribe un número o déjalo vacío: si la casilla queda vacía, se marca **Sin límite de capacidad** y esa unidad admite cualquier número de personas. Al escribir un número se desmarca la casilla; al marcarla se borra el número.

Las unidades con capacidad muestran su ocupación, p. ej. `5/6`; las que no tienen límite muestran un simple recuento. El motor nunca llena una unidad por encima de su capacidad. Si colocas a alguien a mano en una unidad llena, Moimio te pregunta antes de sobrepasarla, y la unidad queda marcada como **capacidad superada**.

### Género

Cada unidad tiene su propio ajuste de género, en todos los tipos de grupo:

- **Mixto** (por defecto): se puede colocar a cualquiera.
- **Solo hombres**: solo participantes de género masculino.
- **Solo mujeres**: solo participantes de género femenino.

Los participantes sin género registrado (no todos los eventos lo preguntan) **no pueden** colocarse en una unidad solo para hombres o solo para mujeres. Es una regla estricta, tanto para el motor como para la colocación manual: el motor prefiere dejarlos sin colocar antes que romperla.

Las restricciones de género importan sobre todo en las habitaciones para dormir. Para talleres, equipos y la mayoría de los demás tipos de grupo, déjalo en **Mixto**.

### Restricción por marca

Cada tarjeta de unidad tiene un botón de marcas ●. Asigna ahí una marca para reservar la unidad a quienes la llevan (la tarjeta muestra entonces «Solo *{marca}*»). Haz clic en **Quitar** para levantar la restricción. Consulta la [sección 4](04-marks.es.md).

### Notas

Cada tarjeta de unidad tiene un icono de notas. Las notas de unidad funcionan como las notas de participante: privadas para ti salvo que marques **Compartir con el equipo**. Se muestran en el tablero, no en las listas.

Las unidades se pueden reordenar con las flechas ↑ ↓ de sus tarjetas (o arrastrándolas en un ordenador), editar con el icono del lápiz y eliminar con el icono rojo de la papelera. Al eliminar una unidad se eliminan permanentemente la unidad y todas sus asignaciones de participantes; esas personas vuelven a la lista de sin asignar.

---

## Mantener a alguien fuera de un tipo de grupo

A veces una persona debe entrar en el reparto de habitaciones pero no en un grupo pequeño (por ejemplo, un ponente que solo viene un día). En lugar de cancelarla, **exclúyela** solo de ese tipo de grupo. Dentro del tipo de grupo, en el tablero de Asignación, puedes:

- pasar el ratón por encima de una persona y hacer clic en el icono de excluir (**Excluir de la asignación**),
- arrastrarla a la lista **Excluidos**, debajo del panel de sin asignar, o
- seleccionar a varias personas y hacer clic en **Excluir** en la barra inferior.

Las personas excluidas salen de cualquier unidad de ese tipo de grupo, el motor no las toca ahí y siguen con normalidad en todos los demás tipos de grupo. La lista **Excluidos (N)** muestra quiénes son; usa el icono de deshacer (**Incluir en la asignación**) para recuperar a alguien. Si asignas a mano a una persona excluida a una unidad, Moimio te pregunta primero (**Asignar de todos modos**) y levanta la exclusión.

Las exclusiones aparecen en la exportación de Participantes (columna **Excluded From**), en el historial y en la exportación de datos del participante, y en una página aparte de la lista en PDF.

---

## Qué se puede cambiar más adelante

| Propiedad | ¿Se puede cambiar más adelante? |
|---|---|
| Nombre del tipo de grupo y etiqueta Nombre | Sí, en cualquier momento. |
| ¿Puede una persona estar en más de uno? | Sí, pero cambiarlo con personas ya colocadas puede dejar asignaciones que ya no encajan con la intención de la regla. Vuelve a ejecutar el motor después. |
| Configuración del motor | Sí, en cualquier momento. Vuelve a ejecutar el motor para aplicarla. |
| Nombre y descripción de la unidad | Sí, en cualquier momento. |
| Capacidad de la unidad | Sí. Si la bajas por debajo del número de personas que ya hay, no se mueve a nadie; la unidad queda marcada como **capacidad superada** hasta que lo corrijas. |
| Restricción de género o por marca de la unidad | Sí. Las personas ya colocadas no se mueven automáticamente; vuelve a ejecutar el motor o muévelas a mano. |
| Añadir unidades nuevas | Sí. Vuelve a ejecutar el motor (por ejemplo, con **Asignar solo nuevos participantes**) para llenarlas. |
| Eliminar unidades | Sí, tras una confirmación. Sus participantes vuelven a sin asignar. |
| Eliminar un tipo de grupo | Sí, tras una confirmación. Todo su contenido se elimina permanentemente. |

Cambiar «¿Puede una persona estar en más de uno?» es el tipo de cambio para el que conviene tener ya un plan claro: pasar de **No, solo uno** a **Sí, varios** en mitad de un evento suele significar replantear la configuración, no solo cambiar el ajuste.

---

## Siguiente paso

La [sección 06 — Motor de asignación](06-allocation-engine.es.md) explica cómo coloca realmente el motor a los participantes en las unidades que has configurado: el orden en que trabaja, los ajustes, los motivos por los que alguien puede quedarse sin colocar y cómo leer la propuesta.
