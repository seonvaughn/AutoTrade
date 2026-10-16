import * as THREE from "three";
import { OrbitControls } from "/static/vendor/OrbitControls.js";

const COLORS = { CALL: 0x26ffa0, PUT: 0xff2d6f, cyan: 0x3ee8ff, gold: 0xffd84a, violet: 0xb98cff };
const $ = (id) => document.getElementById(id);
const money = (x) => `${x >= 0 ? "+" : "-"}$${Math.abs(x).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const cls = (x) => (x >= 0 ? "pos" : "neg");
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
  const dome = new THREE.Mesh(new THREE.SphereGeometry(3.4, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffe6c4, emissiveIntensity: 0.9 }));
  dome.position.y = 3.2;
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(3.4, 3.4, 2.2, 40, 1, true), new THREE.MeshStandardMaterial({ color: 0xc8735a, emissive: 0x7a2c1a, emissiveIntensity: 0.6 }));
  drum.position.y = 2.1;
  vault.add(base, drum, dome);
  vault.userData.dome = dome;
  scene.add(vault);
}

const towers = new Map(); // worker name -> {group, beam, halo, top, mats, label}
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
    const a = (i / workers.length) * Math.PI * 2 - Math.PI / 2;
    const r = 13;
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
canvas.addEventListener("click", (ev) => {
  const v = new THREE.Vector2((ev.clientX / innerWidth) * 2 - 1, -(ev.clientY / innerHeight) * 2 + 1);
  raycaster.setFromCamera(v, camera);
  const hit = raycaster.intersectObjects([...towers.values()].map((t) => t.group), true).find((h) => h.object.userData.worker);
  if (hit) select(hit.object.userData.worker);
});

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
  controls.update();
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

const TRIGGER = { vwap_cross: "VWAP cross", ema50_cross: "EMA50 cross", orb: "15-min range break" };

function renderRight(s) {
  const w = s.workers.find((x) => x.name === store.selected) || s.workers[0];
  if (!w) return;
  $("tower-name").textContent = `${w.name} · ${w.symbol}${w.dte ? ` · ${w.dte}DTE` : " · 0DTE"}`;
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
  const posHtml = pos ? `<div class="${cls(pos.pnl)}">IN A TRADE · ${pos.right === "CALL" ? "▲" : "▼"} ${pos.qty}× ${pos.strike} ${pos.right} @ ${pos.entry.toFixed(2)} → ${pos.mark.toFixed(2)} (${money(pos.pnl)})</div>` : "";
  const wr = w.trades ? Math.round((100 * w.wins) / w.trades) : 0;
  $("earned").innerHTML = `<div class="big ${cls(total)}">${money(total)}</div>
    <div class="dim">${w.trades} trades · ${w.wins} wins · ${wr}% win rate · goal ${money(w.goal)} / stop ${money(-w.max_loss)}</div>${posHtml}
    <table>${w.last_trades.map((t) => `<tr><td>${t.t} ${t.side === "CALL" ? "▲" : "▼"} ${t.qty} ${esc(t.sym)} · ${esc(t.reason.replace("_", " "))}</td><td class="${cls(t.pnl)}">${money(t.pnl)}</td></tr>`).join("")}</table>`;
  $("thoughts").innerHTML = (store.thoughts[w.name] || []).slice(0, 40).map((t) => `<li class="${t.tone}"><span class="t">${t.t.slice(0, 5)}</span><span>${esc(t.text)}</span></li>`).join("");
  $("chart-title").textContent = `${w.symbol} · 1-min${s.prices[w.symbol] ? ` · ${s.prices[w.symbol].toFixed(2)}` : ""}`;
  drawChart(w, s);
}

function drawChart(w, s) {
  const cv = $("chart");
  const g = cv.getContext("2d");
  const W = cv.width, H = cv.height;
  g.clearRect(0, 0, W, H);
  const bars = (store.candles[w.symbol] || []).slice(-90);
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
  for (const v of [hi - pad, lo + pad]) g.fillText(v.toFixed(2), W - 44, y(v) + 3);
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
  const px = s.prices[w.symbol];
  if (px) { g.setLineDash([4, 4]); g.strokeStyle = "rgba(62,232,255,.7)"; g.beginPath(); g.moveTo(0, y(px)); g.lineTo(W - 46, y(px)); g.stroke(); g.setLineDash([]); }
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
