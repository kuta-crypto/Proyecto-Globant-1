# TimbaRNG

TimbaRNG is a 2D slot-inspired RNG game built with Python and Pygame.

## Features

- 6x6 board
- 5-symbol RNG logic
- casino-style scatter pays for 12+ matching symbols anywhere on the board
- gravity cascades with fresh symbols entering from the top
- downward-scrolling reels with staggered stops
- colored outlines and connecting traces for each winning scatter before it falls
- bonus system
- gold, XP, and level progression
- five illustrated anime worlds with animated ambient effects
- 25 pet portraits, individual charged skills, bonds, and role affinity
- eight characters with five mastery ranks each
- ten upgrade tracks with 3-12 ranks and a 25%-budget multi-buy
- 12 active skills and 12 equipment pieces across six slots
- paginated shop, collection filters, and visible skill charge bars
- save/load via JSON
- settings configuration

## Jugar en Windows con el ejecutable (.exe)

El archivo para compartir es **`dist/TimbaRNG.exe`**. Incluye Python, las dependencias y los recursos del juego. En la computadora de destino no hace falta instalar Python, Thonny ni VS Code, ni copiar `.venv` o `assets/`.

1. Copiá `TimbaRNG.exe` a la otra PC con Windows de 64 bits.
2. Abrilo con doble clic. El inicio puede tardar unos segundos mientras extrae los recursos a una carpeta temporal.
3. Las partidas y la configuración se guardan por usuario en `%LOCALAPPDATA%\TimbaRNG\saves\save.json`. Podés abrir esa carpeta pegando `%LOCALAPPDATA%\TimbaRNG\saves` en la barra del Explorador de archivos.

Para trasladar una partida de la versión Python, cerrá el juego y copiá tu archivo `saves/save.json` a esa carpeta. Si ya existe una partida de la versión `.exe`, hacé una copia antes de reemplazarla. Compartir el ejecutable no comparte tus partidas.

### Volver a generar el ejecutable después de modificar el juego

Estos pasos son para quien compila el juego; quien recibe el `.exe` no tiene que ejecutarlos. Compilá en Windows usando Python de 64 bits. Primero creá `.venv` siguiendo las instrucciones de abajo si todavía no existe.

Desde la carpeta del proyecto:

```powershell
.\build_exe.ps1
```

El script instala `requirements-build.txt` y genera `dist/TimbaRNG.exe` con [PyInstaller](https://pyinstaller.org/en/stable/usage.html). Si PowerShell bloquea el script por su política de ejecución, podés ejecutar directamente sus dos comandos principales:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name TimbaRNG --add-data "assets:assets" --exclude-module pytest main.py
```

Esperá a que termine sin errores. Cerrá cualquier instancia del ejecutable antes de recompilar. Cada compilación reemplaza `dist/TimbaRNG.exe`; las partidas quedan fuera del paquete. `build/` y `TimbaRNG.spec` son archivos de trabajo de la compilación y no hace falta distribuirlos. Esta compilación es para Windows; no genera una aplicación para macOS o Linux.

## Instalación y ejecución en Windows (PowerShell)

Estos pasos sirven tanto para esta PC como para otra computadora con Windows. Ejecutá los comandos en una terminal **PowerShell**, por ejemplo desde **Terminal > Nueva terminal** en VS Code. Copiá solamente los comandos dentro de los bloques, una línea por vez, sin las marcas de Markdown ni el prefijo `PS C:\...>` de la terminal.

### 1. Instalar Python

Si la computadora todavía no tiene Python, instalá Python 3 para Windows desde el sitio oficial de Python. Si el instalador ofrece **Add Python to PATH**, marcá esa opción. Después cerrá y volvé a abrir la terminal para que reconozca la instalación.

Comprobá que funciona:

```powershell
python --version
```

Debe mostrar una versión de Python 3. Si `python` no se reconoce o aparece el mensaje de Microsoft Store, probá:

```powershell
py --version
```

Si funciona `py`, usá `py` en lugar de `python` al crear el entorno en el paso 3. Si ninguno funciona, completá o repará la instalación de Python antes de continuar. Thonny y VS Code son opcionales para ejecutar el juego.

### 2. Copiar el proyecto y abrir su carpeta

Copiá o descargá el proyecto completo y, si viene en un ZIP, extraelo antes de ejecutarlo. Conservá la estructura de carpetas: hacen falta `main.py`, `requirements.txt`, `game/`, `assets/` y los demás archivos del proyecto. Copiar solamente `main.py` no alcanza.

**No copies `.venv` desde otra PC:** el entorno virtual contiene rutas y ejecutables propios del equipo donde se creó. Creá uno nuevo en cada computadora. Tampoco hace falta copiar las carpetas `__pycache__`. Si querés conservar tu progreso, copiá también `saves/`, si existe.

En VS Code, abrí la carpeta que contiene `main.py` y luego abrí una terminal PowerShell. También podés entrar desde una terminal existente con `cd`; reemplazá esta ruta por la ubicación real del proyecto:

```powershell
cd "C:\ruta\al\proyecto"
```

Para comprobar que estás en la carpeta correcta:

```powershell
Get-Item .\main.py, .\requirements.txt
```

Si no encuentra alguno de los archivos, corregí la carpeta antes de continuar.

### 3. Crear un entorno virtual (una vez por computadora)

El entorno `.venv` guarda Python y las dependencias del proyecto por separado de otros proyectos.

```powershell
python -m venv .venv
```

Si en el paso 1 funcionó `py` en lugar de `python`, ejecutá esta alternativa:

```powershell
py -m venv .venv
```

Usá solo una de las dos opciones. Si ya tenés un `.venv` creado en esta PC y funciona, podés reutilizarlo. Verificá su intérprete con:

```powershell
.\.venv\Scripts\python.exe --version
```

### 4. Instalar las dependencias

Desde la misma carpeta del proyecto, ejecutá:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Esperá a que termine sin errores. Esto instala las dependencias de `requirements.txt` dentro de `.venv`. Se hace la primera vez y se repite si se actualiza ese archivo o se recrea el entorno.

El comando `python -m pip install -r requirements.txt` también instala dependencias, pero usa el Python que resuelva la terminal. Los comandos de esta guía apuntan explícitamente a `.venv` para instalar y ejecutar con el mismo intérprete.

### 5. Iniciar el juego

```powershell
.\.venv\Scripts\python.exe main.py
```

**Este es el comando que usás cada vez que quieras jugar**, desde la carpeta del proyecto. No hace falta activar el entorno virtual ni volver a instalar las dependencias en cada inicio. Iniciá siempre desde `main.py` para que las importaciones del paquete `game` funcionen correctamente.

### Resumen para una PC nueva

Con Python instalado y la terminal ubicada en la carpeta que contiene `main.py`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Si tu instalación responde a `py`, reemplazá solo el `python` de la primera línea por `py`.

### Alternativa: usar Python de Thonny

Usá esta opción solamente si tenés Thonny instalado y conocés la ruta de su `python.exe`. La ubicación depende de cómo se haya instalado; no es la misma en todas las computadoras.

Podés comprobar esta ubicación de ejemplo con:

```powershell
Test-Path "$env:LOCALAPPDATA\Programs\Thonny\python.exe"
```

Solo si devuelve `True`, podés usar:

```powershell
& "$env:LOCALAPPDATA\Programs\Thonny\python.exe" -m pip install -r requirements.txt
& "$env:LOCALAPPDATA\Programs\Thonny\python.exe" main.py
```

Si devuelve `False`, esa ruta no existe: usá los pasos de `.venv` o reemplazá la ruta por la ubicación real del intérprete. Si Thonny está configurado con el intérprete que querés usar, podés consultar su ruta en la consola de Thonny ejecutando `import sys; print(sys.executable)`.

### Solución de errores frecuentes

| Error o síntoma | Causa y solución |
| --- | --- |
| `Token 'main.py' inesperado` | En PowerShell, una ruta de ejecutable entre comillas necesita el operador `&` delante. Ejemplo: `& "C:\ruta\a\python.exe" main.py`. Copiá también el `&` inicial. |
| `El término '...Thonny\python.exe' no se reconoce` | PowerShell entiende el comando, pero el ejecutable no existe en esa ruta. Comprobala con `Test-Path` y usá la ruta real o el entorno `.venv`. Agregar `&` no corrige una ruta inexistente. |
| `python` no se reconoce, o indica que no se encontró Python y menciona Microsoft Store | Probá `py --version`. Si tampoco funciona, instalá o repará Python y reabrí la terminal. El acceso directo de Windows a Microsoft Store no confirma que haya un intérprete instalado. |
| No se encuentra `.\.venv\Scripts\python.exe` | Comprobá que estás en la carpeta correcta y que creaste `.venv` en esta computadora siguiendo el paso 3. |
| `No module named 'pygame'`, `No module named 'cv2'` u otra dependencia | Repetí el paso 4 y ejecutá el juego con el mismo Python de `.venv`. Instalar paquetes en otro intérprete no los agrega a este entorno. |
| No se encuentra `requirements.txt` o no se puede abrir `main.py` | La terminal está en otra carpeta o la copia del proyecto está incompleta. Volvé al paso 2. |
| Error al activar `Activate.ps1` por la política de ejecución | Esta guía no necesita activar `.venv`: ejecutá directamente `.\.venv\Scripts\python.exe main.py`. |

## Run on macOS/Linux

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Gameplay

- Click GIRAR or press Space to spin. Press 1, 2, or 3 to prepare an equipped skill.
- Match 12 or more copies of a symbol anywhere on the 6x6 board. A spin can have no symbol award.
- Win more when a symbol count reaches 15-17 or 18+.
- Earn gold, points, and XP.
- Unlock worlds and characters.
- Purchase upgrades and skills.
- Prepare up to three active skills. Cooldowns advance on completed paid spins.
- Match your character and pet roles for +5% prizes and +10% XP.
- Visit Taller for permanent upgrades, Mercado for skills/equipment, and Refugio for pets.
- Each paid spin earns travel gold in addition to its prize; the sidebar shows the net balance.

## Slot math

- Fixed base symbol weights are `coin: 27`, `seven: 24`, `joker: 21`, `sixty_nine: 17`, and `sixty_seven: 11` (total 100).
- The Jackpot remains the rarest symbol; existing artwork and names are unchanged.
- Scatter awards use the 12-14, 15-17, and 18+ tiers in `game/scatter.py`. Live draws and refills use `SystemRandom`; deterministic seeds are only used when explicitly requested by a test or offline simulation.
- The base scatter engine targets 96% long-run RTP **before** rounding, character passives, luck, travel gold, charged skills, free spins and equipment. This is not a claim about total RPG gameplay return. `estimate_scatter_rtp()` samples the scatter component alone.
- Cascades stop when no symbol reaches 12, with the existing maximum of 10 cascades. Losing boards are accepted exactly as drawn. Odds are never changed based on bankroll, win/loss history or a running RTP estimate.
- An initial count of exactly 10 or 11 Jackpot symbols shows its real count against the new threshold of 12.
- See [casino mathematics and validation](docs/casino-math.md) for the fixed paytable, independent simulation and integer-rounding effects.

## Testing

```bash
pytest
```

## Balance and artwork

See [the gameplay changes](docs/gameplay-v2.md), [the reproducible income sample](docs/economy-sample.json), and [art prompts](docs/art-prompts.json).

The income sample above records the earlier progression update. Current casino-math reports are `docs/casino-calibration.json` and `docs/casino-validation.json`.

```bash
python tools/simulate_economy.py --spins 1000 --output docs/economy-sample.json
```

World artwork is in `assets/worlds/`; pet portraits are in `assets/pets/`.
World animation runs in Pygame and respects pause and the animation setting.
Old save files are backed up as `saves/save.before-v2.json` before migration;
retired upgrade ranks are refunded once at their historical purchase prices.
