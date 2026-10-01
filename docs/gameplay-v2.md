# Visual and progression update

> Historical balance notes from the visual/progression update. The later [casino mathematics update](casino-math.md) supersedes the scatter weights, paytable, threshold, base bonus thresholds and income sample below. The progression systems and artwork are unchanged.

## Art and presentation

Five original world backgrounds and 25 individual pet portraits use anime linework and simple cel shadows. Generated with the built-in image tool, then copied into this project. Existing character portraits are retained.

World backgrounds are animated in real time: drifting dust in Timba Central, rain and passing light in Metro Neon, leaves and fireflies in Bosque Jade, rising embers in Casino Obsidiana, and stars and meteors in Galaxia Dorada. A gentle camera drift accompanies the ambient effects. Pause freezes them, and disabling animations stops movement. These are layered Pygame scenes, not video files.

The shop, collection, inventory, character mastery, world selector and upgrade screens share a slate, jade and warm gold palette. Skills and equipment use a small native icon set. Pet filters and pagination keep all 25 companions accessible. The game shows the active character, pet, charges, equipped skills and a gold breakdown.

## Characters, pets and skills

- Eight characters unlock at levels **1, 4, 8, 12, 18, 24, 32 and 40**. Each has a passive and a charged skill.
- Character mastery ranges from 1 to 5. Training costs `300 * current_rank²` points. Each rank adds 15% of the base strength to bonuses, up to +60%. Free-spin counts remain whole and are not multiplied.
- Every pet has a distinct passive/charged skill pair. Pet charge advances only while that pet participates in a paid spin. Changing pets preserves individual charge.
- The first copy starts bond rank 1. Every two duplicates raises it by one, up to rank 5. Each duplicate also returns 100 points.
- Matching character and pet roles adds **5% prizes and 10% XP**.
- 12 active skills are available. Equip up to three; prepare them by clicking or pressing **1 / 2 / 3**. Prepared skills persist across saves. Their cooldowns run on subsequent completed paid spins, not real time; waiting in menus cannot recharge them.
- Six equipment slots have two alternatives each. Equipping an alternative replaces the previous piece's effect, while both pieces stay owned.

## Gold and progression

New games start with **100 gold**, with a default wager of 10. Each paid spin grants **6 / 8 / 10 / 12 / 14 travel gold**, depending on world. World unlock levels are **1 / 8 / 18 / 30 / 45**. Free spins do not grant travel gold or charge companions. A natural bonus retrigger during a free spin adds one spin; an actively prepared VIP skill still grants its full bonus.

Common scatter rewards have been raised and extremely rare awards reduced. The paytable in `game/scatter.py` is scaled by 0.37; regular prizes no longer rely on an exceptionally rare jackpot to offset many zero payouts. Gold prizes and refunds round down once at settlement. Bet discounts reduce the amount paid while keeping the original wager as the reward basis.

Bonus percentages of the same type are additive within the build. World and free-spin multipliers apply after these bonuses. Refunds are capped at 80% of the gold actually paid. The travel stipend and fixed charged-skill gold are separate from scatter prizes, and the game displays them separately.

Upgrade costs are stable, rather than increasing when the wallet grows: `round(base * (1 + 0.5 * rank + 0.10 * rank²))`. Entry costs range from 12 to 45 gold. The interface shows each next effect and the cost as a percentage of the current balance. Multi-buy spends at most **25% of the balance at the start of the purchase**, keeping the remainder available for playing.

| Track | Ranks | Effect per rank |
| --- | ---: | --- |
| Spin speed | 8 | -0.10 seconds |
| Luck | 10 | +1 luck |
| Bonus | 8 | +1 bonus level |
| Points | 10 | +8% points |
| XP | 10 | +8% XP |
| Prizes | 12 | +3% prizes |
| Jackpot | 8 | +12% jackpot |
| Bet discount | 5 | -2% cost |
| Bonus spins | 3 | +1 spin per paid-spin bonus trigger |
| Rescue | 8 | +2 emergency gold |

## Reproducible check

`python tools/simulate_economy.py --spins 1000 --seed 20260929` uses an isolated headless game, without reading or writing the user's save. In the recorded sample, Oliva in world 1, wager 10 and no upgrades/equipment/pet, completed **1000 paid spins and 40 free spins**, finishing at **7632 gold** from an initial 100. Median scatter prize was **8 gold**; none of the 1040 spins had a zero scatter prize. Net gain averaged **7.532 gold per paid spin**, including travel gold, the character's charged skill and free rounds.

At that sample's income rate, an entry upgrade represents roughly 2-6 paid spins. Basic active skills start at 35 gold and basic equipment at 45. This is a fixed-seed baseline, not a guarantee for each run or a full equilibrium analysis of every late-game build. Further tuning can use the committed sampler.

## Save compatibility

Before the first old-save migration, a backup is created at `saves/save.before-v2.json`. Owned characters, pets, equipment and skills are retained. Previously purchased upgrade ranks above new caps are refunded at historical prices. A version marker prevents a second refund. Up to three previously equipped skills remain equipped; the others stay owned. Legacy time-based cooldowns reset during migration.

The update is covered by automated checks for payouts, all 12 skills, companion charge, mastery and bond scaling, equipment replacement, purchase budgets, save restoration, migration, asset completeness, and UI button bounds. Screenshots in `docs/previews/` were rendered with Pygame's headless driver for visual inspection.
