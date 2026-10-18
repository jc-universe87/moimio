# 11 — Equipo y permisos

Moimio tiene dos tipos de cuenta de usuario y un equipo para cada evento. Esta sección trata ambas cosas: quién es Superadministrador, quién es Personal y cómo dar a alguien acceso a un evento concreto con los permisos adecuados.

<p align="center">
  <img src="../assets/staff-permissions.png" alt="El formulario Asignar un usuario al evento, con el selector Usuario, el desplegable Rol, Copiar permisos de y los cinco ajustes de permisos" width="560">
  <br>
  <em>Añadir a alguien al equipo de un evento</em>
</p>

---

## Cuentas de usuario

Las cuentas se gestionan en Barra lateral ▸ **Usuarios** (dentro de **Gestión**), en la página **Gestión de usuarios**.

### Superadministrador

El primer Superadministrador se crea durante la configuración inicial. Se pueden añadir más desde **Gestión de usuarios**; solo un Superadministrador puede convertir a otra persona en Superadministrador. Los superadministradores:

- Tienen acceso completo a todos los eventos.
- Pueden crear eventos y gestionar usuarios.
- Son los únicos que pueden archivar, desarchivar, eliminar o fijar eventos, y restaurar copias de seguridad.
- Son los únicos que ven **Copias de seguridad**, **Espacio de trabajo** y **Webhooks** en la barra lateral.

No hace falta añadir a los superadministradores al equipo de un evento: ya tienen acceso a todo.

### Personal

Una cuenta de **Personal** es solo un usuario para iniciar sesión. **Por sí sola, una cuenta de Personal no tiene acceso a ningún evento.** El acceso se obtiene al ser añadido al equipo de un evento, con un rol y unos permisos para ese evento. Un usuario de Personal que todavía no está en ningún equipo ve la pantalla **Esperando tu primera asignación** al iniciar sesión.

A cualquier usuario de Personal se le pueden marcar dos capacidades adicionales:

- **Permitir a este administrador gestionar usuarios**: puede abrir **Gestión de usuarios** y crear, editar, desactivar y eliminar cuentas de Personal (pero no de superadministradores).
- **Puede crear nuevos eventos**: tiene el botón **+ Nuevo evento**. Quien crea un evento se convierte automáticamente en su Administrador del evento.

### Añadir, editar y eliminar cuentas

- **+ Nuevo usuario** abre el formulario: **Nombre completo**, **Correo electrónico**, **Contraseña**, **Rol** y las dos capacidades. Haz clic en **Crear usuario**.
- En la lista, el lápiz gris edita el nombre, el rol y las capacidades de un usuario.
- **Desactivar** impide que alguien inicie sesión sin eliminar nada. **Reactivar** le permite volver a entrar.
- El icono rojo de la papelera elimina la cuenta para siempre (**Eliminar definitivamente**). No puedes eliminarte a ti mismo.

**Eliminar un usuario siempre funciona, haga lo que haya hecho en Moimio.** Sus puestos en los equipos de los eventos desaparecen con él, igual que sus notas no publicadas (borradores). Las notas que publicó se mantienen y aparecen como escritas por **[usuario eliminado]**. Sus entradas en el historial de asignación también se mantienen, igualmente como **[usuario eliminado]**.

Si tienes dudas, desactivar es la opción más suave: se puede deshacer; eliminar, no.

---

## El equipo de cada evento

Cada evento tiene su propia lista de miembros del equipo. Cada uno tiene:

- **Un rol para este evento:** **Administrador del evento** o **Personal**.
- **Permisos** (solo se usan cuando el rol es Personal).

Gestiona el equipo desde la tarjeta **Centro de configuración ▸ Equipo** durante la fase de Configuración, o desde **Más ▸ Equipo y permisos** una vez abiertas las inscripciones. Ambos caminos abren el mismo panel **Equipo y permisos**.

Para añadir personas tienes que ser Superadministrador o tener **Permitir a este administrador gestionar usuarios**: la lista de personas entre las que elegir procede de Gestión de usuarios. Alguien debe tener una cuenta antes de poder añadirlo.

### Rol de Administrador del evento

**Administrador del evento** da acceso completo a *este evento concreto*. Puede:

- Editar los detalles del evento, el formulario de inscripción y los tipos de grupo.
- Abrir y cerrar las inscripciones.
- Ejecutar la asignación, confirmar los resultados y dejar a personas fuera de un tipo de grupo.
- Usar el check-in, incluida su preparación antes del evento.
- Crear, editar y eliminar marcas.
- Descargar informes y exportaciones, incluida la exportación de datos personales de un participante.
- Quitar participantes.
- Gestionar el equipo del evento (con la capacidad de gestionar usuarios, ver arriba).

Archivar, eliminar y restaurar eventos sigue siendo cosa de los superadministradores. Para los administradores del evento, los ajustes de permisos se ignoran: el acceso completo va implícito.

### Rol de Personal

El **Personal** de un evento solo puede hacer lo que le permiten sus permisos. Los cinco ajustes de permisos se describen a continuación.

---

## Los cinco ajustes de permisos

Cada ajuste es independiente. Un miembro del Personal puede tener cualquier combinación: por ejemplo, Participantes en solo lectura más Marcas, o solo Informes.

### Acceso a participantes (Sin acceso / Solo lectura / Lectura y escritura)

La tabla de Participantes y los datos de inscripción.

- **Solo lectura**: ve la lista de participantes; puede buscar, filtrar y ver los detalles.
- **Lectura y escritura**: además puede editar datos, cambiar el estado y los códigos de grupo, inscribir a personas y asignar marcas.
- **Sin acceso**: el elemento Participantes queda oculto.

Quitar participantes y exportar datos personales es solo para administradores del evento.

### Acceso a asignación (Sin acceso / Solo lectura / Lectura y escritura)

El tablero de asignación.

- **Solo lectura**: ve quién está en qué grupo, en todos los tipos de grupo.
- **Lectura y escritura**: puede arrastrar a personas entre grupos y añadir, editar o eliminar grupos.
- **Sin acceso**: el elemento Asignación queda oculto.

Ejecutar la asignación, confirmarla, cambiar la configuración de los tipos de grupo y dejar a personas fuera de un tipo de grupo es cosa de los administradores del evento.

### Acceso al check-in (casilla + opción adicional)

La casilla principal permite al miembro del Personal ver la lista de check-in y marcar a las personas una vez empezado el evento.

Cuando está marcada, aparece una segunda opción: **Acceso antes de que comience el evento**. Con ella puede abrir el check-in durante la fase de Inscripción y añadir o eliminar columnas de check-in antes de las llegadas. Útil cuando un coordinador designado, que no siempre es Administrador del evento, prepara el check-in. Sin ella, el personal de check-in puede marcar casillas pero no cambiar las columnas.

No existe un check-in de solo lectura: marcar a las personas es precisamente su finalidad. La opción adicional controla *cuándo* tienen acceso, no cuánto.

Los superadministradores y los administradores del evento siempre tienen acceso completo al check-in, también antes del evento.

### Acceso a informes (casilla)

La página de Informes.

- **Marcada**: ve los informes y puede descargar las listas en PDF Compacto y Firma.
- **Sin marcar**: el elemento Informes queda oculto.

La lista **detallada** y la hoja de cálculo de participantes contienen datos personales, así que también requieren **Acceso a participantes**: el acceso a informes por sí solo no basta.

### Acceso a marcas (casilla)

- **Marcada**: ve el elemento Marcas en la barra lateral; puede crear marcas, editar o eliminar las marcas que *ha creado* (no las de otros) y asignar marcas a los participantes.
- **Sin marcar**: no hay elemento Marcas.

**Todas las personas con acceso al evento pueden ver las marcas.** Quien puede ver participantes puede hacer clic en una marca para ver qué significa. El acceso a marcas sirve para crearlas y asignarlas. (Participantes en **Lectura y escritura** también permite asignar marcas).

---

## Añadir a alguien a un evento

Desde la tarjeta **Equipo** o desde **Equipo y permisos**:

1. Haz clic en **+ Asignar usuario**.
2. En **Usuario**, elige a alguien (**Selecciona un usuario**). La lista muestra las cuentas activas que todavía no están en este evento.
3. Elige un **Rol**: **Personal** o **Administrador del evento**.
4. Para Personal, configura los cinco permisos.
5. Haz clic en **Asignar usuario**.

### Copiar permisos de

Cuando el evento ya tiene miembros del Personal, **Copiar permisos de** te permite rellenar el formulario con la configuración de otra persona (**Selecciona un miembro del equipo**). Ajusta lo que quieras antes de guardar.

Consejo: al crear el evento del año que viene, puedes copiar todo el equipo; consulta la [§10](10-multi-event-and-archive.es.md#crear-un-evento-nuevo-a-partir-de-uno-anterior).

---

## Editar o quitar a alguien de un evento

La fila de cada miembro del equipo tiene un lápiz gris y un icono rojo de papelera.

- **Editar** (lápiz): el mismo formulario, relleno con su rol y sus permisos actuales. Haz clic en **Guardar**.
- **Quitar** (papelera): confirma en **¿Quitar usuario del evento?**. Su acceso a este evento termina. Su cuenta no se toca: conserva sus otros eventos.

Si alguien está viendo el evento cuando se le quita, en su siguiente clic verá una pantalla de «sin acceso».

---

## Desactivar a un usuario frente a quitarlo de un evento

Dos alcances distintos:

- **Quitar de un evento** → termina el acceso a *un* evento. Conserva su cuenta y sus otros eventos.
- **Desactivar a un usuario** (en Gestión de usuarios) → no puede iniciar sesión en absoluto. Sus puestos en los equipos quedan registrados, pero no se pueden usar.

Desactiva cuando alguien deja la organización. Quita de un evento cuando «ha terminado con este evento, pero sigue en el equipo del año que viene».

---

## Llevar un seguimiento

El historial del panel de perfil de cada participante (el icono **ⓘ Ver perfil**) muestra quién lo colocó o lo movió, y cuándo. Las acciones de administración clave (crear, archivar y eliminar eventos, quitar participantes, exportar datos personales) también quedan registradas en el registro del servidor (`docker compose logs backend` en una instalación propia).

La exportación de datos de un participante no indica qué miembro del equipo hizo cada movimiento (consulta la [§09](09-data-export-gdpr.es.md)).

---

## Siguiente paso

Aquí termina el manual de usuario. Para saber más (en inglés):

- [Glossary](../glossary.md): términos propios de Moimio.
- [FAQ](../faq.md): preguntas frecuentes.
- [GDPR compliance](../gdpr-compliance.md): enfoque de privacidad y detalles técnicos.
- [Moving a workspace to your own Moimio](../moving-a-workspace.md): cómo trasladar todos los eventos a un servidor que gestiones tú.
- [Data model](../data-model.md): referencia del esquema para desarrolladores e integradores.
