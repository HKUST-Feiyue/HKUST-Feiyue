"""Exercise the shared select UI, multilingual content and unchanged logo artwork."""
def check_controls(playwright, base):
    for engine in (playwright.chromium, playwright.webkit):
        browser = engine.launch()
        for width, theme in ((320, 'dark'), (390, 'light'), (1440, 'dark'), (1440, 'light')):
            context = browser.new_context(viewport={'width':width, 'height':900}, reduced_motion='reduce',
                                          is_mobile=width < 500, has_touch=width < 500)
            context.route('**/assets/js/submission-config.js*', lambda route: route.fulfill(
                content_type='application/javascript', body='window.HKUST_SUBMISSION_CONFIG={enabled:false};'))
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base+'/submit.html?lang=zh', wait_until='networkidle')
            page.wait_for_selector('#degree-trigger')
            page.evaluate('(theme)=>document.documentElement.dataset.theme=theme', theme)
            assert page.locator('.brand-logo, .mobile-brand-logo').evaluate_all(
                "items=>items.every(el=>getComputedStyle(el).filter==='none')")
            assert page.locator('.language-toggle [lang]').count() == 2
            assert page.locator('.language-toggle [lang="zh-CN"]').count() == 0
            assert page.locator('.contact-fields > button').evaluate('el=>el.getBoundingClientRect().width<el.parentElement.getBoundingClientRect().width-20')
            assert page.locator('.contact-row > button:visible').count()==0
            page.locator('.contact-fields > button').click()
            assert page.locator('.contact-row > button:visible').count()==2
            page.locator('.contact-row > button').last.click()
            assert page.locator('.contact-row').count()==1
            assert page.locator('.contact-row > button:visible').count()==0
            assert page.locator('#preview-button').evaluate('el=>el.getBoundingClientRect().height<=38 && getComputedStyle(el).width!=="100%"')
            page.locator('#author').fill('简体 / 繁體 / 日本語 / العربية / 🙂')
            page.locator('#year').fill('2024')
            page.locator('#field').fill('计算机 / 計算機 / コンピュータ / حاسوب / 🧪')
            page.locator('#destination').fill('Destination / 去向')
            page.locator('#body').fill('## 经历 / 經歷 / 経験\n\nالعربية 🙂')
            page.locator('#preview-button').click()
            assert page.locator('[name="campus"]:checked').count() == 0
            assert page.locator('#campus-trigger').count() == 0
            page.locator('[name="campus"][value="gz"]').check()
            assert page.locator('#campus').input_value() == 'gz'
            assert page.locator('#term').input_value() == ''
            page.locator('#preview-button').click()
            assert page.locator('#preview').is_hidden()
            assert page.locator('#term-trigger').get_attribute('aria-invalid') == 'true'
            page.locator('#term-trigger').click()
            assert page.locator('#term-options [role=option]').all_text_contents() == ['Fall', 'Spring']
            if width < 500:
                page.locator('#term-options [data-value=spring]').tap()
            else:
                page.locator('#term-options [data-value=spring]').click()
            page.locator('#degree-trigger').click()
            page.wait_for_function("document.querySelector('#degree-trigger').getAttribute('aria-expanded')==='true'")
            assert page.locator('#degree-options .select-group').count() == 4
            assert page.locator('#degree-options [data-value=""]').count() == 0
            if width < 500:
                page.locator('#degree-trigger .select-value').tap()
            else:
                page.locator('#degree-trigger .select-value').click()
            assert not page.locator('#degree-options').evaluate("el=>el.matches(':popover-open')")
            if width < 500:
                page.locator('#degree-trigger svg').tap()
            else:
                page.locator('#degree-trigger svg').click()
            assert page.locator('#degree-options').evaluate("el=>el.matches(':popover-open')")
            assert page.locator('#degree-options').evaluate(
                'el=>el.scrollHeight>el.clientHeight && el.getBoundingClientRect().height<=322 && el.getBoundingClientRect().right<=innerWidth-10 && el.getBoundingClientRect().bottom<=innerHeight-6')
            assert page.locator('#degree-options').evaluate(
                'el=>getComputedStyle(el).backgroundColor===getComputedStyle(document.querySelector("#degree-trigger")).backgroundColor')
            page.keyboard.type('MPhil')
            page.keyboard.press('Enter')
            assert page.locator('#degree').input_value() == 'MPhil', page.evaluate("({value:document.querySelector('#degree').value,focus:document.activeElement.id,active:document.querySelector('#degree-options .is-active')?.textContent})")
            page.locator('#degree-trigger').click()
            page.keyboard.press('Home')
            page.keyboard.press('Escape')
            assert page.locator('#degree').input_value() == 'MPhil'
            if width < 500:
                page.locator('#category-trigger').tap()
                page.locator('#category-options [data-value=research]').tap()
            else:
                page.locator('#category-trigger').click()
                page.locator('#category-options [data-value=research]').click()
            page.locator('#preview-button').click()
            assert page.locator('#preview').is_visible(), page.evaluate("[...document.querySelectorAll('select')].map(el=>[el.id,el.value,el.validationMessage])")
            before = page.locator('#preview-text').inner_text()
            assert 'العربية 🙂' in before and '简体' in before
            assert '2024 Spring' in page.locator('#preview-text .article-byline').inner_text()
            page.locator('.language-toggle').click()
            assert page.locator('html').get_attribute('lang') == 'en'
            assert page.locator('#degree-label').inner_text() == 'MPhil'
            assert page.locator('#term-label').inner_text() == 'Spring'
            assert page.locator('#field').input_value().endswith('🧪')
            page.locator('#degree-trigger').click()
            assert page.locator('#degree-options .select-group').first.inner_text() == 'Undergraduate'
            page.locator('#degree-trigger').press('Escape')
            page.reload(wait_until='networkidle')
            page.wait_for_selector('#degree-trigger')
            assert page.locator('#degree-label').inner_text() == 'MPhil'
            assert page.locator('#term-label').inner_text() == 'Spring'
            assert 'العربية' in page.locator('#author').input_value()
            page.locator('button[type=reset]').click()
            page.wait_for_function("document.querySelector('#degree-label').textContent==='Select degree'")
            assert page.locator('body').evaluate('el=>el.scrollWidth<=innerWidth')
            # Existing saved simplified-UI preferences no longer activate a third interface.
            page.evaluate("localStorage.setItem('hkust-feiyue-lang','zh-CN')")
            page.goto(base+'/?view=all', wait_until='networkidle')
            assert page.locator('html').get_attribute('lang') == 'en'
            for name in ('campus','year','degree'):
                page.locator('#'+name+'-trigger').click()
                assert page.locator('#'+name+'-options').evaluate("el=>el.matches(':popover-open')")
                page.keyboard.press('Escape')
            assert errors == [], errors
            context.close()
            print(f'Shared controls passed: {engine.name}, {width}px, {theme}')
        browser.close()

if __name__ == '__main__':
    from functools import partial
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from playwright.sync_api import sync_playwright
    from browser_smoke import Handler, ROOT
    server = ThreadingHTTPServer(('127.0.0.1',0), partial(Handler,directory=str(ROOT/'_site')))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as playwright:
            check_controls(playwright,f'http://127.0.0.1:{server.server_port}')
    finally:
        server.shutdown()
