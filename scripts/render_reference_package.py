"""Render original administrative/dialog references and rebuild their overview sheets."""
import json,os,functools,http.server,threading,hashlib
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
from playwright.sync_api import sync_playwright
from ssot_sources import ROOT


def run():
    viewports=['390x844','768x1024','1366x768','1920x1080']
    checks=[]
    source=(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    origin='http://127.0.0.1:'+str(server.server_port)
    with sync_playwright() as p:
        browser=p.chromium.launch(**({"executable_path":os.environ["CHROMIUM_PATH"]} if os.environ.get("CHROMIUM_PATH") else {}))
        for group,output_dir in [('pages','04_UI_VIEWS'),('dialogs','05_DIALOG_VIEWS')]:
            paths=[f for f in sorted((ROOT/'03_UI_REFERENCE'/group).glob('*.html')) if not f.stem.startswith('live-') and not f.stem.endswith('-en')]
            for viewport in viewports:
                width,height=map(int,viewport.split('x'))
                page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce')
                tiles=[]
                for path in paths:
                    page.goto(origin+'/'+path.relative_to(ROOT).as_posix());page.wait_for_load_state('networkidle')
                    output=ROOT/output_dir/viewport/(path.stem+'.png');output.parent.mkdir(parents=True,exist_ok=True)
                    page.screenshot(path=str(output),full_page=True)
                    overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth')
                    checks.append({'source':path.relative_to(ROOT).as_posix(),'viewport':viewport,'render':output.relative_to(ROOT).as_posix(),
                                   'horizontalOverflow':overflow,'status':'FAIL' if overflow else 'PASS','visualInspection':'PENDING'})
                    with Image.open(output) as im:
                        thumb=ImageOps.contain(im.convert('RGB'),(360,470));tile=Image.new('RGB',(380,505),'#e9eef2')
                        tile.paste(thumb,((380-thumb.width)//2,25));ImageDraw.Draw(tile).text((10,7),path.stem,fill='#18212d');tiles.append(tile)
                sheet=Image.new('RGB',(4*380,((len(tiles)+3)//4)*505),'white')
                for index,tile in enumerate(tiles):sheet.paste(tile,((index%4)*380,(index//4)*505))
                sheet.save(ROOT/'06_UI_OVERVIEWS'/(group+'-'+viewport+'.png'));page.close()
        browser.close()
    server.shutdown();server.server_close();thread.join()
    assert source==(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes(), 'SSOT_INPUT_CHANGED'
    result={'sourceDocumentSha256':hashlib.sha256(source).hexdigest(),'scope':'Administrative and dialog presentation references; not a backend test.','checks':checks}
    (ROOT/'audit/generated/reference-package-renders.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'renders':len(checks),'overflowFailures':sum(c['horizontalOverflow'] for c in checks)}))
    return result


if __name__=='__main__':run()
