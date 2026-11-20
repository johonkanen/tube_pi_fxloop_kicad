# tools/generate/ - frozen history, do not run

**The board is no longer generated** (user decision 2026-11-20, STATUS.md "Generation stopped
2026-11-20"). Since then the committed KiCad files are the source and are edited in KiCad:
`kicad/*.kicad_sch`, `kicad/tube_pi_fxloop.kicad_pcb`, `kicad/fp-lib-table`, `lib/tube_pi_fxloop.kicad_sym`,
`lib/tube_pi_fxloop.pretty/`, `lib/footprint_map.csv`, `lib/part_map.csv`.

These scripts produced those files from the Proteus data (last run byte-identical at commit 116d923,
moved here unchanged except for their paths). They are kept as the record of how the rev A files were
made and what was decided in them (comments, RULES / PROJECT specs). **Running any of them overwrites
the hand edits** and is never part of the workflow:

| Script | Wrote |
|---|---|
| `make_part_map.py` | `lib/part_map.csv` |
| `gen_symbols.py` | `lib/tube_pi_fxloop.kicad_sym` |
| `sheets/sheet0[1-4].py` (`_common.py`) | `kicad/*.kicad_sch` |
| `gen_footprints.py` | `lib/tube_pi_fxloop.pretty/`, `lib/footprint_map.csv`, `kicad/fp-lib-table` |
| `make_pcb.sh` | `kicad/tube_pi_fxloop.kicad_pcb` (refuses unless `--force-regenerate`) |

One script is still **imported** (never run) by a check: `p2k check_pin_order` reads `RULES` / `PROJECT`
from `gen_footprints.py` (`FOOTPRINT_SCRIPT` in `p2k_config.py`). Keep it importable.

`tools/check_all.sh` does not call any of them; it verifies the committed files against the Proteus
truth (`reference/`, `source/`) and KiCad's rules.
