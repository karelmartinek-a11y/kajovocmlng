"""Build the single navigation index for all actual reference HTML files."""
import html
import re
from ssot_sources import ROOT


def build():
    directory=ROOT/'03_UI_REFERENCE'
    groups=[]
    for group in ('pages','dialogs'):
        links=[]
        for path in sorted((directory/group).glob('*.html')):
            source=path.read_text(encoding='utf-8')
            match=re.search(r'<title>(.*?)</title>',source,re.S)
            title=html.unescape(match[1]) if match else path.stem
            locale='EN' if path.stem.endswith('-en') else 'CS / source reference'
            links.append(f'<a href="{group}/{path.name}"><strong>{html.escape(title)}</strong><small>{locale} · {html.escape(path.stem)}</small></a>')
        groups.append('<section><h2>'+('Pohledy / Views' if group=='pages' else 'Dialogy / Dialogs')+'</h2><div class="grid">'+''.join(links)+'</div></section>')
    page='''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KájovoCMLNG — UI reference</title><style>
body{margin:0;background:#f4f6f8;color:#18212d;font:15px "Segoe UI",sans-serif}header{padding:28px 5vw;background:#111923;color:white}main{padding:24px 5vw}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:12px}a{padding:16px;background:white;border:1px solid #dfe4ea;border-radius:6px;color:#18212d;text-decoration:none}a:focus-visible,a:hover{outline:2px solid #007f7a}small{display:block;color:#647181;margin-top:8px}p{max-width:900px;line-height:1.6}.notice{background:#fff2cc;padding:12px;color:#634b00}section{margin-bottom:32px}</style></head><body><header><h1>KájovoCMLNG · UI reference</h1><p>Index skutečných HTML podkladů. Vazby na kanonické funkce a stavy uvádějí matice v 01_UI_CONTRACT.</p></header><main><p class="notice">UKÁZKOVÁ DATA / SAMPLE DATA. Návrhy rozhraní nejsou připojené k provoznímu backendu. Přítomnost pohledu není důkazem jeho úplné validace; rozhoduje audit.</p>'''+''.join(groups)+'''<p><a href="../audit/FINAL_AUDIT.md">Audit</a> <a href="../README_CZ.md">Vstupní index SSOT</a></p></main></body></html>'''
    (directory/'index.html').write_text(page,encoding='utf-8',newline='\n')
    print('Reference index regenerated')


if __name__=='__main__':build()
