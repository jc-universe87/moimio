🌐 [English](beginner.md) · [Deutsch](beginner.de.md) · [한국어](beginner.ko.md) · **Español** · [Português (Brasil)](beginner.pt-BR.md) · [Français](beginner.fr.md)

# Guía de instalación para principiantes

Esta guía es para quien nunca ha abierto una terminal pero necesita tener Moimio funcionando para un evento real. Iremos despacio.

Si ya te manejas con Docker y servidores Linux, la [Guía de instalación rápida](quick-guide.es.md) cubre lo mismo en 30 minutos.

No necesitas ser desarrollador. Necesitas copiar los comandos con cuidado y pedir ayuda cuando algo no funcione.

---

## Una advertencia sincera antes de empezar

Instalar Moimio es más complicado que instalar una aplicación de escritorio. Todavía no existe la experiencia de «pulsa el botón, espera y listo». Si te encuentras con algo que la guía no cubre, preguntar a un amigo con más conocimientos técnicos o pegar el error en un asistente de chat con IA suele desatascarte en pocos minutos.

La primera vez, calcula **unas dos horas**. La mayor parte es esperar a que terminen las descargas. La segunda vez es mucho más rápido.

---

## ¿Deberías alojarlo tú mismo? Una comprobación realista

La instalación es la parte fácil. La pregunta difícil es cómo será mantener un servidor en producción durante los meses siguientes, sobre todo en pleno evento, cuando algo se rompe y lo necesitas funcionando de nuevo en veinte minutos.

Un Moimio alojado por tu cuenta es un pequeño servidor Linux del que ahora eres responsable. En concreto, eso significa:

- **El servidor tiene que estar siempre encendido.** Si en tu oficina se va la luz, se cae la wifi del lugar o el proveedor del VPS sufre una avería, las inscripciones dejan de funcionar hasta que lo vuelvas a poner en marcha.
- **Hay que aplicar actualizaciones.** Nuevas versiones de Moimio (un solo comando; consulta [Actualizar Moimio](#actualizar-moimio)), parches de seguridad de Ubuntu, alguna actualización de Docker de vez en cuando. No cada semana, pero tampoco nunca.
- **Las cosas fallarán en el peor momento.** La renovación del certificado SSL puede fallar; una migración de la base de datos puede negarse a ejecutarse tras una actualización; el contenedor de la base de datos puede negarse a reiniciar. La solución suele ser uno o dos comandos, *si sabes cuáles*.
- **Las copias de seguridad son cosa tuya.** Moimio tiene una función de copia de seguridad, pero usarla de verdad antes de un cambio importante y guardar el resultado en un lugar seguro depende de ti.
- **DNS, certificados y túneles son delicados de mantener.** Un dominio caduca, una IP cambia, un token de Cloudflare se renueva… y el formulario de inscripción da un error 404.

**Una autoevaluación.** Antes de seguir, compruébalo con sinceridad:

- [ ] Te sientes cómodo ejecutando comandos en la terminal y leyendo mensajes de error.
- [ ] Si un servicio no arranca, sabes encontrar y leer sus registros.
- [ ] Si cambia la dirección IP del servidor, sabes actualizar el DNS.
- [ ] Si algo se rompe a las 11 de la noche durante el evento, tienes a alguien (o los conocimientos) para arreglarlo.
- [ ] Tienes una estrategia de copias de seguridad, no solo la intención de tenerla.

**Si alguna respuesta es *no*, plantéate usar [moimio.app](https://moimio.app), la versión alojada del mismo producto.** Ejecuta el mismo código, el mismo motor de asignación y el mismo flujo de inscripción. El alojamiento, las copias de seguridad, las actualizaciones y el SSL corren de su cuenta. Los precios actuales están en la web.

Esta guía sigue explicándote cómo alojarlo tú mismo si es lo que quieres. El coste de alojarlo por tu cuenta no son los pocos euros al mes de un VPS: es estar de guardia durante un evento en directo. Toma la decisión con conocimiento de causa.

---

## Elige cómo alojarlo

Hay dos formas razonables de ejecutar Moimio. Elige la que mejor encaje con tu situación:

### → Ruta A — Alquilar un pequeño servidor (un «VPS»)

Un VPS es un pequeño ordenador que está en un centro de datos, que alquilas por meses y al que accedes a distancia. Cuesta entre 4 y 10 € al mes. Siempre encendido, siempre accesible y sin equipos que mantener por tu parte.

**Ideal si:** quieres poco mantenimiento continuo, abres las inscripciones con meses de antelación o no quieres tener un ordenador en casa ocupado con Moimio.

Continúa en [Ruta A — Configurar un VPS](#ruta-a--alquilar-un-vps), más abajo.

### → Ruta B — Alojarlo en tu propio ordenador o mini-PC

Ejecuta Moimio en un ordenador que ya tengas y exponlo a internet mediante un servicio gratuito llamado Cloudflare Tunnel. Sin costes de alojamiento.

**Ideal si:** la soberanía de los datos es un requisito estricto (necesitas expresamente que los datos de los participantes estén en un equipo de tu propiedad) y tienes a alguien capaz de resolver problemas de una máquina Linux durante un evento.

Un equipo en casa o en la oficina es bastante menos fiable que un VPS. La electricidad, internet, el conector cloudflared y el propio sistema operativo pueden fallar; el formulario de inscripción deja de funcionar hasta que alguien llega a la máquina y lo arregla. Si la soberanía de los datos no es un requisito estricto, la Ruta A (VPS) o [moimio.app](https://moimio.app) son opciones más sencillas.

Continúa en [Ruta B — Alojarlo tú mismo con Cloudflare Tunnel](#ruta-b--alojarlo-tú-mismo-con-cloudflare-tunnel), más abajo.

Ambas rutas confluyen en el **[Paso 4 — Instalar Moimio](#paso-4--instalar-moimio)**, que es igual sea cual sea el lugar donde se ejecute Moimio.

---

## Ruta A — Alquilar un VPS

Un proveedor de VPS te ofrece un pequeño ordenador en un centro de datos. Hay muchos: Hetzner, OVH, Scaleway, DigitalOcean, Linode, Vultr, Contabo y muchos proveedores regionales. La mayoría cobra entre 4 y 10 €/mes por lo que necesita Moimio.

Para iglesias y organizaciones misioneras europeas, los proveedores con centros de datos en Europa suelen ser preferibles por motivos del RGPD (los datos de tus participantes se quedan en la UE). Hetzner Cloud (en Alemania y Finlandia) y OVH (en Francia y Alemania) son opciones habituales. Si organizas desde Corea, Japón, Estados Unidos u otro lugar, tu proveedor de nube local suele estar bien: a Moimio le da igual cuál elijas.

> **No recomendamos ningún proveedor concreto.** Esta guía usa Hetzner Cloud como *ejemplo* porque está bien documentado y es económico, no como recomendación. Elige el que te inspire confianza. La configuración es parecida en todos.

### Paso 1 — Registrarte y crear el servidor

Cada proveedor de VPS tiene su propio proceso de registro y creación de servidores. En lugar de repetir aquí un paso a paso que queda obsoleto cada vez que el proveedor rediseña su panel, sigue la documentación de primeros pasos de tu proveedor.

Para Hetzner Cloud en concreto: <https://docs.hetzner.com/cloud/servers/getting-started/creating-a-server/>

Al crear el servidor, estas son las opciones que importan para Moimio:

- **Sistema operativo:** **Ubuntu 24.04** (o 22.04): son los más fáciles para encontrar ayuda si algo sale mal.
- **Tamaño del servidor:** unos **2 vCPU + 2 GB de RAM + 40 GB de disco** son más que suficientes para un evento de 150 personas. La mayoría de los proveedores lo llaman su plan «pequeño» y cobran 4–5 €/mes.
- **Clave SSH:** añade tu clave SSH durante la creación (para poder conectarte sin contraseña). Si aún no tienes una, salta al [Paso 2 — Generar una clave SSH](#paso-2--generar-una-clave-ssh) antes de crear el servidor y luego vuelve.
- **Ubicación:** elige un centro de datos cercano a tus participantes. Para eventos europeos suelen ser preferibles los centros de datos de la UE; para eventos en otros lugares, elige lo que sea adecuado geográfica y legalmente.

Una vez creado el servidor, el proveedor te da una **dirección IP pública** (algo como `203.0.113.42`). **Apunta esa dirección IP**: la necesitarás para conectarte.

### Paso 2 — Generar una clave SSH

Una clave SSH son dos archivos emparejados: una **clave pública** (que das a tu proveedor de VPS) y una **clave privada** (que se queda en tu portátil, como la llave digital de tu casa). Juntas permiten que tu portátil entre en el servidor sin contraseña.

En tu portátil, abre una terminal:

- **macOS:** Spotlight → «Terminal».
- **Linux:** cualquier aplicación de terminal.
- **Windows:** instala [Windows Terminal](https://aka.ms/terminal) desde Microsoft Store o usa el PowerShell integrado.

Después escribe:

```bash
ssh-keygen -t ed25519 -C "you@your-email.com"
```

(El correo es solo una etiqueta. No se envía ningún correo). Cuando te lo pida:

- Pulsa Intro para aceptar la ubicación predeterminada del archivo.
- Escribe una frase de contraseña que recuerdes (protege la clave si te roban el portátil). Pulsa Intro.
- Vuelve a escribir la frase de contraseña. Pulsa Intro.

Muestra la clave pública:

```bash
cat ~/.ssh/id_ed25519.pub
```

Aparece una línea larga que empieza por `ssh-ed25519 AAAA...`. Copia la línea entera. Añádela en la configuración de claves SSH de tu proveedor de VPS (cada proveedor tiene una sección para esto en su panel). A partir de ahora, tu servidor (cuando lo crees o lo reinstales) acepta inicios de sesión desde tu portátil.

Si te atascas en este paso, busca «[tu proveedor de VPS] añadir clave SSH»: todos los proveedores lo tienen documentado.

### Paso 3 — Conectarte a tu servidor

Abre una terminal en tu portátil:

```bash
ssh root@203.0.113.42
```

(Sustituye `203.0.113.42` por la dirección IP de tu servidor).

La primera vez verás una pregunta sobre si confías en el equipo. Escribe `yes` y pulsa Intro. Introduce la frase de contraseña de tu clave SSH si te la pide. Deberías ver algo así:

```
Welcome to Ubuntu 24.04.x LTS ...
root@your-server:~#
```

Ese es el indicador de la terminal **del servidor**. Todo lo que escribas ahora se ejecuta en el servidor, no en tu portátil. **Ya estás dentro.**

Si aparece `Permission denied (publickey)`, tu clave SSH no está vinculada al servidor. Revisa la configuración de claves SSH de tu proveedor.

Ahora salta al [Paso 4 — Instalar Moimio](#paso-4--instalar-moimio).

---

## Ruta B — Alojarlo tú mismo con Cloudflare Tunnel

Para esta ruta necesitas un ordenador que pueda estar siempre encendido: un ordenador de sobremesa, un mini-PC, un portátil viejo que ya no uses o una Raspberry Pi 4 (de 4 GB u 8 GB). También necesitas una conexión a internet estable donde esté ese ordenador.

### Paso 1 — Preparar tu ordenador

Instala **Linux** si aún no lo tienes:

- **Portátil u ordenador de sobremesa viejo:** Ubuntu Desktop 24.04 LTS es la opción más amigable. Descárgalo en <https://ubuntu.com/download/desktop> y sigue su guía de instalación.
- **Raspberry Pi:** usa Raspberry Pi OS o Ubuntu Server para ARM. Su documentación respectiva explica la instalación.
- **Mini-PC comprado para esto:** la mayoría vienen con Windows, pero Ubuntu se instala sin problemas. Tanto Raspberry Pi Imager como el instalador de Ubuntu están bien documentados.

No *tienes* que usar Linux (Moimio también funciona en macOS con Docker Desktop y en Windows con Docker Desktop y WSL2), pero para un servidor que va a estar encendido durante meses, Linux es la opción más predecible.

### Paso 2 — Instalar Docker

Abre una terminal en el ordenador (no por SSH desde otro sitio: directamente en la máquina, o por SSH desde un portátil de la misma red si lo has activado). Después:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Cierra la sesión y vuelve a entrar (o reinicia) para que se aplique la pertenencia al nuevo grupo. Después comprueba:

```bash
docker --version
docker run --rm hello-world
```

Si aparece «Hello from Docker!», Docker funciona.

### Paso 3 — Configurar Cloudflare Tunnel

Un **Cloudflare Tunnel** es un servicio gratuito que da una dirección pública a tu ordenador de casa u oficina sin que tengas que abrir puertos en el router ni conocer tu IP doméstica. El tráfico pasa por la red de Cloudflare, que se encarga del TLS por ti.

1. Regístrate en <https://dash.cloudflare.com/sign-up> si no tienes cuenta de Cloudflare. El plan gratuito es suficiente.
2. Añade tu dominio a Cloudflare (necesitarás un nombre de dominio; consulta [la sección sobre dominios](#conseguir-un-nombre-de-dominio) más abajo si aún no tienes uno).
3. Ve a **Zero Trust → Networks → Tunnels** en el panel de Cloudflare. Haz clic en **Create a tunnel**, ponle un nombre (p. ej. «moimio-home») y sigue las instrucciones de Cloudflare para instalar el conector en tu máquina Linux. El asistente de Cloudflare te da el comando exacto de instalación de `cloudflared` para tu sistema.
4. En la sección **Public hostnames** del túnel, añade un nombre de host como `events.yourchurch.org` y pon como **Service** `HTTP://localhost:6120`.
5. Guarda. Cloudflare obtiene y renueva automáticamente un certificado TLS.

Abre `https://events.yourchurch.org` en cualquier navegador: cuando Moimio esté en marcha tras el siguiente paso, llegarás a él a través del túnel con HTTPS ya configurado.

Para instrucciones actualizadas: <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/>

### Cuando alojarlo tú mismo sale mal

Cosas que fallan en las instalaciones propias durante un evento real, más o menos por orden de probabilidad:

- **Un corte de luz** en el lugar del evento o en la oficina tumba el servidor. Se mitiga con un SAI (sistema de alimentación ininterrumpida, unos 80 €) para el ordenador y el router.
- **Un corte de internet** en el lugar del evento o en la oficina deja inaccesible la dirección pública. Se mitiga con un plan B de conexión compartida desde el móvil, o asumiendo el riesgo.
- **El conector cloudflared se cae.** Una actualización del sistema, un pico de memoria o un desajuste de versiones del conector pueden desconectar el túnel sin avisar. La solución suele ser `sudo systemctl restart cloudflared` en el equipo: fácil *si* puedes llegar a él y conoces el comando.
- **El propio sistema operativo deja de responder.** Es menos probable con una instalación nueva de Ubuntu y más probable en una Raspberry Pi que hace otras tareas o en un equipo que lleva meses sin reiniciarse. La recuperación suele requerir acceso físico.

Nada de esto es raro: son los fallos normales de tener un servidor en un sitio que no es un centro de datos. La cuestión es si tienes a alguien que pueda arreglarlos durante el evento. Si es así, alojarlo tú mismo es un intercambio razonable a cambio de mantener los datos físicamente en tus instalaciones. Si no, [moimio.app](https://moimio.app) se hace cargo de esos cuatro tipos de fallo.

Ahora salta al [Paso 4 — Instalar Moimio](#paso-4--instalar-moimio).

---

## Paso 4 — Instalar Moimio

Esto es igual tanto si elegiste un VPS como si lo alojas tú mismo. La terminal en la que estás es o bien un VPS por SSH (Ruta A) o bien tu propia máquina (Ruta B). A partir de aquí, **«el servidor»** es el ordenador en el que se ejecuta Moimio, sea cual sea.

### 4.1 Obtener el código

```bash
git clone https://github.com/pistio/moimio.git
cd moimio
```

`git` viene preinstalado en Ubuntu. La clonación tarda unos segundos.

El indicador muestra ahora que estás dentro de la carpeta `moimio`.

### 4.2 Configurar Moimio

```bash
cp .env.example .env
nano .env
```

`nano` es un editor de texto sencillo. Usa las flechas del teclado para moverte. Busca estas líneas y edítalas:

**`SECRET_KEY`**: sustituye el marcador por una cadena aleatoria de verdad. Para generarla, en una **segunda terminal** de tu portátil:

```bash
openssl rand -hex 64
```

Copia el resultado. Pégalo como nuevo valor de `SECRET_KEY` en `nano`.

**`POSTGRES_PASSWORD`**: sustituye `moimio_dev` por otra cadena aleatoria (ejecuta `openssl rand -hex 32` para obtener una más corta). Hazlo ahora, antes del primer arranque: la base de datos recuerda la contraseña con la que se arrancó por primera vez.

**`DATABASE_URL`**: puedes dejar esta línea como está; Moimio construye por ti la dirección real de la base de datos a partir de `POSTGRES_PASSWORD`. Si te gusta tenerlo todo ordenado, sustituye también el `moimio_dev` que contiene por tu nueva contraseña.

**`LOG_LEVEL`**: déjalo en `INFO`. El valor `DEBUG` escribe en los archivos de registro del servidor los nombres, direcciones y fechas de nacimiento de los participantes, así que solo sirve para depurar con datos inventados.

Guarda: **Ctrl-O** y luego **Intro**. Sal: **Ctrl-X**.

Ahora no hace falta tocar nada más en este archivo. La configuración del correo es opcional y se explica en [Enviar correo electrónico (opcional)](#enviar-correo-electrónico-opcional), más abajo.

### 4.3 Arrancar Moimio

```bash
docker compose up -d --build
```

Docker descarga las imágenes base, construye las imágenes de Moimio y arranca tres contenedores (base de datos, backend y frontend). La primera vez tarda **de 5 a 10 minutos**.

Cuando termine:

```bash
docker compose logs --tail=30 backend
```

Busca:

```
INFO  [alembic.runtime.migration] Running upgrade ... -> <latest migration>
INFO  Application startup complete.
```

Si las ves, Moimio está en marcha. (La primera línea solo aparece cuando hacía falta preparar o actualizar la base de datos, así que no pasa nada si solo ves la segunda). **No sigas si ves líneas de error**: consulta la sección de solución de problemas al final de esta guía.

### 4.4 Configuración inicial (crear tu cuenta de administrador)

<p align="center">
  <img src="../assets/first-time-setup.png" alt="Asistente de configuración inicial para la primera cuenta de Superadministrador" width="420">
  <br>
  <em>Asistente de configuración inicial para la primera cuenta de Superadministrador</em>
</p>

Abre un navegador:

- **Ruta A (VPS):** ve a `http://YOUR_SERVER_IP:6120` (p. ej. `http://203.0.113.42:6120`).
- **Ruta B (alojamiento propio):** ve a `http://localhost:6120` si estás en la misma máquina, o a `https://events.yourchurch.org` si ya tienes configurado tu Cloudflare Tunnel.

Llegarás automáticamente a la pantalla **Configuración inicial**. Moimio solo la muestra mientras no exista ninguna cuenta. Rellena:

- **Nombre completo**: cómo aparecerá tu nombre en Moimio.
- **Correo electrónico**: con lo que iniciarás sesión.
- **Contraseña** y **Confirmar la contraseña**: al menos 8 caracteres. Un gestor de contraseñas es tu mejor aliado.

Puedes cambiar el idioma de la pantalla con el selector que hay debajo. Haz clic en **Crear superadministrador**. Moimio muestra entonces la página de inicio de sesión: entra con el correo y la contraseña que acabas de elegir. Esta primera cuenta es la de **Superadministrador**, la única cuenta que puede hacerlo todo.

🎉 **Has instalado Moimio.**

<p align="center">
  <img src="../assets/welcome-splash.png" alt="La pantalla Bienvenido a Moimio, que aparece mientras todavía no hay eventos" width="560">
  <br>
  <em>La pantalla Bienvenido a Moimio</em>
</p>

Como aún no hay eventos, verás la pantalla **Bienvenido a Moimio**, que explica las tres fases de un evento (Configuración, Inscripción, Evento). Haz clic en **Crea tu primer evento** para empezar.

Otra cosa que conviene hacer ahora: haz clic en **Espacio de trabajo** en el menú de la izquierda y pega la dirección web del **aviso de privacidad** de tu organización, si tienes uno. Quienes rellenen tu formulario de inscripción verán un enlace a él justo al lado de la casilla de consentimiento.

---

## Paso 5 — Hacerlo accesible en un dominio real (opcional, recomendado)

Entrar en Moimio por `http://203.0.113.42:6120` te sirve a ti, pero no es la dirección que darías a los participantes. Para inscripciones reales, quieres algo como `https://events.yourchurch.org`. HTTPS activa además algunas comodidades que los navegadores solo permiten en sitios seguros, como el aviso de «nueva versión disponible» y la caché sin conexión.

Si elegiste la **Ruta B (alojamiento propio con Cloudflare Tunnel)**, ya lo has hecho: la dirección de tu túnel es la dirección pública. Sáltate esta sección.

Si elegiste la **Ruta A (VPS)**, sigue leyendo:

### Conseguir un nombre de dominio

Si aún no tienes uno, cómpralo en cualquier registrador de dominios (Namecheap, Porkbun, INWX, Cloudflare Registrar, OVH; todos sirven). Un dominio `.org` cuesta unos 10–15 € al año.

No necesitas un dominio aparte: un subdominio de uno que ya tengas funciona perfectamente. Si tu iglesia está en `yourchurch.org`, un subdominio como `events.yourchurch.org` es más limpio que un dominio nuevo.

Si registrar un dominio y configurar el DNS te intimida, es buen momento para preguntar a un amigo con más conocimientos técnicos o explicar tu situación a un asistente de chat con IA: puede guiarte por el proceso de tu registrador en pocos minutos.

### Apuntar el dominio a tu servidor (ruta VPS)

En la configuración DNS de tu registrador, añade un **registro A**:

| Nombre | Tipo | Valor |
|---|---|---|
| `events` (o el subdominio que quieras) | A | `203.0.113.42` (la IP de tu servidor) |

Guarda. El DNS se propaga en unos minutos (a veces hasta una hora). Compruébalo:

```bash
ping events.yourchurch.org
```

Si responde la IP de tu servidor, el DNS funciona.

### Añadir HTTPS (TLS)

Tienes dos opciones limpias. Ambas funcionan; elige la que te resulte más cómoda.

#### Opción 1 — Cloudflare delante

La más sencilla si TLS es nuevo para ti: usar Cloudflare como proxy inverso.

1. Añade tu dominio a una cuenta (gratuita) de Cloudflare.
2. Configura un Cloudflare Tunnel en tu VPS, exactamente como en el [Paso 3 de la Ruta B](#paso-3--configurar-cloudflare-tunnel), apuntándolo a `HTTP://localhost:6120`. (Con un túnel no necesitas el registro A de arriba; Cloudflare crea la entrada DNS por ti).
3. Cloudflare se encarga automáticamente de HTTPS: abres `https://events.yourchurch.org` y el túnel lo lleva hasta Moimio.

Un simple registro A «proxied» no basta: Cloudflare enviaría a los visitantes a los puertos web estándar (80/443), y Moimio escucha en el 6120. El túnel lo evita, y además no tienes que abrir ningún puerto.

Es lo que acaban haciendo muchas personas que alojan su propio Moimio, porque en la práctica es «configurar y olvidarse».

#### Opción 2 — Caddy en el servidor

Instala Caddy junto a Moimio en el mismo servidor. Caddy obtiene automáticamente un certificado de Let's Encrypt.

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

Edita `/etc/caddy/Caddyfile`:

```bash
sudo nano /etc/caddy/Caddyfile
```

Sustituye su contenido por:

```
events.yourchurch.org {
    reverse_proxy localhost:6120
}
```

(Pon tu dominio real). Guarda (Ctrl-O, Intro) y sal (Ctrl-X). Recarga Caddy:

```bash
sudo systemctl reload caddy
```

Caddy obtiene automáticamente un certificado TLS de Let's Encrypt (de 30 a 60 segundos la primera vez). Abre `https://events.yourchurch.org`.

Ahora puedes (y deberías) cerrar el puerto 6120 a internet, porque solo Caddy, en el mismo servidor, necesita hablar con él. La forma fiable es decirle a Docker que escuche solo en el propio servidor. Abre de nuevo `.env` (`nano .env`) y pon:

```
FRONTEND_PORT=127.0.0.1:6120
BACKEND_PORT=127.0.0.1:6121
DB_PORT=127.0.0.1:6122
```

Guarda y aplícalo con `docker compose up -d`. (Una regla de `ufw` por sí sola no basta: Docker abre sus puertos directamente y se salta `ufw`). El cortafuegos de tu proveedor, en su panel web, es una buena segunda capa: permite solo los puertos 22, 80 y 443.

---

## Enviar correo electrónico (opcional)

Moimio funciona sin correo. Con él, las personas reciben un correo de confirmación al inscribirse y tú puedes restablecer una contraseña olvidada. Para activarlo necesitas los datos de una cuenta de correo que permita enviar por «SMTP» (las páginas de ayuda de tu proveedor de correo lo llamarán así). Abre `.env` y rellena el bloque que empieza por `SMTP_`:

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=events@yourchurch.org
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=events@yourchurch.org
SMTP_FROM_NAME=Your Church Events
```

Guarda y ejecuta `docker compose up -d` para aplicarlo. Para comprobar que funciona, abre la configuración del formulario de inscripción de un evento y haz clic en **Enviar correo de prueba**, en **Confirmación por correo electrónico**: te llegará un mensaje de prueba a tu propia bandeja de entrada. La [Guía de instalación rápida](quick-guide.es.md#referencia-de-smtp-opcional) incluye la configuración de los proveedores más comunes.

---

## Actualizar Moimio

Cuando salga una nueva versión, en el servidor:

```bash
cd ~/moimio
./upgrade.sh
```

El script te muestra lo que va a cambiar y pregunta **Proceed with upgrade? [y/N]**. Escribe `y`. Después:

- guarda una copia de tu archivo de configuración `.env`,
- guarda una copia de seguridad de la base de datos junto a la carpeta `moimio` (un archivo llamado `pgdata-pre-upgrade-<fecha-y-hora>.sql.gz`),
- descarga la nueva versión, reconstruye Moimio y lo reinicia,
- muestra los comandos exactos para volver a la versión anterior si lo necesitas.

Puede que te pida tu contraseña, porque usa `sudo`. Para pasar a una versión concreta en lugar de la más reciente, indica su nombre, por ejemplo `./upgrade.sh v1.0.6` (los nombres de las versiones aparecen en el registro de cambios). Para ver lo que haría sin cambiar nada, ejecuta `./upgrade.sh --dry-run`.

Al final, el script espera hasta 90 segundos a que Moimio indique que está en buen estado. Si muestra «backend did not become healthy», abre Moimio en tu navegador antes de seguir sus instrucciones para volver atrás: si carga y puedes iniciar sesión, lo más probable es que la actualización solo necesitara más tiempo para arrancar.

Las actualizaciones suelen tardar de 3 a 5 minutos. El sitio no está disponible durante parte de ese tiempo, mientras Moimio se reconstruye y reinicia. Si tienes un evento en curso, hazlo fuera del horario del evento.

Los datos de tus participantes se conservan entre actualizaciones; los cambios de base de datos que necesite una nueva versión se aplican automáticamente al arrancar. Conserva los archivos de copia de seguridad hasta que estés conforme con la nueva versión y luego bórralos.

---

## Copias de seguridad

La copia de seguridad más sencilla es un volcado de la base de datos. En el servidor:

```bash
cd ~/moimio
docker compose exec -T db pg_dump -U moimio moimio | gzip > ~/moimio-backup-$(date +%F).sql.gz
```

Esto crea un archivo de copia de seguridad con la fecha en tu carpeta personal. Cópialo a tu portátil o a un almacenamiento en la nube con regularidad.

Restaurar sustituye todo el contenido de la base de datos por lo que hay en la copia, así que hazlo solo cuando de verdad quieras. Primero hay que vaciar la base de datos, que es lo que hacen las líneas `dropdb` y `createdb`:

```bash
cd ~/moimio
docker compose stop backend
docker compose exec -T db dropdb -U moimio moimio
docker compose exec -T db createdb -U moimio moimio
gunzip -c ~/moimio-backup-2026-04-28.sql.gz | docker compose exec -T db psql -U moimio moimio
docker compose start backend
```

(Usa el nombre de tu propio archivo de copia de seguridad).

Para instalaciones reales en producción, automatiza la copia con `cron` y envía el archivo fuera del servidor. Si eso se te escapa, pide ayuda a un amigo con conocimientos técnicos o abre una incidencia en GitHub pidiendo una guía de «copias de seguridad programadas».

**Copias de seguridad dentro de Moimio.** Los administradores tienen además una página **Copias de seguridad** en el menú de la izquierda. Descarga un archivo ZIP por evento, y su botón **Restaurar desde copia** recupera un evento como un nuevo borrador. Es útil antes de un cambio importante en un evento o para copiar un evento a otro Moimio. Las cuentas de los miembros del equipo no se incluyen, así que tendrías que volver a invitarlos en un servidor nuevo.

**¿Vas a trasladarlo todo a un servidor nuevo** o a traer tus eventos desde el servicio alojado? Consulta [Moving a workspace to your own Moimio](../moving-a-workspace.md) (en inglés).

---

## Solución de problemas

**`docker compose up` falla con «permission denied».**
No estás en el grupo `docker`. Cierra la sesión y vuelve a entrar (la instalación añade tu usuario al grupo, pero solo surte efecto después de volver a iniciar sesión) o usa `sudo docker compose up -d --build`.

**El navegador dice que no se puede acceder al sitio.**
Tres comprobaciones, en orden:
1. ¿Está funcionando el servidor? En un VPS, mira el panel del proveedor. En un alojamiento propio, el ordenador tiene que estar encendido y conectado.
2. ¿Está funcionando Moimio? En el servidor: `docker compose ps`. Las tres filas (db, backend, frontend) deberían indicar `Up`. Si no, `docker compose logs <service>` muestra por qué.
3. ¿Te está bloqueando el cortafuegos? Los proveedores de VPS suelen tener una capa de cortafuegos aparte; asegúrate de que el puerto que necesitas está abierto.

**El navegador carga, pero no puedo iniciar sesión (y no aparece la pantalla de configuración inicial).**
Ya existe una cuenta. La pantalla de configuración solo aparece cuando no hay ninguna cuenta. Usa el formulario de inicio de sesión. Si has olvidado la contraseña y el correo no está configurado, puedes crear una segunda cuenta de Superadministrador desde el servidor (con otra dirección de correo), entrar con ella y seguir:

```bash
docker compose exec backend python -m app.cli.create_admin
```

**La página solo dice «No se pudo conectar con el servidor».**
La parte web de Moimio funciona, pero la parte que hay detrás no responde. Ejecuta `docker compose ps` y comprueba que la fila `backend` indica `Up`; si no, `docker compose logs --tail=50 backend` suele explicar por qué.

**El registro del backend dice `password authentication failed`.**
La contraseña de la base de datos en `.env` se cambió después del primer arranque de Moimio; la base de datos sigue esperando la original. Vuelve a poner la contraseña original en `.env` y ejecuta `docker compose up -d`.

**Cloudflare Tunnel no llega a Moimio.**
En el servidor: `sudo systemctl status cloudflared` indica si el conector está en marcha, y `sudo journalctl -u cloudflared -f` muestra su registro en directo (pulsa Ctrl-C para dejar de verlo). Causa habitual: el túnel apunta a `localhost:80`, pero Moimio está en `localhost:6120`. Actualiza la configuración del nombre de host público del túnel.

**Errores de HTTPS después de configurar el dominio (ruta de Caddy).**
Puede que el DNS aún no se haya propagado. Espera 5 minutos y vuelve a intentarlo. O puede que Caddy no haya obtenido todavía el certificado: `sudo systemctl status caddy` muestra lo que está haciendo. Los registros están en `journalctl -u caddy`.

**Cualquier cosa más rara.**
Abre un [informe de error](https://github.com/pistio/moimio/issues/new?template=bug_report.md). Incluye:
- Qué intentabas hacer.
- Qué viste realmente (el mensaje de error exacto).
- Lo que muestra `docker compose logs --tail=50 backend`.
- Oculta cualquier dato de participantes antes de pegarlo.

---

## Siguiente paso

Ya tienes Moimio instalado. Para organizar un evento, el [Manual de usuario](../manual/README.es.md) explica cómo crear un evento, preparar las inscripciones, ejecutar el motor de asignación, hacer el check-in y exportar listas.

Si has llegado hasta aquí sin ayuda de un desarrollador, has hecho algo que la mayoría de la gente consideraría «demasiado técnico para mí». Bienvenido al software autoalojado.
