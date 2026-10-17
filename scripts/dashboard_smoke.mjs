// Headless walkthrough of the Scalp City dashboard. Usage:
//   node scripts/dashboard_smoke.mjs [url=http://127.0.0.1:8765] [outDir=.]
// Saves screenshots and exits 1 if the page throws or a step fails.
import { existsSync, mkdirSync } from "node:fs";

const pwPath = ["/opt/node22/lib/node_modules/playwright/index.mjs"].find(existsSync);
const { chromium } = await import(pwPath || "playwright");
const url = process.argv[2] || "http://127.0.0.1:8765";
const out = process.argv[3] || ".";
mkdirSync(out, { recursive: true });

const errors = [];
const browser = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
const watch = (page) => {
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
  page.on("console", (m) => m.type() === "error" && errors.push(`console: ${m.text()}`));
};
const step = async (name, fn) => {
  try { await fn(); console.log(`ok   ${name}`); } catch (e) { errors.push(`${name}: ${e.message}`); console.log(`FAIL ${name}`); }
};

const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
watch(page);
await page.goto(url);
await page.waitForTimeout(6000);
await page.screenshot({ path: `${out}/1-city.png` });

await step("enter a tower", async () => {
  await page.click("#enter-btn");
  await page.waitForSelector("#inside:not([hidden]) #elevator button", { timeout: 5000 });
  await page.screenshot({ path: `${out}/2-inside.png` });
});
for (const f of ["research", "charts", "thoughts", "trades", "rules", "crew", "trading"]) {
  await step(`floor ${f}`, async () => {
    await page.click(`#elevator [data-floor="${f}"]`);
    await page.waitForTimeout(300);
    if (!(await page.textContent("#floor")).trim() && f !== "charts") throw new Error("empty floor");
    await page.screenshot({ path: `${out}/3-floor-${f}.png` });
  });
}
await step("exit building", async () => {
  await page.click("#inside-exit");
  await page.waitForTimeout(1200);
  if (!(await page.evaluate(() => document.querySelector("#inside").hidden))) throw new Error("still inside");
});
await step("robot card", async () => {
  let hit = null;
  for (let x = 380; x < 1060 && !hit; x += 14) {
    for (const y of [690, 720, 740, 760]) {
      await page.mouse.move(x, y);
      await page.waitForTimeout(70);
      const tip = await page.evaluate(() => { const t = document.querySelector("#hovertip"); return t.hidden ? "" : t.textContent; });
      if (tip.includes("click for details")) { hit = [x, y]; break; }
    }
  }
  if (!hit) throw new Error("no robot found under the cursor");
  await page.mouse.click(hit[0], hit[1]);
  await page.waitForSelector("#botcard:not([hidden])", { timeout: 2000 });
  await page.screenshot({ path: `${out}/4-botcard.png` });
});

const phone = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
watch(phone);
await phone.goto(url);
await phone.waitForTimeout(5000);
await phone.screenshot({ path: `${out}/5-phone-city.png` });
await step("phone: enter a tower", async () => {
  await phone.evaluate(() => document.querySelector("#enter-btn").click());
  await phone.waitForSelector("#inside:not([hidden]) #elevator button", { timeout: 5000 });
  await phone.screenshot({ path: `${out}/6-phone-inside.png` });
});

await browser.close();
if (errors.length) { console.log(errors.join("\n")); process.exit(1); }
console.log(`all good, screenshots in ${out}`);
