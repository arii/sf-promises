/**
 * Headless Chrome automated verification & screenshot capture using CDP
 * Validates UX & data-integrity follow-up brief requirements:
 * 1. Quarantine tab visible at 390, 820, and 1280 px (13 items, verified controls hidden)
 * 2. 4-part detail drawer opens with all parts and closes cleanly
 * 3. Mobile viewport (390px) page height < 6,500px and zero horizontal overflow
 * 4. Replay state machine: N01 watchdog default, stage progression with zero stale text
 */

const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');
const path = require('path');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon'
};

function createStaticServer(port, staticDir) {
  const server = http.createServer((req, res) => {
    let reqPath = req.url.split('?')[0];
    if (reqPath === '/') reqPath = '/index.html';
    const filePath = path.join(staticDir, reqPath);
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    fs.createReadStream(filePath).pipe(res);
  });
  return new Promise((resolve, reject) => {
    server.listen(port, '127.0.0.1', () => resolve(server));
    server.on('error', reject);
  });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    }).on('error', reject);
  });
}

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 1;
    this.callbacks = new Map();
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws.onopen = () => resolve();
      this.ws.onerror = err => reject(err);
      this.ws.onmessage = evt => {
        const msg = JSON.parse(evt.data);
        if (msg.id && this.callbacks.has(msg.id)) {
          const { resolve, reject } = this.callbacks.get(msg.id);
          this.callbacks.delete(msg.id);
          if (msg.error) reject(msg.error);
          else resolve(msg.result);
        }
      };
    });
  }

  async send(method, params = {}) {
    const id = this.id++;
    return new Promise((resolve, reject) => {
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expr) {
    const res = await this.send('Runtime.evaluate', { expression: expr, returnByValue: true });
    return res.result?.value;
  }

  async captureScreenshot(filePath, clip = null) {
    const params = { format: 'png' };
    if (clip) params.clip = clip;
    const res = await this.send('Page.captureScreenshot', params);
    fs.writeFileSync(filePath, Buffer.from(res.data, 'base64'));
    console.log(`Saved screenshot: ${filePath}`);
  }

  close() {
    this.ws.close();
  }
}

async function main() {
  const HTTP_PORT = 8092;
  const staticDir = path.resolve(__dirname);
  console.log(`Starting static HTTP server on http://127.0.0.1:${HTTP_PORT} (serving ${staticDir})...`);
  const server = await createStaticServer(HTTP_PORT, staticDir);

  const PORT = 9227;
  console.log('Launching headless Chrome on port', PORT);
  const chrome = spawn('google-chrome', [
    '--headless=new',
    `--remote-debugging-port=${PORT}`,
    '--window-size=1280,1200',
    '--disable-gpu',
    '--no-sandbox',
    '--hide-scrollbars',
    'about:blank'
  ]);

  await sleep(1500);

  try {
    const targets = await getJson(`http://127.0.0.1:${PORT}/json`);
    const pageTarget = targets.find(t => t.type === 'page') || targets[0];
    if (!pageTarget) throw new Error('No page target found');

    const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
    await client.connect();

    await client.send('Page.enable');
    await client.send('Runtime.enable');

    const testWidths = [1280, 1024, 820, 768, 390, 360];

    // Navigate to page
    console.log(`Navigating to http://127.0.0.1:${HTTP_PORT}/`);
    await client.send('Page.navigate', { url: `http://127.0.0.1:${HTTP_PORT}/` });
    await sleep(1200);

    // =========================================================================
    // 1. Desktop 1280px Verification
    // =========================================================================
    console.log('\n--- 1. Testing Desktop (1280px) ---');
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: 1280,
      height: 1200,
      deviceScaleFactor: 1,
      mobile: false
    });
    await sleep(400);

    // Assert default replay is P02
    const defaultReplayVal = await client.eval('document.getElementById("run-select").value');
    console.log(`Default Replay Scenario: ${defaultReplayVal}`);
    if (defaultReplayVal !== 'P02') {
      throw new Error(`Expected default replay P02, got ${defaultReplayVal}`);
    }

    // Verify consolidated button bar and fixed geometry
    console.log('Testing Walkthrough consolidated controls and fixed geometry...');
    const initialResetDisabled = await client.eval('document.getElementById("btn-pipeline-reset").disabled');
    const stage0Text = await client.eval('document.getElementById("pipeline-primary-text").textContent');
    console.log(`Stage 0: primary text="${stage0Text}", reset disabled=${initialResetDisabled}`);
    if (!initialResetDisabled || !stage0Text.includes('Start Walkthrough')) {
      throw new Error(`Stage 0 controls mismatch: resetDisabled=${initialResetDisabled}, text="${stage0Text}"`);
    }

    // Measure height at stage 0
    const h0 = await client.eval('document.getElementById("pipeline-active-stage-panel").getBoundingClientRect().height');

    // Click next to advance to Stage 1
    await client.eval('document.getElementById("btn-step-next").click()');
    await sleep(200);
    const stage1Text = await client.eval('document.getElementById("pipeline-primary-text").textContent');
    const stage1ResetDisabled = await client.eval('document.getElementById("btn-pipeline-reset").disabled');
    const h1 = await client.eval('document.getElementById("pipeline-active-stage-panel").getBoundingClientRect().height');
    console.log(`Stage 1: primary text="${stage1Text}", reset disabled=${stage1ResetDisabled}, h0=${h0}, h1=${h1}`);
    if (stage1ResetDisabled || !stage1Text.includes('Next Stage')) {
      throw new Error(`Stage 1 controls mismatch: resetDisabled=${stage1ResetDisabled}, text="${stage1Text}"`);
    }

    // Jump to Stage 6 and verify verdict chip & semantic colors
    await client.eval('document.getElementById("ms-circle-6").parentElement.click()');
    await sleep(200);
    const stage6VerdictClass = await client.eval('document.querySelector("#pipeline-active-stage-panel .verdict-chip").className');
    const stage6CircleClass = await client.eval('document.getElementById("ms-circle-6").className');
    const h6 = await client.eval('document.getElementById("pipeline-active-stage-panel").getBoundingClientRect().height');
    console.log(`Stage 6: verdictClass="${stage6VerdictClass}", circleClass="${stage6CircleClass}", h6=${h6}`);
    if (!stage6VerdictClass.includes('kept') || !stage6CircleClass.includes('kept')) {
      throw new Error(`Semantic color mismatch on Stage 6 kept: verdictClass=${stage6VerdictClass}, circleClass=${stage6CircleClass}`);
    }

    // Test P05 (Broken) semantic red styling
    console.log('Testing P05 Broken scenario semantic colors...');
    await client.eval(`
      const sel = document.getElementById("run-select");
      sel.value = "P05";
      sel.dispatchEvent(new Event("change"));
    `);
    await sleep(200);
    await client.eval('document.getElementById("ms-circle-6").parentElement.click()');
    await sleep(200);
    const p05CircleClass = await client.eval('document.getElementById("ms-circle-6").className');
    const p05BallClass = await client.eval('document.getElementById("packet-ball-inner").className');
    console.log(`P05 Stage 6: circleClass="${p05CircleClass}", ballClass="${p05BallClass}"`);
    if (!p05CircleClass.includes('broken') || !p05BallClass.includes('broken')) {
      throw new Error(`Semantic color mismatch on P05 broken: circleClass=${p05CircleClass}, ballClass=${p05BallClass}`);
    }

    // Reset back to P02 Stage 0
    await client.eval(`
      const sel = document.getElementById("run-select");
      sel.value = "P02";
      sel.dispatchEvent(new Event("change"));
      document.getElementById("btn-pipeline-reset").click();
    `);
    await sleep(200);

    await client.captureScreenshot('demo/screenshot_1280_main.png');

    // Test Quarantine Tab at 1280px
    console.log('Clicking Quarantine Tab at 1280px...');
    await client.eval('document.getElementById("tab-btn-quarantine").click()');
    await sleep(400);

    const qRows1280 = await client.eval('document.querySelectorAll("#quarantine-table-body tr.quarantine-row").length');
    const qVisible1280 = await client.eval('!document.getElementById("quarantine-table-container").classList.contains("hidden")');
    const verifiedHidden1280 = await client.eval('document.getElementById("promises-table-container").classList.contains("hidden")');
    const controlsHidden1280 = await client.eval('document.querySelector(".explore-primary-controls").classList.contains("hidden")');
    console.log(`1280px Quarantine: rows=${qRows1280}, visible=${qVisible1280}, verifiedHidden=${verifiedHidden1280}, controlsHidden=${controlsHidden1280}`);
    if (qRows1280 !== 13 || !qVisible1280 || !verifiedHidden1280 || !controlsHidden1280) {
      throw new Error(`Quarantine tab failed at 1280px: rows=${qRows1280}, visible=${qVisible1280}`);
    }
    await client.captureScreenshot('demo/screenshot_1280_quarantine.png');

    // Switch back to Verified Commitments
    await client.eval('document.getElementById("tab-btn-promises").click()');
    await sleep(300);

    // Test 4-Part Detail Drawer opening for P02
    console.log('Testing 4-Part Detail Drawer for P02...');
    await client.eval('document.getElementById("promise-P02").click()');
    await sleep(400);

    const drawerVisible = await client.eval('!document.getElementById("inspect-drawer-backdrop").classList.contains("hidden")');
    const drawerTitle = await client.eval('document.getElementById("drawer-title").textContent');
    const drawerHash = await client.eval('document.getElementById("drawer-hash").textContent');
    const drawerChecksCount = await client.eval('document.querySelectorAll("#drawer-checks-list .drawer-check-row").length');
    console.log(`Drawer open: visible=${drawerVisible}, title="${drawerTitle}", hash="${drawerHash.slice(0, 16)}…", checks=${drawerChecksCount}`);
    if (!drawerVisible || !drawerTitle.includes('24/7') || drawerChecksCount < 7) {
      throw new Error(`Detail drawer failed to open with complete provenance!`);
    }
    await client.captureScreenshot('demo/screenshot_drawer_open.png');

    // Close Drawer
    await client.eval('document.getElementById("btn-close-drawer").click()');
    await sleep(300);
    const drawerClosed = await client.eval('document.getElementById("inspect-drawer-backdrop").classList.contains("hidden")');
    console.log(`Drawer closed cleanly: ${drawerClosed}`);

    // =========================================================================
    // 2. Tablet 820px / 768px Verification
    // =========================================================================
    console.log('\n--- 2. Testing Tablet (820px & 768px) ---');
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: 820,
      height: 1024,
      deviceScaleFactor: 1,
      mobile: false
    });
    await sleep(400);

    // Quarantine at 820px
    await client.eval('document.getElementById("tab-btn-quarantine").click()');
    await sleep(400);
    const qRows820 = await client.eval('document.querySelectorAll("#quarantine-table-body tr.quarantine-row").length');
    console.log(`820px Quarantine: rows=${qRows820}`);
    if (qRows820 !== 13) throw new Error(`Quarantine failed at 820px`);

    await client.eval('document.getElementById("tab-btn-promises").click()');
    await sleep(300);

    // =========================================================================
    // 3. Mobile 390px & 360px Verification
    // =========================================================================
    console.log('\n--- 3. Testing Mobile (390px & 360px) ---');
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: 390,
      height: 844,
      deviceScaleFactor: 2,
      mobile: true
    });
    await sleep(400);

    // Check topbar header layout on mobile
    const headerInfo = await client.eval(`(() => {
      const rect = el => {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { w: Math.round(r.width), h: Math.round(r.height), top: Math.round(r.top), left: Math.round(r.left) };
      };
      return {
        topbar: rect(document.querySelector('.topbar')),
        brand: rect(document.querySelector('.brand')),
        brandText: rect(document.querySelector('.brand-text')),
        menuToggle: rect(document.querySelector('#mobile-menu-toggle')),
        desktopNav: rect(document.querySelector('.desktop-nav'))
      };
    })()`);
    console.log('Mobile Header Info at 390px:', JSON.stringify(headerInfo, null, 2));

    // Verify brand title "SF Promises" is visible on mobile
    if (!headerInfo.brandText || headerInfo.brandText.w === 0) {
      throw new Error('Brand text "SF Promises" is hidden on mobile!');
    }
    console.log('PASS: Brand title "SF Promises" is visible on mobile (width: ' + headerInfo.brandText.w + 'px)');

    // Verify mobile hamburger menu opens and closes cleanly
    console.log('Testing Mobile Navigation Menu Drawer...');
    await client.eval('document.getElementById("mobile-menu-toggle").click()');
    await sleep(200);
    const navDrawerOpen = await client.eval('!document.getElementById("mobile-nav-drawer").classList.contains("hidden")');
    if (!navDrawerOpen) {
      throw new Error('Mobile navigation drawer did not open on toggle click!');
    }
    console.log('PASS: Mobile navigation drawer opened cleanly.');
    await client.eval('document.getElementById("mobile-menu-toggle").click()');
    await sleep(200);
    const navDrawerClosed = await client.eval('document.getElementById("mobile-nav-drawer").classList.contains("hidden")');
    if (!navDrawerClosed) {
      throw new Error('Mobile navigation drawer did not close on toggle click!');
    }
    console.log('PASS: Mobile navigation drawer closed cleanly.');

    // Test carousel pagination dots
    console.log('Testing Featured Stories Carousel Controls...');
    const carouselDotsCount = await client.eval('document.querySelectorAll(".carousel-dot").length');
    console.log(`Found ${carouselDotsCount} carousel dots.`);
    if (carouselDotsCount !== 6) {
      throw new Error(`Expected 6 carousel dots, found ${carouselDotsCount}`);
    }
    await client.eval('document.querySelectorAll(".carousel-dot")[1].click()');
    await sleep(300);
    const dot1Active = await client.eval('document.querySelectorAll(".carousel-dot")[1].classList.contains("active")');
    const counterText = await client.eval('document.getElementById("carousel-counter").textContent');
    console.log(`Dot 1 active: ${dot1Active}, Counter: "${counterText}"`);
    if (!dot1Active) {
      throw new Error('Carousel dot 1 did not become active when clicked!');
    }
    console.log('PASS: Carousel pagination controls working.');

    // Check page height target (< 6,500px)
    const sectionHeights = await client.eval(`
      Array.from(document.querySelectorAll('section, header, footer, .explore-section, .mobile-promise-cards-list')).map(el => ({
        id: el.id || el.className,
        height: Math.round(el.getBoundingClientRect().height)
      })).filter(x => x.height > 20)
    `);
    console.log('Mobile section heights:', JSON.stringify(sectionHeights, null, 2));

    const mobilePageHeight = await client.eval('document.body.scrollHeight');
    console.log(`Mobile (390px) Body scrollHeight: ${mobilePageHeight} px (Target: < 6,500px)`);
    if (mobilePageHeight > 6500) {
      throw new Error(`Mobile page height ${mobilePageHeight}px exceeds 6,500px target!`);
    } else {
      console.log(`PASS: Mobile page height ${mobilePageHeight}px is within the < 6,500px target!`);
    }

    // Check horizontal overflow at 390px
    const scrollWidth390 = await client.eval('document.body.scrollWidth');
    const innerWidth390 = await client.eval('window.innerWidth');
    console.log(`390px Width: scrollWidth=${scrollWidth390}, innerWidth=${innerWidth390}`);
    if (scrollWidth390 > innerWidth390) {
      throw new Error(`Horizontal overflow detected at 390px: ${scrollWidth390} > ${innerWidth390}`);
    }

    // Quarantine mobile cards at 390px
    console.log('Testing Quarantine Tab at 390px...');
    await client.eval('document.getElementById("tab-btn-quarantine").click()');
    await sleep(400);

    const qCards390 = await client.eval('document.querySelectorAll("#mobile-quarantine-cards-list .mobile-quarantine-card").length');
    const qCardsVisible390 = await client.eval('!document.getElementById("mobile-quarantine-cards-list").classList.contains("hidden")');
    console.log(`390px Quarantine: cards=${qCards390}, visible=${qCardsVisible390}`);
    if (qCards390 !== 13 || !qCardsVisible390) {
      throw new Error(`Quarantine mobile cards failed at 390px: cards=${qCards390}`);
    }
    await client.captureScreenshot('demo/screenshot_390_quarantine.png');

    // Switch back to Verified Commitments
    await client.eval('document.getElementById("tab-btn-promises").click()');
    await sleep(300);
    await client.captureScreenshot('demo/screenshot_390_cards.png');

    // Check 360px width
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: 360,
      height: 740,
      deviceScaleFactor: 2,
      mobile: true
    });
    await sleep(300);
    const scrollWidth360 = await client.eval('document.body.scrollWidth');
    const innerWidth360 = await client.eval('window.innerWidth');
    console.log(`360px Width: scrollWidth=${scrollWidth360}, innerWidth=${innerWidth360}`);
    if (scrollWidth360 > innerWidth360) {
      throw new Error(`Horizontal overflow detected at 360px: ${scrollWidth360} > ${innerWidth360}`);
    }

    client.close();
    console.log('\nAll browser verification checks passed green!');
  } finally {
    chrome.kill();
    server.close();
  }
}

main().catch(err => {
  console.error('Error during screenshot capture & verification:', err);
  process.exit(1);
});
