const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
    chromiumSandbox: true,
    headless: true,
  });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {
      if (['error', 'warning'].includes(message.type())) errors.push(message.text());
    });
    await page.goto(pathToFileURL(path.resolve('demo/v2-preview.html')).href);
    assert.match(await page.locator('#status').innerText(), /choose/i);
    const data = {
      snapshot_kind: 'candidate_not_published',
      as_of: '2026-01-01T00:00:00+00:00',
      tallies: {KEPT_THEN_REVERSED: 1},
      promises: [{
        promise_id: 'P1', entity_name: 'City', entity_type: 'City Agency',
        sector: 'Housing & Land Use', neighborhood: 'Parkmerced',
        promise_text: '<img src=x onerror=alert(1)> We will build a library.',
        date_promised: '2024-01-01', date_deadline: '2025-01-01',
        verdict: 'KEPT_THEN_REVERSED', verdict_reason: 'Closed',
        decided_at: '2025-12-01T00:00:00+00:00',
        relevance: {real_promise: 2, measurable: 1, sf_relevant: 2, interesting: 0, total: 5},
        evidence: [{
          phase: 'ORIGIN', url: 'https://sf.gov/example', source_tier: 'TIER1_GOV',
          published_date: '2024-01-02', local_source_path: '/saved/source.txt',
          content_sha256: 'a'.repeat(64), verbatim_quote: 'We will build a library.',
        }],
      }],
    };
    const input = page.locator('#snapshot-file');
    await input.setInputFiles({
      name: 'candidate.json', mimeType: 'application/json',
      buffer: Buffer.from(JSON.stringify(data)),
    });
    await page.getByText('We will build a library.', { exact: false }).first().waitFor();
    assert.equal(await page.locator('#promise-list img').count(), 0);
    assert.match(await page.locator('#status').innerText(), /1 promise/i);
    await page.locator('#verdict-filter').selectOption('BROKEN');
    assert.match(await page.locator('#status').innerText(), /0 of 1/i);
    await page.locator('#verdict-filter').selectOption('KEPT_THEN_REVERSED');
    assert.match(await page.locator('#status').innerText(), /1 of 1/i);
    await page.locator('details > summary').focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('details').evaluate(element => element.open), true);
    assert.match(await page.locator('#promise-list').innerText(), /Closed/);
    assert.equal(await page.locator('#promise-list a').first().getAttribute('href'), 'https://sf.gov/example');
    data.promises[0].evidence[0].url = 'javascript:alert(1)';
    await input.setInputFiles({
      name: 'untrusted.json', mimeType: 'application/json',
      buffer: Buffer.from(JSON.stringify(data)),
    });
    await page.waitForFunction(() => document.querySelectorAll('#promise-list a').length === 0);
    await page.locator('details > summary').click();
    assert.equal(await page.locator('#promise-list a').count(), 0);
    for (const width of [320, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    }
    const cdp = await page.context().newCDPSession(page);
    const tree = await cdp.send('Accessibility.getFullAXTree');
    assert.ok(tree.nodes.some(item => item.role?.value === 'heading'
      && item.name?.value === 'Review a candidate snapshot'));
    await cdp.detach();
    if (process.env.PREVIEW_SCREENSHOT) {
      await page.setViewportSize({ width: 1024, height: 900 });
      await page.screenshot({path: process.env.PREVIEW_SCREENSHOT, fullPage: true});
    }
    if (process.env.CANDIDATE_FILE) {
      const actual = JSON.parse(fs.readFileSync(process.env.CANDIDATE_FILE, 'utf8'));
      await input.setInputFiles(process.env.CANDIDATE_FILE);
      assert.match(await page.locator('#status').innerText(), new RegExp(`of ${actual.promises.length} promise`));
      assert.equal(await page.locator('#promise-list details').count(), actual.promises.length);
      if (actual.promises.length) {
        assert.match(await page.locator('#promise-list').innerText(), new RegExp(actual.promises[0].promise_id));
        assert.ok((await page.locator('#promise-list').innerText()).includes(actual.promises[0].promise_text));
      }
    }
    await input.setInputFiles({
      name: 'invalid.json', mimeType: 'application/json', buffer: Buffer.from('{"promises":[]}'),
    });
    assert.match(await page.locator('#status').innerText(), /invalid/i);
    assert.equal(await page.locator('#promise-list details').count(), 0);
    assert.deepEqual(errors, []);
    console.log('Candidate preview browser checks passed.');
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
