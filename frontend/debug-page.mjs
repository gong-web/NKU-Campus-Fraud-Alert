import { chromium } from "playwright";

const browser = await chromium.launch({ channel: "chrome", headless: true });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, locale: "zh-CN" });
const page = await ctx.newPage();
page.on("console", (msg) => console.log(">>", msg.type(), msg.text()));
page.on("pageerror", (err) => console.log("!!", err.message));
const resp = await page.goto("http://localhost:5173/auth/mock-login", { waitUntil: "networkidle", timeout: 20000 });
console.log("status", resp?.status(), "url", page.url(), "title", await page.title());
const html = await page.content();
console.log("h1:", await page.locator("h1").allTextContents());
console.log("buttons:", (await page.locator("button").allTextContents()).slice(0, 8));
await page.screenshot({ path: "../tools/shots/r1/_debug-mock.png", fullPage: true });
await browser.close();
