# 03 — Participantes

La tabla de Participantes es donde pasarás la mayor parte del tiempo durante la fase de Inscripción. Es una lista de todas las personas inscritas en tu evento, con herramientas para verlas, editarlas, confirmarlas, marcarlas y agruparlas.


<p align="center">
  <img src="../assets/people-table.png" alt="Tabla de Participantes con cuadro de búsqueda, filtros de estado, botones Columnas, Exportar e Importar CSV, y acciones por fila" width="560">
  <br>
  <em>Tabla de Participantes con cuadro de búsqueda, filtros de estado, botones Columnas, Exportar e Importar CSV, y acciones por fila</em>
</p>


---

## La tabla de Participantes

Abre **Participantes** desde la barra lateral. Verás una tabla con una fila por inscripción. Las columnas que se muestran por defecto son:

- **N.º**: el número correlativo del participante dentro del evento (p. ej. `#1`, `#12`). Un identificador sencillo y fácil de usar. Siempre visible y siempre en primer lugar.
- **Nombre**: el nombre completo tal como se inscribió, seguido de los puntos de las marcas del participante (ver [Marcas](04-marks.es.md)). Siempre visible.
- **Correo electrónico**.
- **Código de grupo**: el código con el que se inscribió o el que Moimio le generó. Pasa el ratón por encima (o mantén pulsado en un móvil) para ver quién más comparte ese código.
- **Estado**: Pendiente / Confirmado / Cancelado (con colores).
- **Inscrito**: fecha y hora de la inscripción.
- **Notas**: abre las notas de ese participante; un pequeño número indica cuántas hay.
- **Acciones**: controles por fila: **✉ Reenviar** (reenvía el correo de inscripción; no aparece para participantes cancelados), **↓ Exportar datos** (la exportación completa de datos del participante según el RGPD, en JSON) y **Quitar** (elimina al participante de forma reversible en la base de datos). Exportar datos y Quitar son solo para administradores del evento.

Haz clic en **Columnas** para mostrar u ocultar más columnas: **Género**, **Fecha de nacimiento**, **Teléfono**, **Dirección**, **País**, **Iglesia / organización** y **Mensaje** (aparecen en la lista en cuanto al menos un participante las ha rellenado), **Check-in realizado** y todos los campos personalizados de tu formulario de inscripción (en **Campos personalizados**). También puedes arrastrar el encabezado de una columna (por su asa ⠿) para cambiar el orden de las columnas.

La tabla permite:

- **Filtrar por estado.** Botones en la parte superior: **Todos**, **Pendiente**, **Confirmado**, **Cancelado**. En **Todos**, las personas canceladas bajan al final de la lista y sus nombres aparecen tachados.
- **Ordenar**: haz clic en cualquier encabezado de columna; vuelve a hacer clic para invertir el orden.
- **Buscar**: busca por nombre, correo, código de grupo, teléfono, iglesia/organización y nombres de marcas. Es tolerante con acentos, guiones, apóstrofos y grafías alternativas de la diéresis (buscar «Mueller» encuentra «Müller»).

Encima de la tabla, un contador indica cuántos participantes coinciden con tu búsqueda y filtro (p. ej. «12 de 80 participantes»).

Moimio recuerda tus columnas, su orden y la ordenación para cada usuario en este navegador, así que la tabla tendrá el mismo aspecto la próxima vez que la abras. (Ordenar por un campo personalizado funciona, pero no se recuerda).

En la tabla de Participantes no hay selección múltiple de filas; las acciones por fila (editar, marcar, exportar, quitar) se hacen de una en una.

### Vista en móvil y en pantalla ancha

En un móvil o una tableta estrecha, cada participante se muestra como una tarjeta con número, nombre, marcas, estado, correo y código de grupo. Toca **▸ N detalles** (o **▸ Más**) para desplegar la tarjeta y ver las demás columnas que hayas activado, además de **Reenviar**, **Exportar datos** y **Quitar**. En pantallas más anchas tienes la tabla completa con todas las columnas una al lado de otra. Las funciones son las mismas; solo cambia la disposición.

---

## Editar campos directamente en la tabla

Necesitas permiso para editar participantes (administradores del evento o personal con acceso de escritura a Participantes). Pasa el ratón por un valor: si aparece subrayado, puedes hacer clic en él.

**Nombre y correo**: haz clic en el valor. Moimio te pide primero que confirmes (**¿Editar el nombre?** / **¿Editar la dirección de correo?**), porque estás cambiando datos personales. Haz clic en **Editar**, cambia el valor y pulsa Intro o haz clic en ✓. No se envía ningún correo.

**Código de grupo**: haz clic en el código (o en **+ Añadir** si no tiene), escribe y pulsa Intro o haz clic en ✓. Se guarda al momento.

**Estado**: haz clic en la etiqueta de estado. Aparecen tres opciones (Pendiente / Confirmado / Cancelado); haz clic en la que quieras. ✕ cierra sin cambiar nada. Consulta [Estados de inscripción](#estados-de-inscripción) más abajo.

**Género, fecha de nacimiento, teléfono, dirección, país, iglesia/organización**: haz clic en el valor, cámbialo y pulsa Intro (o haz clic en ✓). Una ventana **Confirmar cambio** muestra el valor anterior → el valor nuevo. Haz clic en **Confirmar cambio** para guardar; **Cancelar** lo descarta.

Los **campos personalizados** funcionan igual (con la ventana de confirmación). El control se adapta al tipo de campo: cuadro de texto para texto, cuadro numérico para números, lista desplegable para campos de opciones, desplegable ✓ / ✕ para campos sí/no y selector de fecha para fechas.

**El mensaje es de solo lectura**: es el mensaje del participante para los organizadores, no algo que los organizadores deban sobrescribir. Haz clic en **Ver** para leerlo completo.

**N.º**, **Inscrito** y **Check-in realizado** los establece Moimio y no se pueden editar aquí.

---

## Estados de inscripción

Cada participante tiene un estado. El estado determina casi todo lo demás: las personas canceladas quedan fuera de la asignación, del check-in y de la mayoría de los recuentos.

| Estado | Significado | Cómo llega un participante a este estado |
|---|---|---|
| **Pendiente** | Inscrito, pero todavía no ha hecho clic en el enlace de confirmación del correo. | Solo ocurre si **Requerir confirmación por correo para inscribirse** está activado (Más ▸ Formulario de inscripción). |
| **Confirmado** | La inscripción está completa. | Justo después de inscribirse si la confirmación por correo está desactivada (por defecto), después de hacer clic en el enlace del correo, tras una importación CSV o cuando un administrador lo establece a mano. |
| **Cancelado** | El participante se ha retirado, o lo has cancelado tú en su nombre. | Lo establece un administrador. Al cancelar, la persona sale de todos los grupos en los que estaba colocada. |

Por defecto, el motor de asignación también coloca a los participantes pendientes (el ajuste **Incluir participantes sin confirmar**; ver la [sección 6](06-allocation-engine.es.md)).

Puedes cambiar el estado desde la fila cuando:

- Un correo nunca llegó (se lo comió el filtro de spam, dirección antigua). Cambia el estado a **Confirmado** a mano.
- Alguien llama para cancelar. Cambia el estado a **Cancelado**.
- Alguien se inscribió dos veces. Cancela una de las inscripciones.

Puedes cambiar de un estado a otro libremente.

---

## Códigos de grupo

Los códigos de grupo vinculan inscripciones relacionadas para que el motor de asignación las trate como un clúster.

### Cómo indican los participantes su código de grupo

El formulario de inscripción incluye un campo opcional de **código de grupo**. El formato habitual es `RAIZ-NNN` (p. ej. `SMITH-742`). Una familia de cuatro que se inscribe junta introduciría `SMITH-742` en todos los casos. El motor intentará entonces mantenerla unida al asignar habitaciones (o cualquier otro tipo de grupo).

Si alguien no introduce ninguno, Moimio crea una raíz a partir de su apellido y le añade un sufijo numérico único (normalmente de tres cifras, p. ej. `SMITH-742`, y de cuatro o cinco solo si ese apellido ya tiene muchos clústeres en el evento), e incluye el resultado en el correo de inscripción para que la persona pueda compartirlo con quien quiera estar en su grupo.

Si alguien escribe solo la raíz (p. ej. `SMITH` sin número), se aplica la misma lógica: se añade un sufijo único antes de guardar. Así se evitan coincidencias: dos familias sin relación que escriben `SMITH` terminan con códigos distintos y no acaban agrupadas por error. Para unirse a propósito a un clúster existente, hay que escribir el código completo (`SMITH-742`), que se guarda tal cual. Los códigos se guardan en mayúsculas.

### Cómo gestionan los administradores los códigos de grupo

Desde la tabla de Participantes puedes:

- **Establecer o cambiar** el código de grupo de un participante haciendo clic en el valor (o en **+ Añadir**). Útil cuando alguien se inscribió sin código y te das cuenta de que viene con una familia. Escribe el código completo de la otra persona para ponerlo en el mismo clúster.
- **Ver quién está en un clúster** pasando el ratón por encima de un código. La ventana emergente muestra a todas las demás personas con el mismo código, o indica que nadie más lo tiene.

### Por qué un «clúster de uno» no cuenta

Si un participante tiene un código de grupo que nadie más comparte, es un «clúster de uno». El motor lo trata como a cualquier otra persona individual. El código de grupo se conserva (lo verás en la interfaz y en los informes), simplemente no activa ningún comportamiento de agrupación.

---

## Notas

Haz clic en **Notas** en una fila para abrir las notas de ese participante. Escribe en **Escribe una nota…** y haz clic en **Añadir nota**.

- Una nota es **Privada** por defecto: solo la ves tú. Marca **Compartir con el equipo** antes de añadirla para convertirla en una nota de **Equipo** que podrá ver el resto del personal del evento.
- Cada nota muestra quién la escribió y cuándo. Si la cuenta de la persona autora se ha eliminado después, aparece **[usuario eliminado]**.
- Puedes eliminar notas con el icono de la papelera. Solo quien la escribió (o un Superadministrador) puede eliminarla realmente.

Las mismas notas aparecen en el panel de perfil del participante en el tablero de Asignación y en el Check-in.

### Historial

El historial de asignación de un participante (quién lo colocó y dónde, movimientos, retiradas, exclusiones y si lo hizo una persona o el motor) no está en la tabla de Participantes. Abre su perfil (**Ver perfil**, el icono ⓘ) en el tablero de Asignación o en el Check-in para verlo. Consulta la [sección 6](06-allocation-engine.es.md).

---

## Inscripción por lotes (importación CSV)

Para eventos en los que los participantes no usan el formulario público (por ejemplo, un retiro cerrado con asistentes seleccionados de antemano y una hoja de cálculo con la lista), puedes importarlos directamente.

En la parte superior de la tabla de Participantes, haz clic en **↑ Importar CSV**. Se abre la ventana **Importar participantes**:

1. Haz clic en **Descargar plantilla** para obtener un CSV con los encabezados de columna correctos (incluidos tus campos personalizados).
2. Rellena tus datos y guárdalos como CSV.
3. En **Formato de fecha en tu archivo**, elige **Europeo (DD.MM.AAAA)** o **ISO / Coreano (AAAA.MM.DD)** para que las fechas de nacimiento se lean correctamente.
4. Suelta el archivo en la ventana (o haz clic para elegirlo). Moimio muestra una vista previa: las filas 🟢 están bien, las 🟡 tienen un aviso y las 🔴 tienen un error (falta el nombre, el apellido o el correo, correo no válido, correo repetido dentro del archivo, género no válido, fecha ambigua, un valor que no es una de las opciones de un campo de selección, etc.).
5. Haz clic en **Importar N filas válidas**. Las filas con errores se omiten; las filas que solo tienen avisos se importan.

Los participantes importados entran con el estado **Confirmado** y reciben un número de participante y (si hace falta) un código de grupo generado. No se envía ningún correo: quien hace la importación responde de las direcciones.

Presta atención a los avisos amarillos:

- **Ya registrado**: esa dirección de correo ya está en el evento. La fila se importa igualmente, así que tendrías dos registros de la misma persona. Quita la fila de tu archivo si no es lo que quieres.
- **Sin consentimiento RGPD**: la fila no tiene `true`/`yes` en la columna de consentimiento.
- Si todas las filas tienen el mismo género, Moimio te avisa: las hojas de cálculo a veces rellenan automáticamente un valor en toda una columna.

El formato CSV es flexible:

- El orden de las columnas da igual y se reconocen las variantes de encabezado más comunes («First Name», «Surname», «E-mail», «DOB», «Mobile», «Church», etc.).
- Las columnas de la exportación de Participantes `No.`, `Status`, `Checked In`, `Registered`, `Marks` y `Message` se ignoran sin aviso, así que puedes volver a importar una exportación.
- Las demás columnas no reconocidas aparecen en un aviso amarillo en la vista previa. Al importar, cada una se convierte en un campo personalizado nuevo (oculto en el formulario público de inscripción), y su columna se activa de inmediato en la tabla de Participantes. Las columnas que solo existen en la propia exportación de Moimio (`No.`, `Status`, `Checked In`, `Marks`, `Registered`, `Message`, `Excluded From`) se omiten sin aviso, de modo que puedes volver a importar una exportación tal cual.
- Las columnas opcionales que falten quedan vacías.
- **Las asignaciones de marcas y las exclusiones no se importan.** Asigna las marcas después de importar, en la tabla de Participantes o en el tablero de Asignación.

Para importaciones muy grandes (más de 1000 filas), divide el archivo en lotes de unos cientos para que la vista previa vaya ágil.

---

## Exportar

En la parte superior de la tabla de Participantes, bajo el botón **↓ Exportar ▾**, hay dos opciones de exportación CSV:

- **Lista completa de participantes**: todos los participantes del evento (salvo los quitados), con independencia de la búsqueda o el filtro de estado que tengas en pantalla. Columnas (con encabezados en inglés): First Name, Last Name, Email, Gender, Date of Birth, Phone, Address, Country, Church/Organisation, Group Code, GDPR Consent, No., Status, Checked In, **Marks** (nombres de las marcas separados por comas), **Excluded From** (los tipos de grupo de los que está excluida la persona), una columna por cada campo personalizado y Message. Las asignaciones *no* están en este CSV a propósito: para una instantánea de las asignaciones, usa las listas en PDF de Informes o la copia de seguridad.
- **Solo nombres + correos**: un CSV de dos columnas (nombre, correo) listo para pegar en una herramienta de listas de correo.

También hay una acción **↓ Exportar datos** por fila (en la columna Acciones) que descarga la **exportación de datos RGPD** de un participante en JSON; consulta la [sección 9](09-data-export-gdpr.es.md).

---

## Situaciones habituales

### «Nunca le llegó el correo»

En la tabla de Participantes, haz clic en la etiqueta de estado **Pendiente** del participante y elige **Confirmado**. Listo.

Si quieres que reciba el correo de todos modos, haz clic en **✉ Reenviar** en su fila. Un participante pendiente vuelve a recibir el enlace de confirmación; uno confirmado recibe el correo de inscripción con su código de grupo.

### «Dos inscripciones son de la misma persona»

En la tabla de Participantes, busca ambas filas (por nombre o correo). Elige la que vas a conservar (normalmente la que se confirmó primero o la que tiene la información más completa). Pon la otra en **Cancelado**. Si la cancelada ya estaba colocada en grupos, esas plazas se liberan automáticamente.

### «Quiero marcar a todos los líderes»

Crea una marca en **Más ▸ Marcas** en la barra lateral (o en la tarjeta **Marcas** del centro de configuración). Llámala, por ejemplo, «Líder», elige un color distintivo y asegúrate de que **Personas** está marcado en **Visible en**.
Después, en la tabla de Participantes, busca a cada líder. Junto a su nombre hay un pequeño botón ● (un círculo si aún no tiene marcas). Haz clic en él y luego en **Asignar** junto a «Líder».

### «Exportar a todos para una lista de correo»

Usa **↓ Exportar ▾ → Solo nombres + correos**. Un CSV de dos columnas que puedes pegar directamente en tu herramienta de correo.

---

## Cuando el participante cancela más tarde

Hay dos opciones:

- **Cancelar** (estado → **Cancelado**): el registro sigue visible en la tabla de Participantes (tachado, al final de **Todos** o en el filtro **Cancelado**), pero queda fuera de la asignación, del check-in y de la mayoría de los recuentos. Sus plazas en grupos se liberan. Puedes volver a ponerlo en Pendiente o Confirmado en cualquier momento; útil para recuperar a alguien de la lista de espera.
- **Quitar** (la acción **Quitar** en la columna Acciones de la fila, solo administradores del evento): después de confirmar con **Quitar participante**, la persona desaparece de todas las listas, asignaciones y recuentos. El registro se conserva en la base de datos como constancia (la exportación de datos RGPD lo sigue incluyendo; ver la [sección 9](09-data-export-gdpr.es.md)), pero no hay ningún botón para recuperarlo; para restaurarlo hace falta alguien con acceso a la base de datos.

El borrado físico completo del registro (para el raro caso en que la normativa lo exija) también es, por ahora, una operación manual en la base de datos; consulta la [sección 9](09-data-export-gdpr.es.md) para conocer el motivo.

---

## Siguiente paso

La [sección 04 — Marcas](04-marks.es.md) explica el sistema de marcas: cómo definir etiquetas de color, asignarlas a los participantes y configurar cómo influyen en el motor de asignación.
