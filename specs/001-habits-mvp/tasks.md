# Tareas 001 — MVP de habits-cli

Estado: borrador pendiente de aprobación. Deriva de `spec.md` y `plan.md` (misma carpeta).

## Cómo usar esta lista

- Orden de dependencia: no empieces una tarea sin tener hechas las de su línea "Depende de".
- Cada tarea es de 20 a 30 minutos como máximo. Si se alarga, divídela antes de seguir.
- Método: primero el test (que falle), luego el código mínimo para que pase. Cada tarea termina con `pytest -q` en verde.
- "Hecho cuando" es la única prueba de que la tarea está terminada. Si no se cumple, no se marca.
- Los tests usan siempre `today = date(2026, 10, 23)` inyectado y `tmp_path`; nunca el reloj ni el archivo reales.

---

## Fase 0 — Preparación

- [x] **T01 — Cerrar las dudas de la spec**
  - Cubre: bloquea todos los RF (constitución, principio 2).
  - Depende de: nada.
  - Qué: llevar a `spec.md` las decisiones de la sección 9.1 del plan (día a medianoche local, orden de creación, nombre como se creó, formato del listado, primera ejecución, fechas futuras, orden `ayuda`, nombres de órdenes, un único argumento, archivo vacío = dañado, códigos de salida). Requiere tu petición expresa, porque AGENTS.md prohíbe tocar `specs/` por iniciativa propia.
  - Hecho cuando: `spec.md` no contiene ninguna marca `[NECESITA ACLARACIÓN]` y tú has aprobado el cambio.

- [x] **T02 — Esqueleto del proyecto**
  - Cubre: base de todos los RF.
  - Depende de: T01.
  - Qué: crear `habits/__init__.py` y la carpeta `tests/` con un `conftest.py` vacío; añadir `.gitignore` con `__pycache__/` y `.pytest_cache/`.
  - Hecho cuando: `python -c "import habits"` termina sin error y `git status` no muestra `__pycache__` ni `.pytest_cache`.

---

## Fase 1 — Núcleo (`habits/core.py`, sin I/O)

- [ ] **T03 — `Habit` y excepciones**
  - Cubre: base de RF-1 y RF-2.
  - Depende de: T02.
  - Qué: `Habit` (dataclass inmutable con `name` y `done`), `MAX_NAME_LENGTH = 50`, y las excepciones `HabitsError`, `EmptyNameError`, `NameTooLongError`, `DuplicateHabitError`, `HabitNotFoundError`, `AlreadyDoneError` (con sus atributos).
  - Hecho cuando: `tests/test_core.py` comprueba que `Habit` no se puede modificar (`FrozenInstanceError`) y que cada excepción hereda de `HabitsError` y conserva su atributo; `pytest -q` pasa.

- [ ] **T04 — `normalize_name`**
  - Cubre: RF-1.2, RF-2.2. Caso CL-2.
  - Depende de: T03.
  - Hecho cuando: el test confirma que `"  Leer  "` -> `"Leer"`, que los tabuladores y saltos de línea de los extremos también se quitan, que los espacios internos no cambian, y que `"   "` -> `""`.

- [ ] **T05 — `validate_name`**
  - Cubre: RF-1.3, RF-1.4, RF-1.5. Casos CL-3, CL-4, CL-5.
  - Depende de: T04.
  - Hecho cuando: el test confirma que `""` lanza `EmptyNameError`; que 50 caracteres pasa; que 51 lanza `NameTooLongError` con `length == 51`; y que nombres con tildes, ñ y emojis pasan.

- [ ] **T06 — `find_habit` y clave de comparación**
  - Cubre: RF-1.6, RF-2.2.
  - Depende de: T04.
  - Qué: clave privada `NFC + casefold`; `find_habit` normaliza el nombre pedido antes de comparar.
  - Hecho cuando: el test confirma que `"leer"`, `"LEER"` y `"  Leer "` encuentran el hábito `Leer`; que `"Correr"` devuelve `None`; y que "é" compuesta y descompuesta coinciden.

- [ ] **T07 — `add_habit`**
  - Cubre: RF-1.1, RF-1.3, RF-1.4, RF-1.6. Caso CL-1.
  - Depende de: T05, T06.
  - Hecho cuando: el test confirma que añade un hábito con `done` vacío al final y con el nombre normalizado; que un duplicado sin distinguir mayúsculas lanza `DuplicateHabitError` con el nombre existente; que un nombre inválido lanza el error de T05; y que en todos los casos la lista original no cambia.

- [ ] **T08 — `current_streak`: casos base**
  - Cubre: RF-3.2, RF-3.3. Casos CL-8, CL-9, CL-10, CL-11.
  - Depende de: T03.
  - Hecho cuando: con `today = 2026-10-23`, el test confirma: {21, 22} -> 0; {21, 22, 23} -> 3; {21, 23} -> 1; vacío -> 0; {23} -> 1.

- [ ] **T09 — `current_streak`: bordes**
  - Cubre: RF-3.2.
  - Depende de: T08.
  - Hecho cuando: el test confirma la racha correcta al cruzar fin de mes, fin de año y el 29 de febrero de un año bisiesto; que las fechas futuras en `done` no alteran la racha; y que una cadena de 1 100 días devuelve 1 100.

- [ ] **T10 — `mark_done`**
  - Cubre: RF-2.1, RF-2.2, RF-2.3, RF-2.4, RF-2.5. Casos CL-6, CL-7.
  - Depende de: T06, T08.
  - Hecho cuando: el test confirma que añade `today` solo al hábito indicado (sin distinguir mayúsculas); que repetirlo lanza `AlreadyDoneError`; que un hábito inexistente lanza `HabitNotFoundError` sin crear nada; que un nombre vacío lanza `HabitNotFoundError`; y que la lista original no cambia.

- [ ] **T11 — `streaks`**
  - Cubre: RF-3.1, RF-3.4.
  - Depende de: T08.
  - Hecho cuando: el test confirma que devuelve `(nombre, racha)` por hábito en el orden de la lista, y que una lista vacía devuelve una lista vacía.

---

## Fase 2 — Persistencia (`habits/storage.py`)

- [ ] **T12 — `load`: datos válidos y archivo ausente**
  - Cubre: RF-4.1. Caso CL-14.
  - Depende de: T03.
  - Qué: `StorageError`, `DataCorruptedError`, `FORMAT_VERSION`, `load` para el formato de la sección 3 del plan.
  - Hecho cuando: el test confirma que un JSON válido escrito a mano (con ñ, tildes, emoji y varias fechas) produce los `Habit` esperados, y que un archivo inexistente devuelve `[]` sin crearlo.

- [ ] **T13 — `save` y ida y vuelta**
  - Cubre: RF-4.1. RNF-4.
  - Depende de: T12.
  - Qué: escritura atómica con `.tmp` y `os.replace`, UTF-8, `ensure_ascii=False`, fechas ordenadas.
  - Hecho cuando: el test confirma que `load(save(x)) == x`; que en el archivo las fechas salen ordenadas y los caracteres no ASCII salen sin escapar; y que no queda ningún `.tmp` en la carpeta.

- [ ] **T14 — `load`: estructura dañada**
  - Cubre: RF-4.2. Caso CL-13.
  - Depende de: T12.
  - Hecho cuando: un test parametrizado confirma que cada caso lanza `DataCorruptedError` con `reason` no vacío y deja el archivo con los mismos bytes: JSON inválido, archivo vacío, raíz que no es objeto, falta `version` o `habits`, `version` distinta de 1, `habits` que no es lista, elemento que no es objeto o sin `name` o `done`.

- [ ] **T15 — `load`: contenido dañado**
  - Cubre: RF-4.2, RF-1.5, RF-1.6.
  - Depende de: T14, T05.
  - Hecho cuando: un test parametrizado confirma que cada caso lanza `DataCorruptedError` con el archivo intacto: `name` que no es texto, vacío o de más de 50 caracteres; nombres repetidos sin distinguir mayúsculas; `done` que no es lista; fecha mal formada (`2026-13-40`, `20261023`, número); fechas repetidas. Y que una fecha futura en `done` se carga sin error.

- [ ] **T16 — Errores de lectura y escritura**
  - Cubre: RNF-4.
  - Depende de: T13.
  - Hecho cuando: el test confirma que guardar en una carpeta inexistente lanza `StorageError`, que el archivo original (si existía) conserva sus bytes y que no queda `.tmp`; y que leer una ruta que es una carpeta lanza `StorageError`.

---

## Fase 3 — Interfaz (`habits/cli.py` y `habits/__main__.py`)

- [ ] **T17 — `main`: uso, ayuda y errores de uso**
  - Cubre: RF-4.3, RF-4.4, RF-4.5.
  - Depende de: T02.
  - Qué: `main(argv, *, path, today) -> int`, texto de uso, análisis de `argv` a mano.
  - Hecho cuando: el test confirma que `ayuda`, `-h` y `--help` devuelven 0 y escriben el uso en la salida estándar; que sin orden, orden desconocida, falta de nombre y argumentos de más devuelven 2 con el mensaje exacto del plan (sección 5.3) y el uso en la salida de errores; y que ninguno toca el archivo.

- [ ] **T18 — `crear`: caso correcto**
  - Cubre: RF-1.1, RF-1.2, RF-4.1, RF-4.4. Caso CL-2.
  - Depende de: T07, T13, T17.
  - Hecho cuando: el test confirma que `crear "  Leer  "` imprime `Hábito "Leer" creado.`, devuelve 0 y el hábito queda guardado como `Leer`; y que, en una segunda llamada a `main` con el mismo archivo, el hábito sigue ahí.

- [ ] **T19 — `crear`: errores**
  - Cubre: RF-1.3, RF-1.4, RF-1.5, RF-1.6, RF-4.5. Casos CL-1, CL-3, CL-4, CL-5.
  - Depende de: T18.
  - Hecho cuando: el test confirma que vacío, solo espacios, 51 caracteres y duplicado (`leer` frente a `Leer`) devuelven 1, escriben el mensaje exacto en español en la salida de errores y dejan el archivo con los mismos bytes; y que 50 caracteres y un nombre con ñ, tildes y emoji se aceptan.

- [ ] **T20 — `hecho`**
  - Cubre: RF-2.1, RF-2.2, RF-2.3, RF-2.4, RF-2.5, RF-4.4. Casos CL-6, CL-7.
  - Depende de: T10, T13, T17.
  - Hecho cuando: el test confirma que `hecho leer` sobre `Leer` imprime `Hábito "Leer" marcado como hecho hoy.`, devuelve 0 y guarda la fecha de `today`; que repetirlo devuelve 1 con el mensaje exacto y sin cambiar el archivo; que un hábito inexistente devuelve 1 con la pista de `crear` y sin crear nada; y que ninguna opción de la orden permite elegir otra fecha.

- [ ] **T21 — `listar`**
  - Cubre: RF-3.1, RF-3.2, RF-3.3, RF-3.4, RF-3.5, RF-4.5. Casos CL-8 a CL-12.
  - Depende de: T11, T12, T17.
  - Hecho cuando: el test confirma, con hábitos de racha 3, 1 y 0, que se imprime una línea `<nombre>: <n> día(s)` por hábito en orden de creación, con "1 día" en singular; que un hábito marcado ayer y anteayer pero no hoy muestra 0; que sin hábitos se imprime `Aún no tienes hábitos. Crea uno con: python -m habits crear "Leer"` y se devuelve 0; y que los bytes del archivo no cambian.

- [ ] **T22 — Datos dañados y fallos de archivo en la CLI**
  - Cubre: RF-4.2, RNF-4.
  - Depende de: T15, T16, T18, T20, T21.
  - Hecho cuando: el test confirma que con un archivo dañado `crear`, `hecho` y `listar` devuelven 1, imprimen `Error: no se pudo leer <ruta>: <motivo>. El archivo no se ha modificado.` en la salida de errores y dejan el archivo con los mismos bytes; y que un fallo de escritura devuelve 1 con el mensaje de acceso al archivo.

- [ ] **T23 — Punto de entrada `python -m habits`**
  - Cubre: RF-4.4, RF-4.5 (codificación de salida, plan 5.6).
  - Depende de: T17.
  - Qué: `habits/__main__.py` reconfigura salida y errores a UTF-8 y hace `sys.exit(main())`.
  - Hecho cuando: un test que ejecuta `python -m habits ayuda` como proceso devuelve 0 con el uso en español, y `python -m habits xyz` devuelve 2; ninguno lee ni escribe el archivo de datos real.

- [ ] **T24 — Persistencia entre ejecuciones y cambio de día**
  - Cubre: RF-4.1. Caso CL-15.
  - Depende de: T20, T21.
  - Hecho cuando: el test hace `crear`, `hecho` con `today` = 22, `hecho` con `today` = 23 y `listar` con `today` = 23 sobre el mismo archivo, y la salida muestra `Leer: 2 días`; y con `listar` y `today` = 25 muestra `Leer: 0 días`.

- [ ] **T25 — Rendimiento**
  - Cubre: RNF-3.
  - Depende de: T21.
  - Hecho cuando: el test genera 100 hábitos con 3 años de marcas cada uno y `main(["listar"])` termina en menos de 1 segundo.

---

## Fase 4 — Cierre

- [ ] **T26 — Auditoría final contra spec y constitución**
  - Cubre: todos los RF, RNF-1, RNF-2, RNF-5, RNF-6.
  - Depende de: T01 a T25.
  - Hecho cuando se cumple todo esto:
    1. `pytest -q` pasa sin fallos y confirma el resultado en tu respuesta.
    2. Cada RF y cada caso límite CL-1 a CL-15 tiene al menos un test que pasa (se comprueba con la tabla de cobertura de abajo).
    3. `core.py` no contiene `print`, `input`, `open`, `date.today` ni imports de `os`, `sys`, `pathlib` o `json` (revisión con `grep`).
    4. Solo `storage.py` importa `json` y abre archivos.
    5. Ningún `import` en el proyecto sale de la biblioteca estándar (pytest solo en `tests/`).
    6. Comprobación manual del criterio de finalización 3 de la spec: en una carpeta nueva, con solo la ayuda de `python -m habits ayuda`, se crea un hábito, se marca y se ve su racha 1.
    7. Todos los mensajes que ve el usuario están en español.

---

## Cobertura de requisitos

| Requisito | Tareas |
|-----------|--------|
| RF-1.1 | T07, T18 |
| RF-1.2 | T04, T18 |
| RF-1.3 | T05, T07, T19 |
| RF-1.4 | T05, T07, T19 |
| RF-1.5 | T05, T15, T19 |
| RF-1.6 | T06, T07, T15, T19 |
| RF-2.1 | T10, T20 |
| RF-2.2 | T04, T06, T10, T20 |
| RF-2.3 | T10, T20 |
| RF-2.4 | T10, T20 |
| RF-2.5 | T10, T20 |
| RF-3.1 | T11, T21 |
| RF-3.2 | T08, T09, T21 |
| RF-3.3 | T08, T21 |
| RF-3.4 | T11, T21 |
| RF-3.5 | T21 |
| RF-4.1 | T12, T13, T18, T24 |
| RF-4.2 | T14, T15, T22 |
| RF-4.3 | T17 |
| RF-4.4 | T17, T18, T20, T23 |
| RF-4.5 | T17, T19, T21, T23, T26 |
| RNF-3 | T25 |
| RNF-4 | T13, T16, T22 |
| RNF-5 | T26 |

Casos límite: CL-1 (T07, T19), CL-2 (T04, T18), CL-3 (T05, T19), CL-4 (T05, T19), CL-5 (T05, T19), CL-6 (T10, T20), CL-7 (T10, T20), CL-8 a CL-11 (T08, T21), CL-12 (T21), CL-13 (T14, T15, T22), CL-14 (T12), CL-15 (T24).
