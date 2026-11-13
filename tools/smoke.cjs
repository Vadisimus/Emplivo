const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const fs = require('node:fs');
const base = 'http://127.0.0.1:8082';

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] });
  const errors = [];
  let apiCalls = 0;
  const submissionIds = [];
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
    await context.route('https://**/*', route => route.abort());
    await context.addInitScript(() => { window.emplivoAnalyticsEnabled = true; });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/applications.php', async route => {
      apiCalls++;
      const body = route.request().postData();
      const id = body.match(/name="submissionId"\r\n\r\n([^\r]+)/)?.[1];
      assert(id, 'Application must include an idempotency identifier');
      assert(!body.includes('demo-spa-01'), 'Demo job must never be submitted');
      submissionIds.push(id);
      await route.fulfill({ status: apiCalls === 1 ? 503 : 200, contentType: 'application/json', body: JSON.stringify(apiCalls === 1 ? { message: 'Simulated outage' } : { ok: true, id }) });
    });
    await page.goto(base + '/');
    assert.equal(await page.locator('[data-job-id]:visible').count(), 6);
    await page.locator('#sector-filter').selectOption('spa');
    assert.equal(await page.locator('[data-job-id]:visible').count(), 2);
    await page.locator('#job-search').fill('Львів');
    assert.equal(await page.locator('[data-job-id]:visible').count(), 1);
    await page.locator('[data-save-job="demo-spa-02"]').click();
    await page.locator('#saved-only').click();
    assert.equal(await page.locator('[data-job-id]:visible').count(), 1);
    await page.reload();
    assert.equal(await page.locator('[data-save-job="demo-spa-02"]').getAttribute('aria-pressed'), 'true');
    await page.locator('[name=fullName]').fill('Demo Candidate');
    await page.locator('[data-lang=en]').click();
    assert.equal(new URL(page.url()).pathname, '/en/');
    assert.equal(await page.locator('[name=fullName]').inputValue(), 'Demo Candidate');
    assert.equal(await page.locator('[data-route="jobs/spa-therapist/"]').getAttribute('href'), '/en/jobs/spa-therapist/');
    assert.equal(await page.locator('[href="tel:+380677778060"]').textContent(), '+380 (67) 777 80 60');

    const fillContacts = async () => {
      await page.locator('[name=fullName]').fill('Demo Candidate');
      await page.locator('[name=phone]').fill('+380671234567');
      await page.locator('[name=email]').fill('candidate@example.test');
      await page.locator('#form-next').click();
      await page.locator('#form-next').click();
      await page.locator('[name=consent]').check();
    };
    await page.goto(base + '/en/?job=demo-spa-01#application');
    assert.equal(await page.locator('#role-select').inputValue(), 'demo-spa-01');
    await fillContacts();
    await page.locator('#cv-file').setInputFiles({ name: 'demo.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4\nDEMO\n') });
    await page.locator('#submit-button').click();
    await page.locator('#form-success').waitFor({ state: 'visible' });
    assert.match(await page.locator('#form-success').textContent(), /not sent/);
    assert.equal(apiCalls, 0, 'Demo application must make zero API calls');

    await page.locator('#new-application').click();
    await page.locator('#form-next').click();
    assert.equal(await page.locator('[name=fullName]').getAttribute('aria-invalid'), 'true');
    await fillContacts();
    await page.locator('#submit-button').click();
    await page.locator('#form-error').waitFor({ state: 'visible' });
    await page.waitForFunction(() => !document.querySelector('#submit-button').disabled);
    assert.equal(await page.locator('[name=fullName]').inputValue(), 'Demo Candidate');
    await page.locator('#submit-button').click();
    await page.locator('#form-success').waitFor({ state: 'visible' });
    assert.equal(apiCalls, 2);
    assert.equal(submissionIds[0], submissionIds[1], 'Retry must preserve the submission ID');
    const telemetry = await page.evaluate(() => JSON.stringify(window.dataLayer));
    assert(!telemetry.includes('Demo Candidate') && !telemetry.includes('candidate@example.test'));
    const storage = await page.evaluate(() => JSON.stringify(localStorage));
    assert(!storage.includes('Demo Candidate') && !storage.includes('candidate@example.test'));

    await page.goto(base + '/en/contact/?type=consultation#request');
    await page.locator('[name=role]').fill('Spa hiring consultation');
    await page.locator('[name=location]').fill('Ukraine');
    await page.locator('[name=message]').fill('Demonstration message. Please discuss a suitable time.');
    await page.locator('#email-request button').click();
    assert.match(await page.locator('#request-status').textContent(), /not been sent/);
    assert.equal(await page.locator('#email-fallback').isVisible(), true);

    const mobile = await browser.newContext({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });
    await mobile.route('https://**/*', route => route.abort());
    const small = await mobile.newPage();
    small.on('pageerror', error => errors.push(error.message));
    await small.goto(base + '/');
    assert(await small.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Homepage must not overflow mobile width');
    await small.locator('#menu-toggle').click();
    assert.equal(await small.locator('#menu-toggle').getAttribute('aria-expanded'), 'true');
    await small.locator('#navigation [data-route="blog/"]').click();
    assert.equal(new URL(small.url()).pathname, '/blog/');
    assert(await small.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Editorial page must not overflow mobile width');

    const staticContext = await browser.newContext({ javaScriptEnabled: false });
    await staticContext.route('https://**/*', route => route.abort());
    const staticPage = await staticContext.newPage();
    await staticPage.goto(base + '/en/jobs/spa-therapist/');
    assert.match(await staticPage.locator('h1').textContent(), /Spa therapists/);
    assert.equal(await staticPage.locator('[hreflang=uk][rel=alternate]').getAttribute('href'), 'https://www.emplivo.com.ua/jobs/spa-therapist/');

    fs.mkdirSync('/workspace/reports', { recursive: true });
    await page.goto(base + '/');
    await page.screenshot({ path: '/workspace/reports/emplivo-home-desktop.png' });
    await small.goto(base + '/jobs/spa-therapist/');
    await small.screenshot({ path: '/workspace/reports/emplivo-role-mobile.png', fullPage: true });
    assert.deepEqual(errors, [], 'Browser JavaScript exceptions');
    console.log('PASS: six jobs, category/city filters, persistent saves, language/form preservation, demo zero-POST, mocked real submission/retry, privacy, email fallback, mobile layout/navigation, static English content. No external application writes.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
