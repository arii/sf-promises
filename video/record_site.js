// Records the real demo page's replay runs as PNG frame sequences via CDP (no audio, no deps).
// Usage: python3 -m http.server 8088 --directory demo  (in another shell), then: node record_site.js
const {spawn} = require('child_process');
const fs = require('fs');
const http = require('http');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const getJson = (u) => new Promise((res, rej) => http.get(u, (r) => { let d=''; r.on('data', c => d+=c); r.on('end', () => res(JSON.parse(d))); }).on('error', rej));
const PORT = 9226, FPS = 15;

async function main() {
  const chrome = spawn('google-chrome', ['--headless=new', `--remote-debugging-port=${PORT}`, '--window-size=1920,1080', '--disable-gpu', '--no-sandbox', '--hide-scrollbars', 'about:blank']);
  await sleep(1500);
  const t = (await getJson(`http://127.0.0.1:${PORT}/json`)).find(x => x.type === 'page');
  const ws = new WebSocket(t.webSocketDebuggerUrl); let id = 1; const cb = new Map();
  await new Promise(r => { ws.onopen = r; });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (cb.has(m.id)) { cb.get(m.id)(m.result); cb.delete(m.id); } };
  const send = (method, params = {}) => new Promise(r => { const i = id++; cb.set(i, r); ws.send(JSON.stringify({id: i, method, params})); });
  const ev = (expression) => send('Runtime.evaluate', {expression, returnByValue: true});
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', {width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false});
  await send('Page.navigate', {url: 'http://127.0.0.1:8088/'});
  await sleep(2000);

  async function record(name, runId, seconds) {
    const dir = `public/rec/${name}`; fs.rmSync(dir, {recursive: true, force: true}); fs.mkdirSync(dir, {recursive: true});
    await ev(`document.getElementById("pipeline-interactive").scrollIntoView({behavior:"instant",block:"start"})`);
    await ev(`(()=>{const s=document.getElementById("run-select"); s.value=${JSON.stringify(runId)}; s.dispatchEvent(new Event("change",{bubbles:true}));})()`);
    await ev(`document.getElementById("btn-pipeline-reset").click()`);
    await sleep(500);
    await ev(`document.getElementById("btn-run-selected").click()`);
    const n = seconds * FPS;
    for (let i = 0; i < n; i++) {
      const t0 = Date.now();
      const r = await send('Page.captureScreenshot', {format: 'jpeg', quality: 80});
      fs.writeFileSync(`${dir}/${String(i).padStart(4, '0')}.jpg`, Buffer.from(r.data, 'base64'));
      await sleep(Math.max(0, 1000 / FPS - (Date.now() - t0)));
    }
    console.log(name, n, 'frames');
  }
  const opts = (await ev(`[...document.getElementById("run-select").options].map(o=>o.value).join(",")`)).result.value;
  console.log('run options:', opts);
  const ids = opts.split(',');
  await record('p02', ids.find(v => /P02/i.test(v)), 14);
  await record('n01', ids.find(v => /N01/i.test(v)), 14);
  chrome.kill(); process.exit(0);
}
main().catch(e => { console.error(e); process.exit(1); });
