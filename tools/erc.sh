#!/usr/bin/env bash
# ERC of the project schematic; fails on ERC errors and on footprint_link_issues warnings (a
# Footprint field that names a missing library / footprint, e.g. without kicad/fp-lib-table);
# other warnings are listed only.
# Full report: reports/erc.rpt
set -u
cd "$(dirname "$0")/.."
mkdir -p reports
tools/p2k/bin/kicad-cli sch erc --severity-all -o reports/erc.rpt kicad/tube_pi_fxloop.kicad_sch >/dev/null || exit 1
errs=$(grep -c '; error' reports/erc.rpt)
warns=$(grep -c '; warning' reports/erc.rpt)
echo "erc: $errs errors, $warns warnings (reports/erc.rpt)"
links=$(grep -c "footprint_link_issues" reports/erc.rpt)
[ "$links" -eq 0 ] || echo "erc: $links footprint_link_issues (Footprint fields vs fp-lib-table)"
[ "$errs" -eq 0 ] && [ "$links" -eq 0 ]
