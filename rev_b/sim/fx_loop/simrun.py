"""ngspice helper for the rev B FX loop runs."""
import os
import re
import subprocess
import tempfile

import numpy as np


def run(net, ctl):
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, 'x.cir'), 'w').write(net + '\n.control\n' + ctl + '\n.endc\n.end\n')
        r = subprocess.run(['ngspice', '-b', 'x.cir'], cwd=d, capture_output=True, text=True, timeout=600)
        files = {f: np.loadtxt(os.path.join(d, f)) for f in os.listdir(d) if f.endswith('.txt')}
    out = r.stdout + r.stderr
    vals = dict((k.lower(), float(v)) for k, v in re.findall(r'^(\w+)\s*=\s*([-+0-9.eE]+)', out, re.M))
    thd = [float(x) for x in re.findall(r'THD:\s*([-+0-9.eE]+)', out)]
    return vals, files, thd, out
