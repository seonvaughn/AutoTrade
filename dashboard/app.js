import * as THREE from "three";
import { OrbitControls } from "/static/vendor/OrbitControls.js";

const COLORS = { CALL: 0x26ffa0, PUT: 0xff2d6f, cyan: 0x3ee8ff, gold: 0xffd84a, violet: 0xb98cff };
const $ = (id) => document.getElementById(id);
const money = (x) => `${x >= 0 ? "+" : "-"}$${Math.abs(x).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const cls = (x) => (x >= 0 ? "pos" : "neg");
const px = (x) => (x == null ? "—" : x >= 1000 ? x.toLocaleString(undefined, { maximumFractionDigits: 0 }) : x >= 1 ? x.toFixed(2) : x.toFixed(4));
const qty = (q) => (q >= 1 ? `${+q.toFixed(4)}` : `${+q.toFixed(6)}`);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const store = { state: null, thoughts: {}, candles: {}, ticker: [], alerts: [], selected: null };

// ============================================================ 3D scene
const canvas = $("city");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x07041a);
scene.fog = new THREE.Fog(0x07041a, 70, 190);
const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 500);
camera.position.set(0, 34, 58);
const controls = new OrbitControls(camera, canvas);
controls.target.set(0, 6, 0);
controls.enableDamping = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.35;
controls.maxPolarAngle = Math.PI * 0.47;
controls.minDistance = 20;
controls.maxDistance = 120;

scene.add(new THREE.HemisphereLight(0x8f7bff, 0x0a0520, 0.9));
const key = new THREE.DirectionalLight(0x9fdcff, 0.6);
key.position.set(20, 40, 10);
scene.add(key);

const grid = new THREE.GridHelper(400, 100, 0x4b2bbf, 0x22145e);
grid.position.y = -0.01;
scene.add(grid);
const floor = new THREE.Mesh(new THREE.CircleGeometry(26, 64), new THREE.MeshStandardMaterial({ color: 0x120a46, emissive: 0x1b1070, emissiveIntensity: 0.5 }));
floor.rotation.x = -Math.PI / 2;
scene.add(floor);
for (const [r, c] of [[26, COLORS.cyan], [18, 0x6a4dff]]) {
  const ring = new THREE.Mesh(new THREE.TorusGeometry(r, 0.12, 8, 160), new THREE.MeshBasicMaterial({ color: c }));
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 0.1;
  scene.add(ring);
}

function windowTexture(seed) {
  const c = document.createElement("canvas");
  c.width = 64; c.height = 128;
  const g = c.getContext("2d");
  g.fillStyle = "#06041a"; g.fillRect(0, 0, 64, 128);
  let s = seed * 9301 + 49297;
  const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
  for (let y = 4; y < 124; y += 8) for (let x = 4; x < 60; x += 8) {
    const r = rnd();
    if (r > 0.45) { g.fillStyle = r > 0.85 ? "#ffd84a" : r > 0.65 ? "#7ff3ff" : "#5b7bff"; g.fillRect(x, y, 4, 5); }
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// background skyline (instanced)
{
  const geo = new THREE.BoxGeometry(1, 1, 1);
  const mat = new THREE.MeshStandardMaterial({ color: 0x0d0830, emissive: 0xffffff, emissiveMap: windowTexture(7), emissiveIntensity: 0.55 });
  const n = 420;
  const inst = new THREE.InstancedMesh(geo, mat, n);
  const m = new THREE.Matrix4();
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2;
    const r = 50 + Math.random() * 100;
    const h = 3 + Math.random() ** 2 * 22;
    const w = 2 + Math.random() * 4;
    m.compose(new THREE.Vector3(Math.cos(a) * r, h / 2, Math.sin(a) * r), new THREE.Quaternion(), new THREE.Vector3(w, h, w));
    inst.setMatrixAt(i, m);
  }
  scene.add(inst);
}

// the Vault (center dome)
const vault = new THREE.Group();
{
  const base = new THREE.Mesh(new THREE.CylinderGeometry(4.2, 4.6, 1, 40), new THREE.MeshStandardMaterial({ color: 0x1a1250, emissive: 0x231a80, emissiveIntensity: 0.6 }));
  base.position.y = 0.5;
  base.userData.vault = true;
  const dome = new THREE.Mesh(new THREE.SphereGeometry(3.4, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffe6c4, emissiveIntensity: 0.9 }));
  dome.position.y = 3.2;
  dome.userData.vault = true;
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(3.4, 3.4, 2.2, 40, 1, true), new THREE.MeshStandardMaterial({ color: 0xc8735a, emissive: 0x7a2c1a, emissiveIntensity: 0.6 }));
  drum.position.y = 2.1;
  vault.add(base, drum, dome);
  vault.userData.dome = dome;
  scene.add(vault);
}

const towers = new Map(); // worker name -> {group, beam, halo, top, mats, label}
let ringR = 13;            // radius of the tower ring (grows with the number of towers)
const labelsEl = $("labels");
const vaultLabel = document.createElement("div");
vaultLabel.className = "label vault";
labelsEl.appendChild(vaultLabel);

function buildTowers(workers) {
  const names = workers.map((w) => w.name);
  if (names.join("|") === [...towers.keys()].join("|")) return;
  for (const t of towers.values()) { scene.remove(t.group); t.label.remove(); }
  towers.clear();
  workers.forEach((w, i) => {
    ringR = Math.max(13, (workers.length * 7) / (2 * Math.PI));
    const a = (i / workers.length) * Math.PI * 2 - Math.PI / 2;
    const r = ringR;
    const g = new THREE.Group();
    g.position.set(Math.cos(a) * r, 0, Math.sin(a) * r);
    const tex = windowTexture(i + 3);
    const mats = [];
    let y = 0;
    const tiers = [[5, 7], [3.8, 6], [2.6, 5 + (i % 3) * 1.5]];
    for (const [width, h] of tiers) {
      const t = tex.clone(); t.needsUpdate = true; t.repeat.set(width / 3, h / 4);
      const mat = new THREE.MeshStandardMaterial({ color: 0x0c0a2e, emissive: 0xffffff, emissiveMap: t, emissiveIntensity: 0.9 });
      mats.push(mat);
      const m = new THREE.Mesh(new THREE.BoxGeometry(width, h, width), mat);
      m.position.y = y + h / 2;
      m.userData.worker = w.name;
      g.add(m);
      y += h;
    }
    const top = y;
    const antenna = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 4), new THREE.MeshBasicMaterial({ color: 0xffffff }));
    antenna.position.y = top + 2;
    const halo = new THREE.Mesh(new THREE.TorusGeometry(2.2, 0.1, 8, 64), new THREE.MeshBasicMaterial({ color: COLORS.cyan }));
    halo.rotation.x = Math.PI / 2;
    halo.position.y = top + 0.6;
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 1, 24, 1, true),
      new THREE.MeshBasicMaterial({ color: COLORS.CALL, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false }));
    beam.position.y = top;
    beam.visible = false;
    g.add(antenna, halo, beam);
    scene.add(g);
    const label = document.createElement("div");
    label.className = "label";
    label.addEventListener("click", () => select(w.name));
    label.addEventListener("dblclick", () => enterTower(w.name));
    label.style.pointerEvents = "auto";
    label.style.cursor = "pointer";
    labelsEl.appendChild(label);
    towers.set(w.name, { group: g, beam, halo, top, mats, label, charge: 0, side: "CALL", status: "watching" });
  });
  if (!store.selected && workers.length) select(workers[0].name);
}

function pulse(worker, color) {
  const t = towers.get(worker);
  if (!t) return;
  const ring = new THREE.Mesh(new THREE.TorusGeometry(2, 0.25, 8, 64), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.9 }));
  ring.rotation.x = Math.PI / 2;
  ring.position.copy(t.group.position).setY(0.4);
  ring.userData.born = performance.now();
  scene.add(ring);
  pulses.push(ring);
}
const pulses = [];

function floater(worker, text, good) {
  const t = towers.get(worker);
  if (!t) return;
  const p = t.group.position.clone().setY(t.top + 6).project(camera);
  const el = document.createElement("div");
  el.className = `floater ${good ? "pos" : "neg"}`;
  el.textContent = text;
  el.style.left = `${(p.x * 0.5 + 0.5) * innerWidth}px`;
  el.style.top = `${(-p.y * 0.5 + 0.5) * innerHeight}px`;
  $("floaters").appendChild(el);
  setTimeout(() => el.remove(), 2300);
}

const raycaster = new THREE.Raycaster();
function pick(ev) {
  const v = new THREE.Vector2((ev.clientX / innerWidth) * 2 - 1, -(ev.clientY / innerHeight) * 2 + 1);
  raycaster.setFromCamera(v, camera);
  const targets = [...towers.values()].map((t) => t.group).concat([...crewBots.values()].map((b) => b.group), [vault]);
  const hit = raycaster.intersectObjects(targets, true).find((h) => h.object.userData.worker || h.object.userData.bot || h.object.userData.vault);
  return hit ? hit.object.userData : null;
}
canvas.addEventListener("click", (ev) => {
  const hit = pick(ev);
  if (!hit) { hideBotCard(); return; }
  if (hit.worker) { hideBotCard(); select(hit.worker); }
  else if (hit.bot) showBotCard(hit.bot, ev.clientX, ev.clientY);
  else if (hit.vault) enterVault();
});
canvas.addEventListener("dblclick", (ev) => {
  const hit = pick(ev);
  if (hit && hit.worker) enterTower(hit.worker);
});
let hoverAt = 0;
canvas.addEventListener("pointermove", (ev) => {
  const now = performance.now();
  if (now - hoverAt < 60 || ev.pointerType === "touch") return;
  hoverAt = now;
  const hit = pick(ev);
  const tip = $("hovertip");
  if (!hit) { tip.hidden = true; canvas.style.cursor = ""; return; }
  canvas.style.cursor = "pointer";
  tip.textContent = hit.worker ? `${hit.worker} · click to select, double-click to enter`
    : hit.bot ? `${hit.bot} · click for details` : "The Vault · click to enter";
  tip.style.left = `${ev.clientX}px`; tip.style.top = `${ev.clientY}px`;
  tip.hidden = false;
});
canvas.addEventListener("pointerleave", () => ($("hovertip").hidden = true));

function resize() {
  renderer.setSize(innerWidth, innerHeight, false);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();
if (innerWidth / innerHeight < 1) camera.position.multiplyScalar(1.5); // portrait: pull back to fit the city

function project(vec, el) {
  const p = vec.clone().project(camera);
  const visible = p.z < 1;
  el.style.display = visible ? "block" : "none";
  el.style.left = `${(p.x * 0.5 + 0.5) * innerWidth}px`;
  el.style.top = `${(-p.y * 0.5 + 0.5) * innerHeight}px`;
}

function animate(now) {
  requestAnimationFrame(animate);
  stepFlight(now);
  controls.update();
  animateCrew(now);
  for (const t of towers.values()) {
    const active = t.status === "in_trade";
    const show = active || t.charge >= 5;
    t.beam.visible = show;
    if (show) {
      const h = active ? 70 : 4 + t.charge * 0.55;
      t.beam.scale.y = h;
      t.beam.position.y = t.top + h / 2;
      t.beam.material.color.setHex(COLORS[t.side] || COLORS.CALL);
      t.beam.material.opacity = active ? 0.55 + 0.25 * Math.sin(now / 180) : 0.15 + t.charge / 220;
    }
    const haloColor = { in_trade: COLORS[t.side] || COLORS.CALL, charging: COLORS.gold, clocked_out: COLORS.violet }[t.status] || COLORS.cyan;
    t.halo.material.color.setHex(haloColor);
    t.halo.rotation.z = now / 1200;
    for (const m of t.mats) m.emissiveIntensity = t.status === "clocked_out" ? 0.35 : 0.9;
    project(t.group.position.clone().setY(t.top + 5.5), t.label);
  }
  project(new THREE.Vector3(0, 7.5, 0), vaultLabel);
  for (let i = pulses.length - 1; i >= 0; i--) {
    const r = pulses[i];
    const age = (now - r.userData.born) / 1600;
    r.scale.setScalar(1 + age * 5);
    r.material.opacity = Math.max(0, 0.9 * (1 - age));
    if (age >= 1) { scene.remove(r); pulses.splice(i, 1); }
  }
  renderer.render(scene, camera);
}
requestAnimationFrame(animate);

// ============================================================ panels
function select(name) {
  store.selected = name;
  renderPanels();
}

function timeLeft(state) {
  if (!state.clock || !state.close) return "";
  const ms = new Date(state.close) - new Date(state.clock);
  if (ms <= 0) return "";
  const m = Math.floor(ms / 60000);
  return ` · ${Math.floor(m / 60)}h ${m % 60}m to close`;
}

function renderTop(s) {
  const mode = $("mode");
  mode.textContent = s.mode === "replay" || s.mode === "backtest" ? `REPLAY${s.day ? " · " + s.day : ""}` : s.mode.toUpperCase();
  mode.className = `badge ${s.mode}`;
  $("clock").textContent = s.clock ? `${s.clock.slice(11, 19)} ET` : "--:--:-- ET";
  const open = ["open", "closing", "flattening"].includes(s.session);
  const mk = $("market");
  mk.textContent = `● ${open ? "market open" : s.session === "pre-market" ? "pre-market" : "market closed"}${open ? timeLeft(s) : ""}`;
  mk.className = `market ${open ? "open" : ""}`;
  const problems = Object.values(s.health || {});
  const h = $("health");
  h.textContent = problems.length ? `● ${problems[0]}` : "● systems ok";
  h.className = `health ${problems.length ? "bad" : "ok"}`;
  const v = $("vault-amt");
  v.textContent = money(s.vault);
  v.className = cls(s.vault);
  const k = $("kill");
  k.classList.toggle("engaged", s.kill.engaged);
  k.textContent = s.kill.engaged ? "Kill switch ON" : "Kill switch";
  k.title = s.kill.reason || "Flatten every position and stop all new trades";
  vaultLabel.innerHTML = `THE VAULT · ${esc(s.day || "")}<br><b class="${cls(s.vault)}">${money(s.vault)}</b><br><span class="dim">${s.workers.length} workers on shift</span>`;
}

function workerTotal(w) { return w.realized + w.unrealized; }

function renderLeft(s) {
  const ranked = [...s.workers].sort((a, b) => workerTotal(b) - workerTotal(a));
  $("leaderboard").innerHTML = ranked.map((w) =>
    `<li data-w="${esc(w.name)}" class="${w.name === store.selected ? "sel" : ""}"><span>${esc(w.name)}</span><b class="${cls(workerTotal(w))}">${money(workerTotal(w))}</b></li>`).join("");
  const maxAbs = Math.max(50, ...s.workers.map((w) => Math.abs(workerTotal(w))));
  $("heatmap").innerHTML = s.workers.map((w) => {
    const v = workerTotal(w);
    const a = 0.15 + 0.75 * Math.min(1, Math.abs(v) / maxAbs);
    const bg = v >= 0 ? `rgba(38,255,160,${a})` : `rgba(255,45,111,${a})`;
    return `<div class="tile" data-w="${esc(w.name)}" style="background:${bg}">${esc(w.name)}<small>${money(v)}</small></div>`;
  }).join("");
  for (const el of document.querySelectorAll("[data-w]")) el.onclick = () => select(el.dataset.w);
  $("alerts").innerHTML = store.alerts.slice(0, 12).map((a) => `<li class="${a.level}">${a.t} ${esc(a.text)}</li>`).join("");
}

const TRIGGER = { vwap_cross: "VWAP cross", ema50_cross: "EMA50 cross", orb: "15-min range break",
  zone_reaction: "Supply/demand zone (30s)", structure_break: "Structure break (5m)", fib_pullback: "Fib pullback (1m)",
  smc_retrace: "TJR: sweep → break → retrace → break", smc_bos: "TJR: sweep → break",
  orb15_breakout: "15m range breakout (gap)", orb15_retest: "15m range retest", orb15_reversal: "15m range reversal",
  orb_ntz_retest: "ORB retest outside the no-trading zone" };

function renderRight(s) {
  const w = s.workers.find((x) => x.name === store.selected) || s.workers[0];
  if (!w) return;
  $("tower-name").textContent = `${w.name} · ${w.symbol}${s.market === "crypto" ? "" : w.dte ? ` · ${w.dte}DTE` : " · 0DTE"}`;
  const st = $("tower-status");
  st.textContent = w.status === "clocked_out" ? `clocked out (${w.clock_reason})` : w.status.replace("_", " ");
  st.className = `pill ${w.status}`;
  $("scanner").innerHTML = w.triggers.map((t) => {
    const x = w.setups[t];
    if (!x) return `<div class="scan"><div class="row"><span>${TRIGGER[t]}</span><span class="dim">warming up</span></div><div class="bar"><i style="width:0"></i></div></div>`;
    const arrow = x.side === "CALL" ? "▲" : "▼";
    return `<div class="scan"><div class="row"><span>${TRIGGER[t]} ${arrow} ${x.side} · ${x.distance.toFixed(2)} ATR away</span><b>${x.charge}%</b></div>
      <div class="bar ${x.side}"><i style="width:${x.charge}%"></i></div></div>`;
  }).join("");
  const total = workerTotal(w);
  const pos = w.position;
  const posHtml = pos ? `<div class="${cls(pos.pnl)}">IN A TRADE · ${pos.right === "CALL" ? "▲" : "▼"} ${qty(pos.qty)}× ${esc(pos.label)} @ ${px(pos.entry)} → ${px(pos.mark)} (${money(pos.pnl)})</div>` : "";
  const wr = w.trades ? Math.round((100 * w.wins) / w.trades) : 0;
  $("earned").innerHTML = `<div class="big ${cls(total)}">${money(total)}</div>
    <div class="dim">${w.trades} trades · ${w.wins} wins · ${wr}% win rate · goal ${money(w.goal)} / stop ${money(-w.max_loss)}</div>${posHtml}
    <table>${w.last_trades.slice(0, 8).map((t) => `<tr><td>${t.t} ${t.side === "CALL" ? "▲" : "▼"} ${qty(t.qty)} ${esc(t.sym)} · ${esc(t.reason.replace("_", " "))}</td><td class="${cls(t.pnl)}">${money(t.pnl)}</td></tr>`).join("")}</table>`;
  $("thoughts").innerHTML = (store.thoughts[w.name] || []).slice(0, 40).map((t) => `<li class="${t.tone}"><span class="t">${t.t.slice(0, 5)}</span><span>${esc(t.text)}</span></li>`).join("");
  $("chart-title").textContent = `${w.symbol} · 1-min${s.prices[w.symbol] ? ` · ${s.prices[w.symbol].toFixed(2)}` : ""}`;
  drawChart(w, s);
}

function drawChart(w, s, cv = $("chart"), count = 90) {
  const g = cv.getContext("2d");
  const W = cv.width, H = cv.height;
  g.clearRect(0, 0, W, H);
  const bars = (store.candles[w.symbol] || []).slice(-count);
  if (!bars.length) { g.fillStyle = "#9a93c9"; g.font = "13px sans-serif"; g.fillText("waiting for the first candle…", 16, 28); return; }
  const vals = bars.flatMap((b) => [b.h, b.l, b.vwap, b.ema50].filter((v) => v != null));
  if (s.prices[w.symbol] != null) vals.push(s.prices[w.symbol]);
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.08 || 0.5; lo -= pad; hi += pad;
  const y = (v) => H - 14 - ((v - lo) / (hi - lo)) * (H - 24);
  const step = (W - 50) / bars.length;
  g.strokeStyle = "rgba(255,255,255,.06)";
  for (let i = 0; i < 4; i++) { const yy = 6 + i * (H - 20) / 3; g.beginPath(); g.moveTo(0, yy); g.lineTo(W - 46, yy); g.stroke(); }
  g.fillStyle = "#9a93c9"; g.font = "10px monospace";
  for (const v of [hi - pad, lo + pad]) g.fillText(px(v), W - 44, y(v) + 3);
  bars.forEach((b, i) => {
    const x = i * step + step / 2;
    const up = b.c >= b.o;
    g.strokeStyle = g.fillStyle = up ? "#26ffa0" : "#ff2d6f";
    g.beginPath(); g.moveTo(x, y(b.h)); g.lineTo(x, y(b.l)); g.stroke();
    const top = y(Math.max(b.o, b.c)), bot = y(Math.min(b.o, b.c));
    g.fillRect(x - step * 0.32, top, step * 0.64, Math.max(1, bot - top));
  });
  for (const [k, color] of [["vwap", "#ffd84a"], ["ema50", "#b98cff"]]) {
    g.strokeStyle = color; g.lineWidth = 1.6; g.beginPath();
    let started = false;
    bars.forEach((b, i) => { if (b[k] == null) return; const x = i * step + step / 2; started ? g.lineTo(x, y(b[k])) : g.moveTo(x, y(b[k])); started = true; });
    g.stroke(); g.lineWidth = 1;
  }
  for (const z of ((s.analysis || {})[w.symbol] || {}).zones || []) {
    if (z.hi < lo || z.lo > hi) continue;
    const top = y(Math.min(z.hi, hi)), bot = y(Math.max(z.lo, lo));
    g.fillStyle = z.kind === "demand" ? "rgba(38,255,160,.10)" : "rgba(255,45,111,.10)";
    g.fillRect(0, top, W - 46, Math.max(2, bot - top));
    g.fillStyle = z.kind === "demand" ? "rgba(38,255,160,.8)" : "rgba(255,45,111,.8)";
    g.font = "10px sans-serif";
    g.fillText(`${z.tf} ${z.kind}`, W - 120, top + 11);
  }
  for (const lv of (s.levels || {})[w.symbol] || []) {
    if (lv.price < lo || lv.price > hi) continue;
    const yy = y(lv.price);
    g.strokeStyle = "rgba(244,241,255,.45)"; g.setLineDash([2, 5]); g.lineWidth = 1;
    g.beginPath(); g.moveTo(0, yy); g.lineTo(W - 46, yy); g.stroke(); g.setLineDash([]);
    g.fillStyle = "rgba(244,241,255,.75)"; g.font = "10px sans-serif";
    g.fillText(lv.label, 4, yy - 3);
  }
  const last = s.prices[w.symbol];
  if (last) { g.setLineDash([4, 4]); g.strokeStyle = "rgba(62,232,255,.7)"; g.beginPath(); g.moveTo(0, y(last)); g.lineTo(W - 46, y(last)); g.stroke(); g.setLineDash([]); }
}

function renderBottom(s) {
  const today = s.day;
  $("calendar").innerHTML = s.calendar.map((d) => {
    const dt = new Date(d.day + "T12:00:00");
    const lbl = dt.toLocaleDateString(undefined, { weekday: "short", month: "numeric", day: "numeric" });
    return `<div class="chip ${d.day === today ? "today" : ""}">${lbl}<b class="${cls(d.pnl)}">${money(d.pnl)}</b></div>`;
  }).join("") || `<div class="chip dim">no finished days yet</div>`;
  $("ticker-track").innerHTML = store.ticker.slice(0, 12).map((t) => `<span class="${t.tone}">${esc(t.text)}</span>`).join("");
}

function renderPanels() {
  const s = store.state;
  if (!s) return;
  buildTowers(s.workers);
  for (const w of s.workers) {
    const t = towers.get(w.name);
    if (!t) continue;
    t.status = w.status;
    t.charge = w.status === "in_trade" ? 100 : w.charge || 0;
    t.side = w.position ? w.position.right : w.side || "CALL";
    const total = workerTotal(w);
    const st = { watching: "watching", charging: `charging ${w.side === "PUT" ? "▼ PUT" : "▲ CALL"} ${w.charge}%`,
      in_trade: `in a trade ${w.position ? money(w.position.pnl) : ""}`, clocked_out: "clocked out" }[w.status];
    t.label.className = `label ${w.status}`;
    t.label.innerHTML = `<div class="n">${w.name === store.selected ? "★ " : ""}${esc(w.name)}</div><div class="dim">${st}</div><div class="${cls(total)}">earned ${money(total)}</div>`;
  }
  renderTop(s); renderLeft(s); renderRight(s); renderBottom(s);
  updateCrew(s.crew || []);
  if (!$("inside").hidden) renderInside();
}

function showSummary(m) {
  $("summary-day").textContent = m.day;
  const tot = $("summary-total");
  tot.textContent = money(m.total);
  tot.className = `big center ${cls(m.total)}`;
  $("summary-meta").textContent = `${Object.keys(m.by_worker).length} workers · ${m.trades} trades · ${m.wins} wins · one trading day`;
  const maxAbs = Math.max(1, ...Object.values(m.by_worker).map(Math.abs));
  $("summary-bars").innerHTML = Object.entries(m.by_worker).map(([n, v]) =>
    `<div class="sbar"><span class="${cls(v)}">${money(v)}</span><i style="height:${Math.max(2, (90 * Math.abs(v)) / maxAbs)}%;background:${v >= 0 ? "#26ffa0" : "#ff2d6f"}"></i><span>${esc(n)}</span></div>`).join("");
  $("summary-top").textContent = m.top ? `👑 TOP WORKER ${m.top} ${money(m.by_worker[m.top])}` : "";
  $("summary").hidden = false;
}
$("summary-close").onclick = () => ($("summary").hidden = true);
$("roster-btn").onclick = () => {
  const r = (store.state && store.state.roster) || [];
  $("roster-list").innerHTML = r.map((b) => `<li><b>${esc(b.name)}</b> — ${esc(b.skill)}</li>`).join("");
  $("roster").hidden = false;
};
$("roster-close").onclick = () => ($("roster").hidden = true);
$("kill").onclick = async () => {
  const engaged = store.state && store.state.kill.engaged;
  const msg = engaged ? "Release the kill switch and allow new trades again?" : "KILL SWITCH: close every open position and stop all new trades?";
  if (!confirm(msg)) return;
  await fetch("/api/kill", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ engage: !engaged }) });
};

// ============================================================ live connection
let renderQueued = false;
function scheduleRender() {
  if (renderQueued) return;
  renderQueued = true;
  requestAnimationFrame(() => { renderQueued = false; renderPanels(); });
}

function handle(m) {
  switch (m.type) {
    case "snapshot":
      store.state = m.state; store.thoughts = m.thoughts; store.candles = m.candles;
      store.ticker = m.ticker; store.alerts = m.alerts;
      break;
    case "state": store.state = m.state; break;
    case "thought": (store.thoughts[m.worker] ||= []).unshift(m); store.thoughts[m.worker].length = Math.min(60, store.thoughts[m.worker].length); break;
    case "ticker": store.ticker.unshift(m); store.ticker.length = Math.min(40, store.ticker.length); break;
    case "alert": store.alerts.unshift(m); store.alerts.length = Math.min(20, store.alerts.length); break;
    case "candle": {
      const arr = (store.candles[m.symbol] ||= []);
      const i = arr.findIndex((c) => c.t === m.t);
      if (i >= 0) arr[i] = m; else { arr.push(m); if (arr.length > 400) arr.shift(); }
      break;
    }
    case "fire": pulse(m.worker, COLORS[m.side]); break;
    case "closed": floater(m.worker, money(m.pnl), m.pnl >= 0); pulse(m.worker, m.pnl >= 0 ? COLORS.CALL : COLORS.PUT); break;
    case "summary": showSummary(m); break;
    case "reset_day": store.candles = {}; store.thoughts = {}; break;
    case "batch": m.items.forEach(handle); return;
  }
  scheduleRender();
}

function connect() {
  const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
  ws.onopen = () => ($("offline").hidden = true);
  ws.onmessage = (ev) => handle(JSON.parse(ev.data));
  ws.onclose = () => { $("offline").hidden = false; setTimeout(connect, 1500); };
}
connect();

// ============================================================ the crew: one little robot per bot
const CREW_GROUPS = [
  { cat: "Data", color: COLORS.cyan, bots: ["price_feed", "candles", "options_chain", "clock"] },
  { cat: "Research", color: 0xf4f1ff, bots: ["key_levels", "edge_tracker", "research_gate"] },
  { cat: "Chart reading", color: 0x7cf3c8, bots: ["timeframes", "htf_levels", "structure", "zones"] },
  { cat: "Indicators & signals", color: COLORS.gold, bots: ["atr", "vwap", "ema50", "opening_range", "sig_vwap_cross", "sig_ema50_cross", "sig_orb",
    "sig_zone_reaction", "sig_structure_break", "sig_fib_pullback"] },
  { cat: "Decisions", color: COLORS.violet, bots: ["signal_filter", "contract_selector", "position_sizer", "risk_manager"] },
  { cat: "Execution", color: COLORS.CALL, bots: ["execution", "exit_manager", "reconciliation"] },
  { cat: "Records & ops", color: 0xff7ac8, bots: ["ledger", "daily_goal", "journal", "analyst", "health", "alerts", "dashboard", "orchestrator"] },
];
const crewInfo = new Map(); // name -> {cat, color}
for (const g of CREW_GROUPS) for (const b of g.bots) crewInfo.set(b, { cat: g.cat, color: g.color });
const crewBots = new Map(); // name -> {group, eye, head, handled, activeUntil, phase}
const crewData = new Map(); // name -> latest crew row from the server

function buildCrew(names) {
  if (names.join("|") === [...crewBots.keys()].join("|")) return;
  for (const b of crewBots.values()) scene.remove(b.group);
  crewBots.clear();
  const r = ringR + 8;
  names.forEach((name, i) => {
    const info = crewInfo.get(name) || { cat: "Crew", color: 0xffffff };
    const a = (i / names.length) * Math.PI * 2 + Math.PI / names.length;
    const g = new THREE.Group();
    g.position.set(Math.cos(a) * r, 0, Math.sin(a) * r);
    g.rotation.y = -a - Math.PI / 2; // face the center
    const shell = new THREE.MeshStandardMaterial({ color: 0x1a1450, emissive: info.color, emissiveIntensity: 0.25, metalness: 0.3, roughness: 0.5 });
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.45, 0.7, 4, 12), shell);
    body.position.y = 0.95;
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.38, 16, 12), shell);
    head.position.y = 1.85;
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.11, 10, 8), new THREE.MeshBasicMaterial({ color: info.color }));
    eye.position.set(0, 1.88, 0.33);
    const antenna = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.4), new THREE.MeshBasicMaterial({ color: 0xffffff }));
    antenna.position.y = 2.35;
    const pad = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.75, 0.12, 24), new THREE.MeshBasicMaterial({ color: info.color, transparent: true, opacity: 0.35 }));
    pad.position.y = 0.06;
    for (const m of [body, head, eye, antenna, pad]) m.userData.bot = name;
    g.add(pad, body, head, eye, antenna);
    scene.add(g);
    crewBots.set(name, { group: g, eye, head, shell, body, handled: null, activeUntil: 0, phase: i * 0.7 });
  });
}

function updateCrew(rows) {
  if (!rows.length) return;
  buildCrew(rows.map((r) => r.name));
  const now = performance.now();
  for (const row of rows) {
    crewData.set(row.name, row);
    const b = crewBots.get(row.name);
    if (!b) continue;
    if (b.handled !== null && row.handled > b.handled) b.activeUntil = now + 900;
    b.handled = row.handled;
  }
  const card = $("botcard");
  if (!card.hidden && card.dataset.bot) fillBotCard(card.dataset.bot);
}

function animateCrew(now) {
  for (const b of crewBots.values()) {
    const busy = now < b.activeUntil;
    const lift = busy ? 0.25 + 0.15 * Math.sin(now / 90 + b.phase) : 0.05 * Math.sin(now / 900 + b.phase);
    b.body.position.y = 0.95 + lift;
    b.head.position.y = 1.85 + lift;
    b.eye.position.y = 1.88 + lift;
    b.head.rotation.y = busy ? Math.sin(now / 160 + b.phase) * 0.6 : Math.sin(now / 2400 + b.phase) * 0.3;
    b.shell.emissiveIntensity = busy ? 0.9 : 0.25;
    b.eye.scale.setScalar(busy ? 1.5 : 1);
  }
}

function fillBotCard(name) {
  const card = $("botcard");
  const row = crewData.get(name) || { name, skill: "", handled: 0, last: "", ts: null };
  const info = crewInfo.get(name) || { cat: "Crew" };
  const busy = (crewBots.get(name)?.activeUntil || 0) > performance.now();
  const s = store.state;
  const towersFor = s ? s.workers.filter((w) => (w.crew || []).includes(name)).map((w) => w.name) : [];
  card.innerHTML = `<button class="x" type="button" aria-label="Close">×</button>
    <div class="cat">${esc(info.cat)}</div>
    <h3><span class="dot ${busy ? "busy" : ""}"></span>${esc(name)}</h3>
    <p>${esc(row.skill)}</p>
    <dl>
      <dt>events handled</dt><dd>${(row.handled || 0).toLocaleString()}</dd>
      <dt>last job</dt><dd>${esc(row.last || "—")}${row.ts ? ` @ ${row.ts}` : ""}</dd>
      <dt>works for</dt><dd>${towersFor.length ? esc(towersFor.join(", ")) : "the whole city"}</dd>
    </dl>`;
  card.querySelector(".x").onclick = hideBotCard;
}

function showBotCard(name, x, y) {
  const card = $("botcard");
  card.dataset.bot = name;
  fillBotCard(name);
  card.hidden = false;
  card.style.left = `${Math.min(x + 14, innerWidth - 300)}px`;
  card.style.top = `${Math.min(y + 14, innerHeight - 220)}px`;
}
function hideBotCard() { $("botcard").hidden = true; delete $("botcard").dataset.bot; }

// ============================================================ camera flights
let flight = null;
let home = null; // where the camera was before entering a building
function flyTo(pos, target, ms, then) {
  flight = { p0: camera.position.clone(), t0: controls.target.clone(), p1: pos, t1: target, start: performance.now(), ms, then };
  controls.autoRotate = false;
  controls.enabled = false;
}
function stepFlight(now) {
  if (!flight) return;
  const k = Math.min(1, (now - flight.start) / flight.ms);
  const e = k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2; // ease in-out
  camera.position.lerpVectors(flight.p0, flight.p1, e);
  controls.target.lerpVectors(flight.t0, flight.t1, e);
  if (k >= 1) {
    const done = flight.then;
    flight = null;
    controls.enabled = true;
    if (done) done();
  }
}
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

// ============================================================ inside a building
const inside = { kind: null, name: null, floor: null, html: "" };

function enterTower(name) {
  const t = towers.get(name);
  if (!t) return;
  select(name);
  hideBotCard();
  const p = t.group.position;
  const out = p.clone().setY(0).normalize();
  home = home || { pos: camera.position.clone(), target: controls.target.clone() };
  openInside("tower", name, "trading", p.clone().add(out.multiplyScalar(6)).setY(2.2), p.clone().setY(2.2));
}

function enterVault() {
  hideBotCard();
  home = home || { pos: camera.position.clone(), target: controls.target.clone() };
  openInside("vault", "The Vault", "vault", new THREE.Vector3(0, 2.4, 8), new THREE.Vector3(0, 2, 0));
}

function openInside(kind, name, floor, camPos, camTarget) {
  Object.assign(inside, { kind, name, floor, html: "" });
  const show = () => { $("inside").hidden = false; renderInside(); $("inside-exit").focus(); };
  if (reducedMotion) show(); else flyTo(camPos, camTarget, 900, show);
}

function exitInside() {
  $("inside").hidden = true;
  inside.kind = null;
  if (home) {
    const back = home;
    home = null;
    const restore = () => { controls.autoRotate = true; };
    if (reducedMotion) { camera.position.copy(back.pos); controls.target.copy(back.target); restore(); }
    else flyTo(back.pos, back.target, 900, restore);
  }
}

$("enter-btn").onclick = () => store.selected && enterTower(store.selected);
$("inside-exit").onclick = exitInside;
addEventListener("keydown", (ev) => {
  if (ev.key !== "Escape") return;
  if (!$("inside").hidden) exitInside();
  else hideBotCard();
});

const TOWER_FLOORS = [
  ["research", "6", "Research room"], ["trading", "5", "Trading floor"], ["charts", "4", "Chart room"], ["thoughts", "3", "Thoughts"],
  ["trades", "2", "Trade log"], ["rules", "1", "Lobby · rules"], ["crew", "B", "Crew room"],
];
const VAULT_FLOORS = [["vault", "1", "Vault floor"], ["days", "2", "Day by day"], ["crew", "B", "The whole crew"]];

function renderInside() {
  const s = store.state;
  if (!s || !inside.kind) return;
  const floors = inside.kind === "vault" ? VAULT_FLOORS : TOWER_FLOORS;
  const w = inside.kind === "tower" ? s.workers.find((x) => x.name === inside.name) : null;
  if (inside.kind === "tower" && !w) { exitInside(); return; }
  $("inside-kicker").textContent = inside.kind === "vault" ? "Central bank of Scalp City" : `Tower · ${w.symbol}`;
  $("inside-title").textContent = inside.name;
  const st = $("inside-status");
  if (w) {
    st.hidden = false;
    st.textContent = w.status === "clocked_out" ? `clocked out (${w.clock_reason})` : w.status.replace("_", " ");
    st.className = `pill ${w.status}`;
  } else st.hidden = true;
  const nav = floors.map(([id, lvl, label]) =>
    `<button type="button" data-floor="${id}" aria-current="${id === inside.floor}"><span class="lvl">${lvl}</span>${label}</button>`).join("");
  if ($("elevator").dataset.nav !== nav) {
    $("elevator").innerHTML = nav;
    $("elevator").dataset.nav = nav;
    for (const b of $("elevator").querySelectorAll("button")) b.onclick = () => { inside.floor = b.dataset.floor; inside.html = ""; renderInside(); };
  }
  const html = w ? towerFloor(w, s) : vaultFloor(s);
  if (html !== inside.html) { $("floor").innerHTML = html; inside.html = html; wireFloor(); }
  const cv = $("floor-chart");
  if (cv && w) drawChart(w, s, cv, 240);
}

function wireFloor() {
  for (const el of $("floor").querySelectorAll("[data-bot]")) {
    el.onclick = (ev) => showBotCard(el.dataset.bot, ev.clientX, ev.clientY);
  }
  for (const el of $("floor").querySelectorAll("[data-enter]")) {
    el.onclick = () => { $("inside").hidden = true; inside.kind = null; enterTower(el.dataset.enter); };
  }
}

const card = (k, v, c = "") => `<div class="card"><div class="k">${k}</div><div class="v ${c}">${v}</div></div>`;
const REASON = { profit_lock: "🔒 profit lock", target: "🎯 target", stop: "🛑 stop", time: "⏱ time", reversal: "↩ reversal", end_of_day: "🔔 end of day", kill: "⛔ kill switch" };

function goalBar(w) {
  const total = workerTotal(w);
  const span = Math.max(w.goal, w.max_loss);
  const pct = Math.min(50, (Math.abs(total) / span) * 50);
  const style = total >= 0 ? `left:50%;width:${pct}%;background:var(--call)` : `right:50%;width:${pct}%;background:var(--put)`;
  return `<div class="progress" role="img" aria-label="day P&L ${money(total)} between loss limit ${money(-w.max_loss)} and goal ${money(w.goal)}"><i style="${style}"></i><span class="zero"></span></div>
    <div class="dim" style="display:flex;justify-content:space-between;font-size:11px;margin-top:3px"><span>loss limit ${money(-w.max_loss)}</span><span>goal ${money(w.goal)}</span></div>`;
}

function crewCards(names) {
  const now = performance.now();
  return `<div class="crew">${names.map((n) => {
    const row = crewData.get(n) || { skill: "", handled: 0 };
    const busy = (crewBots.get(n)?.activeUntil || 0) > now;
    return `<div class="card" data-bot="${esc(n)}"><span class="dot ${busy ? "busy" : ""}" style="margin-top:5px"></span>
      <div><b>${esc(n)}</b><small>${esc(row.skill)}</small><small class="mono">${(row.handled || 0).toLocaleString()} events · ${esc(row.last || "idle")}</small></div></div>`;
  }).join("")}</div>`;
}

const TRIG_NAME = TRIGGER;

function tjrBlock(t) {
  if (!t || !t.bias) return "";
  const tone = (x) => (x === "bullish" ? "pos" : x === "bearish" ? "neg" : "dim");
  const cells = Object.entries({ weekly: t.bias.W, daily: t.bias.D, "4 hour": t.bias["4h"], ...Object.fromEntries(
    Object.entries(t.structure || {}).map(([tf, v]) => [tf, v])) }).map(([k, v]) =>
    `<td class="${tone(v)}"><small class="dim">${k}</small><br><b>${v || "unknown"}</b></td>`).join("");
  const rng = t.daily_range ? `daily equilibrium ${px(t.daily_range.eq)} (range ${px(t.daily_range.bottom)} – ${px(t.daily_range.top)})` : "daily range not known yet";
  const setups = (t.setups || []).map((x) => `<tr><td>${x.tf}</td><td class="${x.side === "CALL" ? "pos" : "neg"}">${x.side === "CALL" ? "▲ long" : "▼ short"}</td>
    <td>${x.sweep ? `swept ${x.sweep.tf} ${px(x.sweep.level)}` : "no sweep"}</td><td>${x.armed ? `in ${esc((x.poi || []).join(", "))}, waiting for the break` : "waiting for the retrace"}</td><td class="mono">stop ${px(x.stop)}</td></tr>`).join("");
  const plan = t.plan
    ? `<div class="${t.plan.cleared ? "pos" : "neg"}" style="margin:6px 0"><b>🌅 Morning study ${t.plan.at}: ${t.plan.cleared ? "cleared to trade today" : "standing down today"}</b>${t.plan.reasons.length ? ` · ${t.plan.reasons.map(esc).join("; ")}` : ""}</div>`
    : `<div class="dim" style="margin:6px 0">🌅 Morning study runs at ${t.study_time || "07:00"} ET. Nothing trades before it.</div>`;
  return `<h2 style="margin-top:16px">TJR read · daily bias first</h2>${plan}
    <div class="dim">Plan: setups that run ${t.bias_mode === "against" ? "against" : t.bias_mode === "with" ? "with" : "either way to"} the daily bias.</div>
    <table><tbody><tr>${cells}</tr></tbody></table>
    <div class="dim" style="margin:6px 0">${rng}${t.news_today ? ` · <b class="neg">${esc(t.news_today)}</b>` : ""}</div>
    ${setups ? `<table><thead><tr><th>setup</th><th>side</th><th>sweep</th><th>stage</th><th></th></tr></thead><tbody>${setups}</tbody></table>` : `<div class="empty">No sweep-and-break setup open right now.</div>`}
    ${(t.lessons || []).length ? `<h2 style="margin-top:12px">Lessons book · learned from every setup and trade</h2><table><tbody>${t.lessons.map((l) =>
      `<tr><td class="${l.kind === "avoid" ? "neg" : "pos"}">${l.kind === "avoid" ? "avoid" : "favor"}</td><td>${esc(l.feature.replace(/_/g, " "))} = ${esc(l.value)}</td><td class="r">${l.avg_r >= 0 ? "+" : ""}${l.avg_r.toFixed(2)}R over ${l.n}</td></tr>`).join("")}</tbody></table>` : `<div class="dim" style="margin-top:6px">Lessons book: no rule yet (a lesson needs 30+ cases and a clear result).</div>`}
    ${(t.news_week || []).length ? `<div class="dim" style="margin-top:6px">News this week: ${t.news_week.map(esc).join(" · ")}</div>` : ""}`;
}

function researchFloor(w, s) {
  const r = w.research || { edges: [], vetoes: [], cleared: [] };
  const cfg = s.research || {};
  const price = s.prices[w.symbol];
  const study = (s.analysis || {})[w.symbol] || {};
  const levels = [...((s.levels || {})[w.symbol] || []), ...(study.htf_levels || [])].sort((a, b) => b.price - a.price);
  const TF_NAME = { "5m": "5 min", "15m": "15 min", "30m": "30 min", "1h": "1 hour", D: "daily", W: "weekly" };
  const trendCells = Object.entries(study.trend || {}).map(([tf, t]) =>
    `<td class="${t === "bullish" ? "pos" : t === "bearish" ? "neg" : "dim"}"><small class="dim">${TF_NAME[tf] || tf}</small><br><b>${t}</b></td>`).join("");
  const zoneRows = (study.zones || []).slice().sort((a, b) => b.hi - a.hi).map((z) =>
    `<tr><td class="${z.kind === "demand" ? "pos" : "neg"}">${z.kind}</td><td>${z.tf}</td><td class="mono">${px(z.lo)} – ${px(z.hi)}</td><td class="r">${z.touches} touch${z.touches === 1 ? "" : "es"}</td></tr>`).join("");
  const fib = study.fib;
  const fibLine = fib ? `15 min ${fib.direction === "up" ? "up" : "down"}-leg ${px(fib.from)} → ${px(fib.to)}: 50% ${px(fib.levels["0.5"])} · 61.8% ${px(fib.levels["0.618"])} · 78.6% ${px(fib.levels["0.786"])}`
    : "no clear 15 min swing yet";
  const edgeRows = r.edges.map((e) => `<tr><td>${TRIG_NAME[e.trigger] || esc(e.trigger)}</td><td class="r">${e.n}</td>
    <td class="r">${e.wins} / ${e.losses} / ${e.timeouts}</td><td class="r">${Math.round(e.win_rate * 100)}%</td>
    <td class="r ${cls(e.avg_r)}">${e.avg_r >= 0 ? "+" : ""}${e.avg_r.toFixed(2)}R</td>
    <td>${e.proven ? '<b class="pos">proven</b>' : `<span class="neg">not proven</span>${e.n < cfg.min_samples ? ` <small class="dim">(${e.n}/${cfg.min_samples} samples)</small>` : ""}`}</td></tr>`).join("");
  const levelRows = levels.map((lv) => {
    const dist = price ? ((lv.price - price) / price) * 100 : null;
    return `<tr><td class="mono">${px(lv.price)}</td><td>${esc(lv.label)}</td><td class="r">${dist == null ? "—" : `${dist >= 0 ? "+" : ""}${dist.toFixed(2)}%`}</td></tr>`;
  }).join("");
  const decisions = [...r.cleared.map((c) => ({ ...c, ok: true })), ...r.vetoes.map((v) => ({ ...v, ok: false }))]
    .sort((a, b) => (a.t < b.t ? 1 : -1)).slice(0, 25);
  const decRows = decisions.map((d) => `<tr><td>${d.t}</td><td>${d.side === "CALL" ? "▲" : "▼"} ${TRIG_NAME[d.trigger] || esc(d.trigger)}</td>
    <td>${d.ok ? `<b class="pos">cleared</b> <span class="dim">${d.edge ? `won ${d.edge.wins}/${d.edge.n}, ${d.edge.avg_r >= 0 ? "+" : ""}${d.edge.avg_r.toFixed(2)}R` : "gate off"}${d.next ? ` · ${d.next.room_atr} ATR to ${esc(d.next.label)}` : ""}</span>`
      : `<b class="neg">vetoed</b> <span class="dim">${esc(d.reason)}</span>`}</td></tr>`).join("");
  return `<h2>Research room · evidence before every trade</h2>
    <p class="dim" style="margin:0 0 12px">${r.gate && w.triggers.some((t) => t.startsWith("smc"))
      ? `TJR's plan, step by step: the daily bias must agree; no CPI/PPI/FOMC/NFP days; a sweep of resting liquidity, then a candle body closing beyond the latest high or low; a retrace into an order block or fair value gap in the discount (longs) or premium (shorts) half; then a break one timeframe lower. Stop beyond the swept high/low, target the next resting liquidity at least ${cfg.min_rr || 1}:1 away. The setup also needs a record: over the last ${cfg.lookback_days} sessions, at least ${cfg.min_samples} past setups the plan would have taken (all tickers together) averaging above ${cfg.min_avg_r}R. No evidence, no trade.`
      : r.gate
      ? `Every entry needs a trigger proven on ${esc(w.symbol)} over the last ${cfg.lookback_days} sessions (at least ${cfg.min_samples} past signals, ${Math.round(cfg.min_win_rate * 100)}%+ reaching ${cfg.target_atr} ATR before ${cfg.stop_atr} ATR against, average above ${cfg.min_avg_r}R) and ${cfg.min_room_atr}+ ATR of room before the next marked level or opposing zone, and no ${(cfg.align_timeframes || []).join(" / ")} trend pointing the other way. No evidence, no trade.`
      : "The research gate is off for this tower: entries are not checked against past sessions."}</p>
    <h2>Trigger track record</h2>
    ${edgeRows ? `<table><thead><tr><th>trigger</th><th class="r">signals</th><th class="r">won / lost / timed out</th><th class="r">win</th><th class="r">avg</th><th>status</th></tr></thead><tbody>${edgeRows}</tbody></table>` : `<div class="empty">Still studying past sessions.</div>`}
    ${tjrBlock(study.tjr)}
    <h2 style="margin-top:16px">Chart study</h2>
    ${trendCells ? `<table><tbody><tr>${trendCells}</tr></tbody></table>` : `<div class="empty">Reading the charts…</div>`}
    <p class="dim" style="margin:8px 0">${esc(fibLine)}</p>
    ${zoneRows ? `<table><thead><tr><th>zone</th><th>timeframe</th><th>price</th><th class="r">tested</th></tr></thead><tbody>${zoneRows}</tbody></table>` : `<div class="empty">No fresh supply or demand zones right now.</div>`}
    <h2 style="margin-top:16px">Marked levels</h2>
    ${levelRows ? `<table><thead><tr><th>price</th><th>why it matters</th><th class="r">from now</th></tr></thead><tbody>${levelRows}</tbody></table>` : `<div class="empty">Levels appear with the first live candle of the session.</div>`}
    <h2 style="margin-top:16px">Today's decisions</h2>
    ${decRows ? `<table><tbody>${decRows}</tbody></table>` : `<div class="empty">No signals checked yet today.</div>`}`;
}

function towerFloor(w, s) {
  const total = workerTotal(w);
  const pos = w.position;
  switch (inside.floor) {
    case "research":
      return researchFloor(w, s);
    case "trading": {
      const wr = w.trades ? Math.round((100 * w.wins) / w.trades) : 0;
      const posCard = pos
        ? `<div class="card"><div class="k">Open position</div>
            <div class="v ${cls(pos.pnl)}">${money(pos.pnl)}</div>
            <div>${pos.right === "CALL" ? "▲" : "▼"} ${qty(pos.qty)} × ${esc(pos.label)}${pos.expiry ? ` · exp ${pos.expiry}` : ""}</div>
            <div class="dim mono">${px(pos.entry)} → ${px(pos.mark)} · since ${pos.opened.slice(11, 16)}</div></div>`
        : `<div class="card"><div class="k">Open position</div><div class="v dim">none</div><div class="dim">waiting for a trigger</div></div>`;
      const scans = w.triggers.map((t) => {
        const x = w.setups[t];
        if (!x) return `<div class="scan"><div class="row"><span>${TRIGGER[t]}</span><span class="dim">warming up / market closed</span></div><div class="bar"><i style="width:0"></i></div></div>`;
        return `<div class="scan"><div class="row"><span>${TRIGGER[t]} ${x.side === "CALL" ? "▲" : "▼"} ${x.side} · level ${px(x.level)} · ${x.distance.toFixed(2)} ATR away</span><b>${x.charge}%</b></div>
          <div class="bar ${x.side}"><i style="width:${x.charge}%"></i></div></div>`;
      }).join("");
      return `<h2>Trading floor</h2>
        <div class="grid">${card("Earned today", money(total), cls(total))}${card("Trades · wins", `${w.trades} · ${w.wins} <small class="dim">(${wr}%)</small>`)}${card(`${esc(w.symbol)} now`, px(s.prices[w.symbol]))}</div>
        <div class="grid">${posCard}<div class="card"><div class="k">Today vs. goal</div>${goalBar(w)}</div></div>
        <h2>Signal scanner</h2>${scans}`;
    }
    case "charts":
      return `<h2>Chart room · ${esc(w.symbol)} 1-minute</h2><canvas id="floor-chart" width="1100" height="440" aria-label="${esc(w.symbol)} one-minute chart with VWAP and EMA50"></canvas>
        <div class="legend"><span class="lg vwap">VWAP</span><span class="lg ema">EMA50</span><span class="lg entry">last price</span></div>`;
    case "thoughts": {
      const list = store.thoughts[w.name] || [];
      return `<h2>Thoughts · what ${esc(w.name)} saw and did</h2>${list.length
        ? `<ul class="thoughts">${list.map((t) => `<li class="${t.tone}"><span class="t">${t.t}</span><span>${esc(t.text)}</span></li>`).join("")}</ul>`
        : `<div class="empty">Nothing yet today. Thoughts appear as setups form and trades fire.</div>`}`;
    }
    case "trades":
      return `<h2>Trade log · today</h2>${w.last_trades.length ? `<table><thead><tr><th>in</th><th>out</th><th>what</th><th class="r">qty</th><th class="r">entry</th><th class="r">exit</th><th>why out</th><th class="r">P&L</th></tr></thead><tbody>
        ${w.last_trades.map((t) => `<tr><td>${t.t}</td><td>${t.out || ""}</td><td>${t.side === "CALL" ? "▲" : "▼"} ${esc(t.label || t.sym)}</td><td class="r">${qty(t.qty)}</td>
          <td class="r">${px(t.entry)}</td><td class="r">${px(t.exit)}</td><td>${REASON[t.reason] || esc(t.reason)}</td><td class="r ${cls(t.pnl)}">${money(t.pnl)}</td></tr>`).join("")}
        </tbody></table>` : `<div class="empty">No closed trades today.</div>`}`;
    case "rules": {
      const c = w.settings || {};
      const z = c.sizing || {}, x = c.exits || {};
      const size = z.mode === "fixed" ? `${z.contracts} fixed` : z.mode === "budget" ? `$${z.budget} budget, max ${z.max_contracts}` : `$${z.risk} risk to stop, max ${z.max_contracts}`;
      return `<h2>Lobby · how ${esc(w.name)} trades</h2><dl class="rules">
        <dt>symbol</dt><dd>${esc(w.symbol)}</dd>
        <dt>triggers</dt><dd>${w.triggers.map((t) => TRIGGER[t]).join(", ")}</dd>
        ${s.market === "crypto" ? "<dt>direction</dt><dd>long only (buys the coin; sell signals only close)</dd>" : `<dt>contract</dt><dd>${esc(c.strike)} strike · nearest listed expiry ≥ ${c.dte}DTE</dd>`}
        <dt>trading window</dt><dd>${esc(c.window)} ET · max ${c.max_trades} trades · ${c.cooldown} min cooldown</dd>
        <dt>trend filter</dt><dd>${c.trend_filter ? "on (only trade with EMA50 and VWAP)" : "off"}</dd>
        <dt>size</dt><dd>${esc(size)}</dd>
        <dt>take profit</dt><dd>+${x.take_profit_pct}%</dd>
        <dt>stop loss</dt><dd>−${x.stop_loss_pct}%</dd>
        <dt>profit lock</dt><dd>after +${x.trail_activate_pct}%, keep ${Math.round((x.trail_lock_ratio || 0) * 100)}% of the best gain</dd>
        <dt>time stop</dt><dd>${x.max_hold_minutes} min · reversal exit ${x.exit_on_reversal ? "on" : "off"}</dd>
        <dt>daily goal / limit</dt><dd>${money(w.goal)} / ${money(-w.max_loss)} then clock out</dd></dl>`;
    }
    case "crew":
      return `<h2>Crew room · the bots working for ${esc(w.name)}</h2>${crewCards(w.crew || [])}`;
  }
  return "";
}

function vaultFloor(s) {
  switch (inside.floor) {
    case "vault": {
      const ranked = [...s.workers].sort((a, b) => workerTotal(b) - workerTotal(a));
      const open = s.workers.filter((w) => w.position).length;
      return `<h2>Vault floor · ${esc(s.day || "")}</h2>
        <div class="grid">${card("Vault today", money(s.vault), cls(s.vault))}${card("Open positions", open)}${card("Kill switch", s.kill.engaged ? "ON" : "off", s.kill.engaged ? "neg" : "")}</div>
        <table><thead><tr><th>tower</th><th class="r">trades</th><th class="r">realized</th><th class="r">open</th><th class="r">total</th><th></th></tr></thead><tbody>
        ${ranked.map((w) => `<tr><td>${esc(w.name)}</td><td class="r">${w.trades}</td><td class="r ${cls(w.realized)}">${money(w.realized)}</td><td class="r ${cls(w.unrealized)}">${money(w.unrealized)}</td>
          <td class="r ${cls(workerTotal(w))}"><b>${money(workerTotal(w))}</b></td><td class="r"><button class="enter" type="button" data-enter="${esc(w.name)}">Enter ▸</button></td></tr>`).join("")}
        </tbody></table>`;
    }
    case "days":
      return `<h2>Day by day · finished sessions</h2>${s.calendar.length ? `<table><thead><tr><th>day</th><th class="r">P&L</th></tr></thead><tbody>
        ${[...s.calendar].reverse().map((d) => `<tr><td>${d.day}</td><td class="r ${cls(d.pnl)}">${money(d.pnl)}</td></tr>`).join("")}</tbody></table>`
        : `<div class="empty">No finished days yet.</div>`}`;
    case "crew":
      return `<h2>The whole crew · one skill per bot</h2>${crewCards((s.crew || []).map((c) => c.name))}`;
  }
  return "";
}
