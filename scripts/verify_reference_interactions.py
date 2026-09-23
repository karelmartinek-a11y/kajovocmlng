"""Check presentation interactions in a real browser. No domain execution."""
import json
from itertools import product
from playwright.sync_api import sync_playwright
from ssot_sources import ROOT


def run():
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for locale,viewport in product(['cs','en'],[{'width':1366,'height':768},{'width':768,'height':1024},{'width':390,'height':844}]):
            page=browser.new_page(viewport=viewport,has_touch=viewport['width']==390,reduced_motion='reduce')
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto((ROOT/('03_UI_REFERENCE/pages/dashboard'+('-en' if locale=='en' else '')+'.html')).as_uri())
            try:
                trigger=page.locator('[data-menu]')
                trigger.tap() if viewport['width']==390 else trigger.click()
                assert page.locator('.sample-menu').is_visible()
                page.keyboard.press('ArrowDown');assert page.locator('.sample-menu button').nth(1).evaluate('(el)=>el===document.activeElement')
                page.keyboard.press('Escape');assert not page.locator('.sample-menu').is_visible()
                assert trigger.evaluate('(el)=>el===document.activeElement')
                page.locator('.graph').focus();page.keyboard.press('Shift+F10');assert page.locator('.sample-menu').is_visible()
                assert trigger.get_attribute('aria-expanded')=='true'
                page.keyboard.press('Escape')
                assert page.locator('.graph').evaluate('(el)=>el===document.activeElement')
                page.locator('.graph').click(button='right',position={'x':5,'y':5})
                assert page.locator('.sample-menu').is_visible()
                page.locator('.sample-menu button').first.click();assert page.locator('dialog').is_visible()
                page.keyboard.press('Escape');assert not page.locator('dialog').is_visible()
                assert page.locator('.sample-menu').is_visible()
                assert page.locator('.sample-menu button').first.evaluate('(el)=>el===document.activeElement')
                page.keyboard.press('Escape')
                help_button=page.locator('.cardhead button[data-help]').first;help_button.click()
                assert page.locator('dialog').is_visible();page.keyboard.press('Escape');assert not page.locator('dialog').is_visible()
                assert help_button.evaluate('(el)=>el===document.activeElement')
                assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                assert page.locator('[data-demo=true]').count()==1
                assert not errors,errors
                results.append({'locale':locale,'viewport':viewport,'status':'PASS','checks':['visible-menu','touch-tap-or-click','arrow-navigation','escape','shift-f10','right-click','nested-dialog-focus-return','help-dialog','focus-return','sample-label','no-horizontal-overflow','no-js-error']})
            except Exception as exc:results.append({'locale':locale,'viewport':viewport,'status':'FAIL','reason':str(exc),'browserErrors':errors})
            page.close()
        browser.close()
    out=ROOT/'audit/generated/reference-interactions.json';out.write_text(json.dumps({'checks':results,'scope':'Presentation only; no backend calls.'},indent=2)+'\n',encoding='utf-8')
    return results


if __name__=='__main__':
    import sys
    r=run();print(json.dumps(r));sys.exit(any(x['status']=='FAIL' for x in r))
