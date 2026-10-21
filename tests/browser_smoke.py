"""Run manually against localhost:8501; requires Playwright and Chromium."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
SCENARIO=json.loads((Path(__file__).resolve().parents[1] / 'data/scenarios_tier1.json').read_text())[0]
KEYS=['company','competitors','customers','collaborators','climate','segmentation','targeting','positioning','concept_check']

def nav(page, name):
    page.get_by_role('link', name=name, exact=True).click()
    page.wait_for_timeout(250)

def store(page):
    return page.evaluate('JSON.parse(localStorage.getItem("cmo_desk_learning_v2"))')

def saved(page, test):
    for _ in range(60):
        value=store(page)
        if test(value): return value
        page.wait_for_timeout(100)
    raise AssertionError(f'Save did not settle: {store(page)}')

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1280,'height':1000})
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://localhost:8501')
    page.get_by_role('heading',name='Your next marketing decision').wait_for()
    assert store(page) is None
    page.get_by_role('button',name='Open case',exact=True).click()
    page.get_by_role('heading',name='Brief',exact=True).wait_for()
    page.get_by_role('button',name='Continue',exact=True).click()
    page.get_by_role('heading',name='Company',exact=True).wait_for()
    assert page.get_by_role('radio').count()>0
    assert page.get_by_role('radio',checked=True).count()==0
    page.get_by_role('textbox',name='Which fact matters most?').fill('Limited capital and comfortable seating')
    page.get_by_role('textbox',name='What might this mean for the strategy?').fill('Focus on a segment we can serve credibly')
    page.get_by_role('heading',name='Company',exact=True).click()
    assert store(page) is None
    nav(page,'Settings')
    page.get_by_text('Remember my progress on this device',exact=True).click()
    saved(page,lambda v:v and v['draft']['notes']['company']['evidence']=='Limited capital and comfortable seating')
    page.reload()
    page.get_by_role('heading',name='Your data, your choice').wait_for()
    nav(page,'Home')
    page.get_by_role('heading',name='Your next marketing decision').wait_for()
    page.get_by_role('button',name='Continue my case').click()
    page.get_by_role('heading',name='Company',exact=True).wait_for()
    expect(page.get_by_role('textbox',name='Which fact matters most?')).to_have_value('Limited capital and comfortable seating')
    page.screenshot(path='/tmp/cmo-investigate.png',full_page=True)
    for key in KEYS:
        q=SCENARIO['analysis_questions'][key] if key in KEYS[:5] else SCENARIO['steps'][key] if key in KEYS[5:8] else SCENARIO['concept_check']
        page.get_by_text(q['options'][q['correct_idx']],exact=True).click()
        print('Answering',key,flush=True)
        page.get_by_role('button',name='Check my reasoning',exact=True).click()
        expect(page.get_by_role('button',name='Continue',exact=True)).to_be_enabled()
        page.get_by_role('button',name='Continue',exact=True).click()
    page.get_by_role('textbox',name='Why is your strategy a good fit for this business?').fill('Remote workers value seating and Wi-Fi, which fits existing capabilities.')
    page.get_by_role('button',name='Finish case',exact=True).click()
    page.get_by_text('Practice target reached independently',exact=True).wait_for()
    value=saved(page,lambda v:v and len(v['progress']['attempts'].get('1',[]))==1)
    assert value['progress']['attempts']['1'][0]['points']==100
    page.screenshot(path='/tmp/cmo-debrief.png',full_page=True)
    with page.expect_download() as download:
        page.get_by_role('button',name='Download my strategy brief').click()
    assert download.value.suggested_filename=='cmo-strategy-1.md'
    nav(page,'Settings')
    with page.expect_download() as download:
        page.get_by_role('button',name='Download learning backup').click()
    backup_path='/tmp/cmo-learning-backup.json'
    download.value.save_as(backup_path)
    # New browser context has no other learner's history.
    private=browser.new_context()
    other=private.new_page()
    other.goto('http://localhost:8501')
    other.get_by_role('heading',name='Your next marketing decision').wait_for()
    assert other.get_by_role('button',name='Continue my case').count()==0
    nav(other,'Settings')
    other.locator('input[type=file]').set_input_files(backup_path)
    other.get_by_role('button',name='Replace current learning with this backup').click()
    other.get_by_text('Backup restored. Continue from Home or explore your notebook.').wait_for()
    assert store(other) is None
    nav(other,'Progress')
    other.get_by_text('1 of 15 cases completed',exact=True).wait_for()
    nav(page,'Review')
    page.get_by_text(SCENARIO['analysis_questions']['company']['options'][0],exact=True).click()
    page.get_by_role('button',name='Check recall').click()
    page.get_by_text('Model answer:',exact=False).wait_for()
    page.get_by_role('button',name='Try another question').click()
    nav(page,'Settings')
    page.get_by_text('I want to erase my session and browser-saved learning data.',exact=True).click()
    page.get_by_role('button',name='Clear my learning data',exact=True).click()
    saved(page,lambda v:v is None)
    page.reload()
    page.get_by_role('heading',name='Your data, your choice').wait_for()
    nav(page,'Home')
    page.get_by_role('heading',name='Your next marketing decision').wait_for()
    assert page.get_by_role('button',name='Continue my case').count()==0
    mobile=browser.new_context(viewport={'width':390,'height':844})
    mobile_page=mobile.new_page()
    mobile_page.goto('http://localhost:8501')
    mobile_page.get_by_role('heading',name='Your next marketing decision').wait_for()
    mobile_page.screenshot(path='/tmp/cmo-mobile.png',full_page=True)
    assert mobile_page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    # A blocked component storage API must not block learning or backup access.
    blocked=browser.new_context()
    blocked.add_init_script("if (window !== window.top) { Storage.prototype.getItem = function() { throw new Error('blocked'); }; Storage.prototype.setItem = function() { throw new Error('blocked'); }; }")
    blocked_page=blocked.new_page()
    blocked_page.goto('http://localhost:8501')
    blocked_page.get_by_role('heading',name='Your next marketing decision').wait_for()
    blocked_page.get_by_text('Browser storage is unavailable.',exact=False).wait_for()
    nav(blocked_page,'Settings')
    expect(blocked_page.get_by_role('button',name='Download learning backup')).to_be_enabled()
    assert not errors,errors
    assert page.locator('[data-testid="stException"]').count()==0
    print('PASS: session-only default, explicit answers, notes, opt-in save, refresh resume, full case, scoring, exports, isolated visitors, import, review, deletion, and mobile overflow')
    browser.close()
