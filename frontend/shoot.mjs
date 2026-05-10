// UI screenshot harness.
// Authenticates via the backend REST endpoint directly (node fetch),
// injects the session cookie into Playwright, then visits each page.
//
// Usage:
//   node shoot.mjs [round]           -> all pages
//   node shoot.mjs r2 10             -> only pages whose name starts with "10"

import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { execSync } from "node:child_process";

const ROUND   = process.argv[2] ?? "r1";
const FILTER  = process.argv[3] ?? "";
const BASE    = "http://localhost:5173";
const BACKEND = "http://localhost:8000";
const OUT_DIR = path.join("..", "tools", "shots", ROUND);

const VP = {
  desktop: { width: 1440, height: 900 },
  tablet:  { width:  834, height: 1112 },
  mobile:  { width:  390, height:  844 },
};

const ROLE_ACCOUNT = {
  sysadmin:    "sysadmin001",
  admin_school:"reviewer_school001",
  student:     "student001",
};

const PAGES = [
  { name: "01-mock-login",       url: "/auth/mock-login",      role: null,          vp: "desktop" },
  { name: "02-cas-login",        url: "/login",                role: null,          vp: "desktop" },
  { name: "03-mock-login-mob",   url: "/auth/mock-login",      role: null,          vp: "mobile"  },
  { name: "10-student-home",     url: "/student/home",         role: "student",     vp: "desktop" },
  { name: "11-student-home-mob", url: "/student/home",         role: "student",     vp: "mobile"  },
  { name: "20-admin-dashboard",  url: "/admin/dashboard",      role: "admin_school",vp: "desktop" },
  { name: "30-sys-dashboard",    url: "/sys/dashboard",        role: "sysadmin",    vp: "desktop" },
  { name: "31-sys-users",        url: "/sys/users",            role: "sysadmin",    vp: "desktop" },
  { name: "32-sys-audit",        url: "/sys/audit",            role: "sysadmin",    vp: "desktop" },
  { name: "33-sys-judicial",     url: "/sys/judicial-assist",  role: "sysadmin",    vp: "desktop" },
];

// Clear the mock CAS ticket stored in Redis so we can re-login.
function clearTicket(account) {
  try {
    execSync(
      `docker compose exec -T redis redis-cli -a redispassword DEL "afp:cas_ticket:${account}"`,
      { cwd: path.join("..", "."), stdio: "pipe" }
    );
  } catch { /* ignore */ }
}

// Login via backend REST, return parsed Set-Cookie value for the session.
async function getSessionCookie(account) {
  clearTicket(account);
  const resp = await fetch(`${BACKEND}/api/v1/auth/cas/mock-login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "Origin": BASE,
    },
    body: JSON.stringify({ cas_account: account }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`mock-login ${resp.status}: ${text.slice(0, 200)}`);
  }
  // Extract the session cookie from the Set-Cookie header.
  const raw = resp.headers.get("set-cookie") ?? "";
  // raw looks like: afp_session=<value>; HttpOnly; Path=/; ...
  const match = raw.match(/afp_session=([^;]+)/);
  if (!match) throw new Error(`No afp_session cookie in response. Set-Cookie: ${raw}`);
  return match[1];
}

async function shoot(browser, target) {
  const vp  = VP[target.vp];
  const ctx = await browser.newContext({
    viewport:            vp,
    deviceScaleFactor:   1,
    colorScheme:         "light",
    locale:              "zh-CN",
    serviceWorkers:      "block",
    bypassCSP:           true,
  });
  // Disable HTTP cache for this context
  await ctx.route("**/*", (route) => route.continue());

  try {
    if (target.role) {
      const account = ROLE_ACCOUNT[target.role];
      const value   = await getSessionCookie(account);
      await ctx.addCookies([{
        name:   "afp_session",
        value,
        domain: "localhost",
        path:   "/",
      }]);
      console.log("[auth ok]", target.role, "->", account);
    }

    const page = await ctx.newPage();
    await page.setViewportSize(vp);

    const resp = await page
      .goto(`${BASE}${target.url}`, { waitUntil: "networkidle", timeout: 20000 })
      .catch(() => null);
    await page.waitForTimeout(1200);

    const file = path.join(OUT_DIR, `${target.name}.png`);
    await page.screenshot({ path: file, fullPage: true });
    console.log("captured", file, "|", page.url(), resp?.status() ?? "?");
  } finally {
    await ctx.close();
  }
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  const targets = FILTER
    ? PAGES.filter((p) => p.name.startsWith(FILTER))
    : PAGES;

  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
    args: [
      "--disable-blink-features=AutomationControlled",
      "--disable-application-cache",
      "--disable-cache",
      "--disk-cache-size=0",
    ],
  });

  try {
    for (const t of targets) {
      try {
        await shoot(browser, t);
      } catch (err) {
        console.error("FAILED", t.name, err.message);
      }
    }
  } finally {
    await browser.close();
  }
}

main().catch((err) => { console.error(err); process.exit(1); });
