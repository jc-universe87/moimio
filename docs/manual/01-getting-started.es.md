🌐 [English](01-getting-started.md) · [Deutsch](01-getting-started.de.md) · [한국어](01-getting-started.ko.md) · **Español** · [Português (Brasil)](01-getting-started.pt-BR.md) · [Français](01-getting-started.fr.md)

# 01 — Primeros pasos

Esta sección trata las partes de Moimio que usarás en tu primera sesión: la configuración inicial, la interfaz de administración, la lista de eventos, el modelo de fases que rige todo lo demás y lo básico de la gestión de usuarios.

---

## Configuración inicial (todavía sin usuarios)

<p align="center">
  <img src="../assets/first-time-setup.png" alt="Pantalla de configuración inicial para la primera cuenta de Superadministrador" width="420">
  <br>
  <em>Pantalla de configuración inicial para la primera cuenta de Superadministrador</em>
</p>

La primera vez que visitas un Moimio recién instalado, todavía no hay usuarios en el sistema. Al abrir la dirección llegas directamente a la pantalla **Configuración inicial**. Antes de empezar, puedes cambiar el idioma con el selector 🌐 que hay debajo del formulario.

Rellena:

- **Nombre completo**: tu nombre visible en el área de administración.
- **Correo electrónico**: tu usuario para iniciar sesión.
- **Contraseña** y **Confirmar la contraseña**: mínimo 8 caracteres. Usa un buen gestor de contraseñas.

Haz clic en **Crear superadministrador**. Tu cuenta se crea con el rol de **Superadministrador** y acceso completo, y quedas con la sesión iniciada.

La pantalla de configuración solo aparece una vez. En cuanto existe un usuario, ese paso se desactiva y la dirección muestra la página de inicio de sesión normal.

> **Alternativa: configuración por línea de comandos.** Si prefieres crear el primer administrador desde una terminal (por ejemplo, en instalaciones automatizadas o sin interfaz gráfica), el proyecto incluye también una herramienta de línea de comandos: `docker compose exec backend python -m app.cli.create_admin`. Ambos caminos llevan al mismo resultado; la configuración en pantalla es la opción recomendada.

---

## Iniciar sesión (después de la configuración inicial)

La página de inicio de sesión está en `/login` (p. ej. `https://events.yourchurch.org/login`). Introduce tu correo y tu contraseña y haz clic en **Iniciar sesión**. El selector 🌐 debajo del formulario cambia el idioma; el botón del sol y la luna, arriba a la derecha, alterna entre el modo claro y el oscuro.

Si has olvidado tu contraseña, haz clic en **¿Olvidaste tu contraseña?**, introduce tu correo y haz clic en **Enviar enlace de restablecimiento**. El enlace del correo caduca a los 30 minutos. Esto solo funciona si tu servidor tiene configurado el correo (SMTP). Si no es así, en la aplicación no hay ningún botón para que un administrador restablezca contraseñas: un Superadministrador puede eliminar tu cuenta y volver a crearla (después tendrán que volver a añadirte a tus eventos), o puedes pedir ayuda a quien gestione tu servidor.

---

## La interfaz de administración

Después de iniciar sesión, el área de administración tiene dos partes:

- **Barra lateral** (izquierda): aquí está toda la navegación. Su contenido cambia según el evento en el que estés, la fase en la que se encuentre y lo que tengas permitido hacer.
- **Área principal**: lo que hayas abierto.

**No hay barra superior.** En un móvil o en una ventana estrecha, la barra lateral se oculta; toca el botón **≡** de la esquina superior izquierda para volver a abrirla (en un ordenador, el **◀** de la parte superior de la barra lateral la contrae).

De arriba abajo, la barra lateral contiene:

1. **Navegación.** En la lista de eventos solo aparece **Eventos**. Dentro de un evento tienes un enlace **Todos los eventos** para volver a la lista y, después, los elementos propios del evento (consulta «Las tres fases» más abajo).
2. **Gestión**: herramientas del espacio de trabajo, visibles solo para quienes pueden usarlas:
   - **Usuarios**: crear y gestionar las cuentas del equipo (superadministradores y personal con permiso para gestionar usuarios).
   - **Copias de seguridad**: descargar copias de seguridad de eventos o restaurar una (superadministradores).
   - **Webhooks**: enviar las actualizaciones de asignación a otro sistema que gestiones (superadministradores, solo en instalaciones propias).
   - **Espacio de trabajo**: ajustes de todo el espacio de trabajo (superadministradores). Aquí añades la **URL del aviso de privacidad** de tu organización: una vez configurada, el formulario público de inscripción muestra un enlace **Aviso de privacidad** justo después de la frase de consentimiento. Si lo dejas vacío, no se muestra ningún enlace.
3. **Tu nombre y tu rol** (p. ej. *Superadministrador*).
4. **Ver introducción**: vuelve a abrir la presentación «Bienvenido a Moimio».
5. **Preferencias**: abre un pequeño panel con tu **Idioma**, **Formato de fecha** y **Zona horaria**. Haz clic en **Guardar** para conservarlos. El formato de fecha se usa en todas las fechas del área de administración (hay seis formatos, p. ej. DD/MM/AAAA o AAAA-MM-DD); tu zona horaria se convierte en la zona horaria predeterminada de los eventos nuevos que crees.
6. **Cerrar sesión**.
7. **Línea de versión y aviso legal** (p. ej. `v1.0.6 · © Pistio`) y el interruptor de **modo claro/oscuro**. Al hacer clic en la línea de versión se abre el **Aviso legal**, que muestra los términos de la licencia del software y un botón **Borrar caché y recargar** (ver más abajo).

### Mantener la aplicación actualizada

Cuando tu servidor se ha actualizado, Moimio muestra en una esquina de la pantalla una tarjeta **Actualización disponible** («Hay una nueva versión de Moimio disponible.»). Haz clic en **Actualizar** para cargar la nueva versión. Si algo parece atascado o desactualizado y esa tarjeta no aparece nunca, abre el **Aviso legal** (haz clic en la línea de versión al pie de la barra lateral) y pulsa **Borrar caché y recargar**.

En móviles y tabletas puede aparecer también un aviso **Instalar Moimio** que te ofrece añadir la aplicación a la pantalla de inicio. Es opcional; **Ahora no** lo cierra.

---

## Las tres fases

Cada evento se encuentra en una de tres fases. La fase determina qué muestra la barra lateral y qué acciones están disponibles. Una franja de color en la parte superior del centro de configuración indica en qué punto está el evento.

### Fase de Configuración

El evento es un **borrador**. Estás preparando los detalles del evento, el formulario de inscripción, los tipos de grupo, las marcas y la lista del equipo. El formulario público de inscripción **todavía no** acepta inscripciones.

Barra lateral en Configuración: solo **Configuración**, que abre el centro de configuración con sus cinco tarjetas.

### Fase de Inscripción

Las inscripciones están **abiertas** y la fecha de inicio aún no ha llegado. El formulario público está activo; los participantes se inscriben y tú ves crecer las cifras.

Barra lateral en Inscripción: **Inscripción** (la página de resumen con los recuentos de inscripciones y el botón **Compartir formulario**), **Asignación**, **Participantes**, **Informes** y un menú **Más** para lo ocasional: **Detalles del evento**, **Formulario de inscripción**, **Marcas** y **Equipo y permisos** (este último solo si puedes gestionar usuarios).

### Fase de Evento

Las inscripciones están **cerradas**, o siguen abiertas pero ha llegado la fecha de inicio. El foco pasa de recoger inscripciones a llevar el evento.

La fase de Evento tiene tres subestados, que se calculan automáticamente a partir de las fechas:

- **Antes del inicio**: las inscripciones están cerradas y la fecha de inicio aún no ha llegado. Aquí se hacen los últimos retoques de la asignación.
- **En curso**: hoy está entre la fecha de inicio y la de finalización (ambas incluidas). El protagonista es el check-in.
- **Finalizado**: la fecha de finalización ya ha pasado. Informes, exportaciones, archivo.

Barra lateral en la fase de Evento: **Asignación**, **Participantes**, **Informes** y el mismo menú **Más**. El check-in se abre con el botón **Abrir modo de check-in →** de la parte superior de **Asignación** (visible para los administradores hasta que el evento está Finalizado).

Los miembros del personal que no son administradores del evento ven una barra lateral más sencilla, solo con las áreas que se les han concedido: **Participantes**, **Asignación**, **Check-in**, **Informes** o **Marcas**. Consulta la [sección 11](11-staff-permissions.es.md).

### Cómo cambian realmente las fases

La fase se deduce del estado del evento y del calendario:

- Borrador → fase de Configuración.
- Abierto, fecha de inicio en el futuro → fase de Inscripción.
- Abierto, fecha de inicio hoy o antes → fase de Evento (automático, sin necesidad de hacer clic).
- Cerrado → fase de Evento.

El estado en sí solo cambia cuando tú actúas:

- **De borrador a abierto**: cuando haces clic en **Listo para abrir las inscripciones →** al final del centro de configuración. El botón solo se activa cuando las tarjetas **Detalles** e **Inscripción** están confirmadas.
- **De abierto a cerrado**: cuando haces clic en **Cerrar inscripción** en la página de resumen **Inscripción** durante la fase de Inscripción, o en **Cerrar inscripciones** en el aviso **Las inscripciones siguen abiertas** de la parte superior de **Asignación** una vez empezado el evento.
- **De cerrado a abierto**: es posible en cualquier momento con **Reabrir inscripciones** en el aviso **Las inscripciones están cerradas** de la parte superior de **Asignación**.
- **No** se puede volver a borrador una vez abiertas las inscripciones.

**Archivar es independiente del estado.** Los eventos nunca se archivan automáticamente. Un Superadministrador archiva un evento desde el menú **⋯** de la lista de eventos o desde **Más ▸ Detalles del evento ▸ Zona peligrosa ▸ Archivar** (en la fase de Configuración, la misma **Zona peligrosa** está al final del centro de configuración). Un evento archivado es de solo lectura para todos, superadministradores incluidos, no admite nuevas inscripciones y pasa a la pestaña **Archivados**. Se puede revertir: **Desarchivar**, desde los mismos sitios.

---

## Gestión de usuarios

El resto de tu equipo (organizadores, voluntarios, personal de la entrada) se añade en la página **Usuarios**, dentro de **Gestión** en la barra lateral. Tu primera cuenta de Superadministrador siempre puede verla.

En la página Usuarios puedes:

- **Crear usuarios**: haz clic en **+ Nuevo usuario**, rellena **Nombre completo**, **Correo electrónico**, **Contraseña** (al menos 8 caracteres) y **Rol**, y haz clic en **Crear usuario**. Comunica tú mismo la contraseña a la persona; Moimio no la envía por correo.
- **Editar usuarios**: el icono del lápiz te permite cambiar su nombre, su rol y los permisos adicionales. (Las direcciones de correo no se pueden cambiar aquí).
- **Desactivar / Reactivar**: un usuario desactivado no puede iniciar sesión, pero su cuenta y sus datos se conservan. Úsalo cuando alguien se tome un descanso.
- **Eliminar**: el icono rojo de la papelera elimina permanentemente la cuenta y todas sus asignaciones a eventos. No se puede deshacer. Las notas que compartió con el equipo se mantienen, marcadas como escritas por un usuario eliminado.

Hay dos roles:

- **Superadministrador**: acceso completo a todos los eventos, todos los usuarios y todos los ajustes.
- **Personal**: solo ve los eventos a los que está asignado, con el acceso que se le conceda en cada uno.

A un usuario de Personal también se le pueden dar dos permisos adicionales, de forma independiente:

- **Permitir a este administrador gestionar usuarios**: le da acceso a la página **Usuarios**.
- **Puede crear nuevos eventos**: le da el botón **+ Nuevo evento**. Quien crea un evento se convierte automáticamente en **Administrador del evento** (acceso completo) de ese evento.

Una vez creada la cuenta, añades a la persona a un evento concreto desde dentro de ese evento: con la tarjeta **Equipo** del centro de configuración o, más adelante, en **Más ▸ Equipo y permisos**. Ahí eliges si es **Administrador del evento** (acceso completo a ese evento) o **Personal** con acceso a áreas concretas. Consulta la [sección 11](11-staff-permissions.es.md) para ver el modelo de permisos completo.

Un usuario de Personal que todavía no ha sido añadido a ningún evento ve, al iniciar sesión, la página **Esperando tu primera asignación**, con un botón **Actualizar**.

---

## La lista de eventos

<p align="center">
  <br>
  <img src="../assets/events-list.png" alt="Lista de eventos con las pestañas Activos / Pasados / Archivados" width="560">
  <br>
  <em>Lista de eventos con las pestañas Activos / Pasados / Archivados</em>
</p>

Después de iniciar sesión llegas a la lista de eventos. Los superadministradores ven todos los eventos; los demás, solo los eventos a los que están asignados o que han creado.

Cada tarjeta de evento muestra:

- El nombre del evento, sus fechas y su ubicación.
- Una etiqueta de fase de color: **Configuración**, **Inscripción**, **Evento**, **Pasado** o **Archivado**.
- Una etiqueta **Admin** si eres el Administrador de ese evento.
- Una cifra destacada según la fase: tarjetas confirmadas (Configuración, p. ej. «1 / 2»), personas inscritas (Inscripción), personas con check-in hecho (Evento) o asistentes en los eventos pasados.

Haz clic en una tarjeta para abrir el evento. La barra lateral cambia a los elementos de ese evento.

También puedes:

- **Crear un evento nuevo** con **+ Nuevo evento** (superadministradores y personal que puede crear eventos).
- **Restaurar un evento desde una copia de seguridad** con **↑ Desde copia**, justo al lado.
- **Buscar** eventos por nombre.
- **Cambiar de pestaña** entre **Activos**, **Pasados** (la fecha de finalización ya pasó) y **Archivados**.
- Usar el menú **⋯** de una tarjeta (superadministradores) para **Fijar arriba**, **Archivar** / **Desarchivar** o **Eliminar evento**. Los eventos fijados se quedan arriba en la pestaña Activos.

Para reutilizar la configuración de un evento anterior, marca **Usar la configuración de otro evento** al crear el nuevo; consulta la [sección 02](02-events-and-registration.es.md).

---

## Tu primera sesión: qué hacer

<p align="center">
  <img src="../assets/welcome-splash.png" alt="Tarjeta Bienvenido a Moimio, visible mientras todavía no hay eventos" width="560">
  <br>
  <em>Tarjeta Bienvenido a Moimio, visible mientras todavía no hay eventos</em>
</p>

Mientras no hay eventos, la lista de eventos muestra una tarjeta **Bienvenido a Moimio** que explica las tres fases, con un botón **Crea tu primer evento**. Puedes volver a verla en cualquier momento con **Ver introducción** en la barra lateral.

Después:

1. **Configura tu idioma, formato de fecha y zona horaria** en **Preferencias**, al pie de la barra lateral, y haz clic en **Guardar**.
2. **(Superadministradores)** Añade el enlace al aviso de privacidad de tu organización en **Gestión ▸ Espacio de trabajo ▸ URL del aviso de privacidad**, para que aparezca en todos los formularios de inscripción.
3. **Crea tu primer evento** para explorar el centro de configuración. Siempre puedes eliminarlo después.
4. **(Opcional)** Crea cuentas para el resto de tu equipo en la página **Usuarios**.

La siguiente sección ([Eventos e inscripción](02-events-and-registration.es.md)) explica en detalle cómo crear un evento.

---

## Dos términos que verás por todas partes

**Participante** y **usuario** son cosas distintas en Moimio.

- Un **participante** es alguien inscrito en un evento. No tiene cuenta para iniciar sesión: existe como una fila en tu tabla de Participantes. Rellena el formulario de inscripción, recibe correos y pasa por el check-in. Nunca ve el área de administración.
- Un **usuario** es alguien con cuenta: tú y el resto del equipo organizador. Cada usuario tiene un rol (**Superadministrador** o **Personal**). Dentro de un evento concreto, un usuario de Personal es **Administrador del evento** (acceso completo a ese evento) o **Personal** con acceso a áreas seleccionadas. Consulta la [sección 11](11-staff-permissions.es.md) para ver el modelo completo.

No los confundas al leer el resto del manual. Participantes = las personas que vienen al evento. Usuarios = las personas que lo organizan.
