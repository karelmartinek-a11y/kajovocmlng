import sys,os
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');O=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
import render_reference
# Effective canonical resources/projections/assets were snapshotted byteexact.
# Outputs exclusively owned; no source/projection mutation or old execution relabel.
render_reference.ROOT=O/'snapshot';render_reference.SSOT=render_reference.ROOT/'00_SSOT/KajovoCMLNG_SSOT.md';render_reference.SCRIPT=render_reference.ROOT/'scripts/render_reference.py'
os.environ['REFERENCE_OUTPUT_ROOT']=str(O/'live-render')
raise SystemExit(render_reference.run())
