# 06 — Motor de asignación

El motor de asignación es lo que diferencia a Moimio de una hoja de cálculo. Cuando llegan las inscripciones, el motor propone una asignación completa con un solo clic, respetando los códigos de grupo, las marcas, las restricciones de género y por marca, las exclusiones y la capacidad de los grupos. Tú revisas la propuesta y luego la confirmas o la descartas.

Esta sección explica cómo ejecutarlo, qué hace, cómo ajustarlo y qué hacer cuando la propuesta no termina de convencerte.

<p align="center">
  <img src="../assets/allocation-board.png" alt="El tablero de asignación de un tipo de grupo, con la asignación a medias" width="560">
  <br>
  <em>El tablero de asignación de un tipo de grupo, con la asignación a medias</em>
</p>

---

## Dónde encontrarlo

**Asignación** en la barra lateral ▸ haz clic en la tarjeta de un tipo de grupo (por ejemplo, **Asignación de habitaciones** o **Grupos pequeños**). Así se abre el tablero de asignación de ese tipo de grupo. **← Volver** te lleva de nuevo a la lista de tipos de grupo.

El tablero tiene tres partes:

- **Barra de herramientas superior**: el botón **✦ Asignación automática** con un **⚙** (configuración del motor) al lado, un enlace **+ Añadir [elemento]** para crear un grupo nuevo (por ejemplo, **+ Añadir Habitación**) y un menú **⋯** (notas, **↗ Abrir resumen**, descargas en PDF, **Borrar todas las asignaciones**).
- **Panel izquierdo, Sin asignar**: todas las personas que aún no están en un grupo, con un cuadro de búsqueda y los filtros **Todos / ♂ Masculino / ♀ Femenino**. Quienes no han confirmado su correo llevan la etiqueta **Pendiente**. Debajo de la lista está el bloque **Excluidos** (consulta [Mantener a alguien fuera de un tipo de grupo](#mantener-a-alguien-fuera-de-un-tipo-de-grupo)). El panel se puede convertir en una ventana flotante y volver a su sitio con el pequeño icono de su parte superior.
- **Cuadrícula derecha, los grupos**: una tarjeta por grupo con su ocupación (por ejemplo, `5/8`), su restricción de género si la tiene (por ejemplo, **Solo mujeres**), un punto de color si el grupo está reservado a quienes llevan una marca, y las personas que contiene.

**Colocar a personas a mano.** En un ordenador, arrastra a una persona desde el panel izquierdo hasta la tarjeta de un grupo, o de un grupo a otro. En un móvil o una tableta, toca a las personas para seleccionarlas y luego toca la tarjeta de un grupo (o usa **Asignar a →** en la barra inferior de la pantalla). Para sacar a alguien de un grupo, pasa el ratón por su nombre y haz clic en la ✕ roja (**Quitar asignación**), o arrástralo de vuelta al panel izquierdo.

Los movimientos manuales se guardan al momento. Si al soltar a alguien un grupo superara su capacidad, Moimio te pregunta primero (**Superar capacidad**). La restricción de género de un grupo no se puede saltar a mano.

---

## Cómo ejecutarlo

Haz clic en **✦ Asignación automática**. Se abre un pequeño menú **Modo de asignación** con dos opciones:

- **Asignar solo nuevos participantes**: mantiene todas las asignaciones existentes de este tipo de grupo y solo coloca a quienes aún no están en un grupo. Úsalo cuando ya hayas colocado a algunas personas a mano y quieras que el motor complete el resto a su alrededor.
- **Reasignar todo desde cero**: ignora las asignaciones actuales y calcula una asignación nueva para todos. Úsalo cuando hayas cambiado la configuración del motor o las marcas y quieras una propuesta limpia.

En ambos casos, los grupos que hayas bloqueado con **Mantener** se quedan exactamente como están (consulta [Bloquear un grupo](#bloquear-un-grupo-mantener)).

### Revisar la propuesta

Al cabo de un momento, el tablero se sustituye por la pantalla **Asignación propuesta**. Todavía no se ha guardado nada y los demás organizadores no pueden ver tu propuesta.

<p align="center">
  <img src="../assets/allocation-review.png" alt="La pantalla Asignación propuesta con las columnas Antes y Después para cada grupo" width="560">
  <br>
  <em>Revisar una propuesta antes de confirmarla</em>
</p>

- Una línea de resumen arriba, por ejemplo *«31 de 34 participantes asignados · 3 grupos mantenidos juntos · 2 grupos divididos · 2 grupos formados por marcas»*.
- **N no pudieron ser asignados**: las personas para las que el motor no encontró sitio.
- Para cada grupo, una columna **Antes** (quién está ahora) y una columna **Después** (a quién propone el motor), con las personas marcadas como **nuevo** o **sale** y un recuento de cambios como **+2** o **sin cambios**.

**¿Por qué está aquí esta persona?** Pasa el ratón por cualquier nombre (o tócalo en un móvil) para ver el motivo del motor, por ejemplo *«asignado con el código de grupo SMITH (4 personas)»*, *«se repartiría porque esta marca está configurada para repartir uniformemente»* o *«se movería para equilibrar el tamaño de los grupos»*. Para las personas que no se han podido colocar, el motivo explica qué lo ha impedido.

Después, elige:

- **Confirmar asignación**: guarda la propuesta. Vuelve el tablero con las nuevas asignaciones.
- **Descartar**: desecha la propuesta tras una confirmación (*«¿Descartar la propuesta? Se perderán las sugerencias del motor.»*). Tus asignaciones existentes no se tocan. El botón **← Volver** del tablero hace la misma pregunta mientras hay una propuesta abierta.

En la pantalla de revisión no se puede arrastrar a las personas. Si la propuesta está casi bien, confírmala y haz luego los ajustes en el tablero.

---

## Qué hace el motor, explicado con sencillez

El motor sigue estos pasos en orden. Coinciden con el orden de los interruptores de la configuración del motor, así que leer el panel de configuración de arriba abajo es leer la asignación.

**Antes de nada: quién participa.** Las personas canceladas nunca se incluyen. Las no confirmadas (pendientes) se incluyen salvo que desactives **Incluir participantes sin confirmar**. Quien hayas **excluido** de este tipo de grupo queda totalmente fuera. Las personas de los grupos bloqueados (**Mantener**) se quedan donde están, y no se añade a nadie nuevo a esos grupos.

**Paso 1: códigos de grupo.** Las personas que comparten un código de grupo (familias, amigos que se inscribieron juntos) se colocan juntas, empezando por los grupos más grandes. Cada uno va al grupo más pequeño que pueda acogerlos a todos. Si ningún grupo es lo bastante grande, se reparten lo más equilibradamente posible entre el menor número de grupos que puedan acogerlos, siempre que **Dividir códigos de grupo si es necesario** esté activado. Si **Un código de grupo ocupa un grupo entero** está activado, no se pone a nadie más en un grupo donde haya entrado un código de grupo. Un «código de grupo» que solo usa una persona no tiene nada que mantener unido, así que esa persona se trata como cualquier otra.

**Paso 2: marcas, en tu orden.** El motor recorre tu lista de marcas desde arriba. Para cada marca:

- **Mantener juntos**: las personas con esa marca se ponen en el mismo grupo. Si no caben todas, el motor llena un grupo por completo antes de empezar el siguiente, de modo que como mucho un grupo queda mezclado.
- **Distribuir uniformemente**: las personas con esa marca se reparten una a una entre los grupos, para que ningún grupo acumule varias. Útil para «un líder por grupo pequeño».
- **Sin efecto**: aquí se ignora la marca.

A quien se colocó por su código de grupo en el paso 1 no se le mueve por sus marcas. Quien tiene varias marcas se trata según la que esté más arriba en la lista.

**Paso 3: grupos restringidos.** Los grupos restringidos a un solo género, o a quienes llevan una marca (por ejemplo, una habitación reservada para líderes), se llenan con personas que cumplen la restricción.

**Paso 4: todos los demás.** Las personas que siguen esperando se reparten por turnos entre los grupos sin restricción restantes. Con **Mantener juntas a las personas del mismo género** activado, aquí se tiene en cuenta el género; si está desactivado, el género se ignora salvo en los grupos restringidos.

**Paso 5: equilibrar.** Con **Equilibrar el tamaño de los grupos** activado (por defecto), el motor mueve entonces códigos de grupo completos, grupos de marca de «mantener juntos» completos y personas sueltas entre grupos para que todos los grupos queden más o menos igual de llenos según su tamaño. Para ello nunca separa un código de grupo, y no toca a quienes se repartieron entre grupos, se distribuyeron por una marca o se colocaron en un grupo restringido. Un grupo sin límite de capacidad se trata como un grupo de tamaño medio.

**Paso 6: rellenar huecos.** Quien siga sin sitio se coloca en el grupo adecuado que tenga más espacio libre.

**Paso 7: explicar el resto.** Quien siga sin sitio recibe un motivo, que se muestra en la pantalla de revisión (consulta [Cuando algo sale mal](#cuando-algo-sale-mal)).

**Lo que el motor nunca incumple:** la capacidad de un grupo, su restricción de género, su restricción por marca, una exclusión o un grupo bloqueado. Todo lo demás (mantener juntos los códigos de grupo y las marcas, igualar tamaños) se hace lo mejor posible dentro de esas reglas.

El motor es predecible: las mismas personas con la misma configuración dan siempre la misma propuesta.

---

## ⚙ Configuración del motor

<p align="center">
  <img src="../assets/engine-settings.png" alt="El panel de configuración del motor, que se abre con el icono del engranaje junto a Asignación automática" width="480">
  <br>
  <em>El panel de configuración del motor, que se abre con el icono del engranaje junto a Asignación automática</em>
</p>

Haz clic en el **⚙** junto a **✦ Asignación automática**. Los ajustes se guardan en cuanto los cambias y son **por tipo de grupo**: Asignación de habitaciones puede funcionar de una forma y Grupos pequeños de otra. Aparecen en el orden en que los aplica el motor:

| Ajuste | Por defecto | Qué hace |
|---|---|---|
| **Incluir participantes sin confirmar** | Activado | Quienes no han confirmado su correo se asignan junto con los demás. Desactivado: se quedan fuera hasta que confirmen. |
| **Mantener juntos los códigos de grupo** | Activado | Las personas que comparten un código de grupo se colocan juntas siempre que haya sitio para todas. Desactivado: los códigos de grupo se ignoran y cada persona se coloca por separado. |
| **Dividir códigos de grupo si es necesario** | Activado | Si ningún grupo tiene sitio para todos los que comparten un código, se reparten entre varios grupos. Desactivado: se quedan sin asignar, para que los coloques tú. Se aplica solo a los códigos de grupo, nunca a las marcas. **Aparece en gris mientras Mantener juntos los códigos de grupo está desactivado**, porque entonces no tiene efecto; tu elección se conserva para cuando vuelvas a activar los códigos de grupo. |
| **Un código de grupo ocupa un grupo entero** | Desactivado | Si se activa, no se coloca a nadie más junto a un código de grupo, aunque sobren plazas. Útil para dormitorios y habitaciones familiares. Desactivado es lo adecuado para mesas y grupos pequeños. |
| **Aplicar las marcas en este orden** | (vacío) | Tu lista de marcas (ver más abajo). |
| **Mantener juntas a las personas del mismo género** | Activado | Se aplica a todos los que sigan sin asignar después de los códigos de grupo y las marcas. Desactivado: se ignora el género, salvo donde un grupo esté restringido a un solo género. |
| **Equilibrar el tamaño de los grupos** | Activado | Una última pasada iguala el nivel de ocupación de los grupos, sin romper códigos de grupo, marcas ni restricciones de género. Desactivado: los grupos se quedan como los dejaron los pasos anteriores. |

**Aplicar las marcas en este orden.** Las marcas que hayas añadido a la lista aparecen numeradas, la primera arriba. Arrástralas (o usa ↑ ↓) para cambiar el orden, haz clic en ✕ para quitar una de la lista y haz clic en **+ Añadir** junto a cualquier marca de debajo para incorporarla. Cada marca tiene su propio desplegable: **Sin efecto**, **Mantener juntos** o **Distribuir uniformemente**.

La misma marca puede hacer cosas distintas en tipos de grupo distintos. Por ejemplo, «Líder» puede estar en **Mantener juntos** para Asignación de habitaciones y en **Distribuir uniformemente** para Grupos pequeños.

---

## Bloquear un grupo (Mantener)

Cuando un grupo está exactamente como debe (la habitación de los ponentes, por ejemplo), haz clic en el pequeño candado de su tarjeta. El candado se cierra y el aviso dice *«Se mantiene. La asignación automática no lo modificará.»* A partir de ahí, ningún modo de asignación añade a nadie a ese grupo ni saca a nadie de él. Vuelve a hacer clic en el candado para liberarlo.

**Borrar todas las asignaciones**, en el menú **⋯**, vacía también los grupos bloqueados.

---

## Mantener a alguien fuera de un tipo de grupo

A veces una persona forma parte del evento pero no de un tipo de grupo concreto: la cocinera que no necesita grupo pequeño o un visitante de un día que no necesita habitación. **Exclúyela** de ese tipo de grupo y seguirá en todos los demás.

- Pasa el ratón por un nombre (en el panel izquierdo o en un grupo) y haz clic en el icono del círculo tachado (**Excluir de la asignación**), o arrastra a la persona al bloque **Excluidos**, debajo del panel izquierdo. En un móvil, selecciona a las personas y toca **Excluir** en la barra inferior.
- Al excluir a alguien también sale de cualquier grupo que ocupara en este tipo de grupo. Si ese grupo estaba bloqueado, Moimio te avisa de que la plaza se queda vacía y te ofrece **Desbloquear**.
- Las personas excluidas aparecen en el bloque **Excluidos (N)**, debajo del panel izquierdo, y los recuentos del tablero muestran *«N excluidos»* para que las cifras sigan cuadrando.
- El motor nunca coloca a una persona excluida.
- Para deshacerlo, haz clic en el icono de deshacer junto a su nombre en el bloque Excluidos (**Incluir en la asignación**), o selecciona a varias y toca **Incluir**. Si arrastras a una persona excluida a un grupo, Moimio te pregunta primero, y **Asignar de todos modos** levanta la exclusión.

Las exclusiones aparecen también en el CSV completo de Participantes (columna **Excluded From**) y en las listas en PDF (consulta la [sección 08](08-reports-and-pdf-exports.es.md)).

---

## Volver a ejecutar y ajustar

Si un resultado no es el que quieres, hay tres caminos para mejorarlo:

1. **Cambia la configuración y vuelve a empezar desde cero.** Ajusta el orden de las marcas, su comportamiento o los interruptores y luego usa **✦ Asignación automática ▸ Reasignar todo desde cero**.
2. **Coloca a mano a las personas importantes y completa el resto.** Arrastra a los grupos adecuados a las personas cuya colocación importa (estos movimientos se guardan al momento), bloquea los grupos que no quieras que se toquen y luego usa **✦ Asignación automática ▸ Asignar solo nuevos participantes**. El motor completa el resto a su alrededor.
3. **Hazlo a mano.** Arrastra a las personas entre grupos y prescinde del motor. El motor propone; tú decides.

En **Asignar solo nuevos participantes**, quien ya no cumple la restricción de género o por marca de su grupo (porque añadiste la restricción después de colocarlo) se saca y se vuelve a colocar.

---

## Historial y motivos

Haz clic en la **ⓘ** junto al nombre de una persona para abrir su **Perfil del participante**. Para los administradores termina con una sección **Historial** que muestra todos los cambios de esa persona: *«Asignado a Habitación 3»*, *«Movido de Habitación 1 a Habitación 2»*, *«Excluido de Grupos pequeños»*, etc., con quién lo hizo, y *«(motor)»* cuando procede de una propuesta confirmada. Las colocaciones del motor conservan su motivo debajo, por ejemplo *«asignado con 3 de 6 personas del código de grupo KIM»* o *«movido para equilibrar el tamaño de los grupos»*.

---

## Trabajar a la vez que otros administradores

El tablero se actualiza en tiempo real en todos los dispositivos. Cuando otro administrador mueve a alguien, confirma una propuesta o cambia un grupo, tu vista se actualiza en uno o dos segundos, sin recargar la página. Una propuesta que estás revisando es privada hasta que la confirmas.

Si dos personas mueven al mismo participante en el mismo instante, gana el último movimiento y ambas pantallas muestran el resultado. En eventos con varios administradores, poneos de acuerdo sobre quién trabaja en cada tipo de grupo.

---

## Confirmar un tipo de grupo

Confirmar una propuesta guarda las asignaciones. Aparte de eso, puedes **confirmar** un tipo de grupo para indicar a todos que está terminado:

- Cuando todos están asignados, el tablero muestra **Listo para confirmar** con un botón **Confirmar este tipo de grupo →**.
- En la página **Asignación**, un tipo de grupo en curso muestra un botón **Confirmar tipo de grupo** en su tarjeta.

Un tipo de grupo confirmado muestra **Confirmado** en su tarjeta y un aviso en su tablero. Cualquier cambio posterior (un movimiento manual, una propuesta confirmada, **Borrar todas las asignaciones**) lo reabre automáticamente; también puedes hacer clic en **Reabrir para editar** en el aviso. Cuando todos los tipos de grupo están confirmados, el aviso ofrece **Check-in listo →**.

---

## Cuando algo sale mal

**«Una familia ha acabado repartida entre varios grupos aunque los códigos de grupo están activados».**

Su grupo era mayor que el espacio libre de cualquier grupo, así que **Dividir códigos de grupo si es necesario** la repartió entre el menor número de grupos posible. Para mantenerla unida, aumenta la capacidad de un grupo o desactiva la división: entonces se quedará sin colocar para que la coloques tú.

**«Algunas personas no se han podido colocar».**

En la pantalla de revisión, pasa el ratón por (o toca) cada nombre de **N no pudieron ser asignados** para ver el motivo. Los motivos que verás:

- *«todos los grupos están llenos»*: no queda sitio en ningún grupo en el que puedan entrar.
- *«demasiadas personas comparten este código para caber juntas y la división está desactivada»*: el código de grupo es mayor que cualquier grupo y **Dividir códigos de grupo si es necesario** está desactivado.
- *«No se ha podido asignar a las personas con el código de grupo …. Necesitan un grupo que no esté restringido a un solo género.»*: normalmente, una familia mixta cuando todos los grupos son solo para hombres o solo para mujeres (aparece cuando la división está desactivada).
- *«no consta el género y todos los grupos están restringidos a un solo género»*: indica su género en Participantes o añade un grupo mixto.

Corrige la causa (añade un grupo, aumenta una capacidad, indica el género de la persona) y vuelve a ejecutar el motor, o confirma y colócalos a mano.

**«La asignación parece desigual».**

Con **Equilibrar el tamaño de los grupos** activado, la mayoría de las asignaciones salen bastante equilibradas. Si queda desigualdad, normalmente es porque un código de grupo grande tenía que mantenerse unido, porque las únicas personas que podrían moverse son de las que el paso de equilibrado no toca (grupos divididos, marcas de distribuir uniformemente, grupos restringidos) o porque el ajuste está desactivado. El motor siempre mantiene unido un código de grupo antes de igualar tamaños: un código de grupo significa «mantener juntos sí o sí». Si lo que quieres es *repartir* a las personas, usa una marca en **Distribuir uniformemente** en lugar de un código de grupo.

**«He confirmado y ahora quiero deshacerlo».**

No hay un único botón de deshacer, pero nada es definitivo: mueve a las personas a mano, vuelve a ejecutar el motor o usa **⋯ ▸ Borrar todas las asignaciones** y empieza de nuevo.

---

## Siguiente paso

La [sección 07 — Check-in](07-check-in.es.md) explica lo que ocurre el día del evento: el modo de check-in a pantalla completa, las columnas de check-in personalizadas, cómo marcar las llegadas y cómo trabajar junto a otros miembros del personal en la entrada.
