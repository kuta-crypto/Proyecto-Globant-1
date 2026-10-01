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

## Play on Windows with the executable (.exe)

The file to share is **`dist/TimbaRNG.exe`**. It includes Python, dependencies, and game assets. The destination computer does not need Python, Thonny, or VS Code installed, or copies of `.venv` or `assets/`.

1. Copy `TimbaRNG.exe` to the other 64-bit Windows PC.
2. Double-click it. Startup may take a few seconds while it extracts resources to a temporary folder.
3. Saved games and settings are stored per user in `%LOCALAPPDATA%\TimbaRNG\saves\save.json`. Open this folder by pasting `%LOCALAPPDATA%\TimbaRNG\saves` into the File Explorer address bar.

To transfer a saved game from the Python version, close the game and copy your `saves/save.json` file into that folder. If a save from the `.exe` version already exists, back it up before replacing it. Sharing the executable does not share your saved games.

### Rebuild the executable after modifying the game

These steps are for the person building the game; anyone receiving the `.exe` does not need to run them. Build on Windows using 64-bit Python. If `.venv` does not exist yet, create it using the instructions below.

From the project folder:

```powershell
.\build_exe.ps1
```

The script installs `requirements-build.txt` and generates `dist/TimbaRNG.exe` with [PyInstaller](https://pyinstaller.org/en/stable/usage.html). If PowerShell blocks the script because of its execution policy, you can run its two main commands directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name TimbaRNG --add-data "assets:assets" --exclude-module pytest main.py
```

Wait for the build to finish without errors. Close any running instance of the executable before rebuilding. Each build replaces `dist/TimbaRNG.exe`; saved games remain outside the bundle. `build/` and `TimbaRNG.spec` are build files and do not need to be distributed. This build targets Windows; it does not produce a macOS or Linux application.

## Install and run on Windows (PowerShell)

These steps apply to both this PC and another Windows computer. Run the commands in a **PowerShell** terminal, for example through **Terminal > New Terminal** in VS Code. Copy only the commands inside the code blocks, one line at a time, without Markdown markers or the terminal's `PS C:\...>` prompt.

### 1. Install Python

If the computer does not have Python yet, install Python 3 for Windows from the official Python website. If the installer offers **Add Python to PATH**, select that option. Then close and reopen the terminal so it recognizes the installation.

Check that it works:

```powershell
python --version
```

It should display a Python 3 version. If `python` is not recognized or you see a Microsoft Store message, try:

```powershell
py --version
```

If `py` works, use `py` instead of `python` when creating the environment in step 3. If neither works, complete or repair the Python installation before continuing. Thonny and VS Code are optional for running the game.

### 2. Copy the project and open its folder

Copy or download the entire project. If it comes in a ZIP file, extract it before running it. Keep the folder structure intact: you need `main.py`, `requirements.txt`, `game/`, `assets/`, and the other project files. Copying only `main.py` is not enough.

**Do not copy `.venv` from another PC:** the virtual environment contains paths and executables specific to the computer where it was created. Create a new one on each computer. You do not need to copy `__pycache__` folders either. To keep your progress, also copy `saves/` if it exists.

In VS Code, open the folder containing `main.py`, then open a PowerShell terminal. You can also navigate there from an existing terminal using `cd`; replace this example path with the actual project location:

```powershell
cd "C:\path\to\project"
```

To check that you are in the correct folder:

```powershell
Get-Item .\main.py, .\requirements.txt
```

If either file cannot be found, switch to the correct folder before continuing.

### 3. Create a virtual environment (once per computer)

The `.venv` environment keeps Python and the project's dependencies separate from other projects.

```powershell
python -m venv .venv
```

If `py` worked instead of `python` in step 1, use this alternative:

```powershell
py -m venv .venv
```

Use only one of these options. If you already have a working `.venv` created on this PC, you can reuse it. Check its interpreter with:

```powershell
.\.venv\Scripts\python.exe --version
```

### 4. Install dependencies

From the same project folder, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Wait for the command to finish without errors. This installs the dependencies listed in `requirements.txt` into `.venv`. Run it during initial setup and again if that file changes or you recreate the environment.

The command `python -m pip install -r requirements.txt` also installs dependencies, but uses whichever Python the terminal resolves. The commands in this guide explicitly target `.venv` so installation and execution use the same interpreter.

### 5. Start the game

```powershell
.\.venv\Scripts\python.exe main.py
```

**Use this command every time you want to play**, from the project folder. You do not need to activate the virtual environment or reinstall dependencies each time. Always start the game from `main.py` so imports from the `game` package work correctly.

### Quick setup on a new PC

With Python installed and the terminal in the folder containing `main.py`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

If your installation responds to `py`, replace only `python` on the first line with `py`.

### Alternative: use Thonny's Python

Use this option only if Thonny is installed and you know the path to its `python.exe`. The location depends on how it was installed and is not the same on every computer.

Check this example location with:

```powershell
Test-Path "$env:LOCALAPPDATA\Programs\Thonny\python.exe"
```

Only if it returns `True`, you can use:

```powershell
& "$env:LOCALAPPDATA\Programs\Thonny\python.exe" -m pip install -r requirements.txt
& "$env:LOCALAPPDATA\Programs\Thonny\python.exe" main.py
```

If it returns `False`, that path does not exist: follow the `.venv` instructions or replace the path with the interpreter's actual location. If Thonny is configured with the interpreter you want to use, you can find its path by running `import sys; print(sys.executable)` in Thonny's shell.

### Troubleshooting common errors

| Error or symptom | Cause and solution |
| --- | --- |
| `Unexpected token 'main.py'` | In PowerShell, a quoted executable path requires the `&` operator before it. Example: `& "C:\path\to\python.exe" main.py`. Include the leading `&` when copying the command. |
| `The term '...Thonny\python.exe' is not recognized` | PowerShell understands the command, but the executable does not exist at that path. Check it with `Test-Path` and use the actual path or the `.venv` environment. Adding `&` does not fix a nonexistent path. |
| `python` is not recognized, or a message says Python was not found and mentions Microsoft Store | Try `py --version`. If that does not work either, install or repair Python and reopen the terminal. The Windows shortcut to Microsoft Store does not confirm that an interpreter is installed. |
| `.\.venv\Scripts\python.exe` cannot be found | Check that you are in the correct folder and created `.venv` on this computer by following step 3. |
| `No module named 'pygame'`, `No module named 'cv2'`, or another missing dependency | Repeat step 4 and run the game with the same Python from `.venv`. Installing packages into another interpreter does not add them to this environment. |
| `requirements.txt` cannot be found or `main.py` cannot be opened | The terminal is in another folder or the project copy is incomplete. Return to step 2. |
| Execution policy error when running `Activate.ps1` | This guide does not require activating `.venv`: run `.\.venv\Scripts\python.exe main.py` directly. |

## Run on macOS/Linux

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Gameplay

- Click the spin button or press Space to spin. Press 1, 2, or 3 to prepare an equipped skill.
- Match 12 or more copies of a symbol anywhere on the 6x6 board. A spin can have no symbol award.
- Win more when a symbol count reaches 15-17 or 18+.
- Earn gold, points, and XP.
- Unlock worlds and characters.
- Purchase upgrades and skills.
- Prepare up to three active skills. Cooldowns advance on completed paid spins.
- Match your character and pet roles for +5% prizes and +10% XP.
- Visit the workshop for permanent upgrades, the market for skills/equipment, and the shelter for pets.
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
