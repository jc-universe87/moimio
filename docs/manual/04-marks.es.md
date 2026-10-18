🌐 [English](04-marks.md) · [Deutsch](04-marks.de.md) · [한국어](04-marks.ko.md) · **Español** · [Português (Brasil)](04-marks.pt-BR.md) · [Français](04-marks.fr.md)

# 04 — Marcas

Una **marca** es una etiqueta de color que asignas a un participante. Las marcas las ve el personal en el área de administración, pero no los participantes. Sirven para dos cosas:

1. **Identificar de un vistazo.** «Esta persona es líder». «Esta persona necesita planta baja». «Esta persona trae guitarra». Tu equipo ve de un vistazo lo que necesita saber.
2. **Influir en la asignación.** Las marcas pueden influir en el motor de asignación: mantener juntas a las personas con la misma marca, repartirlas por igual o no tener ningún efecto. También pueden reservar una habitación o un grupo para quienes las llevan.

Esta sección explica cómo definir marcas, asignarlas y configurar su comportamiento.

---

## Dónde está el editor de marcas

Puedes llegar al editor de marcas desde varios sitios, según tu acceso y la fase del evento:

- **Fase de Configuración:** la tarjeta **Marcas** del centro de configuración.
- **Fases de Inscripción y Evento**, para administradores del evento y superadministradores: **Más ▸ Marcas** en la barra lateral.
- Para el personal con acceso de escritura a las marcas (pero sin permisos de administración): **Marcas** aparece como elemento propio en la barra lateral.

Todos los caminos abren el mismo editor para el evento actual.

---

## El editor de marcas

El editor muestra todas las marcas definidas para este evento. Cada marca muestra su color, su nombre, dónde es visible, quién la creó («Creada por …») y cuántas personas la llevan (**N personas**; pasa el ratón por encima para ver los nombres).

Para crear una marca, haz clic en **+ Añadir marca** y rellena:

- **Nombre de la marca**: cómo se llama la marca («Líder», «Primera vez»).
- **Color**: elige uno de la paleta rápida (rojo, naranja, amarillo, verde, verde azulado, azul, morado, rosa, gris) o usa el selector de color para introducir un valor hexadecimal o RGB.
- **Visible en**: casillas para los tres lugares donde la marca puede aparecer como un punto de color junto al nombre del participante: **Personas**, **Asignación**, **Check-in**. Las tres están marcadas por defecto. Una marca sin ninguna casilla marcada aparece como «Oculto en todas partes».

Después haz clic en **Crear marca**. Para cambiar una marca, haz clic en su icono gris del lápiz; para eliminarla, en el icono rojo de la papelera.

Al eliminar una marca, se quita a todos los participantes que la tienen. La ventana de eliminación indica cuántas personas la llevan en ese momento (y algunos de sus nombres), y tienes que escribir el nombre de la marca para confirmar.

Los administradores del evento ven además **Importar de evento**, que copia las definiciones de las marcas (nombres, colores, visibilidad, pero no quién las tiene) de un evento anterior.

El personal con acceso de escritura a las marcas puede crear marcas, pero solo puede editar o eliminar las que ha creado. El personal con acceso de solo lectura ve la lista sin los botones de edición.

### Cómo diseñar tu conjunto de marcas

Algunos principios que hacen más útiles las marcas:

- **Pocas.** Entre cinco y diez marcas por evento es lo ideal. Si hay más, el ruido visual pesa más que la información.
- **Colores bien distintos.** Dos verdes parecidos no sirven de nada. La paleta rápida tiene colores bien diferenciados; no te alejes mucho de ella.
- **Nombres breves.** «Líder», no «Líder designado de grupo pequeño (inscrito como tal)». El nombre aparece en muchos sitios y las etiquetas cortas se leen mejor.

Algunos conjuntos de marcas que pueden funcionar bien:

- **Retiro:** Líder (verde), Primera vez (amarillo), Vegetariano (morado), Alergia a los frutos secos (rojo), Necesita planta baja (azul).
- **Congreso:** Ponente (naranja), Voluntario (verde azulado), VIP (morado), Prensa (rojo).
- **Campamento juvenil:** Monitor de cabaña (verde), Pequeños (amarillo), Mayores (azul), Necesidades especiales (rosa).

---

## Asignar marcas a los participantes

Puedes asignar marcas en la tabla de **Participantes**, en el tablero de **Asignación** y en el **Check-in**. Haz clic en el pequeño botón ● (o en cualquier punto de color) junto al nombre del participante. Se abre una ventana con la lista de marcas; haz clic en **Asignar** para añadir una o en **Quitar** para retirarla. Cada marca asignada muestra quién la asignó y cuándo.

La ventana solo muestra las marcas visibles en el lugar desde el que la abriste. Si falta una marca, revisa su ajuste **Visible en**.

Un participante puede tener tantas marcas como quieras: alguien puede ser Líder, Vegetariano y Necesitar planta baja a la vez.

Si no tienes permiso para cambiar marcas, la ventana se abre en modo de solo lectura, para que al menos puedas ver qué significan los puntos.

---

## Prioridades de las marcas: por tipo de grupo

Las marcas solo influyen en el motor en los tipos de grupo donde las hayas activado, y cada tipo de grupo tiene su propia lista.

Abre el tipo de grupo en la página **Asignación** y haz clic en el icono ⚙ **Configuración del motor**, junto al botón **Asignación automática**. En **Aplicar las marcas en este orden** verás:

- las marcas activas para este tipo de grupo, numeradas, cada una con un desplegable: **Sin efecto**, **Mantener juntos** o **Distribuir uniformemente**;
- debajo, las demás marcas, con **+ Añadir** para activarlas.

Arrastra las marcas activas (o usa las flechas ↑ ↓) para cambiar el orden; ✕ quita una marca de la lista. La marca de arriba se aplica primero.

La misma marca puede hacer cosas distintas en tipos de grupo distintos. Una marca «Líder» podría estar en **Distribuir uniformemente** en Grupos pequeños (un líder por grupo) y no figurar en la lista de Asignación de habitaciones.

Cuando un participante lleva varias marcas, **solo una de ellas guía al motor** en un tipo de grupo determinado: la que esté más arriba en la lista con Mantener juntos o Distribuir uniformemente. Las demás se siguen mostrando como puntos, simplemente no influyen en la colocación ahí. Los códigos de grupo van primero: a alguien colocado con su código de grupo no se le mueve por una marca.

Un orden típico:

1. Las marcas que más deben influir en la colocación (Líder, Ponente).
2. Otras marcas con efecto (Pequeños, Primera vez).
3. Marcas informativas (Vegetariano, Alergia, Planta baja): déjalas fuera de la lista o ponlas en **Sin efecto**. El motor nunca las tiene en cuenta.

---

## Reservar un grupo para una marca

En el tablero de Asignación, cada tarjeta de habitación o grupo tiene su propio botón de marcas ●. Úsalo para **Asignar** una marca a ese grupo: pasa a ser «Solo *{marca}*», y el motor solo coloca ahí a personas que la llevan. Muy útil para una habitación de líderes o una habitación tranquila. Quienes llevan la marca se dirigen primero a su habitación reservada. Consulta la [sección 5](05-group-types-and-units.es.md).

---

## Cuando las marcas cambian después de ejecutar el motor

Añadir, eliminar o asignar una marca, o cambiar su comportamiento o prioridad, no vuelve a ejecutar el motor. La asignación actual se queda como estaba.

Para aplicar los cambios de marcas, ve a **Asignación**, abre el tipo de grupo y vuelve a pulsar **Asignación automática**. El motor es determinista: los mismos participantes, grupos, ajustes y marcas producen siempre la misma asignación, así que al volver a ejecutarlo obtienes una propuesta actualizada y limpia que puedes revisar antes de que cambie nada.

Si solo quieres un cambio pequeño, también puedes arrastrar participantes a mano en el tablero.

---

## Las marcas en informes y exportaciones

- **Las listas en PDF** muestran las marcas como puntos de color junto al nombre de cada participante, con una leyenda. Solo se imprimen las marcas visibles en **Asignación**.
- **La exportación CSV de Participantes** (Lista completa de participantes) tiene una columna **Marcas** con los nombres de las marcas separados por comas.
- **La exportación de datos RGPD de un participante** incluye sus marcas.

---

## Errores habituales

- **Usar demasiadas marcas.** Veinte marcas en un evento son inmanejables. Revisa y depura a medida que se acerca el evento.
- **Esperar que una marca cambie la asignación por sí sola.** Una marca no hace nada en el motor hasta que está en la lista **Aplicar las marcas en este orden** de un tipo de grupo con Mantener juntos o Distribuir uniformemente.
- **Ocultar una marca en una vista y luego buscarla ahí.** La ventana de asignación solo muestra las marcas visibles en esa vista.

---

## Siguiente paso

La [sección 05 — Tipos de grupo y unidades](05-group-types-and-units.es.md) trata los tipos de grupo y las habitaciones o grupos que contienen, que es donde el motor coloca realmente a los participantes, con sus capacidades y restricciones de género.
