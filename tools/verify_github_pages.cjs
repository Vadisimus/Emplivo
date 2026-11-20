const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const origin = 'https://vadisimus.github.io';
const prefix = '/Emplivo/';
const base = origin + prefix;
const types = {
  '.html':'text/html; charset=utf-8', '.mjs':'text/javascript', '.css':'text/css',
  '.webp':'image/webp', '.jpg':'image/jpeg', '.svg':'image/svg+xml', '.woff2':'font/woff2',
};
const labels = [['','uk'],['en/','en'],['ru/','ru']];
const endpoint = 'https://intake.example';

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] });
  try {
    const context = await browser.newContext({ viewport: { width: 320, height: 820 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const errors = [];
    let ids = [];
    let posts = 0;
    page.on('pageerror', error => errors.push(error.message));
    await context.route('**/*', async route => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.hostname === 'challenges.cloudflare.com') {
        return route.fulfill({ contentType: 'text/javascript',
          body: 'window.turnstile={render:()=>1,getResponse:()=>"test",reset:()=>{}};window.emplivoChallengeReady()' });
      }
      if (url.origin === endpoint) {
        const headers = { 'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type' };
        if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, headers });
        const requestBody = request.postData();
        const id = requestBody.match(/name="submissionId"\s+([\da-f-]{36})/)?.[1];
        assert(id);
        ids.push(id);
        posts++;
        const rejected = url.pathname === '/api/apply' && ids.length === 1;
        return route.fulfill({ status: rejected ? 502 : 200, headers, json: rejected ?
          { error: 'delivery_rejected', id } : { ok: true, id } });
      }
      assert.equal(url.origin, origin);
      assert(url.pathname.startsWith(prefix));
      assert.equal(request.method(), 'GET');
      let file = path.resolve(root, decodeURIComponent(url.pathname.slice(prefix.length)));
      assert(file === root || file.startsWith(root + path.sep));
      if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
      assert(fs.existsSync(file), url.pathname);
      let body = fs.readFileSync(file);
      if (url.pathname.endsWith('/intake-config.mjs')) {
        body = 'export const intakeConfig = { workerOrigin:"' + endpoint + '", siteKey:"test-site" };';
      }
      return route.fulfill({ contentType: types[path.extname(file)] || 'application/octet-stream', body });
    });

    for (const [locale, lang] of labels) {
      for (const route of ['', 'jobs/', 'about/', 'blog/', 'apply/', 'submit-vacancy/', 'vacancies/ever-tech-product-engineer/']) {
        await page.goto(base + locale + route);
        assert.equal(await page.locator('html').getAttribute('lang'), lang);
        assert.equal(await page.locator('header .navigation li').count(), 6);
        assert.equal(await page.locator('footer').count(), 1);
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), locale + route);
      }
    }
    await page.goto(base + 'jobs/');
    await page.locator('[data-menu-toggle]').click();
    assert(await page.locator('#site-menu').isVisible());
    await page.keyboard.press('Escape');
    await page.waitForFunction(() => document.activeElement.matches('[data-menu-toggle]'));
    await page.locator('[name=pay]').selectOption('USD/HOUR');
    assert.equal(await page.locator('[data-job-id]:visible').count(), 0);
    await page.locator('[name=undisclosed]').check();
    assert.equal(await page.locator('[data-job-id]:visible').count(), 3);
    await page.locator('[name=q]').fill('senior');
    assert.equal(await page.locator('[data-job-id]:visible').count(), 1);
    assert(new URL(page.url()).searchParams.has('pay'));
    await page.locator('[data-save-job]:visible').click();
    assert.equal(await page.locator('[data-saved-count]').textContent(), '1');
    await page.goto(base + 'saved/');
    assert.equal(await page.locator('[data-job-id]:visible').count(), 1);
    await page.reload();
    assert.equal(await page.locator('[data-save-job]:visible').getAttribute('aria-pressed'), 'true');

    await page.goto(base + 'apply/');
    const form = page.locator('[data-intake=apply]');
    await form.locator('[name=name]').fill('Fixture');
    await form.locator('[name=email]').fill('test@example.test');
    await form.locator('[name=consent]').check();
    await form.locator('[name=cv]').setInputFiles({ name:'cv.pdf', mimeType:'application/pdf', buffer:Buffer.from('%PDF-test') });
    await form.locator('button').click();
    await page.getByText(/Сервіс відхилив/).waitFor();
    await form.locator('button').click();
    await page.getByRole('heading', { name: 'Резюме отримано' }).waitFor();
    assert.equal(ids[0], ids[1]);
    await page.goto(base + 'ru/submit-vacancy/?service=contract');
    const brief = page.locator('[data-intake=employer]');
    assert.equal(await brief.locator('[name=service]').inputValue(), 'contract');
    for (const [name, value] of Object.entries({ name:'Fixture', email:'hr@example.test', company:'Fixture', role:'Role', description:'Details' })) {
      await brief.locator('[name=' + name + ']').fill(value);
    }
    await brief.locator('[name=consent]').check();
    await brief.locator('button').click();
    await page.getByRole('heading', { name: 'Бриф получен' }).waitFor();
    assert.equal(posts, 3);
    await page.setViewportSize({ width:1440, height:960 });
    assert(await page.locator('header .navigation').isVisible());
    assert.deepEqual(errors, []);
    const { matchesSalary } = await import('../jobs.mjs');
    const pay = { currency:'USD', unit:'HOUR', min:49, max:49 };
    assert(matchesSalary(pay, { currency:'USD', unit:'HOUR', min:45, max:55 }));
    assert(!matchesSalary(pay, { currency:'UAH', unit:'MONTH' }));
    assert(!matchesSalary(pay, { currency:'USD', unit:'MONTH' }));
    console.log('PASS: project subpath, UA/EN/RU, mobile menu, saved jobs, currency and period, CV retry and employer brief.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
