🌐 [English](02-events-and-registration.md) · [Deutsch](02-events-and-registration.de.md) · [한국어](02-events-and-registration.ko.md) · **Español** · [Português (Brasil)](02-events-and-registration.pt-BR.md) · [Français](02-events-and-registration.fr.md)

# 02 — Eventos e inscripción

Cómo crear un evento, rellenar sus detalles, preparar su formulario de inscripción, abrirlo a las inscripciones y seguir de cerca las que van llegando.

---

## Crear un evento

Desde la lista de eventos, haz clic en **+ Nuevo evento**. El formulario **Crear evento** es mínimo a propósito:

- **Nombre del evento**: aparece en la parte superior del formulario de inscripción y en tu lista de eventos. Que sea comprensible («Retiro de primavera 2026» mejor que «RP2026-EVENTO-001»).
- **Usar la configuración de otro evento** (opcional; aparece cuando ya tienes al menos un evento): márcalo, elige el evento del que copiar y luego decide **Qué copiar**: **Marcas**, **Formulario de inscripción**, **Campos personalizados**, **Tipos de grupo** (con sus habitaciones y grupos) y **Miembros del equipo**. Al principio están marcadas las cinco; desmarca lo que no quieras. Solo se copia la configuración: nunca participantes, asignaciones, check-ins ni notas.

Haz clic en **Crear evento**. El evento se crea como borrador y llegas al **centro de configuración**.

Si has empezado de cero (sin copiar configuración), ya te esperan dos tipos de grupo: **Asignación de habitaciones** y **Grupos pequeños**. (Aparecen en el idioma de tu interfaz y puedes renombrarlos o eliminarlos). Si has copiado tipos de grupo de otro evento, tendrás esos en su lugar.

Todo lo demás (fechas, ubicación, descripción, zona horaria, campos del formulario, grupos, marcas, equipo) se configura a continuación, en el centro de configuración.

> **Restaurar en lugar de crear.** Si tienes un archivo de copia de seguridad de Moimio de un evento anterior, **↑ Desde copia**, junto a **+ Nuevo evento**, lo vuelve a crear como un nuevo evento en borrador.

---

## El centro de configuración

<p align="center">
  <br>
  <img src="../assets/setup-hub.png" alt="El centro de configuración con sus cinco tarjetas" width="560">
  <br>
  <em>El centro de configuración con sus cinco tarjetas</em>
</p>

Cinco tarjetas, cada una con un área de configuración. Haz clic en una tarjeta para abrirla.

| Tarjeta | Qué incluye |
|---|---|
| **Detalles** | Nombre del evento, descripción, ubicación, fechas de inicio y finalización, zona horaria. |
| **Inscripción** | El formulario público de inscripción: qué campos estándar mostrar y tus propios campos personalizados. |
| **Tipos de grupo** | Las formas en que repartirás a las personas: habitaciones, grupos pequeños, talleres (ver la [sección 5](05-group-types-and-units.es.md)). Incluye de entrada **Asignación de habitaciones** y **Grupos pequeños**. Las habitaciones y los grupos concretos de cada tipo se añaden más adelante desde **Asignación**, no desde esta tarjeta. |
| **Marcas** | Opcional. Etiquetas de color como «Vegetariano» o «Líder» (ver la [sección 4](04-marks.es.md)). |
| **Equipo** | Opcional. Añade a otros usuarios al evento y elige a qué pueden acceder (ver la [sección 11](11-staff-permissions.es.md)). |

Las tarjetas **Detalles** e **Inscripción** tienen cada una un botón **Guardar y confirmar** al final. **Las dos deben estar confirmadas** para poder abrir las inscripciones. La tarjeta **Inscripción** solo puede confirmarse si el evento tiene al menos un tipo de grupo; como los dos predeterminados están ahí desde el principio, esto solo importa si los has eliminado todos.

Confirmar no es irreversible: **Quitar la confirmación** vuelve a abrir una tarjeta para hacer cambios, y después puedes confirmarla de nuevo. Este paso extra simplemente evita que abras las inscripciones con la configuración a medias.

> **Fechas y horas.** Las fechas aparecen en el formato que elegiste en **Preferencias**; el selector de fechas sigue la configuración de tu navegador. Las horas se muestran en formato de 24 horas, en la zona horaria del propio evento.

---

## Preparar el formulario de inscripción

Abre la tarjeta **Inscripción**.

### Campos estándar

**Nombre**, **Apellido**, **Correo electrónico** y la casilla de **consentimiento** están siempre en el formulario y no se pueden desactivar. En **Campos estándar** puedes añadir más, cada uno con dos casillas:

- **Mostrar**: el campo aparece en el formulario.
- **Obligatorio**: hay que rellenar el campo (solo disponible si **Mostrar** está marcado).

Los cambios se guardan automáticamente.

| Campo | Notas |
|---|---|
| Género | La persona elige **Masculino** o **Femenino**. El motor de asignación lo usa para los grupos restringidos a un solo género. |
| Fecha de nacimiento | Útil en retiros con grupos por edades. |
| Teléfono | |
| Dirección | |
| País | Útil en eventos internacionales. |
| Iglesia / organización | Útil cuando los participantes vienen de varias iglesias u organizaciones. |

Todos los formularios incluyen además un cuadro opcional **Mensaje a los organizadores** (para necesidades alimentarias, de accesibilidad y similares) y una casilla de consentimiento. Si un Superadministrador ha configurado una **URL del aviso de privacidad** en **Gestión ▸ Espacio de trabajo**, aparece un enlace **Aviso de privacidad** justo después de la frase de consentimiento.

### Campos personalizados

Para todo lo que no cubren los campos estándar, haz clic en **+ Añadir campo** en **Campos personalizados**. Elige:

- **Nombre del campo**: lo que ve la persona al inscribirse («Talla de camiseta», «¿Has venido antes?»).
- **Tipo**: **Texto**, **Número**, **Lista desplegable**, **Sí/No** o **Fecha**.
- **Obligatorio**: si hay que rellenarlo o no.
- **Opciones**: para una **Lista desplegable**, las opciones separadas por comas (p. ej. `S, M, L, XL`).
- **Mostrar en el formulario de registro**: desmárcalo para un campo que solo rellena tu equipo (sigue apareciendo en la tabla de Participantes).

Haz clic en **Añadir campo personalizado** para guardarlo.

Campos personalizados habituales:

- «Talla de camiseta» (Lista desplegable: XS, S, M, L, XL, XXL)
- «¿Eres líder de grupo pequeño?» (Sí/No)
- «¿Es tu primera vez en este evento?» (Lista desplegable: Sí, No, He venido una vez)
- «Necesidades alimentarias» (Texto o Lista desplegable, según lo cerrado que sea tu menú)
- «Consentimiento de imagen» (Sí/No, para usar la imagen del participante en las fotos del evento)

Los campos personalizados pertenecen a un solo evento: añadir «Talla de camiseta» aquí no lo añade a tus otros eventos. Puedes editar o eliminar un campo aunque ya hayan llegado inscripciones, pero **al eliminar un campo también se eliminan todas las respuestas que ya se hayan dado**.

> **Reutilizar un formulario.** El menú **⋯** de la parte superior de la tarjeta tiene **Exportar formulario** e **Importar formulario**, para guardar un formulario en un archivo y cargarlo en otro evento (o en otra instalación de Moimio). Al importar nunca se duplican los campos que ya tienes.

### Códigos de grupo: mantener juntos a familias y amigos

Todos los formularios tienen la sección **¿Vienes con familia o amigos?**. Quien se inscribe elige una de estas opciones:

- **Vengo solo/a**.
- **Soy el primero de mi grupo en registrarme**: Moimio crea un nuevo código de grupo (a partir del apellido, p. ej. `SMITH-742`) y lo incluye en el correo de confirmación para que la persona pueda compartirlo.
- **Tengo un código de grupo**: escribe el código que le han dado (p. ej. `KIM-104`) y se le coloca con ese grupo.
- **Sí, pero no tengo código, solo su nombre**: solo aparece si has activado **Permitir preferencias de grupo** (ver más abajo). La persona escribe un nombre y algunos datos, y tú emparejas a la gente a mano.

Todas las personas que comparten un código de grupo forman un grupo que el motor de asignación intenta mantener unido. Consulta la [sección 5](05-group-types-and-units.es.md) para conocer el funcionamiento completo.

Los códigos de grupo tienen el formato `RAIZ-NNN`: hasta ocho letras del apellido (o de un nombre que elija la persona), un guion y un número. Se eliminan los acentos, así que Müller se convierte en `MULLER` y García en `GARCIA`; un apellido sin letras latinas (por ejemplo 김) recibe `GROUP`. Incluso quien se inscribe solo recibe un código, normalmente con un número de tres cifras (más largo solo si muchas personas del evento comparten ese apellido). Al inscribir a varias personas a la vez, cada persona adicional puede compartir el código de la primera (recomendado para familias), no tener ninguno o usar uno diferente.

---

## Abrir las inscripciones

Al final del centro de configuración está el recuadro **Abrir inscripciones**. Hasta que **Detalles** e **Inscripción** estén confirmadas, dice *«Confirma Detalles e Inscripción para desbloquear.»* y el botón aparece en gris. Cuando lo están, cambia a **Listo para abrir las inscripciones →**. Haz clic en él.

El evento pasa de borrador a abierto, estás en la **fase de Inscripción** y el formulario público de inscripción está activo.

Para encontrar el enlace público, haz clic en **Compartir formulario** en la parte superior de la página **Inscripción** (el primer elemento de la barra lateral). Verás:

- Un código QR para carteles y boletines impresos.
- El **Enlace del formulario** (p. ej. `https://events.yourchurch.org/register/abc-123-def`), con los botones **Copiar** y **Abrir ↗**.
- **Compartir…**, en móviles y tabletas, para enviarlo directamente a una aplicación de mensajería.

Comparte este enlace como sueles llegar a tus participantes: correo, boletín de la parroquia, grupo de WhatsApp, la web de tu iglesia. No cambia durante toda la vida del evento. Si prefieres insertar el formulario en tu web, usa el **Código de inserción** de **Más ▸ Formulario de inscripción ▸ Compartir inscripción**.

### Ajustes disponibles después de abrir

Una vez abiertas las inscripciones, **Más ▸ Formulario de inscripción** reúne todo lo de la tarjeta Inscripción y algunos extras:

- **Permitir preferencias de grupo**: permite indicar con quién se quiere estar aunque no se tenga código de grupo. Revisas tú mismo estas peticiones antes de asignar.
- **Personalizar la apariencia**: **Abrir el personalizador** para cambiar los colores, la fuente y el estilo de las esquinas del formulario.
- **Confirmación por correo electrónico**: **Requerir confirmación por correo para inscribirse** (desactivado por defecto), el **Nombre del remitente**, la **Dirección de respuesta** y **Enviar correo de prueba** para comprobar que el correo funciona. Haz clic en **Guardar configuración de correo** después de cambiarlos.

Si quieres confirmación por correo, actívala nada más abrir, antes de compartir el enlace.

### Seguir las inscripciones

La página **Inscripción** muestra cuántas personas se han inscrito (**Inscritos**), con los recuentos de **Confirmados**, **Pendientes** y **Cancelados**, un gráfico de inscripciones de los **Últimos 7 días**, los **Últimos 30 días** o **Desde la apertura**, un recuadro **Requiere atención** (por ejemplo, personas que aún no han confirmado su correo) y una lista de **Inscripciones recientes**. Se actualiza sola a medida que la gente se inscribe, sin necesidad de recargar. **Ver todos los participantes** te lleva a la tabla de Participantes ([sección 03](03-people.es.md)).

---

## Qué ven los participantes al inscribirse

<p align="center">
  <img src="../assets/public-registration-form.png" alt="Formulario público de inscripción" width="420">
  <br>
  <em>Formulario público de inscripción</em>
</p>

Los participantes llegan a un formulario limpio con el nombre, la descripción, la ubicación y la fecha de tu evento. Entonces:

1. Eligen su idioma con el selector 🌐 al pie de la página si lo necesitan (el formulario está en los mismos seis idiomas que el área de administración).
2. Rellenan los campos que hayas configurado y eligen una opción en **¿Vienes con familia o amigos?**.
3. Marcan la casilla de consentimiento (y pueden abrir tu **Aviso de privacidad**, si lo has configurado).
4. Hacen clic en **Inscribirse**.

Para inscribir a varias personas de una vez (una familia, un grupo de jóvenes), hacen clic en **+ Registrar otra persona**. Cada persona adicional tiene su propia tarjeta, con el atajo **Copiar datos de …**, y el botón pasa a ser **Registrar 2 personas** (3, 4, …).

Si falta algo o hay un error, el formulario lo indica en el idioma de la persona, justo al lado del campo que hay que corregir.

Lo que ocurre después depende de tu ajuste de **Confirmación por correo electrónico**:

- **Desactivada (por defecto).** La inscripción queda **confirmada** de inmediato. La persona ve **Inscripción completada** y recibe un correo con su código de grupo (si tu servidor puede enviar correos).
- **Activada.** La inscripción empieza como **pendiente**. La persona ve **Revisa tu correo** y recibe un correo con un enlace de confirmación. Al hacer clic, la inscripción pasa a **confirmada**, ve **¡Confirmado!** y recibe un segundo correo con su código de grupo.

Si tu servidor no está configurado para enviar correos (SMTP) y la confirmación está activada, los correos se omiten sin aviso y esas inscripciones se quedan **pendientes**, porque nadie puede hacer clic en un enlace que nunca recibió. Confírmalas a mano en la página Participantes o activa **Incluir participantes sin confirmar** en la configuración del motor de asignación. Si a alguien no le llegó el correo, la página Participantes tiene también un botón **Reenviar** que vuelve a enviar el correo de inscripción.

---

## Cerrar las inscripciones

Las inscripciones **no se cierran automáticamente** al llegar la fecha de inicio. Siempre las cierras tú.

- **Durante la fase de Inscripción:** haz clic en **Cerrar inscripción →** en la página **Inscripción**.
- **Una vez empezado el evento:** aparece el aviso **Las inscripciones siguen abiertas** en la parte superior de **Asignación** («Las personas aún pueden inscribirse durante el evento.»), con un botón **Cerrar inscripciones**.

Después de cerrar, el aviso de la parte superior de **Asignación** dice **Las inscripciones están cerradas**, con un botón **Reabrir inscripciones**. Puedes reabrir en cualquier momento, incluso con el evento ya empezado: muy práctico para quienes llegan tarde o para invitados de un día que se inscriben en la puerta.

Mientras las inscripciones están cerradas, quien intente enviar el formulario verá el mensaje *«La inscripción no está abierta para este evento.»*

---

## Errores habituales en esta fase

- **Olvidar confirmar la tarjeta Detalles.** Hay quien prepara el formulario de inscripción, pulsa **Guardar y confirmar** y no entiende por qué el botón para abrir las inscripciones sigue en gris. Hay que confirmar **Detalles** e **Inscripción**.
- **Añadir campos personalizados obligatorios con las inscripciones ya abiertas.** Quienes ya se inscribieron no los habrán respondido. Las nuevas inscripciones funcionan bien, pero tendrás que pedir la información que falta a las anteriores.
- **No probar el flujo de correo.** Antes de difundir el enlace, usa **Más ▸ Formulario de inscripción ▸ Confirmación por correo electrónico ▸ Enviar correo de prueba** para comprobar que el correo funciona y luego rellena tu propio formulario para hacer una prueba completa de principio a fin.

---

## Siguiente paso

La [sección 03 — Participantes](03-people.es.md) explica qué hacer con las inscripciones cuando empiezan a llegar: la tabla de Participantes, los estados, la edición, las confirmaciones manuales y los códigos de grupo desde el lado de la administración.
