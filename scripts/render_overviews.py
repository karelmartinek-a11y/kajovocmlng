from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'06_UI_OVERVIEWS';out.mkdir(exist_ok=True)
lines=['# Index grafických návrhů','','Kanonické vazby A–L: `01_UI_CONTRACT/ui/contracts/visual-artifact-bindings.json`.','HTML: `03_UI_REFERENCE/pages/dashboard.html` a `generation.html`. PNG jsou odvozené renderem, nikoli druhým zdrojem pravidel.','']
for vp in ['390x844','768x1024','1366x768','1920x1080']:
 for kind,folder,pattern in [('pages','04_UI_VIEWS','*.png'),('dialogs','05_DIALOG_VIEWS','*.png'),('workspace','04_UI_VIEWS','workspace-*.png')]:
  ps=sorted((ROOT/folder/vp).glob(pattern))
  if kind=='pages':ps=[p for p in ps if not p.name.startswith('workspace-')]
  w,h=320,250;sheet=Image.new('RGB',(w*4,((len(ps)+3)//4)*h),'#eef2f5');draw=ImageDraw.Draw(sheet)
  for i,p in enumerate(ps):
   image=Image.open(p).convert('RGB');image.thumbnail((w-12,h-35));x=(i%4)*w;y=(i//4)*h;sheet.paste(image,(x+(w-image.width)//2,y+5));draw.text((x+8,y+h-24),p.stem,fill='#18212d')
  dest=out/f'{kind}-{vp}.png';sheet.save(dest);lines.append(f'- [{kind} · {vp}]({dest.name})')
(out/'VIEW_INDEX.md').write_text('\n'.join(lines)+'\n')
