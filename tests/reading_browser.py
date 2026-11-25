"""Handbook typography, deliberate mobile layout and approved maintainer identity."""
def check_reading(playwright, base, articles):
    for engine in (playwright.chromium,playwright.webkit):
        browser=engine.launch()
        for width,theme in ((320,'light'),(390,'dark'),(1440,'light')):
            context=browser.new_context(viewport={'width':width,'height':900},reduced_motion='reduce')
            context.add_init_script(f"localStorage.setItem('hkust-theme','{theme}')")
            context.route('**/assets/js/submission-config.js*',lambda route:route.fulfill(content_type='application/javascript',body='window.HKUST_SUBMISSION_CONFIG={enabled:false};'))
            page=context.new_page()
            for lang,name in (('zh','傅謝懿(Shine)'),('en','FuTseYi(Shine)')):
                page.goto(base+'/community.html?lang='+lang,wait_until='networkidle')
                assert page.locator('.community-person-name').inner_text().startswith(name)
                assert page.locator('.community-person-info p').inner_text()=='2026 Fall · MPhil'
                page.goto(base+'/?view=all&lang='+lang,wait_until='networkidle')
                assert page.locator('.article-item').count()==len(articles)
                assert page.locator('.article-item-footer').count()==len(articles)
                assert page.locator('.article-item-footer').first.evaluate("""el=>{
                    const date=el.querySelector('time'),link=el.querySelector('a');
                    const a=date.getBoundingClientRect(),b=link.getBoundingClientRect();
                    return Math.abs(a.top-b.top)<1 && Math.abs(a.height-b.height)<1 && getComputedStyle(date).fontSize===getComputedStyle(link).fontSize;
                }""")
                if 360<=width<=900:
                    assert page.locator('.attribute-filters').evaluate("""el=>{
                        const campus=document.querySelector('#campus-trigger').getBoundingClientRect();
                        const year=document.querySelector('#year-trigger').getBoundingClientRect();
                        const degree=document.querySelector('#degree-trigger').getBoundingClientRect();
                        return Math.abs(campus.top-year.top)<1 && Math.abs(campus.width-year.width)<1 && degree.width>campus.width*1.8;
                    }""")
                assert page.locator('.article-excerpt').first.evaluate('el=>el.getBoundingClientRect().height<=parseFloat(getComputedStyle(el).lineHeight)*3+1')
                page.goto(base+'/'+articles[0]['url']+'?lang='+lang,wait_until='networkidle')
                assert page.locator('.article-page > h1').evaluate("""el=>{
                    const style=getComputedStyle(el),article=getComputedStyle(el.parentElement);
                    return style.fontFamily===article.fontFamily && !style.fontFamily.includes('Georgia') && style.fontStyle==='normal' && style.transform==='none' && parseFloat(style.fontSize)<=36;
                }""")
                assert page.locator('.article-page').evaluate('el=>el.getBoundingClientRect().width<=761')
                assert page.locator('body').evaluate('el=>el.scrollWidth<=innerWidth')
                for route in ('/community.html', '/submit.html', '/'+articles[0]['url']):
                    page.goto(base+route+'?lang='+lang,wait_until='networkidle')
                    page.locator('.search-open').click()
                    assert page.locator('.search-field').evaluate('el=>el.getBoundingClientRect().height<=47')
                    assert page.locator('#search').evaluate('el=>document.activeElement===el')
                    if width>900:
                        assert page.locator('#search-dialog').evaluate('el=>el.getBoundingClientRect().height<=47')
                    page.locator('#search').fill(articles[0]['author'])
                    page.locator('#search-results li a').first.wait_for(state='visible')
                    page.keyboard.press('Escape')
                    assert page.locator('.search-open').evaluate('el=>document.activeElement===el')
                    assert page.locator('#search').input_value()==''
            context.close()
            print(f'Handbook reading passed: {engine.name}, {width}px, {theme}')
        browser.close()

if __name__=='__main__':
    import json
    from functools import partial
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from playwright.sync_api import sync_playwright
    from browser_smoke import Handler,ROOT
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT/'_site')))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as playwright:
            check_reading(playwright,f'http://127.0.0.1:{server.server_port}',json.loads((ROOT/'_site/data/articles.json').read_text(encoding='utf-8')))
    finally: server.shutdown()
