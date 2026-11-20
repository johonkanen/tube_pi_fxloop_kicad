#!/usr/bin/env bash
# Re-run every sheet script and fail if a kicad/NN_*.kicad_sch changes (the sheets are generated
# and reproducible: two runs are byte-identical).
set -u
cd "$(dirname "$0")/.."
before=$(md5sum kicad/0?_*.kicad_sch)
for s in tools/sheets/sheet0?.py; do python3 "$s" >/dev/null || exit 1; done
after=$(md5sum kicad/0?_*.kicad_sch)
[ "$before" = "$after" ] || { echo "sheet scripts changed kicad/ (run them and commit):"; diff <(echo "$before") <(echo "$after"); exit 1; }
echo "sheets: $(ls tools/sheets/sheet0?.py | wc -l) scripts reproduce kicad/0?_*.kicad_sch"
