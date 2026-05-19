/**
 * Captura telas da API em docs/screenshots/ (requer API em http://127.0.0.1:8000).
 * Uso: node scripts/capture-screenshots.mjs
 */
import { mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const OUT = join(ROOT, "docs", "screenshots");
const BASE = process.env.API_BASE || "http://127.0.0.1:8001";

async function shot(page, name, url, opts = {}) {
  await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
  if (opts.waitMs) await page.waitForTimeout(opts.waitMs);
  const path = join(OUT, name);
  await page.screenshot({ path, fullPage: Boolean(opts.fullPage) });
  console.log("OK", name);
}

async function openSwaggerOp(page, summaryPattern) {
  await page.goto(`${BASE}/docs`, { waitUntil: "networkidle" });
  const toggle = page.getByRole("button", { name: summaryPattern }).first();
  await toggle.scrollIntoViewIfNeeded();
  await toggle.click();
  const op = page.locator(".opblock").filter({ has: toggle });
  await op.getByRole("button", { name: "Try it out" }).click();
  return op;
}

async function swaggerExecuteItems(page, params = {}) {
  const op = await openSwaggerOp(page, /GET\s+\/items\s+Lista paginada/i);
  for (const [key, value] of Object.entries(params)) {
    const row = op.locator(`tr[data-param-name="${key}"] input`);
    if ((await row.count()) > 0) await row.fill(String(value));
  }
  await op.getByRole("button", { name: "Execute" }).click();
  await page.waitForTimeout(2000);
}

async function main() {
  await mkdir(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

  await shot(page, "01-pagina-inicial.png", `${BASE}/`);
  await shot(page, "02-swagger-visao-geral.png", `${BASE}/docs`, { fullPage: true, waitMs: 800 });
  await shot(page, "11-openapi-json.png", `${BASE}/openapi.json`);
  await shot(page, "06-redoc.png", `${BASE}/redoc`, { fullPage: true });
  await shot(page, "07-items-json-limit5.png", `${BASE}/items?limit=5`);
  await shot(page, "08-health.png", `${BASE}/health`);

  await swaggerExecuteItems(page, { limit: "10" });
  await page.screenshot({ path: join(OUT, "03-swagger-listar-items.png"), fullPage: true });

  await swaggerExecuteItems(page, { limit: "15", uf: "MS" });
  await page.screenshot({ path: join(OUT, "04-swagger-filtro-uf.png"), fullPage: true });

  const op = await openSwaggerOp(page, /GET\s+\/items\/\{item_id\}\s+Item por ID/i);
  await op.locator('tr[data-param-name="item_id"] input').fill("1");
  await op.getByRole("button", { name: "Execute" }).click();
  await page.waitForTimeout(1800);
  await page.screenshot({ path: join(OUT, "05-swagger-item-por-id.png"), fullPage: true });

  await swaggerExecuteItems(page, { limit: "5", fields: "full" });
  await page.screenshot({ path: join(OUT, "09-swagger-campos-full.png"), fullPage: true });

  const res = await page.request.get(`${BASE}/items?limit=3`);
  const body = await res.json();
  const cursor = body?.meta?.next_cursor;
  if (cursor) {
    await shot(page, "10-paginacao-cursor.png", `${BASE}/items?limit=3&cursor=${cursor}`);
  }

  await browser.close();
  console.log("Capturas em", OUT);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
