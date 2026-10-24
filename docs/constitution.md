# Constitución de habits-cli

1. **Stack mínimo.** Solo biblioteca estándar de Python 3.12+. pytest es la única dependencia externa y solo para tests.
2. **Spec antes que código.** Todo cambio de comportamiento o del formato JSON se escribe primero en `specs/`. Si no está en la spec, no se implementa.
3. **Núcleo puro.** `habits/core.py` no hace I/O (ni `print`, ni `input`, ni archivos). `habits/cli.py` solo lee argumentos y muestra resultados.
4. **Tests obligatorios.** Cada función pública de `core.py` tiene al menos un test, y `pytest -q` pasa antes de cada commit.
5. **Persistencia local simple.** Los datos viven en un único archivo JSON, que solo `habits/storage.py` lee y escribe.
6. **Idioma.** Los identificadores del código van en inglés y los mensajes al usuario en español.
