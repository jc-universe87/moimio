# 08 — Informes y exportaciones en PDF

La página **Informes** te muestra de un vistazo las cifras principales de tu evento y es donde descargas las listas imprimibles: unos recuadros de resumen arriba y, debajo, las listas en PDF de cada tipo de grupo.

<p align="center">
  <img src="../assets/reports.png" alt="Página de Informes con los recuadros de resumen, el selector de idioma del PDF y las descargas de listas" width="560">
  <br>
  <em>Página de Informes: recuadros de resumen y descargas de listas</em>
</p>

---

## Dónde están los Informes

**Informes** en la barra lateral, durante las fases de Inscripción y Evento. Los administradores y superadministradores siempre la ven; el personal la ve si sus permisos incluyen los informes.

La página tiene dos partes:

- **Arriba: recuadros de resumen**, de inscripción, asignación y (durante la fase de Evento) check-in.
- **Abajo: Descargas de listas**, una fila por tipo de grupo con los botones **Compacto** y **Firma**.

---

## Los recuadros de resumen

### Inscripción

- **Cifra principal:** el número de inscripciones activas (confirmadas más pendientes; las canceladas no cuentan).
- **Debajo:** el desglose, por ejemplo `26 confirmados · 5 pendientes · 2 cancelados`.

De un vistazo: ¿se está inscribiendo la gente y los pendientes están confirmando?

### Asignación

- **Cifra principal:** el porcentaje de participantes activos que están en al menos un grupo, por ejemplo `87%`.
- **Debajo:** `27 de 31 participantes asignados a grupos`.

Cuenta personas, no plazas. 100 % significa que cada participante activo está en al menos uno de tus tipos de grupo. Quien está en una habitación y en un grupo pequeño cuenta igualmente una sola vez.

### Check-in *(solo en la fase de Evento)*

- **Cifra principal:** el porcentaje de participantes activos que ya han hecho el check-in, por ejemplo `82%`.
- **Debajo:** `28 de 34 registrados`.

Este recuadro solo aparece en la fase de Evento; antes no hay check-in que hacer.

---

## Descargas de listas

Encima de la lista de tipos de grupo hay dos opciones que se aplican a todas las descargas de la página:

- **Idioma del PDF**: el idioma en que se imprime el PDF, sea cual sea el idioma en que usas Moimio. Puedes elegir entre English, Deutsch, 한국어, Español, Português (BR) y Français. Al principio coincide con el idioma de tu interfaz, de modo que un organizador alemán puede imprimir igualmente una lista en inglés para un equipo internacional.
- **Incluir portada**: añade una primera página con el nombre del evento, las fechas, la ubicación y las cifras de asignación. Desactivado por defecto para ahorrar papel; útil para entregar una lista a un coordinador o guardar una copia como registro.

Cada fila de tipo de grupo muestra su nombre y un resumen como `5 grupos · 87% de los participantes`, con dos botones:

- **Compacto**: nombres agrupados por grupo, para carpetas y puertas. A4 vertical.
- **Firma**: una hoja con una casilla, una línea para la firma y una columna de notas para cada persona, para el personal de check-in. A4 horizontal.

### La lista detallada

Un tercer formato, la lista **detallada**, incluye todos los datos de contacto (nombre, género, fecha de nacimiento, teléfono, correo, código de grupo). Como contiene datos personales, no está en la página de Informes. Descárgala desde el tablero de asignación: **Asignación ▸** abre un tipo de grupo **▸ ⋯ ▸ Lista detallada (con datos)** o **Detallado + portada**. El selector de idioma **PDF**, justo encima de esas dos opciones, define el idioma. Los administradores siempre pueden descargarla; el personal necesita permiso para ver Participantes.

---

## Qué contiene cada PDF

Cada página tiene un encabezado con el nombre del evento, el tipo de grupo y el formato, además de una franja de color para ordenar fácilmente las hojas sueltas. El pie de página muestra el nombre y las fechas del evento y *«Página 2 de 5»*.

### Compacto

Para cada grupo:

- Una barra de encabezado con el nombre del grupo, cuántas personas tiene en relación con su capacidad (con una pequeña barra de ocupación) y su restricción de género, si la tiene.
- Una lista con viñetas de los miembros, ordenada por apellido. Cada línea muestra el nombre, los puntos de las marcas, la inicial del género y el código de grupo.
- Los grupos de más de 6 personas se imprimen en dos columnas para ahorrar papel.

### Firma

A4 horizontal, con las líneas en blanco **PERSONAL** y **FECHA** en la parte superior. Para cada grupo, una barra de encabezado y luego una fila por persona: una casilla, el nombre (con los puntos de las marcas), el código de grupo, el teléfono, una línea para la firma y un espacio para notas. Pensada para imprimirla, dársela a alguien con una carpeta y marcar a mano a medida que llega la gente.

### Detallado

A4 horizontal. Para cada grupo, una barra de encabezado y una tabla con el nombre (con los puntos de las marcas), el género, la fecha de nacimiento, el teléfono, el correo y el código de grupo. Úsala cuando alguien necesite todos los datos de contacto, por ejemplo un líder de grupo o una entidad colaboradora externa.

### La página «Sin asignar»

Si alguien de este tipo de grupo no está en ningún grupo, todos los formatos (Compacto, Firma y Detallado) terminan con una página **SIN ASIGNAR** que los muestra con su teléfono y correo, en dos bloques:

- **EXCLUIDOS**: personas que has dejado fuera de este tipo de grupo a propósito (consulta la [sección 06](06-allocation-engine.es.md#mantener-a-alguien-fuera-de-un-tipo-de-grupo)).
- **SIN UBICAR**: personas a las que simplemente aún no se ha puesto en un grupo.

Un bloque se omite si estaría vacío, y la página entera se omite si todos están colocados. Las inscripciones canceladas nunca aparecen.

### Portada

Cuando **Incluir portada** está marcado, el PDF empieza con una portada que muestra el nombre, las fechas y la ubicación del evento, el tipo de grupo y el formato, tres cifras (**TOTAL**, **ASIGNADOS** y **SIN ASIGNAR**, esta última resaltada cuando no es cero) y cuándo y quién lo generó.

---

## Las marcas en los PDF

Las marcas visibles en **Asignación** aparecen como pequeños puntos de color justo después del nombre de cada persona, en los tres formatos. Una leyenda de **Marcas** al final de la lista indica qué color corresponde a cada marca, e incluye solo las marcas que aparecen realmente en ese PDF.

Si alguien tiene más marcas de las que caben (4 puntos en Compacto y Detallado, 3 en la hoja de Firma), las que sobran no se muestran. Las marcas aparecen en orden alfabético para que todas las impresiones sean iguales.

---

## Una vista imprimible rápida

En el tablero de asignación, **⋯ ▸ ↗ Abrir resumen** abre en una pestaña nueva una vista de solo lectura del tipo de grupo, con un botón **🖨 Imprimir**. Muy práctica para imprimir rápidamente el estado actual sin descargar un PDF.

---

## ¿Y el CSV?

Las exportaciones a hoja de cálculo están en la página **Participantes**, no en Informes. Haz clic en **↓ Exportar ▾** y elige **Lista completa de participantes** (todos los campos, incluidas las columnas **Status**, **Checked In**, **Marks** y **Excluded From**) o **Solo nombres + correos** (para una herramienta de listas de correo). El CSV de Participantes no indica quién está en qué grupo; para eso, usa las listas en PDF o una copia de seguridad.

---

## Cuando la página está vacía

Si todavía no hay inscripciones ni tipos de grupo, la página solo dice *«Abre la inscripción para empezar a recoger datos. Los informes se llenarán automáticamente.»* Si no hay tipos de grupo, la sección de listas dice *«Aún no hay tipos de grupo.»* Todo se va llenando a medida que llegan inscripciones y asignaciones.

---

## Siguiente paso

La [sección 09 — Exportación de datos y RGPD](09-data-export-gdpr.es.md) trata las exportaciones de datos por participante (la vía de los artículos 15 y 20), las copias de seguridad de los eventos y cómo gestiona Moimio la eliminación y el borrado definitivo.
