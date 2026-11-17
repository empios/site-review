#!/usr/bin/env node
// Full-page screenshots with real device emulation via the Chrome DevTools Protocol.
// usage: node screenshot.mjs CHROME_PATH URL OUTDIR
// Writes OUTDIR/shot-375.png, shot-768.png, shot-1440.png, shot-375-dark.png and OUTDIR/metrics.json.
// Needs Node >= 22 (built-in WebSocket). Exit 1 on failure.
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [chromePath, url, out] = process.argv.slice(2);
if (!chromePath || !url || !out) {
  console.error("usage: node screenshot.mjs CHROME_PATH URL OUTDIR");
  process.exit(2);
}
const MAX_HEIGHT = 6000;
const SHOTS = [
  { name: "shot-375", width: 375, height: 812, mobile: true },
  { name: "shot-768", width: 768, height: 1024, mobile: true },
  { name: "shot-1440", width: 1440, height: 900, mobile: false },
  { name: "shot-375-dark", width: 375, height: 812, mobile: true, dark: true },
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const profile = mkdtempSync(join(tmpdir(), "site-review-chrome-"));
const chrome = spawn(chromePath, [
  "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--hide-scrollbars",
  "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank",
], { stdio: "ignore" });

let ws;
const cleanup = () => {
  try { ws?.close(); } catch {}
  try { chrome.kill("SIGKILL"); } catch {}
  try { rmSync(profile, { recursive: true, force: true }); } catch {}
};
const hardTimeout = setTimeout(() => { console.error("site-review: screenshot timeout"); cleanup(); process.exit(1); }, 150000);

async function devtoolsPort() {
  const file = join(profile, "DevToolsActivePort");
  for (let i = 0; i < 100; i++) {
    if (existsSync(file)) {
      const port = readFileSync(file, "utf8").split("\n")[0].trim();
      if (port) return port;
    }
    await sleep(100);
  }
  throw new Error("Chrome did not expose a DevTools port");
}

function client(socket) {
  let id = 0;
  const pending = new Map();
  const listeners = [];
  socket.addEventListener("message", (ev) => {
    const msg = JSON.parse(typeof ev.data === "string" ? ev.data : ev.data.toString());
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
    } else if (msg.method) {
      listeners.forEach((l) => l(msg));
    }
  });
  return {
    send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const n = ++id;
        pending.set(n, { resolve, reject });
        socket.send(JSON.stringify({ id: n, method, params }));
      });
    },
    waitFor(method, timeout) {
      return new Promise((resolve) => {
        const t = setTimeout(() => resolve(false), timeout);
        listeners.push((m) => { if (m.method === method) { clearTimeout(t); resolve(true); } });
      });
    },
  };
}

async function main() {
  mkdirSync(out, { recursive: true });
  const port = await devtoolsPort();
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const page = targets.find((t) => t.type === "page");
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("WebSocket error")); });
  const cdp = client(ws);
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");

  const metrics = {};
  for (const s of SHOTS) {
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: s.width, height: s.height, deviceScaleFactor: 1, mobile: s.mobile,
    });
    await cdp.send("Emulation.setTouchEmulationEnabled", { enabled: s.mobile });
    await cdp.send("Emulation.setEmulatedMedia", {
      features: [{ name: "prefers-color-scheme", value: s.dark ? "dark" : "light" }],
    });
    const loaded = cdp.waitFor("Page.loadEventFired", 30000);
    const nav = await cdp.send("Page.navigate", { url });
    if (nav.errorText) throw new Error(`navigation failed: ${nav.errorText}`);
    await loaded;
    await sleep(1500);
    const { result } = await cdp.send("Runtime.evaluate", {
      expression: "JSON.stringify({iw: innerWidth, sw: document.documentElement.scrollWidth, sh: document.documentElement.scrollHeight})",
      returnByValue: true,
    });
    const m = JSON.parse(result.value);
    const height = Math.min(Math.max(m.sh, s.height), MAX_HEIGHT);
    const shot = await cdp.send("Page.captureScreenshot", {
      format: "png", captureBeyondViewport: true,
      clip: { x: 0, y: 0, width: s.width, height, scale: 1 },
    });
    writeFileSync(join(out, `${s.name}.png`), Buffer.from(shot.data, "base64"));
    if (!s.dark) {
      metrics[String(s.width)] = {
        innerWidth: m.iw, scrollWidth: m.sw, pageHeight: m.sh, horizontalScroll: m.sw > m.iw + 1,
        truncated: m.sh > MAX_HEIGHT,
      };
    }
  }
  writeFileSync(join(out, "metrics.json"), JSON.stringify(metrics, null, 2));
}

main()
  .then(() => { clearTimeout(hardTimeout); cleanup(); process.exit(0); })
  .catch((e) => { console.error(`site-review: ${e.message}`); clearTimeout(hardTimeout); cleanup(); process.exit(1); });
