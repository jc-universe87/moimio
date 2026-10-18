# Guía de instalación rápida

Para quienes se manejan con la terminal, Docker y un poco de administración de sistemas. Si no es tu caso, la [Guía para principiantes](beginner.es.md) cubre lo mismo con más calma y más acompañamiento.

Tiempo necesario: **de 30 a 60 minutos**, desde un servidor recién creado hasta iniciar sesión como administrador. La mayor parte se va en el primer `docker compose up --build`, que construye las dos imágenes de Moimio a partir del código fuente en tu máquina.

---

## Requisitos previos

- Un equipo Linux (cualquier distribución moderna: Ubuntu 22.04+, Debian 12+, Fedora, cualquiera con systemd).
- **Docker Engine 24+** y **Docker Compose v2** (el subcomando `docker compose`, no el antiguo `docker-compose` independiente).
- **Git** (para clonar), o simplemente descarga y descomprime el archivo del código fuente.
- **Puertos:** `6120` (frontend; además redirige `/api` y `/health` al backend, así que los navegadores solo necesitan este). Compose publica también `6121` (backend, para acceder directamente a la API al depurar) y `6122` (PostgreSQL). Ninguno de los dos tiene que ser público; consulta «Cambiar los puertos» más abajo para vincularlos a localhost.
- Permisos `sudo` para `upgrade.sh`, que llama a `sudo docker compose`.
- Unos **2 GB de RAM** y **5 GB de disco** para una instalación del tamaño de una iglesia pequeña.

Para comprobar que Docker está listo:

```bash
docker --version          # → Docker version 24.0+ ...
docker compose version    # → Docker Compose version v2.x.x
```

Si `docker compose version` falla, tienes el antiguo Compose independiente. Instala el complemento v2: `apt install docker-compose-plugin` (Ubuntu/Debian) o sigue las [instrucciones oficiales de Docker](https://docs.docker.com/compose/install/).

---

## 1. Clonar y configurar

```bash
git clone https://github.com/jc-universe87/moimio.git
cd moimio
cp .env.example .env
```

Abre `.env` y edita como mínimo las dos primeras de estas variables:

| Variable | Qué poner |
|---|---|
| `SECRET_KEY` | Una cadena aleatoria de **al menos 64 caracteres**. Genérala con `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` o `openssl rand -hex 64`. **No dejes el marcador `change-me-...` en producción.** |
| `POSTGRES_PASSWORD` | Una contraseña aleatoria para el usuario de la base de datos. Mismo método de generación. |
| `DATABASE_URL` | Opcional. `docker-compose.yml` construye el `DATABASE_URL` del backend a partir de `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`, así que la línea de `.env` no es la que usa el contenedor. Actualiza igualmente su contraseña si quieres que el archivo sea coherente. |

Define `POSTGRES_PASSWORD` **antes del primer arranque.** Postgres solo la aplica cuando se crea por primera vez el volumen `pgdata`; si la cambias después, obtendrás `password authentication failed` hasta que la cambies también dentro de la base de datos.

Deja `LOG_LEVEL=INFO` (el valor predeterminado). Consulta «Refuerzo para producción» para saber por qué.

Si quieres correo electrónico desde el principio, configura también el bloque SMTP; consulta la tabla SMTP al final de esta guía. Prescindir de SMTP no es problema: la aplicación funciona sin él (simplemente no se envían los correos de confirmación de inscripción, y los administradores pueden confirmar las inscripciones a mano).

### Cambiar los puertos

Los valores predeterminados son 6120 (frontend), 6121 (backend) y 6122 (Postgres). Si alguno ya está en uso en tu equipo, cámbialo en `.env`:

```
FRONTEND_PORT=7120
BACKEND_PORT=7121
DB_PORT=7122
```

`docker-compose.yml` los lee mediante `${FRONTEND_PORT:-6120}`, etc., así que los valores se aplican sin más cambios. Después abrirías `http://localhost:7120` en su lugar.

Los valores se insertan tal cual en la asignación `ports:` de Compose, así que también puedes indicar una dirección. Esto vincula el puerto solo a la interfaz de loopback del equipo:

```
BACKEND_PORT=127.0.0.1:6121
DB_PORT=127.0.0.1:6122
# Solo si tu proxy inverso o túnel se ejecuta en este mismo equipo:
FRONTEND_PORT=127.0.0.1:6120
```

El navegador se comunica con el backend a través del proxy `/api` del frontend, así que cambiar `BACKEND_PORT` no requiere nada más. (Los archivos `.env` antiguos pueden contener todavía `VITE_API_URL`; nada la lee, así que puedes borrar esa línea).

---

## 2. Arrancar los contenedores

![Salida de la terminal durante docker compose up --build](../assets/install-docker-build.png)

```bash
docker compose up -d --build
```

La primera ejecución descarga imágenes y construye: calcula de 3 a 5 minutos con una conexión decente. Las reconstrucciones posteriores son más rápidas.

Sigue el arranque del backend:

```bash
docker compose logs -f backend
```

Busca dos líneas del registro, en este orden:

```
INFO  [alembic.runtime.migration] Running upgrade ... -> <latest migration>
INFO  Application startup complete.
```

La primera significa que el esquema de la base de datos se ha creado o migrado correctamente. La segunda, que uvicorn está sirviendo la API. Si ves la segunda sin la primera, las migraciones ya estaban al día, lo cual también está bien. **Pulsa Ctrl-C para dejar de seguir el registro; los contenedores siguen funcionando.**

Haz una prueba rápida de la API (el mismo endpoint también es accesible a través del frontend en `http://localhost:6120/health`):

```bash
curl http://localhost:6121/health
# → {"status":"ok","database":"healthy","version":"1.0.6"}
```

### Sobre las migraciones de Alembic

Alembic es una herramienta de migración de bases de datos que acompaña a SQLAlchemy. Gestiona la evolución del esquema: cada archivo de migración es un conjunto de cambios versionado que sabe cómo hacer avanzar la base de datos (y, cuando es posible, retroceder).

Dos cosas que conviene saber:

- **Las migraciones se ejecutan automáticamente cada vez que arranca el contenedor del backend.** El CMD del Dockerfile es `alembic upgrade head && uvicorn ...`: Alembic comprueba la revisión actual de la base de datos, aplica las migraciones más recientes que encuentre y luego cede el paso a uvicorn.
- **Las migraciones no borran tus datos.** Cada migración es incremental: «añadir esta columna», «crear esta tabla», «renombrar este índice». Nunca recrean la base de datos desde cero. Mientras no ejecutes `docker compose down -v` (la opción `-v` elimina los volúmenes con nombre, incluido `moimio_pgdata`), tus datos de participantes, eventos y asignaciones se conservan entre actualizaciones.

Si alguna vez necesitas restablecer la base de datos, es con `docker compose down -v` (elimina el volumen `pgdata`, llamado `<project>_pgdata`, p. ej. `moimio_pgdata`). Hazlo solo en una instalación sin datos reales.

---

## 3. Crear el primer administrador

![Asistente de configuración inicial para la primera cuenta de Superadministrador](../assets/first-time-setup.png)

Moimio no incluye ningún administrador predeterminado. Abre `http://localhost:6120` (o el puerto que hayas configurado) en un navegador. Llegarás automáticamente a la **pantalla de configuración inicial**: Moimio detecta que no existe ningún usuario y te ofrece el asistente.

Rellena:

- **Nombre completo**: el nombre visible en el área de administración.
- **Correo electrónico**: tu usuario para iniciar sesión.
- **Contraseña** y **Confirmar la contraseña**: mínimo 8 caracteres. Usa un buen gestor de contraseñas.

La pantalla tiene también un selector de idioma y un interruptor de modo claro/oscuro. Haz clic en **Crear superadministrador**. La cuenta se crea con el rol de **Superadministrador** y pasas a la página de inicio de sesión para entrar con ella. La pantalla de configuración no vuelve a aparecer una vez que existe algún usuario.

**Alternativa: arranque por línea de comandos.** Para instalaciones sin interfaz gráfica o aprovisionamiento automatizado, la misma operación está disponible desde la línea de comandos:

```bash
docker compose exec backend python -m app.cli.create_admin
```

Te pide el correo, el nombre completo y la contraseña, y crea un Superadministrador. Para quien aloja Moimio por su cuenta, la opción recomendada es la pantalla. La línea de comandos es también la forma de volver a entrar si pierdes la contraseña del único Superadministrador y no tienes SMTP para restablecerla: crea un segundo Superadministrador con otro correo.

---

## 4. Iniciar sesión (después de la configuración)

Inicia sesión en `http://localhost:6120/login` con la cuenta que acabas de crear.

Como todavía no hay eventos, llegas a la pantalla **Bienvenido a Moimio**; haz clic en **Crea tu primer evento**. Cuando ya hay eventos, la lista de eventos tiene un botón **+ Nuevo evento**.

Como Superadministrador, abre también **Espacio de trabajo** en la barra lateral y configura tu **URL del aviso de privacidad**. El formulario público de inscripción la enlaza justo después de la frase de consentimiento; si la dejas vacía, no se muestra ningún enlace.

---

## 5. Refuerzo para producción

Antes de exponer Moimio a internet:

- Pon un proxy inverso que gestione TLS delante del puerto 6120. Caddy, Traefik o un Cloudflare Tunnel en el propio equipo funcionan bien; Nginx + Let's Encrypt es la opción clásica.
- HTTPS es además lo que hace funcionar ciertas funciones de la aplicación. Los navegadores solo registran el service worker con HTTPS o en `localhost`, así que una instalación abierta en una dirección de red local con HTTP simple, como `http://192.168.1.20:6120`, no tiene caché sin conexión, ni aviso de «nueva versión disponible», ni nada que borrar con el botón «Borrar caché y recargar», y ningún error indica por qué.
- Mantén el puerto del backend (6121) y el de la base de datos (6122) fuera de internet. Vincúlalos a localhost en `.env` (consulta «Cambiar los puertos»). Una regla de cortafuegos en el equipo no basta: los puertos que publica Docker los abre el propio Docker en iptables y se saltan las reglas de `ufw`/`firewalld`.
- Lee [`SECURITY.md`](../../SECURITY.md) (en inglés): la sección «Hardening recommendations for self-hosters» cubre el resto (SECRET_KEY robusta, rotación de la contraseña de la base de datos, actualizaciones del sistema que ejecuta Docker, cuidado con las credenciales SMTP).
- Deja `LOG_LEVEL=INFO` en cualquier instalación con participantes reales. `LOG_LEVEL=DEBUG` escribe en el registro del contenedor nombres, direcciones y fechas de nacimiento de los participantes en cada petición; depura mejor en una copia con datos inventados.

---

## 6. Actualizar

Desde la raíz de tu clon de git:

```bash
./upgrade.sh                # último commit de tu rama actual
./upgrade.sh v1.0.6         # una etiqueta de versión concreta (consulta CHANGELOG.md)
./upgrade.sh v1.0.6 --yes   # sin pedir confirmación
./upgrade.sh --dry-run      # muestra lo que haría, sin cambiar nada
```

El script comprueba primero que todo esté en orden (`.env` presente, árbol de trabajo limpio, contenedor `db` en marcha), muestra los commits que va a aplicar, hace una copia de seguridad de `.env` en `.env.pre-upgrade-<timestamp>.bak` y de la base de datos en `../pgdata-pre-upgrade-<timestamp>.sql.gz`, y después cambia a la versión de destino y ejecuta `docker compose down`, `build --no-cache` y `up -d`. Al final muestra los comandos exactos para volver atrás. Conserva las copias hasta que estés conforme con la nueva versión. Cambiar a una etiqueta deja el clon en un HEAD separado, así que, una vez fijada una versión, indica también la siguiente de forma explícita (`./upgrade.sh v1.0.7`) en lugar de ejecutarlo sin argumentos.

Después de reiniciar, el script espera hasta 90 segundos a que el contenedor del backend aparezca como «healthy». La comprobación de estado del backend en `docker-compose.yml` llama a `/health` cada 10 segundos tras un periodo inicial de 30 segundos. Si la espera termina con un aviso «did not become healthy» (por ejemplo, por una migración larga), revisa `curl http://localhost:6121/health` y el registro del backend antes de volver atrás.

El equivalente manual, si lo prefieres:

```bash
git pull            # o: git fetch --tags && git checkout v1.0.6
docker compose build --no-cache
docker compose up -d --force-recreate
```

`--no-cache` es importante cuando cambia el Dockerfile (nuevas dependencias, instalación de fuentes, etc.). Si lo omites, podrías acabar ejecutando código nuevo sobre una capa de imagen antigua y encontrarte con fallos desconcertantes.

Las migraciones se ejecutan automáticamente al arrancar el backend: no hace falta ejecutar `alembic upgrade head` a mano. Tus datos se conservan entre actualizaciones (el volumen `pgdata` no se toca). Aun así, haz antes una copia de seguridad, como en cualquier actualización.

`deploy.sh`, en la raíz del repositorio, es otra herramienta: sustituye la instalación a partir de un paquete `../moimio-ce-<tag>.zip` y está pensada para instalaciones que no se hicieron con `git clone`. Si clonaste el repositorio, usa `upgrade.sh`.

### Imágenes de contenedor

Esta guía construye las imágenes a partir del código fuente. Cada versión se publica también como `ghcr.io/jc-universe87/moimio-backend:<tag>` y `ghcr.io/jc-universe87/moimio-frontend:<tag>` (por ejemplo, `v1.0.6`). Si las usas, fija siempre una etiqueta de versión: `:latest` está congelada en v1.0.6, ya no avanza y no tiene soporte. `backend/deploy/production.yml` es la plantilla del servicio alojado, no un archivo compose para instalaciones propias; usa el `docker-compose.yml` de la raíz.

---

## 7. Copias de seguridad

La copia de seguridad más sencilla es un `pg_dump` de Postgres:

```bash
docker compose exec -T db pg_dump -U moimio moimio | gzip > moimio-backup-$(date +%F).sql.gz
```

Prográmalo con cron. Guarda los volcados fuera del equipo.

Para restaurar, carga el volcado en una base de datos vacía (un volcado normal sobre una base de datos con contenido falla por las tablas y filas existentes):

```bash
docker compose stop backend
docker compose exec -T db dropdb -U moimio moimio
docker compose exec -T db createdb -U moimio moimio
gunzip -c moimio-backup-2026-10-01.sql.gz | docker compose exec -T db psql -U moimio moimio
docker compose start backend
```

(Sustituye `POSTGRES_USER` / `POSTGRES_DB` si los has cambiado).

La aplicación incluye además una copia de seguridad por evento: la página **Copias de seguridad** de la barra lateral descarga un ZIP por evento (completo o solo de estructura, sin datos personales), y **Restaurar desde copia** lo recupera como un nuevo evento en borrador, en esta u otra instalación. Los miembros del equipo y sus roles no se incluyen en la copia; vuelve a invitar al equipo en el servidor de destino. Consulta [`docs/manual/09-data-export-gdpr.es.md`](../manual/09-data-export-gdpr.es.md) en el manual de usuario.

Para un archivo de todo el espacio de trabajo desde la línea de comandos: `docker compose exec backend python -m app.cli.export_all --out /tmp/moimio-export.zip`.

Para traer a este servidor un espacio de trabajo completo, con todos sus eventos de una vez, consulta [Moving a workspace to your own Moimio](../moving-a-workspace.md) (en inglés).

---

## Referencia de SMTP (opcional)

Si quieres correos de confirmación de inscripción y restablecimiento de contraseñas, rellena el bloque SMTP de `.env`:

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=events@yourchurch.org
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=events@yourchurch.org
SMTP_FROM_NAME=Your Church Events
SMTP_TLS=true
SMTP_SSL=false
```

`SMTP_TLS=true` es STARTTLS (puerto 587). Para TLS implícito en el puerto 465, pon `SMTP_PORT=465`, `SMTP_SSL=true` y `SMTP_TLS=false`. El correo solo se activa cuando están definidos tanto `SMTP_HOST` como `SMTP_USER`. Reinicia el backend después de cambiar cualquiera de estos valores (`docker compose up -d backend`).

Proveedores habituales y su configuración típica (compruébala en la documentación actual del proveedor, porque cambia de vez en cuando):

| Proveedor | Servidor típico | Puerto típico | Notas |
|---|---|---|---|
| Zoho Mail | `smtp.zoho.eu` / `smtp.zoho.com` | 587 | Genera una contraseña de aplicación en Account → Security |
| Gmail / Google Workspace | `smtp.gmail.com` | 587 | Requiere verificación en dos pasos + contraseña de aplicación |
| Brevo (antes Sendinblue) | `smtp-relay.brevo.com` | 587 | El plan gratuito cubre el volumen de la mayoría de las iglesias pequeñas |
| SMTP2GO | `mail.smtp2go.com` | 587 | Pago por uso con plan gratuito |
| Mailgun | `smtp.mailgun.org` | 587 | Requiere verificar el dominio |

**Consulta siempre la documentación SMTP actual de tu proveedor** antes de configurar: los ajustes, los números de puerto y los requisitos de autenticación cambian. La referencia es la página de estado del proveedor, no esta tabla.

Haz una prueba desde la interfaz después de crear un evento: abre la configuración del formulario de inscripción del evento (**Configuración ▸ Inscripción** mientras el evento está en configuración, **Más ▸ Formulario de inscripción** una vez abiertas las inscripciones) y luego **Confirmación por correo electrónico ▸ Enviar correo de prueba**. El correo de prueba llega a tu propia dirección de inicio de sesión e indica qué nombre de remitente (`From`), qué `Reply-To` y qué servidor SMTP se usaron: muy útil para diagnosticar los casos de «el correo nunca llegó».

Si SMTP se deja vacío, la aplicación omite los envíos y registra `email_skipped` por cada envío que habría hecho. Útil para desarrollo.

---

## Referencia de ajustes opcionales

Todos se leen de `.env` y `docker-compose.yml` los transmite. Reinicia con `docker compose up -d` después de cambiarlos.

| Variable | Valor predeterminado | Qué hace |
|---|---|---|
| `LOG_LEVEL` | `INFO` | `DEBUG` registra cada consulta a la base de datos con sus valores, es decir, datos de participantes. |
| `RATE_LIMIT_REGISTRATION` | `60` | Inscripciones por minuto desde una misma dirección. Cada familiar adicional del formulario cuenta. Súbelo si toda una congregación se inscribe a la vez desde la misma wifi; `0` lo desactiva. Detrás de tu propio proxy inverso o de un Cloudflare Tunnel se usa la dirección real del visitante, siempre que ese proxy llegue a Moimio desde una dirección privada o de loopback y envíe `X-Forwarded-For`. |
| `FEATURE_ALLOCATION` | `true` | `false` desactiva el motor de asignación para una instalación solo de inscripciones. |
| `FEATURE_OUTBOUND_WEBHOOKS` | `true` | `false` oculta la página Webhooks y desactiva los envíos. Consulta [webhooks](../webhooks.md) (en inglés). |
| `WEBHOOK_ALLOW_PRIVATE_TARGETS` | `false` | Las URL de webhook en direcciones privadas, de loopback o de enlace local (`10.x`, `192.168.x`, `localhost`…) se rechazan salvo que esto sea `true`. Actívalo solo si tu receptor está en tu propia red. No está en `.env.example`; añade la línea tú mismo. |
| `WEBHOOK_DELIVERY_RETENTION_DAYS` | `30` | Cuánto tiempo se conserva el historial de envíos de webhooks. |

Las demás variables de `.env.example` y `docker-compose.yml` (`FEATURE_CREATE_EVENT_CONFIRMATION`, `EVENT_CHARGE_*`, `BILLING_CARD_LAST4`, `FEATURE_ACCOUNT_PORTAL`, `ACCOUNT_URL`, `FEATURE_DEMO_NOTICE`, `MOIMIO_DEMO_MAIL_URL`, `MOIMIO_TENANT_ID`, `MOIMIO_WEBHOOK_URL`, `MOIMIO_WEBHOOK_SECRET`) existen para el servicio alojado y sus espacios de demostración. Déjalas con sus valores predeterminados en una instalación propia normal. `APP_URL` ya no se usa: los enlaces de los correos toman su dirección de la petición.

---

## Solución de problemas

**`docker compose up` termina enseguida, sin registros.**
Mira el error real: `docker compose ps` y luego `docker compose logs <service>`. La causa más habitual es un conflicto de puertos: otra cosa del equipo ya usa el 6120, el 6121 o el 6122. Detén el servicio en conflicto o cambia el puerto (consulta «Cambiar los puertos» más arriba).

**Los registros del backend muestran `connection refused` hacia `db:5432`.**
El backend arrancó antes de que Postgres estuviera listo. La cláusula `depends_on: condition: service_healthy` normalmente lo evita; si te ocurre, puede que tu versión de Docker sea demasiado antigua. Actualiza Docker o simplemente ejecuta `docker compose restart backend`.

**Los registros del backend muestran `relation "users" does not exist`.**
Las migraciones de Alembic no se ejecutaron. Busca un error de Alembic más arriba en `docker compose logs backend`. Normalmente se soluciona con `docker compose down && docker compose up -d --force-recreate`.

**La página dice «No se pudo conectar con el servidor» o el inicio de sesión falla con un error de red.**
El contenedor del frontend sirve la página y redirige `/api/*` al contenedor del backend. Comprueba que el backend está en marcha (`docker compose ps` y luego `docker compose logs backend`) y que `curl http://localhost:6120/health` responde. Si has puesto tu propio proxy inverso delante, asegúrate de que reenvía todas las rutas al puerto 6120, no solo `/`.

**Los registros del backend muestran `password authentication failed for user "moimio"`.**
`POSTGRES_PASSWORD` se cambió después de crear por primera vez el volumen de la base de datos; Postgres conserva la original. Vuelve a poner la contraseña antigua en `.env` o cámbiala dentro de la base de datos (`docker compose exec db psql -U moimio -c "ALTER USER moimio PASSWORD '<new>'"`) y reinicia.

**Cualquier otra cosa.**
Abre un [informe de error](https://github.com/jc-universe87/moimio/issues/new?template=bug_report.md) con los registros pertinentes (oculta antes cualquier dato de participantes).

---

¿Listo para usar Moimio? Empieza por el [Manual de usuario](../manual/README.es.md) para conocer el flujo de trabajo de organización de eventos.
