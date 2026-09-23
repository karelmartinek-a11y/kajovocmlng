"""Generate and render illustrative UI surfaces from canonical view records."""
import argparse
import html
import json
from pathlib import Path
from ssot_sources import ROOT, load_resource
from reference_localization import localize


def generate():
    c=json.loads(load_resource('ui/contracts/live-experience.json')['raw']); m=c['messages']
    def text(k): return html.escape(m[k]['cs'])
    def button(key,extra=''): return f'<button {extra}>{text("ui."+key)}</button>'
    nav=[('chat','Centrální chat'),('dashboard','Dashboard'),('generation','Generování'),('agents','AI agenti'),('mcp','MCP servery a nástroje'),('browser','Browser automatizace'),('registered','Registrované prvky'),('components','Katalog komponent'),('external','Externí systémy'),('monitoring','Monitoring'),('runtime-access','API a runtime vazby'),('secrets','Secrets a hesla'),('audit','Audit a logy'),('configuration','Konfigurace'),('tests-api','Testy a API'),('security','Bezpečnost'),('releases','Releases a provoz')]
    links=''.join(f'<a href="{p}.html" class="{"active" if p=="dashboard" else ""}">{s}</a>' for p,s in nav)
    menu='<div class="menu">'+''.join(button(k,'role="menuitem"') for k in ['details','start','stop','restart','edit','history','inputs','files','secrets','chat'])+'<hr>'+button('delete','role="menuitem" class="danger"')+'</div>'
    graph='''<div class="graph" tabindex="0" aria-label="Ukázková topologie. Shift F10 otevře nabídku objektu."><svg viewBox="0 0 640 280" role="img" aria-label="Příjem e-mailu propojený s AI agentem a evidencí zakázek"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0 0L7 3L0 6" fill="#70aaa7"/></marker></defs><g class="topology-content"><path class="edge" d="M195 125C240 125 220 125 265 125" marker-end="url(#arrow)"/><path class="edge" d="M435 125C480 125 455 125 500 125" marker-end="url(#arrow)"/><path class="edge" d="M348 162C348 211 200 210 180 210" marker-end="url(#arrow)"/><rect x="28" y="85" width="170" height="78" rx="6" class="node"/><text x="43" y="108" class="node-meta">VSTUP · E-MAIL</text><text x="43" y="130" class="node-title">Příjem poptávek</text><text x="43" y="149" class="node-meta">✓ Připraveno</text><rect x="265" y="85" width="170" height="78" rx="6" class="node selected"/><text x="280" y="108" class="node-meta">AI AGENT</text><text x="280" y="130" class="node-title">Zpracování poptávky</text><text x="280" y="149" class="node-meta">◷ Čeká na odpověď</text><rect x="500" y="85" width="120" height="78" rx="6" class="node"/><text x="513" y="108" class="node-meta">WEBOVÁ SLUŽBA</text><text x="513" y="130" class="node-title">Evidence</text><text x="513" y="149" class="node-meta">✓ Dostupná</text><rect x="28" y="190" width="152" height="55" rx="6" class="node"/><text x="43" y="213" class="node-title">Potvrzení zákazníkovi</text><text x="43" y="230" class="node-meta">VÝSTUP · E-MAIL</text><circle cx="469" cy="125" r="5" class="particle"/><text x="274" y="60" class="node-meta">Ukázka zachyceného požadavku →</text></g></svg><div class="mobile-nodes"><button data-help="Vstup přijímá e-maily a přílohy pro zpracování poptávky.">Příjem poptávek <small>Vstup · e-mail · připraveno</small></button><span>↓</span><button data-help="Agent zpracuje poptávku a požádá evidenci o uložení zakázky.">Zpracování poptávky <small>AI agent · čeká na odpověď</small></button><span>↓</span><button data-help="Externí webová služba ukládá zakázky.">Evidence zakázek <small>Webová služba · dostupná</small></button><span>↓</span><button data-help="Potvrzení se odešle až po ověření výsledku.">Potvrzení zákazníkovi <small>Výstup · e-mail</small></button></div><div class="graph-controls"><button data-zoom="in" aria-label="Přiblížit graf">+</button><button data-zoom="out" aria-label="Oddálit graf">−</button><button data-zoom="fit">Celý graf</button></div><div class="minimap" aria-label="Minimapa"><svg viewBox="0 0 90 48"><path d="M15 15H75M45 15L18 36" stroke="#70aaa7" fill="none"/><g fill="#007f7a"><rect x="7" y="10" width="15" height="10"/><rect x="38" y="10" width="15" height="10"/><rect x="69" y="10" width="15" height="10"/><rect x="7" y="30" width="20" height="10"/></g></svg></div><div class="sample-menu" role="menu">'''+menu+'''</div></div>'''
    graph=graph.replace('<span>↓</span><button data-help="Potvrzení', '<span>↳ Zpracování poptávky → výstup</span><button data-help="Potvrzení')
    detail=f'''<div class="card"><div class="cardhead"><h2>Zpracování poptávky</h2><span class="tag">AI agent</span></div><div class="pad"><p class="subtle">Z e-mailu připraví zakázku a ověří její uložení ve webové evidenci.</p><dl class="kv"><dt>Objekt</dt><dd>KCML0042</dd><dt>Poslední běh</dt><dd>Ukázka #1048 · před 2 minutami</dd><dt>Vstup</dt><dd>E-mail a přílohy</dd><dt>Výstup</dt><dd>Zakázka a potvrzení</dd><dt>Připojení</dt><dd>Evidence zakázek · účet OWNER</dd></dl><div class="toolbar">{button('details')}{button('history')}{button('secrets')}</div></div></div>'''
    chat=f'''<div class="card"><div class="cardhead"><h2>Chat v kontextu objektu</h2><span class="tag">KCML0042</span></div><div class="pad"><p>„Proč poslední zpracování poptávky trvalo déle?“</p><p class="subtle">Odpověď musí odkazovat na konkrétní běh a jeho časové údaje.</p>{button('chat','class="primary wide"')}</div></div>'''
    timeline='''<div class="card"><div class="cardhead"><h2>Co se právě děje</h2><span class="tag">Ukázka běhu #1048</span></div><div class="pad"><ul class="timeline"><li><time>14:32:08</time><div><strong>✓ Přijal jsem e-mail s poptávkou.</strong><small>Vstupní zpráva · ukázkový záznam E-201</small></div></li><li><time>14:32:09</time><div><strong>✓ Zkontroloval jsem potřebné údaje.</strong><small>Zákazník, položky a příloha jsou dostupné.</small></div></li><li><time>14:32:10</time><div><strong>→ Odeslal jsem požadavek do evidence zakázek.</strong><small>Čekám na potvrzení; výsledek zatím není známý.</small></div></li></ul></div></div>'''
    outputs=[]
    for view in c['views']:
        id=view['id']; title=text(view['titleKey']); state=view['state']
        steps=['Zadání','Kontrola údajů','Odeslání','Ověření výsledku','Uložení','Dokončení']
        active_index=1 if id=='human-wait' else 2
        if id=='human-wait':steps[1]='Přihlášení'
        stephtml=''.join(f'<div class="step {"done" if i<active_index or (i==2 and id=="failure") else "failed" if i==3 and id=="failure" else "current" if i==active_index else ""}"><b>{"✓" if i<active_index or (i==2 and id=="failure") else i+1}</b>{s}</div>' for i,s in enumerate(steps))
        notice='Odeslal jsem požadavek do evidence zakázek a čekám na odpověď. Další krok začne po jejím přijetí.'
        if id=='failure': notice='Evidence zakázek neodpověděla včas. Nejprve ověřím, zda zakázku uložila; opakováním by mohla vzniknout dvakrát.'
        if id=='human-wait': notice='Webová evidence požaduje ověřovací kód. Převezměte prohlížeč a dokončete přihlášení.'
        help_button=button("help", 'data-help="Každý krok zobrazuje potvrzený stav programu. Délka čáry ani pohyb nevyjadřují procento dokončení."')
        process=f'<div class="card"><div class="cardhead"><h2>Průběh operace</h2>{help_button}</div><div class="process">{stephtml}</div><div class="note {"error" if id=="failure" else "warning" if id=="human-wait" else ""}">{notice}</div></div>'
        menu_button=button("menu", 'data-menu aria-expanded="false" aria-haspopup="menu"')
        topology=f'<div class="card"><div class="cardhead"><h2>Vazby a komponenty</h2>{menu_button}</div>{graph}<div class="legend"><span><i class="dot"></i>Uživatelsky spravovaný objekt</span><span>→ Směr požadavku</span><span>✓ Potvrzený stav</span></div></div>'
        main=topology+process+timeline; side=detail+chat
        if id=='process': main=process+timeline+topology
        if id=='context-menu': side='<div class="card"><div class="cardhead"><h2>Akce vybraného objektu</h2></div>'+menu+'</div>'+chat
        if id=='dashboard-empty':
            main='<div class="card empty"><div class="symbol">◇</div><h2>Začněte požadovaným výsledkem</h2><p>Popište, co má váš systém dělat.<br>Komponenty a jejich propojení navrhne KájovoCML NG.</p>'+button('chat','class="primary"')+'</div>'
            side=chat.replace('Chat v kontextu objektu', 'Centrální chat').replace('KCML0042', 'Návrh systému').replace('„Proč poslední zpracování poptávky trvalo déle?“', '„Chci automaticky zpracovat příchozí poptávky.“').replace('Odpověď musí odkazovat na konkrétní běh a jeho časové údaje.', 'Společně upřesníme vstupy, požadovaný výsledek a potřebná propojení.')
        if id=='dashboard-stale': main='<div class="note warning">Spojení s událostmi je přerušené. Poslední potvrzený stav: 14:32:10. Provozní animace jsou zastavené; zkouším obnovit spojení.</div>'+topology+timeline
        if id=='object-detail': main=detail+process+timeline; side=chat
        if id=='inputs-outputs':
            main='<div class="card"><div class="cardhead"><h2>Vstupní e-mail</h2><span class="tag">Ukázkový obsah</span></div><div class="pad"><h3>Poptávka · 3 pracovní stanice</h3><p>Prosím o nabídku tří pracovních stanic a termínu dodání.</p><div class="chips"><span class="tag">polozky.xlsx · list Poptávka</span><span class="tag">zadani.txt</span></div></div></div><div class="card"><div class="cardhead"><h2>Tabulková příloha</h2>'+button('copy')+'</div><div class="table-wrap"><table><thead><tr><th>Položka</th><th>Počet</th><th>Jednotka</th></tr></thead><tbody><tr><td>Pracovní stanice</td><td>3</td><td>ks</td></tr><tr><td>Monitor</td><td>6</td><td>ks</td></tr></tbody></table></div><div class="pad subtle">Hodnoty jsou náhled. Vzorce ani makra se nespouštějí.</div></div><div class="card"><div class="pad"><h2>Výstup</h2><p>Zakázka Z-1048 · ověřeno ve webové evidenci.</p>'+button('evidence')+'</div></div>';side=detail+chat
        if id=='live-communication':
            main=topology+'<div class="card"><div class="cardhead"><h2>Události vybrané vazby</h2><span class="tag">Ukázka · 7 typů</span></div>'+''.join(f'<div class="event-row"><span>{a}</span><span class="subtle">{b}</span></div>' for a,b in [('→ Požadavek odeslán','request'),('← Odpověď přijata','response'),('◇ Změna oznámena','event'),('◷ Výsledek se ověřuje','processing'),('✓ Výsledek potvrzen','success'),('△ Je potřeba pozornost','warning'),('× Operace selhala','failure')])+'</div>';side=detail+chat
        if id=='failure': main=process+'<div class="card"><div class="pad"><h2>Výsledek ještě není bezpečně potvrzený</h2><p>Opakování je pozastavené, dokud se neověří účinek předchozího požadavku.</p><dl class="kv"><dt>Běh</dt><dd>Ukázka #1048</dd><dt>Kód</dt><dd>SIDE_EFFECT_OUTCOME_UNKNOWN</dd></dl>'+button('history')+' '+button('start','aria-disabled="true" data-help="Nejdříve je nutné zjistit, zda předchozí požadavek zakázku vytvořil."')+'</div></div>'+timeline
        if id=='human-wait':main=process+'<div class="card"><div class="cardhead"><h2>Přihlášení do evidence zakázek</h2><span class="tag warn">Čeká na vás</span></div><div class="pad"><div class="browser"><div class="subtle">Ukázková externí služba · zabezpečená relace</div><div class="login"><h3>Ověření přihlášení</h3><p>Zadejte kód z autentizační aplikace.</p><div class="code">······</div></div></div><div class="toolbar" style="margin-top:16px">'+button('takeover','class="primary"')+button('resume','aria-disabled="true" data-help="Nejdříve dokončete přihlášení a ověření aktuální relace."')+'</div></div></div>'
        if id=='multi-component':main=topology+'<div class="card"><div class="cardhead"><h2>Výroba a propojení celku</h2><span class="tag">3 komponenty</span></div><div class="table-wrap"><table><thead><tr><th>Komponenta</th><th>Závislost</th><th>Stav</th></tr></thead><tbody><tr><td>Příjem poptávek</td><td>Společný kontrakt v1</td><td>✓ Ověřena</td></tr><tr><td>Zpracování poptávky</td><td>Příjem + Evidence</td><td>◷ Integrace</td></tr><tr><td>Webový konektor Evidence</td><td>Společný kontrakt v1</td><td>✓ Ověřen</td></tr></tbody></table></div><div class="pad subtle">Celek nebude označen jako dokončený, dokud neprojde společná zkouška propojení.</div></div>'+process
        if id=='specification':
            main='<div class="card"><div class="cardhead"><h2>Zadání · revize 7</h2><span class="tag warn">Rozpracováno</span></div><div class="pad editor"><label for="goal">Požadovaný výsledek</label><textarea id="goal">Z příchozího e-mailu vytvořit ověřenou zakázku a odeslat zákazníkovi potvrzení.</textarea><label for="role">Role vybrané komponenty</label><input id="role" value="Zpracovat poptávku a řídit její předání"><label for="input">Vstup</label><input id="input" value="E-mail, přílohy a společný kontrakt Poptávka v1"><label for="output">Výstup</label><input id="output" value="Ověřená zakázka a potvrzovací e-mail"><div class="toolbar" style="margin-top:18px">'+button('review','class="primary"')+button('approve','aria-disabled="true" data-help="Nejdříve dokončete kontrolu této přesné revize a vyřešte všechny povinné blokery."')+'</div></div></div><div class="card"><div class="cardhead"><h2>Dopad připravené změny</h2></div><div class="pad impact"><div><b>2</b>dotčené komponenty</div><div><b>1</b>společný kontrakt</div><div><b>3</b>opakované kontroly</div></div><div class="note">Schválená revize 6 se nemění. Generování této úpravy bude vyžadovat schválení revize 7.</div></div>';side=chat+'<div class="card"><div class="pad"><h2>Schvalovací postup</h2><p>1. Rozpracováno<br>2. Zkontrolováno<br>3. Schváleno k výrobě</p><p class="subtle">Každá obsahová změna vytváří novou revizi a znovu vyhodnotí závislosti.</p></div></div>'
        page=f'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · KájovoCML NG</title><link rel="stylesheet" href="../assets/live.css"></head><body class="{'stale' if id=='dashboard-stale' else ''}" data-view="{id}" data-state="{state}" data-demo="true"><div class="demo">{text('ui.demo')}</div><div class="shell"><aside class="sidebar"><div class="brand"><img src="../../02_BRAND/logo-kajovocml-ng-mark.svg" alt=""><div><strong>KájovoCML NG</strong><small>CLARITY INTO COMPLEXITY</small></div></div><nav aria-label="Hlavní navigace">{links}</nav><div class="meta">Jeden systém · jeden přehled<br>Ukázkový prostor OWNER</div></aside><main class="workspace"><header class="topbar"><span class="crumb">Pracovní plocha / Poptávky a zakázky</span><span class="avatar" aria-label="OWNER">K</span></header><div class="content"><div class="heading"><div><h1>{title}</h1><div class="subtle">Poptávky a zakázky · vše potřebné v kontextu objektu</div></div><div class="toolbar">{button('chat')}{button('help','aria-label="Nápověda pracovní plochy"')}</div></div><div class="layout"><section>{main}</section><aside class="side">{side}</aside></div><footer class="bottom"><span>Ukázka DEMO-SYSTEM-001 · nikoli skutečný provoz</span><span>Kontrakt {html.escape(view['id'])}</span></footer></div></main></div><dialog class="help-dialog" aria-labelledby="dialog-title"><h2 id="dialog-title">Vysvětlení návrhu</h2><p></p><button data-close>Zavřít</button></dialog><script src="../assets/live.js"></script></body></html>'''
        demo_explanation='Ukázkový návrh: tato akce v produktu použije kanonickou backend operaci. Zde žádnou provozní změnu neprovádí.'
        page=page.replace('<body ', '<body data-demo-explanation="'+html.escape(demo_explanation,quote=True)+'" ',1)
        path=ROOT/'03_UI_REFERENCE/pages'/('dashboard.html' if id=='dashboard' else 'live-'+id+'.html')
        path.write_text(localize(page,m,'cs'),encoding='utf-8');outputs.append((view,path))
        path.with_stem(path.stem+'-en').write_text(localize(page,m,'en'),encoding='utf-8')
    return c,outputs


def render(c,outputs,locale='cs'):
    from playwright.sync_api import sync_playwright
    from PIL import Image,ImageOps,ImageDraw
    checks=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for vp in c['viewports']:
            w,h=map(int,vp.split('x'));page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1,reduced_motion='reduce')
            thumbs=[]
            for view,path in outputs:
                if locale=='en':path=path.with_stem(path.stem+'-en')
                page.goto(path.as_uri());page.wait_for_load_state('networkidle')
                overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth')
                target=ROOT/'04_UI_VIEWS'/((locale+'/') if locale!='cs' else '')/vp/(path.stem+'.png');target.parent.mkdir(parents=True,exist_ok=True)
                page.screenshot(path=str(target),full_page=True)
                checks.append({'view':view['id'],'locale':locale,'viewport':vp,'horizontalOverflow':overflow,'status':'FAIL' if overflow else 'PASS','render':target.relative_to(ROOT).as_posix(),'visualInspection':'PENDING'})
                with Image.open(target) as im:
                    thumb=ImageOps.contain(im.convert('RGB'),(360,470));tile=Image.new('RGB',(380,505),'#e9eef2');tile.paste(thumb,((380-thumb.width)//2,25));ImageDraw.Draw(tile).text((10,7),view['id'],fill='#18212d');thumbs.append(tile)
            sheet=Image.new('RGB',(380*4,505*3),'white')
            for i,im in enumerate(thumbs):sheet.paste(im,((i%4)*380,(i//4)*505))
            sheet.save(ROOT/'06_UI_OVERVIEWS'/('live-'+vp+('-en' if locale=='en' else '')+'.png'));page.close()
        browser.close()
    out=ROOT/('audit/generated/live-render-checks'+('-en' if locale=='en' else '')+'.json');out.write_text(json.dumps({'checks':checks,'runtimeBackendTested':False},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'renders':len(checks),'overflowFailures':sum(x['horizontalOverflow'] for x in checks)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');parser.add_argument('--locale',choices=['cs','en'],default='cs');args=parser.parse_args()
    c,outputs=generate()
    if args.render:render(c,outputs,args.locale)
    else:print(json.dumps({'generated':len(outputs)}))
