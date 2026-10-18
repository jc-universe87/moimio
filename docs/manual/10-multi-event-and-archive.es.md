🌐 [English](10-multi-event-and-archive.md) · [Deutsch](10-multi-event-and-archive.de.md) · [한국어](10-multi-event-and-archive.ko.md) · **Español** · [Português (Brasil)](10-multi-event-and-archive.pt-BR.md) · [Français](10-multi-event-and-archive.fr.md)

# 10 — Varios eventos y archivo

Moimio parte de la idea de que una organización lleva más de un evento. Cuando ya has configurado un formulario de inscripción, unos tipos de grupo y un equipo, a menudo querrás reutilizar esa configuración. Esta sección explica cómo llevar varios eventos desde un mismo Moimio, cómo funciona el archivo y cómo crear un evento nuevo a partir de uno anterior.

<p align="center">
  <img src="../assets/events-list.png" alt="La lista de eventos con las pestañas Activos, Pasados y Archivados, tarjetas de evento con etiquetas de fase y los botones + Nuevo evento y Desde copia" width="720">
  <br>
  <em>La lista de eventos</em>
</p>

---

## La lista de eventos

Barra lateral ▸ **Eventos**. Cuando estés dentro de un evento, usa **Todos los eventos**, en la parte superior de la barra lateral, para volver aquí.

Arriba hay un cuadro de búsqueda y luego tres pestañas, cada una con un recuento:

- **Activos**: eventos que no están archivados y que aún no han terminado (incluidos los que no tienen fechas). Los eventos fijados aparecen primero.
- **Pasados**: eventos cuya fecha de finalización ya ha pasado.
- **Archivados**: eventos que se han archivado (ver más abajo). Los superadministradores siempre ven esta pestaña; los demás solo cuando contiene algo.

Cada tarjeta muestra el nombre del evento, una etiqueta con su situación (**Configuración**, **Inscripción**, **Evento**, **Pasado** o **Archivado**), sus fechas y su ubicación, y una cifra destacada, como el número de inscritos. Los superadministradores tienen además un menú **⋯** en cada tarjeta con **Fijar arriba** / **Desfijar**, **Archivar** / **Desarchivar** y **Eliminar evento**.

El botón **+ Nuevo evento** crea un evento desde cero. **↑ Desde copia** te lleva a la página Copias de seguridad para restaurar un evento desde un archivo de copia de seguridad (consulta la [§09](09-data-export-gdpr.es.md#copias-de-seguridad)). Ambos botones se muestran a los superadministradores y a los miembros del equipo que tienen **Puede crear nuevos eventos**.

---

## Cerrar las inscripciones frente a archivar

Son dos cosas distintas que a menudo se confunden:

- **Cerrar las inscripciones** forma parte de la vida normal de un evento: Configuración → Inscripción → Evento. Al cerrar se dejan de aceptar inscripciones y el evento pasa a la fase de Evento, donde asignas y haces el check-in. Consulta la [§02](02-events-and-registration.es.md).
- **Archivar** guarda un evento en el archivo. Pasa a ser de solo lectura y se mueve a la pestaña **Archivados**, pero se conservan todos sus datos.

Un evento se puede archivar en cualquier momento: un borrador que abandonaste o (lo habitual) un evento que ya terminó y quieres apartar. Archivar es **reversible**.

---

## Archivar un evento

### Dónde está el botón

Archivar es cosa de los **superadministradores**. Cualquiera de estos caminos sirve:

- Lista de eventos ▸ **⋯** en la tarjeta del evento ▸ **Archivar**
- **Centro de configuración ▸ Zona peligrosa ▸ Archivar** (mientras el evento sigue en Configuración)
- **Detalles del evento ▸ Zona peligrosa ▸ Archivar**

La Zona peligrosa está contraída por defecto para evitar clics accidentales: haz clic en su encabezado para abrirla. Confirma con **Archivar** en el cuadro **¿Archivar este evento?**.

### Qué ocurre al archivar

- El evento pasa a la pestaña **Archivados** de la lista de eventos.
- El evento se vuelve **de solo lectura para todos, superadministradores incluidos**. Para cambiar algo, primero desarchívalo.
- El formulario público de inscripción rechaza nuevas inscripciones.
- Los datos existentes (participantes, asignaciones, check-ins, notas) se mantienen intactos.
- Aparece un aviso **Archivado** en la parte superior de las páginas del evento.

### Desarchivar

En los mismos sitios: **⋯ ▸ Desarchivar** en la tarjeta, o **Zona peligrosa ▸ Desarchivar**. El evento vuelve a ser editable y reaparece en **Activos** o **Pasados**, según sus fechas. La inscripción y el check-in continúan donde se quedaron.

---

## Crear un evento nuevo a partir de uno anterior

Cuando organizas un evento que se repite (mismo formulario de inscripción, habitaciones parecidas, el mismo equipo), copiar la configuración de la última vez te ahorra mucho trabajo.

### Cómo hacerlo

1. Lista de eventos ▸ **+ Nuevo evento**.
2. Escribe el nombre del nuevo evento.
3. Marca **Usar la configuración de otro evento** y elige el evento del que copiar.
4. En **Qué copiar**, desmarca lo que no quieras. Al principio están marcadas las cinco opciones:
   - **Marcas**: las definiciones de las marcas (nombre, color, etc.), no quién las llevaba.
   - **Formulario de inscripción**: qué campos estándar se muestran y cuáles son obligatorios.
   - **Campos personalizados**: tus propias preguntas.
   - **Tipos de grupo**: todos los tipos de grupo con sus grupos, capacidades y ajustes de género. Los grupos restringidos a una marca se vinculan a la copia de esa marca en el nuevo evento; si no copias las marcas, esas restricciones se descartan.
   - **Miembros del equipo**: todas las personas del equipo del evento anterior, con el mismo rol y los mismos permisos.
5. Haz clic en **Crear evento**.

El nuevo evento empieza en Configuración, listo para que añadas las fechas y abras las inscripciones. **Nunca se copian datos de participantes**: ni participantes, ni asignaciones, ni check-ins, ni notas.

Solo puedes copiar de eventos a los que tienes acceso.

### Copiar entre instalaciones

Para llevar la configuración a otro Moimio, o a un evento que ya existe, exporta las piezas como archivos: **Exportar tipos de grupo** / **Importar tipos de grupo** en la parte de asignación (consulta la [§05](05-group-types-and-units.es.md)) y **Exportar formulario** / **Importar formulario** para el formulario de inscripción (consulta la [§02](02-events-and-registration.es.md)). Estos archivos solo contienen configuración, nunca datos personales.

### ¿Y las copias de seguridad?

Las copias de seguridad (consulta la [§09](09-data-export-gdpr.es.md#copias-de-seguridad)) son la otra vía: una copia completa lo conserva todo, participantes incluidos. **Copia la configuración cuando empieces una nueva edición; usa una copia de seguridad como resguardo o para trasladar un evento a otro Moimio.** Una copia **Solo estructura (RGPD)** es una plantilla que puedes compartir, sin datos personales.

---

## Llevar varios eventos a la vez

Nada en Moimio lo impide. Cada evento es un mundo aparte: sus propios participantes, sus propios tipos de grupo, su propio equipo. Si la misma persona se inscribe en dos eventos, se trata como dos inscripciones independientes, una por evento.

Cosas prácticas que conviene saber:

- **Cambiar de evento.** Usa **Todos los eventos**, en la parte superior de la barra lateral, y elige otro evento. Todos los roles ven este enlace.
- **El acceso del equipo es por evento.** Un miembro del equipo del evento A no tiene acceso automático al evento B. Añádelo a cada evento (o copia los **Miembros del equipo** al crear el nuevo).
- **Los campos personalizados son por evento.** La pregunta «Talla de camiseta» del evento A es independiente de la del evento B, aunque el texto coincida.
- **Los tipos de grupo son por evento.** «Asignación de habitaciones» en el evento A no tiene nada que ver con «Asignación de habitaciones» en el evento B.

Esta separación es intencionada. Puedes llevar un retiro de mujeres y un congreso de hombres desde el mismo Moimio sin que los datos se mezclen.

---

## Siguiente paso

La [sección 11 — Equipo y permisos](11-staff-permissions.es.md) trata las cuentas de usuario, el equipo de cada evento y los permisos de Participantes, Asignación, Check-in, Informes y Marcas.
