# 07 — Check-in

La pantalla de check-in es la que usa el personal el día del evento para marcar a las personas que llegan. Es una lista sencilla con casillas grandes, pensada para funcionar bien en una tableta o un móvil en la mesa de recepción.

<p align="center">
  <img src="../assets/check-in.png" alt="Modo de check-in con el cuadro de búsqueda, la barra de progreso y las casillas" width="560">
  <br>
  <em>Modo de check-in</em>
</p>

---

## Cómo llegar al check-in

Lo que ves depende de quién eres.

Los **administradores** (Superadministrador o administrador del evento) hacen clic en **Abrir modo de check-in →** en la página principal del evento. El botón aparece durante la fase de Evento, mientras el evento está **Antes del inicio** o **En curso** (no cuando ya está **Finalizado**). Abre una vista a pantalla completa sin barra lateral, que solo muestra el nombre del evento, un interruptor de tema y **Cerrar sesión**. **← Volver a Asignación** regresa a la vista de administración normal. Cuando todos los tipos de grupo están confirmados, el tablero de asignación ofrece también el atajo **Check-in listo →**.

El **personal cuyo único permiso es el check-in** llega directamente a esta vista a pantalla completa al abrir el evento durante la fase de Evento. No hay botón de salida: es su pantalla durante el turno.

El **personal con check-in y otros permisos** (por ejemplo, check-in y Participantes) ve **Check-in** en la barra lateral. Abre la misma lista de check-in dentro de la interfaz de administración normal, para poder alternar entre tareas.

El personal con **Acceso antes de que comience el evento** también puede abrir el check-in durante la fase de Inscripción (consulta la [sección 11](11-staff-permissions.es.md)).

Llegues como llegues, los datos son los mismos: una marca en un dispositivo aparece en todas las demás pantallas en uno o dos segundos.

---

## La lista de check-in

Cada fila es un participante. Aparecen todas las personas inscritas, confirmadas o todavía pendientes; las inscripciones canceladas no.

Arriba encontrarás:

- Un **cuadro de búsqueda** (*«Buscar por nombre, correo o código de grupo...»*). También encuentra números de participante y nombres de marcas, e ignora acentos, guiones y variantes ortográficas como Müller / Mueller.
- Una barra de progreso con *«28 de 34 registrados»*.
- Filtros: **Todos**, **Con check-in**, **Sin check-in**.
- **Columnas**, para elegir qué columnas se muestran.
- **+ Crear columna** (administradores y personal con **Acceso antes de que comience el evento**).

Las columnas que se muestran por defecto son:

- **Nº**: el número del participante en este evento.
- **Nombre**, con los puntos de las marcas de la persona (haz clic en ellos para ver qué significan, o para asignar marcas si tienes permiso).
- **Check-in**: la casilla principal de «ha llegado».
- **Hora de check-in**: cuándo se le marcó.

Haz clic en **Columnas** para mostrar u ocultar más. La lista está agrupada en **Seguimiento del check-in** (tus columnas de casillas personalizadas), **Campos de inscripción** (**Código de grupo**, **Género**, **Teléfono**, **Iglesia / organización**, **País**, **Dirección**, **Fecha de nacimiento**, **Mensaje**, **Inscrito** y **Hora de check-in**), **Campos personalizados** de tu formulario de inscripción y **Otros** (**Notas**, que añade un botón para leer y escribir notas sobre esa persona). Arrastra el encabezado de una columna hacia un lado para reordenarla y haz clic en un encabezado para ordenar por él. Tus columnas se recuerdan en ese dispositivo.

En un móvil, cada persona es una tarjeta con el nombre y las casillas; toca **N detalles** para ver las demás columnas.

---

## Columnas de check-in personalizadas

Además de la casilla principal de **Check-in**, puedes añadir columnas de casillas para todo lo que quieras controlar en la entrada: pago recibido, camiseta entregada, identificador entregado, autorización firmada, etc.

Para añadir una, haz clic en **+ Crear columna**, escribe un nombre como «Pago» o «Camiseta» y haz clic en **Añadir**. La nueva columna aparece con una casilla vacía para cada participante.

Para eliminar una columna personalizada, haz clic en la pequeña ✕ junto a su nombre en el encabezado de la columna (administradores y personal con **Acceso antes de que comience el evento**). Una confirmación (**Eliminar columna**) te avisa de que la columna y todas sus marcas se eliminan para todos. No se puede deshacer.

Conviene saber:

- **Varias personas del equipo pueden trabajar a la vez sobre el mismo participante**, por ejemplo una marca «Pago» mientras otra marca «Camiseta».
- **Solo la casilla principal de Check-in cuenta como llegada.** Las columnas personalizadas se controlan por separado y no cambian las cifras de «con check-in».

---

## Qué hace una marca

Las marcas se guardan al instante; no hay botón de guardar. Al marcar la casilla principal de **Check-in** también se registra la hora, que aparece en la columna **Hora de check-in**. Vuelve a hacer clic en la casilla para deshacerlo; la hora también se borra.

---

## Sincronización en tiempo real

Todas las pantallas de check-in permanecen conectadas al servidor. Cuando alguien marca una casilla (principal o personalizada, en cualquier dispositivo), todas las demás pantallas abiertas se actualizan en uno o dos segundos. No hay botón de actualizar.

En la práctica: llega un participante, la voluntaria A lo marca en su móvil y el voluntario B, en el otro extremo de la mesa, ve cómo cambia la fila al momento. Que dos personas marquen a la misma persona en el mismo instante no es problema; el resultado es simplemente «marcado».

La conexión es automática. Si el wifi se cae un momento, la pantalla se vuelve a conectar sola cuando vuelve.

---

## Perfil del participante

Haz clic en la **ⓘ** junto a un nombre (**Ver perfil**) para abrir el **Perfil del participante**: datos de contacto, datos de inscripción, en qué grupos está la persona en cada tipo de grupo (muy práctico para «¿en qué habitación estoy?»), sus preferencias de grupo, campos personalizados y notas. Es el mismo panel que en el tablero de asignación. Para añadir una nota o cambiar marcas, usa la columna **Notas** y los puntos de las marcas en la fila.

---

## Situaciones habituales

### «Está aquí, pero no la encuentro».

Busca parte de su nombre, su correo o su código de grupo. Si la encuentras, márcala. Si no aparece en la lista, puede que su inscripción se haya cancelado o que nunca se inscribiera. Pide a un administrador que lo compruebe en la página **Participantes**: una inscripción cancelada puede volver a ponerse como confirmada, y entonces aparece en el check-in al momento.

### «Tengo que deshacer una marca».

Vuelve a hacer clic en la casilla. Queda desmarcada y la hora de check-in se borra.

### «Somos dos en la misma mesa. ¿No nos estorbaremos?».

No. Cada uno puede buscar y marcar en su propio dispositivo, y ambas pantallas se mantienen sincronizadas.

### «Usamos nuestro propio sistema de pagos o autorizaciones. ¿Podemos registrar solo las llegadas?».

Sí. No crees columnas personalizadas; la casilla principal de **Check-in** funciona sola.

### «¿Cómo obtengo una lista de quién ha llegado?».

Dos opciones:

- En **Participantes**, haz clic en **↓ Exportar ▾ ▸ Lista completa de participantes**. El CSV tiene una columna **Checked In** (Yes / No) para todos.
- En **Informes**, el recuadro **Check-in** muestra el total actualizado durante la fase de Evento. Para tener una copia en papel en la entrada, imprime la lista **Firma** (consulta la [sección 08](08-reports-and-pdf-exports.es.md)).

---

## Siguiente paso

La [sección 08 — Informes y PDF](08-reports-and-pdf-exports.es.md) trata la página de Informes, las listas imprimibles en PDF en distintos formatos e idiomas y lo que muestran sobre tu asignación.
