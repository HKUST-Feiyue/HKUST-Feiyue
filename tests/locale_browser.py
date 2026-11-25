"""Slow-script first-paint checks, navigation and shared bilingual typography."""
import time

def check_locale(playwright, base, articles):
    for engine in (playwright.chromium, playwright.webkit):
        browser = engine.launch()
        for width in (390,1440):
            context = browser.new_context(viewport={'width':width,'height':900}, reduced_motion='reduce')
            context.add_init_script("""localStorage.setItem('hkust-feiyue-lang','zh');
                window.englishFrames=[];
                function inspectLocale() {
                    const nav=document.querySelector('#category-nav [data-view=home]');
                    if (nav && document.body && getComputedStyle(document.body).visibility==='visible' && nav.textContent.trim()==='Home') {
                        window.englishFrames.push(location.href);
                    }
                    requestAnimationFrame(inspectLocale);
                }
                requestAnimationFrame(inspectLocale);""")
            def delayed_script(route):
                time.sleep(.3)
                route.continue_()
            context.route('**/assets/js/i18n.js*', delayed_script)
            context.route('**/data/i18n.json',lambda route: route.abort())
            context.route('**/assets/js/submission-config.js*',lambda route: route.fulfill(
                content_type='application/javascript',body='window.HKUST_SUBMISSION_CONFIG={enabled:false};'))
            page = context.new_page()
            def verify():
                page.wait_for_function("!document.documentElement.hasAttribute('data-language-pending') && document.querySelector('#category-nav [data-view=home]').textContent.trim()==='首頁'")
                page.wait_for_timeout(50)
                assert page.evaluate('window.englishFrames') == []
                assert page.locator('body').evaluate("el=>getComputedStyle(el).visibility==='visible'")
                assert page.locator('html').get_attribute('lang') == 'zh-Hant'
            for route in ('/','/submit.html','/community.html','/'+articles[0]['url']):
                page.goto(base+route,wait_until='domcontentloaded')
                verify()
                page.reload(wait_until='domcontentloaded')
                verify()
            page.goto(base+'/',wait_until='domcontentloaded')
            verify()
            assert page.locator('#hero-title').evaluate("el=>getComputedStyle(el).fontStyle==='italic' && getComputedStyle(el).transform!=='none'")
            assert page.locator('.footer-brand-name').evaluate("el=>getComputedStyle(el).fontStyle==='italic' && getComputedStyle(el).transform!=='none'")
            if width>900:
                assert page.locator('.sidebar-bottom').evaluate("""el=>{
                    const children=[...el.children].filter(node=>getComputedStyle(node).display!=='none');
                    const first=children[0].getBoundingClientRect(),last=children.at(-1).getBoundingClientRect(),area=el.getBoundingClientRect();
                    return Math.abs((first.left+last.right)-(area.left+area.right))<2;
                }""")
                page.locator('#category-nav .nav-contribute').click()
            else:
                page.locator('#menu-toggle').click()
                page.locator('#category-nav .nav-contribute').click()
            page.wait_for_url('**/submit.html*')
            verify()
            page.go_back(wait_until='domcontentloaded')
            verify()
            page.go_forward(wait_until='domcontentloaded')
            verify()
            context.close()
            print(f'First-paint locale passed: {engine.name}, {width}px')
        browser.close()

if __name__ == '__main__':
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
            check_locale(playwright,f'http://127.0.0.1:{server.server_port}',json.loads((ROOT/'_site/data/articles.json').read_text(encoding='utf-8')))
    finally:
        server.shutdown()
