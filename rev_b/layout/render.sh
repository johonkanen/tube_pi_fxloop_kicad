#!/bin/bash
# render.sh BOARD OUT.png [LAYERS] [DPI]: one PNG of the board (PDF export, cropped). Board frame: the
# view is from the component side (F, faces the floor); chassis x runs right to left in it.
set -euo pipefail
B=$1; O=$2; LAY=${3:-F.Cu,B.Cu,F.CrtYd,F.Fab,Edge.Cuts,User.Comments}; DPI=${4:-300}
CLI="$(cd "$(dirname "$0")/../.." && pwd)/tools/p2k/bin/kicad-cli"
T=$(mktemp -d)
$CLI pcb export pdf --mode-single --scale 0 -l "$LAY" -o "$T/b.pdf" "$B" >/dev/null 2>&1
pdftoppm -r "$DPI" -png -singlefile "$T/b.pdf" "$T/b"
python3 - "$T/b.png" "$O" <<'PY'
import sys
from PIL import Image, ImageChops
Image.MAX_IMAGE_PIXELS = None
im = Image.open(sys.argv[1]).convert("RGB")
bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
im.crop(bb).save(sys.argv[2])
print(sys.argv[2], im.crop(bb).size)
PY
rm -rf "$T"
