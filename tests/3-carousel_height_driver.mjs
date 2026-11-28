// Driver for tests/test_carousel_height.py: launches headless Chrome, opens the
// harness page and prints the JSON result of window.runCheck(). Needs Node 22+
// (global WebSocket).
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [chromePath, url] = process.argv.slice(2);
const dir = mkdtempSync(join(tmpdir(), 'carousel-'));
const chrome = spawn(chromePath, ['--headless=new', '--no-sandbox', '--disable-gpu', '--remote-debugging-port=0',
  `--user-data-dir=${dir}`, '--window-size=1200,950', 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let port = null;
chrome.stderr.on('data', (d) => { const m = /DevTools listening on ws:\/\/[^:]+:(\d+)\//.exec(String(d)); if (m) port = m[1]; });
try {
  for (let i = 0; i < 100 && !port; i++) await sleep(100);
  if (!port) throw new Error('Chrome did not expose DevTools');
  const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r));
  let id = 0; const waiting = new Map();
  ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); } });
  const send = (method, params = {}) => new Promise((r) => { const n = ++id; waiting.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
  await send('Page.enable');
  await send('Page.navigate', { url });
  await sleep(2000);
  const res = await send('Runtime.evaluate', { expression: 'window.runCheck()', awaitPromise: true, returnByValue: true });
  if (res.result.exceptionDetails) throw new Error(JSON.stringify(res.result.exceptionDetails));
  console.log(JSON.stringify(res.result.result.value));
} finally {
  chrome.kill();
}
process.exit(0);
