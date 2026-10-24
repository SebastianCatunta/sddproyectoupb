# Spec 001 — MVP de habits-cli

Estado: borrador pendiente de aprobación. Las dudas abiertas se cerraron en la tarea T01 (ver sección 9).

## 1. Contexto y objetivo

Quien estudia de forma autodidacta o en un curso suele perder la constancia sin darse cuenta. Ver cuántos días seguidos lleva cumpliendo un hábito (la "racha") es una motivación simple y barata.

**Objetivo del MVP:** que una persona pueda, desde la terminal, (1) crear un hábito de estudio, (2) marcarlo como hecho hoy y (3) ver todos sus hábitos con su racha actual de días consecutivos.

**Por qué este alcance:** es lo mínimo que cierra el ciclo "me comprometo → cumplo → veo mi progreso". Todo lo demás se pospone hasta comprobar que este ciclo es útil.

## 2. Usuarios

- **Estudiante individual** que usa la herramienta en su propio equipo, de forma local y sin conexión. Es el único tipo de usuario del MVP.
- **Desarrollador junior mantenedor**, que debe poder entender y modificar el comportamiento a partir de esta spec (ver la constitución del proyecto).

## 3. Historias de usuario

- **HU-1.** Como estudiante, quiero crear un hábito con un nombre, para empezar a registrar mi constancia.
- **HU-2.** Como estudiante, quiero marcar un hábito como hecho hoy, para dejar constancia de que cumplí.
- **HU-3.** Como estudiante, quiero listar mis hábitos con su racha, para saber cuántos días seguidos llevo y no romperla.
- **HU-4.** Como estudiante, quiero que los errores me expliquen qué ocurrió y no alteren mis datos, para confiar en la herramienta.

## 4. Requisitos funcionales

Notación EARS: *El sistema deberá…* (ubicuo), *Cuando…* (evento), *Si… entonces…* (comportamiento ante error).

Definiciones:

- **Órdenes** que ofrece la herramienta: `crear`, `hecho`, `listar` y `ayuda`.
- **Hoy** es la fecha local del equipo del usuario; el día cambia a medianoche.

### RF-1 Crear un hábito (HU-1)

- **RF-1.1** Cuando el usuario cree un hábito con un nombre válido, el sistema deberá guardarlo con racha inicial 0, conservar el nombre con las mayúsculas con que se escribió y mostrar un mensaje de confirmación con el nombre.
- **RF-1.2** El sistema deberá eliminar los espacios al inicio y al final del nombre antes de validarlo y guardarlo.
- **RF-1.3** Si el nombre, tras eliminar los espacios, está vacío, entonces el sistema deberá rechazar la creación, mostrar un error y terminar con un código de salida distinto de cero.
- **RF-1.4** Si el nombre, tras eliminar los espacios, supera los 50 caracteres, entonces el sistema deberá rechazar la creación, mostrar un error y terminar con un código de salida distinto de cero.
- **RF-1.5** El sistema deberá aceptar como válido cualquier otro nombre de 1 a 50 caracteres, incluidas letras con tilde, la ñ y emojis.
- **RF-1.6** Si ya existe un hábito con el mismo nombre, sin distinguir mayúsculas de minúsculas, entonces el sistema deberá rechazar la creación, mostrar un error, terminar con un código de salida distinto de cero y no modificar los hábitos existentes.

### RF-2 Marcar un hábito como hecho hoy (HU-2)

- **RF-2.1** Cuando el usuario marque como hecho un hábito existente que no está marcado hoy, el sistema deberá registrar el día de hoy para ese hábito y mostrar un mensaje de confirmación.
- **RF-2.2** El sistema deberá identificar el hábito por su nombre sin distinguir mayúsculas de minúsculas, con la misma normalización de espacios que RF-1.2.
- **RF-2.3** Si el hábito ya está marcado como hecho hoy, entonces el sistema deberá mostrar un error, terminar con un código de salida distinto de cero y no registrar nada nuevo.
- **RF-2.4** Si el hábito indicado no existe, entonces el sistema deberá mostrar un error, terminar con un código de salida distinto de cero y no crear ningún hábito. Un nombre vacío o demasiado largo se trata como un hábito que no existe.
- **RF-2.5** El sistema deberá permitir marcar únicamente el día de hoy; no se podrán marcar días pasados ni futuros.

### RF-3 Listar hábitos con su racha (HU-3)

- **RF-3.1** Cuando el usuario liste los hábitos, el sistema deberá mostrar una línea por hábito, en el orden en que se crearon, con su nombre y su racha actual en días. El listado no indica si el hábito ya se marcó hoy.
- **RF-3.2** El sistema deberá calcular la racha actual como el número de días consecutivos marcados que terminan en el día de hoy. Los días marcados posteriores a hoy no cuentan para la racha ni son un error.
- **RF-3.3** Si el hábito no está marcado hoy, entonces el sistema deberá mostrar su racha como 0, aunque haya días marcados en días anteriores.
- **RF-3.4** Si no existe ningún hábito, entonces el sistema deberá mostrar un mensaje que indique que aún no hay hábitos e indique cómo crear uno, y terminar con código de salida cero.
- **RF-3.5** El listado no deberá modificar ningún dato.

### RF-4 Errores y persistencia (HU-4)

- **RF-4.1** El sistema deberá conservar los hábitos y los días marcados entre ejecuciones, en una ubicación fija del equipo del usuario que no dependa de la carpeta desde la que se ejecute. Cuando no existan datos guardados (primera ejecución), el sistema deberá comportarse como si no hubiera hábitos, sin mostrar error.
- **RF-4.2** Si los datos guardados están dañados o son ilegibles (incluido un archivo de datos que existe pero está vacío), entonces el sistema deberá mostrar un error que explique el problema, terminar con un código de salida distinto de cero y no modificar ni sobrescribir los datos guardados.
- **RF-4.3** Si el usuario invoca una orden desconocida, no indica ninguna orden, omite un argumento obligatorio o añade argumentos de más, entonces el sistema deberá mostrar el error y una ayuda breve de uso, y terminar con código de salida 2. Cuando el usuario pida la ayuda, el sistema deberá mostrar el uso y terminar con código de salida cero. El nombre del hábito es un único argumento: los nombres con espacios se escriben entre comillas.
- **RF-4.4** Cuando una operación termine correctamente, el sistema deberá terminar con código de salida cero. Si falla por una regla de negocio o por los datos guardados (RF-1.3, RF-1.4, RF-1.6, RF-2.3, RF-2.4, RF-4.2), el código de salida será 1.
- **RF-4.5** El sistema deberá mostrar todos los mensajes dirigidos al usuario en español. Los errores se muestran por el canal de errores y los resultados normales por el canal de salida.

## 5. Requisitos no funcionales

- **RNF-1 Simplicidad.** El proyecto debe poder mantenerlo un desarrollador junior; se prefiere el comportamiento obvio sobre el ingenioso (constitución, principios 1 y 3).
- **RNF-2 Uso sin conexión.** Todas las funciones deben operar sin red.
- **RNF-3 Rapidez.** Cada orden debe responder en menos de 1 segundo con hasta 100 hábitos y 3 años de historial por hábito.
- **RNF-4 Seguridad de los datos.** Ningún error debe provocar pérdida o corrupción de datos ya guardados.
- **RNF-5 Verificabilidad.** Cada requisito funcional debe poder comprobarse con una prueba automática (constitución, principio 4).
- **RNF-6 Idioma.** Mensajes al usuario en español; identificadores del código en inglés (constitución, principio 6).

## 6. Casos límite

| # | Situación | Resultado esperado |
|---|-----------|--------------------|
| CL-1 | Crear "Leer" y luego "leer" | Segundo intento rechazado (RF-1.6) |
| CL-2 | Crear "  Leer  " | Se guarda como "Leer" (RF-1.2) |
| CL-3 | Nombre de solo espacios | Rechazado como vacío (RF-1.3) |
| CL-4 | Nombre de exactamente 50 caracteres / de 51 | Aceptado / rechazado (RF-1.4, RF-1.5) |
| CL-5 | Nombre con emojis o tildes | Aceptado (RF-1.5) |
| CL-6 | Marcar dos veces el mismo día | Segundo intento es error (RF-2.3) |
| CL-7 | Marcar un hábito inexistente | Error, no se crea nada (RF-2.4) |
| CL-8 | Marcado ayer y anteayer, no hoy | Racha 0 (RF-3.3) |
| CL-9 | Marcado hoy, ayer y anteayer | Racha 3 |
| CL-10 | Marcado hoy y anteayer, no ayer | Racha 1 (la cadena se rompió) |
| CL-11 | Hábito recién creado, sin marcas | Racha 0 |
| CL-12 | Listar sin hábitos | Mensaje informativo, código 0 (RF-3.4) |
| CL-13 | Datos guardados dañados | Error, datos intactos (RF-4.2) |
| CL-14 | Primera ejecución, sin datos previos | Se trata como lista vacía, sin error (RF-4.1) |
| CL-15 | Cruce de medianoche entre dos órdenes | Cada orden usa el día vigente al ejecutarse |
| CL-16 | Un día marcado posterior a hoy en los datos | No es error y no cuenta para la racha (RF-3.2) |
| CL-17 | Archivo de datos que existe pero está vacío | Error de datos dañados, archivo intacto (RF-4.2) |

## 7. Fuera de alcance

- Borrar o renombrar hábitos.
- Marcar días pasados o futuros, y desmarcar un día.
- Recordatorios o notificaciones.
- Estadísticas distintas de la racha actual (mejor racha, porcentajes, historial detallado).
- Varios usuarios, sincronización o acceso remoto.
- Hábitos con frecuencia distinta de la diaria (semanal, días laborables, etc.).
- Exportar o importar datos.
- Cambios de zona horaria o de horario de verano.
- Ejecuciones simultáneas de la herramienta sobre los mismos datos.
- Filtrar saltos de línea, caracteres de control o caracteres invisibles dentro del nombre de un hábito.

## 8. Criterios de finalización

El MVP está terminado cuando:

1. Cada RF y cada caso límite de la sección 6 tiene al menos una prueba automática que pasa.
2. `pytest -q` pasa sin fallos.
3. Un usuario nuevo puede crear un hábito, marcarlo y ver su racha en 1 siguiendo solo la ayuda de la herramienta.
4. Todos los mensajes al usuario están en español.
5. No hay ninguna duda abierta sin resolver en la sección 9.

## 9. Dudas abiertas

Ninguna. Las dudas anteriores se resolvieron en la tarea T01 así:

| Duda | Decisión | Dónde queda |
|------|----------|-------------|
| ¿Qué es "hoy"? | Fecha local del equipo; el día cambia a medianoche. | Sección 4, definiciones |
| Orden del listado | Orden de creación. | RF-3.1 |
| Mayúsculas del nombre | Se muestra como se escribió. | RF-1.1 |
| Formato del listado | Una línea por hábito con nombre y racha; no indica si ya se marcó hoy. | RF-3.1 |
| Primera ejecución sin datos | Lista vacía, sin error. | RF-4.1, CL-14 |
| Días marcados posteriores a hoy | No son error y no cuentan para la racha. | RF-3.2, CL-16 |

Huecos que el plan detectó y que también se cerraron aquí:

- Orden `ayuda` y nombres de las órdenes (sección 4, RF-4.3).
- El nombre del hábito es un único argumento; sobrar argumentos es un error de uso (RF-4.3).
- Archivo de datos vacío = dañado (RF-4.2, CL-17).
- Ubicación fija de los datos (RF-4.1).
- Un nombre vacío o demasiado largo al marcar se trata como hábito inexistente (RF-2.4).
- Códigos de salida 0, 1 y 2, y errores por el canal de errores (RF-4.3, RF-4.4, RF-4.5).
