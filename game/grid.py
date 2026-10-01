from collections import defaultdict
from typing import Dict, List


def find_lines(grid: List[List[str]]) -> List[Dict[str, object]]:
    lines = []
    rows, cols = len(grid), len(grid[0]) if grid else 0

    for r in range(rows):
        run = [{"symbol": grid[r][0], "length": 1, "start": (r, 0), "orientation": "horizontal"}]
        for c in range(1, cols):
            symbol = grid[r][c]
            if run and run[-1]["symbol"] == symbol:
                run[-1]["length"] += 1
            else:
                run.append({"symbol": symbol, "length": 1, "start": (r, c), "orientation": "horizontal"})
        for item in run:
            if item["length"] >= 3:
                lines.append({
                    "orientation": "horizontal",
                    "symbol": item["symbol"],
                    "length": item["length"],
                    "start": item["start"],
                    "end": (r, item["start"][1] + item["length"] - 1),
                })

    for c in range(cols):
        run = [{"symbol": grid[0][c], "length": 1, "start": (0, c), "orientation": "vertical"}]
        for r in range(1, rows):
            symbol = grid[r][c]
            if run and run[-1]["symbol"] == symbol:
                run[-1]["length"] += 1
            else:
                run.append({"symbol": symbol, "length": 1, "start": (r, c), "orientation": "vertical"})
        for item in run:
            if item["length"] >= 3:
                lines.append({
                    "orientation": "vertical",
                    "symbol": item["symbol"],
                    "length": item["length"],
                    "start": item["start"],
                    "end": (item["start"][0] + item["length"] - 1, c),
                })

    diagonals = []
    for start_r in range(rows):
        diagonals.append([(start_r + offset, offset) for offset in range(cols) if start_r + offset < rows])
    for start_c in range(1, cols):
        diagonals.append([(offset, start_c + offset) for offset in range(rows) if start_c + offset < cols])

    for points in diagonals:
        if len(points) < 3:
            continue
        sequence = []
        for r, c in points:
            sequence.append(grid[r][c])
        current = {"symbol": sequence[0], "length": 1, "start": points[0], "orientation": "diagonal"}
        for i in range(1, len(sequence)):
            symbol = sequence[i]
            if current["symbol"] == symbol:
                current["length"] += 1
            else:
                if current["length"] >= 3:
                    lines.append({
                        "orientation": "diagonal",
                        "symbol": current["symbol"],
                        "length": current["length"],
                        "start": current["start"],
                        "end": points[i - 1],
                    })
                current = {"symbol": symbol, "length": 1, "start": points[i], "orientation": "diagonal"}
        if current["length"] >= 3:
            lines.append({
                "orientation": "diagonal",
                "symbol": current["symbol"],
                "length": current["length"],
                "start": current["start"],
                "end": points[-1],
            })

    deduped = []
    seen = set()
    for entry in lines:
        key = (entry["orientation"], entry["symbol"], entry["start"], entry["end"], entry["length"])
        if key not in seen:
            seen.add(key)
            deduped.append(entry)
    return deduped
