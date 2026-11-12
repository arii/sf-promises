/**
 * Zero-dependency headless Chrome screenshot capture using native Node WebSocket & CDP
 */

const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');

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
  const PORT = 9225;
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
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: 1280,
      height: 1200,
      deviceScaleFactor: 1,
      mobile: false
    });

    // 1. Main Page Screenshot (Hero + Showcase)
    console.log('Navigating to http://127.0.0.1:8088/');
    await client.send('Page.navigate', { url: 'http://127.0.0.1:8088/' });
    await sleep(1500);
    await client.eval('window.scrollTo(0, 0)');
    await client.captureScreenshot('demo/screenshot_main.png');

    // 2. SF Showcase Tab Switch (Valkyries Sports P04)
    console.log('Selecting SF Valkyries Showcase Tab...');
    await client.eval('document.querySelector("[data-showcase-id=\'P04\']").click()');
    await sleep(600);
    await client.captureScreenshot('demo/screenshot_sf_showcase.png');
    // Switch back to P02
    await client.eval('document.querySelector("[data-showcase-id=\'P02\']").click()');
    await sleep(400);

    // 3. Run P02 Happy Path (Scroll to Pipeline)
    console.log('Running P02 Happy Path...');
    await client.eval('document.getElementById("pipeline-interactive").scrollIntoView({ behavior: "instant", block: "start" })');
    await sleep(300);
    await client.eval('document.getElementById("btn-run-p02").click()');
    await sleep(5500);
    await client.captureScreenshot('demo/screenshot_run_p02.png');

    // 4. Run N01 Watchdog Catch
    console.log('Running N01 Watchdog Catch...');
    await client.eval('document.getElementById("btn-run-n01").click()');
    await sleep(5800);
    await client.captureScreenshot('demo/screenshot_run_n01.png');

    // 5. Open P02 Detail / Inspect Modal
    console.log('Opening P02 Inspect Modal...');
    await client.eval('window.scrollTo(0, 0)');
    await sleep(300);
    await client.eval('(document.getElementById("btn-showcase-inspect") || document.getElementById("btn-open-p02-inspect")).click()');
    await sleep(800);
    await client.captureScreenshot('demo/screenshot_p02_detail.png');
    await client.eval('document.getElementById("btn-close-inspect").click()');
    await sleep(400);

    // 6. Open Quarantine Registry Tab
    console.log('Switching to Quarantine Registry Tab...');
    await client.eval('document.getElementById("data-tables-section").scrollIntoView({ behavior: "instant", block: "start" })');
    await sleep(300);
    await client.eval('document.getElementById("tab-btn-quarantine").click()');
    await sleep(600);
    await client.captureScreenshot('demo/screenshot_quarantine.png');

    // 7. Tracked Promises Table (Desktop)
    console.log('Capturing Tracked Promises Table (Desktop)...');
    await client.eval('document.getElementById("tab-btn-promises").click()');
    await sleep(500);
    await client.captureScreenshot('demo/screenshot_table_desktop.png');

    // 8. Tracked Promises Table (Mobile)
    console.log('Capturing Tracked Promises Table (Mobile)...');
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: 390,
      height: 844,
      deviceScaleFactor: 2,
      mobile: true
    });
    await sleep(500);
    await client.captureScreenshot('demo/screenshot_table_mobile.png');

    client.close();
    console.log('All screenshots captured successfully.');
  } finally {
    chrome.kill();
  }
}

main().catch(err => {
  console.error('Error during screenshot capture:', err);
  process.exit(1);
});
