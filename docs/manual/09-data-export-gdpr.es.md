🌐 [English](09-data-export-gdpr.md) · [Deutsch](09-data-export-gdpr.de.md) · [한국어](09-data-export-gdpr.ko.md) · **Español** · [Português (Brasil)](09-data-export-gdpr.pt-BR.md) · [Français](09-data-export-gdpr.fr.md)

# 09 — Exportación de datos y RGPD

Moimio está pensado para que quien organiza un evento pueda cumplir sus obligaciones del RGPD como responsable del tratamiento sin salir de la aplicación. Las piezas que intervienen son: la exportación de datos por participante (artículos 15 y 20), la edición directa (artículo 16), la eliminación (artículo 17), la copia de seguridad de eventos y un tratamiento claro de los participantes cancelados.

Esta sección es práctica: qué hacer y cuándo. Para el enfoque técnico y jurídico, consulta [Cumplimiento del RGPD](../gdpr-compliance.md) (en inglés).

<p align="center">
  <img src="../assets/insight-panel-export.png" alt="El panel de perfil con los datos de un participante y el botón Exportar datos en la parte superior" width="560">
  <br>
  <em>El panel de perfil, con el botón Exportar datos en la parte superior</em>
</p>

---

## Exportación por participante: cuando alguien pide sus datos

Aquí entran en juego el artículo 15 (derecho de acceso) y el artículo 20 (portabilidad de los datos): un participante te escribe diciendo «envíame todo lo que tengáis sobre mí».

### Cómo hacerlo

Las exportaciones de datos personales son para los **administradores del evento** correspondiente y para los **superadministradores**. Hay dos puntos de partida:

- **Desde la tabla de Participantes.** Busca su fila y haz clic en **↓ Exportar datos** en la columna Acciones. (Recomendado para las solicitudes habituales: es lo más rápido).
- **Desde el panel de perfil.** En el tablero de asignación o en el Check-in, haz clic en el pequeño icono **ⓘ** (**Ver perfil**) junto al nombre del participante y luego en **↓ Exportar datos**, en la parte superior del panel. Mismo archivo, mismo contenido. Práctico cuando ya estás viendo a esa persona y llega una solicitud.

En ambos casos:

1. Tu navegador descarga un único archivo: `participant-export-{participant number}-{date}.json`.
2. Envía el archivo al participante por el mismo canal por el que lo pidió.

Los participantes cancelados se pueden exportar igual: siguen en la tabla de Participantes, en gris.

### Qué contiene el archivo

Un único documento JSON (un formato estándar y legible por máquinas) con estas secciones:

- **`export_metadata`**: versión del formato, cuándo se creó el archivo y una breve nota sobre lo que no incluye.
- **`event`**: el evento en el que se inscribió: nombre, descripción, ubicación, zona horaria y fechas. Nada sobre otros participantes ni sobre el resto de tu configuración.
- **`participant`**: su registro de inscripción: nombre, correo, género, fecha de nacimiento, teléfono, dirección, país, iglesia/organización, mensaje, código de grupo, estado, consentimiento, estado del check-in, idioma y cuándo se creó, modificó o quitó el registro.
- **`custom_fields`**: todas sus respuestas a tus preguntas personalizadas, con el texto de cada pregunta.
- **`marks`**: todas las marcas que lleva, con su nombre, color y cuándo se le asignaron.
- **`preference_requests`**: las peticiones de «quiero estar en el grupo de…» que hizo, y las que otras personas hicieron mencionándolo.
- **`allocations`**: en qué grupo está, en cada tipo de grupo.
- **`exclusions`**: los tipos de grupo de los que lo has dejado fuera.
- **`allocation_history`**: el historial de entradas, cambios y salidas de grupos.
- **`notes`**: solo las notas publicadas escritas sobre este participante.
- **`checkin_values`**: todas las marcas de tus columnas de check-in.

### Qué queda fuera, y por qué

- **Las notas no publicadas (borradores).** Los borradores son notas de trabajo de un miembro del equipo, no comunicaciones publicadas.
- **Qué miembro de tu equipo lo movió.** El historial dice qué pasó y cuándo, no quién del equipo lo hizo.
- **Los datos de otros participantes**, aunque compartan código de grupo o habitación. Cada persona recibe solo sus propios datos.

Además, cada exportación queda registrada en el registro del servidor (`data_export_generated`), con el evento, el participante y quién la descargó.

---

## Artículo 16: rectificación (el participante dice «corrige esto»)

Si el participante te dice que un dato es incorrecto, abre **Participantes** y haz clic en el valor para editarlo directamente. Nombre, correo, género, fecha de nacimiento, teléfono, dirección, país, iglesia/organización, código de grupo, estado y respuestas a campos personalizados se pueden editar así; consulta la [§03](03-people.es.md). El mensaje que el participante te envió es de solo lectura, para que nunca se sobrescriba por error.

---

## Artículo 17: supresión («derecho al olvido»)

Dos operaciones, con dos intenciones distintas:

### Quitar (el caso habitual)

En la tabla de Participantes, haz clic en **Quitar** en la columna Acciones del participante y luego en **Quitar participante** para confirmar. Solo los administradores del evento y los superadministradores ven este botón.

El participante desaparece del uso diario: Participantes, el tablero de asignación, el Check-in, los informes, las exportaciones y la asignación. También queda fuera de cualquier copia de seguridad que se haga después. El registro en sí se conserva en la base de datos como constancia. No hay ningún botón para recuperarlo; quien gestione tu servidor puede restaurarlo en la base de datos si hace falta.

Es el camino adecuado para *«he cambiado de idea, no voy a ir»* o *«por favor, quitadme de vuestras listas»*.

### Borrado definitivo (el caso raro)

En esta versión no hay ningún botón que borre definitivamente a una sola persona: un «eliminar para siempre» irreversible es demasiado fácil de pulsar por accidente. Tus opciones:

- **Eliminar el evento completo** (Superadministrador: **Zona peligrosa ▸ Eliminar evento**, en el centro de configuración o en la página Detalles del evento) cuando haya terminado y ya no lo necesites. Así se borran definitivamente todas las personas inscritas en él. Descarga antes una copia de seguridad si podrías necesitar los registros.
- **Para una sola persona**, pide a quien gestione tu servidor de Moimio que elimine el registro de la base de datos. Consulta [Cumplimiento del RGPD](../gdpr-compliance.md) para conocer el contexto.

---

## Enlace al aviso de privacidad en el formulario de inscripción

Si tu organización tiene su propio aviso de privacidad, pon su dirección web en **Espacio de trabajo ▸ Aviso de privacidad ▸ URL del aviso de privacidad** (Superadministrador) y haz clic en **Guardar**. El formulario público de inscripción muestra entonces un enlace **Aviso de privacidad** justo después de la frase de consentimiento. Si lo dejas vacío, no se muestra ningún enlace.

---

## Copias de seguridad

Además de las exportaciones por participante, Moimio puede hacer copias de seguridad de eventos completos.

### Dónde está

Barra lateral ▸ **Copias de seguridad** (dentro de **Gestión**, solo Superadministrador). La página lleva el título **Exportar**.

### Hacer una copia de seguridad

1. Marca uno o más eventos en **Descargar copias de seguridad de eventos** (o **Seleccionar todo**).
2. En **Contenido de la copia**, elige:
   - **Copia completa**: todas las partes del evento: participantes, sus respuestas, grupos y asignaciones, exclusiones, marcas, preferencias, notas, columnas y marcas de check-in, historial, tu configuración y reglas, y las fechas originales. Úsala como copia de seguridad, antes de un cambio importante o para trasladar un evento a otro Moimio.
   - **Solo estructura (RGPD)**: la forma del evento sin ningún dato personal: formulario de inscripción, preguntas personalizadas, tipos de grupo y sus grupos, marcas, columnas de check-in y configuración. Sin participantes, sin notas y sin los datos de tu remitente de correo. Se puede compartir sin problema con otra organización como plantilla.
3. Haz clic en **Descargar {n} copia(s)**. Cada evento se descarga como su propio archivo `.zip` (los de solo estructura llevan `-structure` en el nombre).

Algunas cosas que conviene saber:

- **Notas:** una copia completa contiene todas las notas publicadas, más *tus propias* notas en borrador. Los borradores de otros miembros del equipo nunca se incluyen.
- **Los participantes quitados** no están en las copias de seguridad.
- **Los miembros del equipo y sus roles nunca forman parte de una copia de seguridad.** Vuelve a invitar a tu equipo después de restaurar.

### Restaurar

En la página Copias de seguridad, haz clic en **↑ Restaurar desde copia** (el botón **↑ Desde copia** de la lista de eventos lleva al mismo sitio). Sube el `.zip`; Moimio muestra una vista previa (nombre del evento, cuándo se exportó, cuántos participantes y asignaciones) y luego haz clic en **Restaurar evento**.

- Se crea un evento **nuevo**, llamado `{nombre original} (Restored)` y devuelto a la fase de Configuración. El original no se toca.
- Conserva sus fechas originales, así que aparece en la lista de eventos donde estaba el original. Haz clic en **Abrir el evento restaurado** para ir directamente a él.
- Si parte del archivo está dañada, Moimio omite solo las líneas que no puede leer y sigue adelante. El resultado te indica cuántas líneas se omitieron, cuántas entradas hubo que acortar y cuántos valores volvieron al ajuste estándar.
- Los archivos de copia de seguridad antiguos también se pueden restaurar.

Restaurar es solo para superadministradores.

### Trasladar un espacio de trabajo completo

La página Copias de seguridad trabaja con un evento cada vez. Para trasladar todos los eventos de una vez a un Moimio que gestiones tú, hay una exportación de todo el espacio de trabajo y un único comando que la restaura (con una prueba previa que no cambia nada). Consulta [Moving a workspace to your own Moimio](../moving-a-workspace.md) (en inglés).

---

## Participantes cancelados

Cancelar no es eliminar: es un cambio de estado. Los participantes cancelados siguen en la tabla de Participantes, en gris, para que conserves un registro claro. Sus datos siguen ahí y la exportación por participante sigue funcionando. Para quitarlos de tus listas, usa **Quitar** (ver arriba).

En cuanto al artículo 18 (limitación del tratamiento), el estado cancelado funciona como una limitación suave: los participantes cancelados quedan fuera de la asignación, del Check-in, de las listas y de la mayoría de los informes. Sus datos no se usan para el evento; solo se conservan.

---

## Siguiente paso

La [sección 10 — Varios eventos y archivo](10-multi-event-and-archive.es.md) explica cómo llevar varios eventos desde la misma instalación de Moimio, cómo archivar eventos pasados sin eliminarlos, qué cambia cuando un evento se archiva y cómo reutilizar la configuración de un evento anterior.
