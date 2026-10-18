# Instalación

Esta guía explica cómo instalar **Moimio CE (Community Edition)**, la versión de código abierto que puedes alojar tú mismo. (Para el producto alojado, regístrate en [moimio.app](https://moimio.app): no hace falta instalar nada).

Moimio CE funciona como tres contenedores Docker (un backend, un frontend y una base de datos) coordinados por Docker Compose. La instalación consiste básicamente en: clonar, configurar, ejecutar `docker compose up --build` (que construye las imágenes de Moimio a partir del código fuente en tu máquina) y crear el primer administrador en la pantalla de configuración inicial.

En esta carpeta hay dos guías, según tu experiencia. Elige una.

---

## ¿Qué guía debo seguir?

### → [Guía de instalación rápida](quick-guide.es.md)

Úsala si ya sabes:

- Qué es Docker y cómo ejecutar comandos `docker compose`.
- Cómo conectarte a un servidor por SSH, editar un archivo y leer registros.
- Cómo configurar un proxy inverso que gestione TLS (Caddy, Nginx, Traefik o un Cloudflare Tunnel).

Tiempo necesario: **de 30 a 60 minutos**, desde clonar el repositorio hasta iniciar sesión como administrador.

### → [Guía para principiantes](beginner.es.md)

Úsala si algo de lo anterior te suena raro. La guía para principiantes:

- Recorre las **dos opciones principales de alojamiento**: un VPS alquilado (servidor en la nube) o tu propio ordenador o mini-PC en casa o en la oficina, con Cloudflare Tunnel para el acceso público.
- Enseña desde cero a trabajar con SSH, incluida la creación de claves.
- Instala Docker con el comando oficial de una sola línea, sin dar nada por supuesto.
- Configura Moimio paso a paso, explicando para qué sirve cada pieza.
- Trata los nombres de dominio y HTTPS con Caddy o Cloudflare.

Tiempo necesario: **unas 2 horas** la primera vez, sobre todo esperando.

No necesitas ser desarrollador para seguirla. Necesitas copiar los comandos con cuidado y pedir ayuda cuando algo no funcione.

---

## Cuánto cuesta

El coste del alojamiento depende por completo de dónde lo pongas.

| Dónde | Coste | Ideal para |
|---|---|---|
| Tu propio portátil u ordenador de sobremesa (para probar) | Gratis | Probar Moimio y aprender el flujo de trabajo. No sirve para eventos reales, porque el portátil tiene que estar siempre encendido. |
| Un mini-PC de la iglesia en la oficina | Hardware, pago único (150–300 €) | Una iglesia pequeña que organiza unos pocos eventos al año. Funciona siempre que la oficina tenga electricidad e internet estables. |
| Un VPS alquilado en cualquier proveedor de nube | ~4–10 € al mes | La mayoría de los usuarios. Siempre encendido y fácil de ampliar. Hay opciones alojadas en la UE para organizadores atentos al RGPD. |

También te conviene un **nombre de dominio** (10–15 € al año) para tener enlaces de inscripción presentables; lo explicamos en la guía para principiantes.

---

## Requisitos de hardware

Moimio consume pocos recursos. Cifras orientativas:

- **CPU:** cualquier procesador moderno x86_64 o ARM64. Con dos núcleos basta.
- **RAM:** **2 GB como mínimo**, 4 GB para ir holgado. El consumo de memoria crece suavemente con el tráfico simultáneo de inscripciones.
- **Disco:** **5 GB** para las imágenes de la aplicación y la base de datos; la base de datos crece despacio (Moimio no almacena archivos subidos).
- **Red:** hace falta una IP pública (o un túnel como Cloudflare Tunnel) para que los participantes lleguen al formulario de inscripción. Puertos de entrada 80/443 (o 6120 si te saltas TLS para hacer pruebas). Para eventos reales, cuenta con HTTPS: algunas funciones de la aplicación (la caché sin conexión, el aviso de «nueva versión disponible») solo funcionan con HTTPS o en `localhost`.

Para comprobar si el equipo que estás valorando cumple estos requisitos:

- **CPU y arquitectura:** `uname -m` (Linux/macOS) o mira «Tipo de sistema» en Información del PC (Windows). Cualquier resultado `x86_64`, `aarch64` o `arm64` vale.
- **RAM:** `free -h` (Linux), Monitor de Actividad (macOS), Administrador de tareas → Rendimiento (Windows).
- **Espacio libre en disco:** `df -h` (Linux/macOS), Explorador de archivos → Este equipo (Windows).
- **Accesibilidad pública:** si es un VPS, el proveedor te indica la IP pública; si es tu propio ordenador, consulta la sección sobre Cloudflare Tunnel de la guía para principiantes.

Un VPS pequeño con 2 vCPU y 2 GB de RAM (suele costar unos 4–5 €/mes en proveedores europeos) aguanta sin problemas un evento de 150 personas. Una **Raspberry Pi 4 (4 GB)** también sirve para eventos pequeños gestionados desde la oficina de una iglesia. Son solo ejemplos: Moimio no exige ningún hardware ni proveedor concreto.

---

## Sistema operativo

Cualquiera en el que funcione Docker:

- **Linux** (Ubuntu 22.04+, Debian 12+, Fedora, Arch, ...): recomendado para producción.
- **macOS** con Docker Desktop: bien para desarrollo; no recomendado para eventos reales con inscripciones de verdad (los portátiles no son servidores).
- **Windows** con Docker Desktop y WSL2: la misma advertencia.

---

## Después de la instalación

Cuando Moimio esté en marcha, tu navegador llegará automáticamente a la pantalla **Configuración inicial**. Rellena tu nombre completo, tu correo y una contraseña (dos veces), haz clic en **Crear superadministrador** e inicia sesión con la cuenta que acabas de crear. Como aún no hay eventos, verás la pantalla **Bienvenido a Moimio** con un botón **Crea tu primer evento**.

Dos cosas que conviene hacer pronto:

- **Configura el enlace a tu aviso de privacidad.** Como Superadministrador, abre **Espacio de trabajo** en la barra lateral e introduce la dirección web del aviso de privacidad de tu organización. El formulario público de inscripción lo enlazará justo después de la frase de consentimiento.
- **Planifica las actualizaciones y las copias de seguridad.** Ambas guías tienen una sección breve sobre cada tema. En resumen: `./upgrade.sh` actualiza una instalación hecha con git y antes hace una copia de seguridad de la base de datos; la página **Copias de seguridad** de la aplicación descarga copias de seguridad por evento.

¿Vienes del servicio alojado o de otro servidor? Consulta [Moving a workspace to your own Moimio](../moving-a-workspace.md) (en inglés).

A partir de ahí, el [Manual de usuario](../manual/README.es.md) explica cómo organizar un evento: crear eventos, preparar las inscripciones, ejecutar el motor de asignación, hacer el check-in y exportar listas.

Si tienes problemas durante la instalación, las secciones de solución de problemas al final de cada guía cubren los fallos más comunes. Para cualquier cosa más rara, [abre un informe de error](https://github.com/jc-universe87/moimio/issues/new?template=bug_report.md).
