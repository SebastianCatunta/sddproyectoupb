# Plan 001 — MVP de habits-cli

Estado: borrador pendiente de aprobación. Implementa `spec.md` (misma carpeta) respetando `docs/constitution.md`.

Este plan es el CÓMO. Si una decisión de aquí cambia un comportamiento visible, antes hay que actualizar la spec (constitución, principio 2). La sección 9 lista las decisiones provisionales que lo requieren.

## 1. Alcance técnico

- Python 3.12+, solo biblioteca estándar (`datetime`, `json`, `pathlib`, `os`, `sys`, `dataclasses`, `unicodedata`). pytest solo para tests. (Constitución 1)
- Type hints en todas las funciones públicas.
- Identificadores en inglés; mensajes al usuario en español. (Constitución 6)
- Ejecución: `python -m habits <orden>`. Tests: `pytest -q`.

## 2. Estructura de módulos

```
habits/
  __init__.py
  __main__.py    # punto de entrada: sys.exit(main())
  core.py        # lógica pura: nombres, hábitos, racha. Sin I/O.
  storage.py     # único módulo que lee y escribe el archivo JSON
  cli.py         # lee argumentos, llama a core/storage, imprime mensajes
tests/
  test_core.py
  test_storage.py
  test_cli.py
```

Dependencias permitidas (flecha = "importa a"):

```
cli  ->  core, storage
storage  ->  core        (solo para el tipo Habit)
core  ->  (nada del proyecto)
```

**Cubre:** constitución 3 y 5. RNF-1, RNF-2.

### 2.1 `core.py` (sin `print`, `input`, archivos, ni reloj)

```python
@dataclass(frozen=True)
class Habit:
    name: str                 # tal como se creó, ya sin espacios en los extremos
    done: frozenset[date]     # días marcados

class HabitsError(Exception): ...
class EmptyNameError(HabitsError): ...
class NameTooLongError(HabitsError):   # atributo: length
class DuplicateHabitError(HabitsError): # atributo: name (el existente)
class HabitNotFoundError(HabitsError):  # atributo: name (el pedido)
class AlreadyDoneError(HabitsError):    # atributo: name

MAX_NAME_LENGTH = 50

def normalize_name(raw: str) -> str
def validate_name(name: str) -> None
def find_habit(habits: list[Habit], raw_name: str) -> Habit | None
def add_habit(habits: list[Habit], raw_name: str) -> list[Habit]
def mark_done(habits: list[Habit], raw_name: str, today: date) -> list[Habit]
def current_streak(done: frozenset[date], today: date) -> int
def streaks(habits: list[Habit], today: date) -> list[tuple[str, int]]
```

Reglas:

- Las excepciones llevan datos, no texto. El texto en español lo decide `cli.py`.
- Las funciones no modifican sus argumentos: devuelven una lista nueva.
- `today` siempre llega como parámetro. `core.py` nunca llama a `date.today()`.
- Clave de comparación de nombres (privada): `unicodedata.normalize("NFC", name).casefold()`.

### 2.2 `storage.py` (único que toca el archivo)

```python
DEFAULT_PATH = Path.home() / ".habits.json"
FORMAT_VERSION = 1

class StorageError(Exception): ...              # no se pudo leer o escribir
class DataCorruptedError(StorageError): ...     # atributos: path, reason

def load(path: Path) -> list[Habit]
def save(path: Path, habits: list[Habit]) -> None
```

- `load`: archivo inexistente -> `[]`. Cualquier otro problema -> `DataCorruptedError` o `StorageError`. Nunca escribe.
- `save`: escritura atómica (ver decisión D5).
- Lectura y escritura siempre con `encoding="utf-8"`.

### 2.3 `cli.py` (solo argumentos y salida)

```python
def main(argv: list[str] | None = None, *, path: Path | None = None,
         today: date | None = None) -> int
```

- Si `argv` es `None`, usa `sys.argv[1:]`; si `path` es `None`, usa `DEFAULT_PATH`; si `today` es `None`, usa `date.today()`. Los parámetros existen para poder probar sin tocar el disco ni el reloj real.
- Devuelve el código de salida; `__main__.py` lo pasa a `sys.exit`.
- Es el único lugar donde se llama a `date.today()`, `print` y se decide el texto de los mensajes.

**Cubre:** RF-4.3, RF-4.4, RF-4.5.

## 3. Modelo de datos JSON

Un único archivo (por defecto `~/.habits.json`).

```json
{
  "version": 1,
  "habits": [
    {"name": "Leer", "done": ["2026-10-21", "2026-10-22", "2026-10-23"]},
    {"name": "Correr 🏃", "done": ["2026-10-20"]},
    {"name": "Escribir", "done": []}
  ]
}
```

Reglas del formato:

| Campo | Tipo | Regla |
|-------|------|-------|
| `version` | entero | Debe ser `1`. |
| `habits` | lista | El orden de la lista es el orden de creación. |
| `name` | texto | Ya normalizado (sin espacios en los extremos), de 1 a 50 caracteres, único sin distinguir mayúsculas. |
| `done` | lista de textos | Fechas `AAAA-MM-DD` estrictas, sin repetidas. Al guardar se escriben ordenadas. |

No se guarda la racha: se calcula siempre desde `done` (RF-3.2).

`load` considera el archivo **dañado** (`DataCorruptedError`) si se cumple cualquiera de estas condiciones:

1. No es JSON válido, o está vacío (0 bytes).
2. La raíz no es un objeto, o falta `version` o `habits`.
3. `version` no es `1`.
4. `habits` no es una lista, o algún elemento no es un objeto con `name` y `done`.
5. Algún `name` no es texto, no cumple la validación de nombre (vacío tras `strip` o de más de 50 caracteres), o dos nombres coinciden sin distinguir mayúsculas.
6. `done` no es una lista, contiene algo que no sea una fecha `AAAA-MM-DD` válida (por ejemplo `2026-13-40` o `20261023`), o contiene fechas repetidas.

Se aceptan fechas futuras en `done` (no son error); la racha las ignora de forma natural (ver sección 4).

**Cubre:** RF-4.1, RF-4.2, RF-1.5, RF-1.6. Constitución 5.

## 4. Algoritmo de la racha

```
función current_streak(done: conjunto de fechas, today: fecha) -> entero
    si today no está en done:
        devolver 0                      # RF-3.3
    racha = 0
    día = today
    mientras día esté en done:
        racha = racha + 1
        día = día - 1 día               # aritmética de fechas: cruza mes, año y bisiestos
    devolver racha
```

Notas:

- Parte siempre de `today`, así que las fechas futuras en `done` nunca se alcanzan y no afectan.
- El coste es proporcional a la racha (como mucho unos 1 100 pasos con 3 años de historial); con `done` como conjunto cada consulta es O(1).
- Un hábito recién creado (`done` vacío) da 0 (CL-11); la primera marca da 1.

Ejemplos con `today = 2026-10-23`:

| `done` | Racha | Caso |
|--------|-------|------|
| 21, 22 (sin 23) | 0 | CL-8 |
| 21, 22, 23 | 3 | CL-9 |
| 21, 23 | 1 | CL-10 |
| vacío | 0 | CL-11 |

**Cubre:** RF-3.2, RF-3.3. CL-8 a CL-11.

## 5. Contrato de la CLI

### 5.1 Órdenes

| Orden | Efecto |
|-------|--------|
| `python -m habits crear <nombre>` | Crea un hábito. |
| `python -m habits hecho <nombre>` | Marca el hábito como hecho hoy. |
| `python -m habits listar` | Lista los hábitos con su racha. |
| `python -m habits ayuda` (también `-h`, `--help`) | Muestra el uso. |

- `<nombre>` es **un único argumento**: si tiene espacios hay que escribirlo entre comillas (`crear "Leer mucho"`).
- No hay opciones de fecha: `hecho` solo puede marcar hoy (RF-2.5).

### 5.2 Códigos de salida

| Código | Significado |
|--------|-------------|
| `0` | Operación correcta, incluido `listar` sin hábitos y `ayuda`. (RF-4.4, RF-3.4) |
| `1` | Error de la operación: nombre inválido, duplicado, hábito inexistente, ya marcado hoy, datos dañados o archivo ilegible/no escribible. |
| `2` | Uso incorrecto: orden desconocida, sin orden, falta el argumento o sobran argumentos. (RF-4.3) |

### 5.3 Salidas

Confirmaciones y listado van por la salida estándar. Errores y avisos de uso incorrecto van por la salida de errores. `ayuda` va por la salida estándar.

| Situación | Mensaje | Código | RF |
|-----------|---------|--------|----|
| `crear "  Leer  "` correcto | `Hábito "Leer" creado.` | 0 | RF-1.1, RF-1.2 |
| `crear ""` o solo espacios | `Error: el nombre del hábito no puede estar vacío.` | 1 | RF-1.3 |
| `crear` con 51+ caracteres | `Error: el nombre no puede superar los 50 caracteres (tiene 51).` | 1 | RF-1.4 |
| `crear leer` y ya existe `Leer` | `Error: ya existe un hábito llamado "Leer".` | 1 | RF-1.6 |
| `hecho leer` correcto | `Hábito "Leer" marcado como hecho hoy.` | 0 | RF-2.1, RF-2.2 |
| `hecho` ya marcado hoy | `Error: "Leer" ya estaba marcado como hecho hoy.` | 1 | RF-2.3 |
| `hecho Correr` inexistente | `Error: no existe el hábito "Correr". Créalo con: python -m habits crear "Correr"` | 1 | RF-2.4 |
| `listar` con hábitos | Una línea por hábito (ver 5.4) | 0 | RF-3.1 |
| `listar` sin hábitos | `Aún no tienes hábitos. Crea uno con: python -m habits crear "Leer"` | 0 | RF-3.4 |
| Datos dañados | `Error: no se pudo leer <ruta>: <motivo>. El archivo no se ha modificado.` | 1 | RF-4.2 |
| Archivo no legible o no escribible | `Error: no se pudo acceder a <ruta>: <motivo>.` | 1 | RNF-4 |
| Orden desconocida | `Error: orden desconocida "xyz".` + texto de uso | 2 | RF-4.3 |
| Sin orden | Texto de uso | 2 | RF-4.3 |
| Falta el nombre | `Error: falta el nombre del hábito.` + texto de uso | 2 | RF-4.3 |
| Sobran argumentos | `Error: sobran argumentos.` + texto de uso | 2 | RF-4.3 |
| `ayuda`, `-h`, `--help` | Texto de uso | 0 | RF-4.3 |

En los mensajes de error de `crear` el nombre mostrado es el que ya está guardado (en el duplicado) o el normalizado (en el resto). En `hecho` y en la inexistencia se muestra el nombre guardado o, si no existe, el normalizado que escribió el usuario.

Texto de uso:

```
Uso:
  python -m habits crear <nombre>   Crea un hábito nuevo
  python -m habits hecho <nombre>   Marca un hábito como hecho hoy
  python -m habits listar           Muestra los hábitos y su racha
  python -m habits ayuda            Muestra esta ayuda
```

### 5.4 Formato del listado

Una línea por hábito, en orden de creación: `<nombre>: <n> día(s)`.

```
Leer: 3 días
Correr 🏃: 0 días
Escribir: 1 día
```

Singular solo cuando la racha es exactamente 1.

### 5.5 Flujo de cada orden

Garantiza que ningún error modifica los datos (RNF-4):

```
crear:   cargar -> core.add_habit -> guardar -> imprimir
hecho:   cargar -> core.mark_done(hoy) -> guardar -> imprimir
listar:  cargar -> core.streaks(hoy) -> imprimir          (no guarda: RF-3.5)
```

- Si `cargar` falla, no se llama a `guardar` (RF-4.2).
- Si `core` lanza una excepción, no se llama a `guardar` (RF-1.3, 1.4, 1.6, 2.3, 2.4).
- El texto de cada error se elige en `cli.py` a partir del tipo de excepción.

### 5.6 Codificación de la salida

`__main__.py` reconfigura la salida y los errores a UTF-8 antes de llamar a `main`, para que ñ, tildes y emojis no fallen cuando la salida se redirige a un archivo o una tubería en Windows.

**Cubre:** RF-1.1 a RF-1.6, RF-2.1 a RF-2.5, RF-3.1, RF-3.4, RF-3.5, RF-4.2 a RF-4.5.

## 6. Decisiones técnicas

| # | Decisión | Por qué | Alternativa descartada |
|---|----------|---------|------------------------|
| D1 | Analizar `argv` a mano: solo hay 3 órdenes con 0 o 1 argumento. | `argparse` imprime textos propios en inglés ("usage", "the following arguments are required") que romperían RF-4.5; adaptarlo exige subclases y plantillas. Con tan pocas órdenes, ocho líneas de código propias son más fáciles para un junior. | `argparse` con mensajes personalizados. |
| D2 | `today` entra como parámetro; solo `cli.py` lee el reloj. | Mantiene `core.py` puro (constitución 3) y permite probar CL-8 a CL-10 y CL-15 con fechas fijas. | `date.today()` dentro de `core.py`. |
| D3 | `Habit` es un `dataclass(frozen=True)` y las funciones devuelven listas nuevas. | Sin efectos laterales: más fácil de probar y de razonar. | Diccionarios mutables que se modifican en sitio. |
| D4 | Fechas guardadas como texto `AAAA-MM-DD`. | Legible a mano, ordenable como texto y sin ambigüedad de zona horaria. | Marcas de tiempo numéricas; listas `[año, mes, día]`. |
| D5 | Escritura atómica: escribir `<archivo>.tmp` en la misma carpeta y reemplazar con `os.replace`. | Si el proceso se interrumpe a mitad, el archivo original queda intacto (RNF-4). El `.tmp` existe solo un instante; los datos permanentes siguen en un único archivo. | Escribir directamente sobre el archivo (riesgo de truncarlo); mantener copias de respaldo permanentes (más de un archivo). |
| D6 | La racha se calcula siempre desde `done`; no se guarda. | Una sola fuente de verdad: no puede quedar desincronizada. | Guardar un contador de racha en el JSON. |
| D7 | Algoritmo con conjunto y retroceso día a día desde hoy. | Es la definición literal de RF-3.2 y de RF-3.3; trivial de leer y de probar. | Ordenar las fechas y recorrer buscando huecos (más casos que cubrir). |
| D8 | Órdenes en español: `crear`, `hecho`, `listar`, `ayuda`. | Son parte de la interfaz de usuario y el público es hispanohablante. Los identificadores del código siguen en inglés (`add_habit`, `mark_done`). | Órdenes en inglés (`add`, `done`, `list`). |
| D9 | Comparar nombres con NFC + `casefold()`. | `casefold` trata bien ñ, tildes y otras mayúsculas Unicode; NFC evita que "é" compuesta y descompuesta cuenten como hábitos distintos. Ambos son de la biblioteca estándar. | `lower()` (falla con casos como "ß"); sin normalización Unicode. |
| D10 | Contar el límite de 50 como `len(texto)` (caracteres Unicode). | Es lo único que ofrece la biblioteca estándar. Limitación aceptada: un emoji compuesto puede contar como varios caracteres. | Contar clústeres de grafemas (requiere una dependencia; prohibido por el principio 1). |
| D11 | Códigos de salida: 0 ok, 1 error de la operación, 2 uso incorrecto. | Convención habitual en CLI, fácil de verificar y de explicar. | Un código distinto por cada tipo de error. |
| D12 | Archivo ausente = lista vacía; archivo vacío = dañado. | Cubre CL-14 sin ocultar corrupción real (un archivo de 0 bytes no lo crea este programa). | Tratar el archivo vacío como lista vacía. |
| D13 | Ruta por defecto `~/.habits.json`; se puede inyectar en `main`. | Estable entre ejecuciones desde cualquier carpeta; la inyección evita tocar el archivo real en tests. | Archivo en la carpeta actual (los datos cambiarían según desde dónde se ejecute). |
| D14 | Sin bloqueo de archivo: gana la última escritura. | Fuera del MVP (un solo usuario, una orden a la vez). Se documenta como riesgo (sección 9). | Bloqueo de archivo entre procesos (complejidad desproporcionada). |

## 7. Estrategia de tests

Herramienta: pytest. Cada función pública de `core.py` tiene al menos un test (constitución 4). Todo test usa fechas fijas (`date(2026, 10, 23)` como "hoy") y `tmp_path` para el archivo: ningún test depende del reloj real ni del archivo del usuario.

### 7.1 `tests/test_core.py` (sin disco, sin reloj)

| Función | Qué se prueba | Cubre |
|---------|---------------|-------|
| `normalize_name` | Quita espacios y tabuladores de los extremos; no toca los internos. | RF-1.2, CL-2 |
| `validate_name` | Vacío y solo espacios fallan; 50 pasa; 51 falla; tildes, ñ y emojis pasan. | RF-1.3, 1.4, 1.5, CL-3, 4, 5 |
| `find_habit` | Encuentra sin distinguir mayúsculas y con espacios en los extremos; devuelve `None` si no existe; "é" compuesta y descompuesta coinciden. | RF-2.2 |
| `add_habit` | Añade con `done` vacío al final; duplicado sin distinguir mayúsculas falla y la lista original no cambia; nombre inválido falla. | RF-1.1, 1.3, 1.4, 1.6, CL-1 |
| `mark_done` | Añade hoy; segunda vez falla (`AlreadyDoneError`); inexistente falla (`HabitNotFoundError`); no modifica la lista original ni otros hábitos. | RF-2.1, 2.2, 2.3, 2.4, CL-6, 7 |
| `current_streak` | Los casos de la sección 4; sin marcas -> 0; primera marca -> 1; cruce de mes, de año y 29-feb de año bisiesto; fechas futuras ignoradas; cadena de 1 100 días. | RF-3.2, 3.3, CL-8 a 11 |
| `streaks` | Mantiene el orden de creación; devuelve nombre y racha por hábito; lista vacía -> lista vacía. | RF-3.1, 3.4 |

### 7.2 `tests/test_storage.py` (con `tmp_path`)

| Prueba | Cubre |
|--------|-------|
| Guardar y volver a cargar devuelve los mismos hábitos (incluye ñ, tildes y emojis; fechas guardadas ordenadas). | RF-4.1 |
| Archivo inexistente -> lista vacía y no crea el archivo. | CL-14 |
| Cada causa de daño de la sección 3 (parametrizada) lanza `DataCorruptedError` y deja el archivo con los mismos bytes: JSON inválido, archivo vacío, raíz no objeto, versión distinta, `habits` no lista, nombre vacío o largo, nombres repetidos, fecha mal formada (`2026-13-40`, `20261023`), fechas repetidas. | RF-4.2, CL-13 |
| Fecha futura en `done` se carga sin error. | Sección 3 |
| Si falla la escritura (carpeta inexistente) lanza `StorageError` y el archivo original no cambia; no queda `.tmp`. | RNF-4 |
| `save` no deja un archivo `.tmp` tras terminar bien. | RNF-4, D5 |

### 7.3 `tests/test_cli.py` (`main(argv, path=..., today=...)` con `capsys`)

| Prueba | Cubre |
|--------|-------|
| `crear` correcto: mensaje exacto, código 0, hábito persistido. | RF-1.1, 4.4 |
| `crear` con espacios en los extremos guarda sin ellos. | RF-1.2, CL-2 |
| `crear` vacío, de 51 y duplicado: mensaje exacto en la salida de errores, código 1, archivo con los mismos bytes. | RF-1.3, 1.4, 1.6 |
| `crear` de 50 caracteres y con emojis/tildes funciona. | RF-1.5 |
| `hecho` correcto, repetido, inexistente y con otra capitalización. | RF-2.1 a 2.4 |
| Hacer `hecho` en dos ejecuciones con `today` distinto (ayer, hoy) permite ambas; `listar` muestra racha 2. | RF-4.1, CL-15 |
| `listar` con rachas 0, 1 y N: singular/plural, orden de creación, y el archivo no cambia. | RF-3.1, 3.2, 3.3, 3.5, CL-8 a 11 |
| `listar` vacío: mensaje con la pista y código 0. | RF-3.4, CL-12 |
| Datos dañados en `crear`, `hecho` y `listar`: código 1, mensaje, archivo intacto. | RF-4.2, CL-13 |
| Orden desconocida, sin orden, falta el nombre, sobran argumentos: código 2, uso en la salida de errores. | RF-4.3 |
| `ayuda`, `-h`, `--help`: código 0 y uso en la salida estándar. | RF-4.3 |
| Todos los mensajes están en español: se comparan con el texto exacto de la sección 5.3 (nada de "usage" ni "error:" en inglés). | RF-4.5 |
| Rendimiento: 100 hábitos con 3 años de marcas, `listar` tarda menos de 1 segundo (umbral amplio para no ser frágil). | RNF-3 |

### 7.4 No automatizable

- Criterio de finalización 3 de la spec ("un usuario nuevo puede… siguiendo solo la ayuda"): lista de comprobación manual con `python -m habits` en una carpeta nueva.
- RNF-2 (sin red): se cumple por construcción, ya que ningún módulo importa nada de red.

### 7.5 Orden de trabajo sugerido

1. `core.py` con sus tests (la mayor parte de las reglas).
2. `storage.py` con sus tests.
3. `cli.py` y `__main__.py` con sus tests.
4. `pytest -q` en verde antes de cada commit.

## 8. Cobertura de requisitos

| Requisito | Dónde se cubre | Tests |
|-----------|----------------|-------|
| RF-1.1 | `core.add_habit`, `cli` crear (5.3) | core, cli |
| RF-1.2 | `core.normalize_name` | core, cli |
| RF-1.3 | `core.validate_name` / `EmptyNameError` | core, cli |
| RF-1.4 | `core.validate_name` / `NameTooLongError` | core, cli |
| RF-1.5 | `core.validate_name`, D10, sección 3 | core, cli, storage |
| RF-1.6 | `core.add_habit` / `DuplicateHabitError`, D9 | core, cli |
| RF-2.1 | `core.mark_done`, `cli` hecho | core, cli |
| RF-2.2 | `core.find_habit`, D9 | core, cli |
| RF-2.3 | `core.mark_done` / `AlreadyDoneError` | core, cli |
| RF-2.4 | `core.mark_done` / `HabitNotFoundError` | core, cli |
| RF-2.5 | `mark_done` solo recibe `today`; la CLI no tiene opción de fecha (5.1) | core, cli |
| RF-3.1 | `core.streaks`, formato 5.4 | core, cli |
| RF-3.2 | `core.current_streak` (sección 4) | core |
| RF-3.3 | `core.current_streak` (primera condición) | core, cli |
| RF-3.4 | `cli` listar vacío (5.3) | core, cli |
| RF-3.5 | Flujo de `listar` sin `guardar` (5.5) | cli |
| RF-4.1 | `storage.load` / `save`, sección 3 | storage, cli |
| RF-4.2 | `storage.load` + flujo sin `guardar` (5.5) | storage, cli |
| RF-4.3 | Análisis de `argv` a mano, código 2 (5.2, D1) | cli |
| RF-4.4 | Códigos de salida (5.2) | cli |
| RF-4.5 | Mensajes solo en `cli.py`, D1 | cli |
| RNF-3 | Algoritmo O(racha), `done` como conjunto | cli (rendimiento) |
| RNF-4 | D5, flujo 5.5, `StorageError` | storage, cli |
| RNF-5 | Secciones 7.1 a 7.3 | todos |

Constitución:

| Principio | Cómo se respeta |
|-----------|-----------------|
| 1 Stack mínimo | Solo biblioteca estándar; pytest solo en `tests/`. |
| 2 Spec antes que código | Las decisiones que añaden comportamiento están en la sección 9 para pasar antes por la spec. |
| 3 Núcleo puro | `core.py` sin I/O ni reloj; `today` inyectado (D2); `print` solo en `cli.py`. |
| 4 Tests obligatorios | Tabla 7.1 prueba cada función pública de `core.py`; también se prueban `storage` y `cli`. |
| 5 Persistencia local simple | Un único archivo JSON, solo `storage.py` lo toca; el `.tmp` es transitorio (D5). |
| 6 Idioma | Identificadores en inglés; todos los textos al usuario, en español. |

## 9. Decisiones provisionales y riesgos

### 9.1 Pendientes de pasar por la spec (principio 2)

Este plan asume lo siguiente. Hasta que la spec lo diga, no debe implementarse:

1. Dudas abiertas de la spec, con el valor que asume el plan:
   - "Hoy" es la fecha local del equipo y el día cambia a medianoche.
   - El listado va en orden de creación.
   - El nombre se muestra como se creó.
   - Formato del listado: `<nombre>: <n> día(s)`, sin indicar si ya se marcó hoy.
   - Primera ejecución sin archivo = lista vacía.
   - Fechas futuras en los datos: no son error y se ignoran en la racha.
2. Huecos que el plan tuvo que cubrir y la spec no menciona:
   - Existe la orden `ayuda` (y `-h`, `--help`), necesaria para el criterio de finalización 3.
   - Nombres de las órdenes en español (D8).
   - `<nombre>` es un único argumento; sobrar argumentos es un error de uso.
   - Archivo de datos vacío = dañado (D12).
   - Ubicación del archivo de datos (D13).
   - Marcar con un nombre vacío o demasiado largo se trata como "hábito inexistente".
   - Códigos de salida concretos 0, 1 y 2 (D11).
   - Los errores van por la salida de errores.

### 9.2 Riesgos aceptados

- **Escrituras simultáneas** (D14): dos ejecuciones a la vez pueden perder una actualización.
- **Conteo de caracteres** (D10): un emoji compuesto puede contar como varios caracteres para el límite de 50.
- **Cambios de zona horaria o de horario de verano:** `date.today()` usa la fecha local; un viaje puede repetir o saltar un día. Fuera del MVP.
- **Texto de los nombres:** no se filtran saltos de línea, caracteres de control ni caracteres invisibles dentro del nombre (solo se recortan los extremos con `str.strip()`).
- **Consola sin UTF-8:** se reduce con la reconfiguración de la sección 5.6, pero no se elimina en todos los terminales.
