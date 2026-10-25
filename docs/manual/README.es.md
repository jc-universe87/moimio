🌐 [English](README.md) · [Deutsch](README.de.md) · [한국어](README.ko.md) · **Español** · [Português (Brasil)](README.pt-BR.md) · [Français](README.fr.md)

# Manual de usuario

Este manual explica cómo usar Moimio para organizar un evento de principio a fin. Da por hecho que ya has instalado Moimio y has iniciado sesión; si no es así, empieza por la [Guía de instalación](../installation/README.es.md).

> Este manual trata sobre **Moimio CE (Community Edition)**, la versión de código abierto que puedes alojar tú mismo. El mismo flujo de trabajo sirve para el producto alojado en [moimio.app](https://moimio.app): ambas ediciones comparten el mismo código.

---

## Cómo leer este manual

Seguramente no necesitas leerlo de principio a fin. Te recomendamos dos caminos:

### → Si quieres organizar un evento para mañana

Lee la **[Guía rápida](quick-guide.es.md)** (unos 10 minutos). Recorre un evento completo, desde su creación hasta la exportación en PDF, sin entrar en detalles ni casos especiales. Sabrás lo suficiente para ponerte en marcha.

### → Si quieres entender todo el producto

Lee las secciones numeradas en orden. Cada una se centra en un área. Unos 30 minutos en total.

---

## Secciones

| # | Sección | Qué contiene |
|---|---|---|
| | [Guía rápida](quick-guide.es.md) | Un evento de principio a fin en diez minutos de lectura. |
| 01 | [Primeros pasos](01-getting-started.es.md) | Configuración inicial e inicio de sesión. La interfaz de administración, las tres fases del evento (Configuración, Inscripción, Evento), las cuentas de usuario, la lista de eventos y tu primera sesión. |
| 02 | [Eventos e inscripción](02-events-and-registration.es.md) | Crear eventos. El centro de Configuración. Preparar el formulario de inscripción, los campos personalizados y los códigos de grupo. Abrir y cerrar las inscripciones. Correos de confirmación. |
| 03 | [Participantes](03-people.es.md) | La tabla de Participantes. Estados (pendiente / confirmado / cancelado). Editar en la tabla, códigos de grupo, notas, importación CSV y exportaciones. |
| 04 | [Marcas](04-marks.es.md) | Etiquetas de color para clasificar a los participantes. El editor de marcas. Prioridades de las marcas por tipo de grupo. Reservar un grupo para una marca. |
| 05 | [Tipos de grupo y unidades](05-group-types-and-units.es.md) | Los tipos de grupo (Asignación de habitaciones, Grupos pequeños y los que añadas) y los grupos que contienen. Capacidad, género y restricciones por marca. Mantener a alguien fuera de un tipo de grupo. Exportar e importar una estructura. |
| 06 | [Motor de asignación](06-allocation-engine.es.md) | Qué hace el motor, explicado con sencillez. Configuración del motor. Revisar una propuesta, bloquear grupos, volver a ejecutarlo, ajustes manuales, historial y motivos. |
| 07 | [Check-in](07-check-in.es.md) | La lista de check-in. Columnas de check-in personalizadas. Sincronización en tiempo real entre tabletas y móviles. |
| 08 | [Informes y PDF](08-reports-and-pdf-exports.es.md) | Los recuadros del panel. Listas en PDF compacta, de firmas y detallada. Las marcas en los PDF. Exportaciones CSV. |
| 09 | [Exportación de datos y RGPD](09-data-export-gdpr.es.md) | La exportación de datos personales de un participante. Editar, quitar y borrar definitivamente. Enlace al aviso de privacidad. Copias de seguridad completas y solo de estructura, restauración y traslado de un espacio de trabajo. |
| 10 | [Varios eventos y archivo](10-multi-event-and-archive.es.md) | La lista de eventos. Archivar y desarchivar. Crear un evento nuevo con la configuración de uno anterior. Llevar varios eventos a la vez. |
| 11 | [Equipo y permisos](11-staff-permissions.es.md) | Cuentas de usuario (Superadministrador, Personal) y eliminación de usuarios. El equipo de cada evento: Administrador del evento o Personal. Los cinco ajustes de permisos. |

---

## Convenciones de este manual

- El texto en **negrita** se refiere a un elemento de la interfaz en el que puedes hacer clic: un botón, una pestaña, una opción de menú.
- El texto en `monoespaciado` se refiere a un valor, una clave de configuración o un concepto técnico.
- Las marcas ▸ indican una secuencia de clics, p. ej. **Usuarios ▸ + Nuevo usuario ▸ Crear usuario**.
- Incluimos capturas de pantalla donde ayudan a orientarse en la interfaz; algunas secciones se apoyan más en el texto cuando la pantalla es sencilla o cambia con frecuencia. Con el tiempo, las capturas pueden diferir un poco de la versión actual.

---

## Cuando el manual no tiene tu respuesta

Tres sitios donde buscar:

- **[Preguntas frecuentes](../faq.md)** (en inglés): dudas habituales sobre alcance, alojamiento, escalabilidad y RGPD.
- **[Glosario](../glossary.md)** (en inglés): definiciones de los términos propios de Moimio (clúster, marca, código de grupo, etc.).
- **La documentación de la API generada automáticamente** en `http://localhost:6121/docs` (o donde esté tu backend): para desarrolladores que trabajan con la API.

Si nada de eso te ayuda, [abre una incidencia](https://github.com/pistio/moimio/issues/new?template=feature_request.md): «el manual no explicaba X» es una petición perfectamente válida y justo el tipo de comentario que mejora la documentación.
