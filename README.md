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

## Run on Windows (PowerShell)

Open the VS Code terminal in the project folder (the one containing `main.py`). If you use Thonny's Python, install the dependencies once and start the game with:

```powershell
& "$env:LOCALAPPDATA\Programs\Thonny\python.exe" -m pip install -r requirements.txt
& "$env:LOCALAPPDATA\Programs\Thonny\python.exe" main.py
```

If `python` is installed and available in your terminal, you can use `python -m pip install -r requirements.txt` and `python main.py` instead. Always start the game from `main.py` so imports from the `game` package work.

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
