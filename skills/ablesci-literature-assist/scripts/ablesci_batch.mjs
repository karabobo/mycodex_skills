#!/usr/bin/env node
// AbleSci (科研通) assist automation: persistent-session login, one-at-a-time
// DOI requests, and batch download of uploaded PDFs — all headless-capable.
//
// Why a script: the browser/UI-control path needs a human in front of the
// screen, which blocks batch work. This script drives Chromium (Playwright)
// against a saved profile, so the only manual step is the first login
// (including any CAPTCHA) and, optionally, the acceptance decision.
//
// Typical use:
//   node scripts/ablesci_batch.mjs --login            # once, headful, saves session
//   node scripts/ablesci_batch.mjs --dois dois.txt --publish --out ./literature_pdfs/AbleSci
//   node scripts/ablesci_batch.mjs --download --out ./literature_pdfs/AbleSci
//   node scripts/ablesci_batch.mjs --download --accept --out ./literature_pdfs/AbleSci
//   node scripts/ablesci_batch.mjs --inspect          # debug selectors / login state
//
// Safety defaults: publishing a request requires --publish; accepting files
// requires --accept. Nothing is published or accepted implicitly.

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { constants as FS } from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";

const BASE = "https://www.ablesci.com";
const CREATE_URL = `${BASE}/assist/create`;
const UPLOADED_URL = `${BASE}/my/assist-my?status=uploaded`;
const DEFAULT_PROFILE = path.join(
  process.env.XDG_CACHE_HOME || path.join(os.homedir(), ".cache"),
  "mycodex-skills",
  "ablesci-profile",
);
const MIN_PDF_BYTES = 10 * 1024;
const NAV_TIMEOUT_MS = 45_000;

const SELECTORS = {
  doiInput: [
    'input[name="doi"]',
    "#doi",
    'input[id*="doi" i]',
    'input[name*="doi" i]',
    'input[placeholder*="DOI" i]',
    'input[placeholder*="doi"]',
    'textarea[name*="doi" i]',
  ],
  extractButton: [
    'button:has-text("智能提取")',
    'a:has-text("智能提取")',
    'button:has-text("提取文献信息")',
    'input[value*="智能提取"]',
  ],
  publishButton: [
    'button:has-text("信息正确")',
    'a:has-text("信息正确")',
    'button:has-text("直接发布")',
    'input[value*="发布"]',
  ],
  detailLink: ['a:has-text("查看求助详情")', 'a[href*="/assist/detail"]', 'a[href*="assist-my"]'],
  uploadedRow: ['table tbody tr', ".list-item", ".assist-item"],
  pdfLink: ['a[href*=".pdf" i]', 'a:has-text(".pdf")', 'a[href*="download"]'],
  lineLink: ['a:has-text("线路1")', 'a:has-text("线路2")', 'a:has-text("线路3")', 'a:has-text("当前源")'],
  acceptButton: ['button:has-text("采纳文件")', 'a:has-text("采纳文件")'],
  batchAccept: ['button:has-text("批量采纳")', 'a:has-text("批量采纳")'],
  confirmButton: ['button:has-text("确定")', 'a:has-text("确定")', 'button:has-text("确认")'],
  emailField: [
    'input[name="email"]',
    "#LAY-user-login2-email",
    'input[type="email"]',
    'input[name*="email" i]',
  ],
  passwordField: ['input[name="password"]', "#LAY-user-login2-password", 'input[type="password"]'],
  loginButton: ['button:has-text("登录")', 'button[type="submit"]', 'input[type="submit"]'],
};

function parseArgs(argv) {
  const options = {
    login: false,
    inspect: false,
    download: false,
    accept: false,
    publish: false,
    headless: true,
    json: false,
    profile: DEFAULT_PROFILE,
    out: null,
    dois: [],
    doiFile: null,
    max: 20,
    loginWaitSeconds: 300,
    email: process.env.ABLESCI_EMAIL ?? "",
    password: process.env.ABLESCI_PASSWORD ?? "",
  };
  const valueFlags = {
    "--profile": (v) => (options.profile = v),
    "--out": (v) => (options.out = v),
    "--dois": (v) => (options.doiFile = v),
    "--doi": (v) => options.dois.push(v),
    "--max": (v) => (options.max = Number.parseInt(v, 10) || options.max),
    "--login-wait": (v) => (options.loginWaitSeconds = Number.parseInt(v, 10) || options.loginWaitSeconds),
    "--email": (v) => (options.email = v),
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") options.help = true;
    else if (arg === "--login") options.login = true;
    else if (arg === "--inspect") options.inspect = true;
    else if (arg === "--download") options.download = true;
    else if (arg === "--accept") options.accept = true;
    else if (arg === "--publish") options.publish = true;
    else if (arg === "--json") options.json = true;
    else if (arg === "--self-test") options.selfTest = true;
    else if (arg === "--headless") options.headless = true;
    else if (arg === "--headful" || arg === "--no-headless") options.headless = false;
    else if (valueFlags[arg]) valueFlags[arg](argv[++i] ?? "");
    else if (arg.startsWith("--")) throw new Error(`unknown flag: ${arg}`);
    else options.dois.push(arg);
  }
  return options;
}

export function normalizeDoi(value) {
  return String(value ?? "")
    .trim()
    .replace(/^https?:\/\/(dx\.)?doi\.org\//i, "")
    .replace(/^doi:\s*/i, "")
    .trim();
}

export function doiSlug(doi) {
  return normalizeDoi(doi).replace(/[^A-Za-z0-9._-]+/g, "_").slice(0, 120) || "unknown-doi";
}

async function firstVisible(scope, selectors, { timeout = 5_000 } = {}) {
  for (const selector of selectors) {
    const locator = scope.locator(selector).first();
    try {
      await locator.waitFor({ state: "visible", timeout });
      return locator;
    } catch {
      // try the next candidate
    }
  }
  return null;
}

function redact(text) {
  return String(text ?? "")
    .replace(/https?:\/\/[^\s"']*download[^\s"']*/gi, "<redacted-download-url>")
    .replace(/token=[^\s&"']+/gi, "token=<redacted>");
}

function keychainPassword(email) {
  if (!email) return "";
  try {
    return execFileSync(
      "security",
      ["find-generic-password", "-s", "codex-ablesci", "-a", email, "-w"],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] },
    ).trim();
  } catch {
    return "";
  }
}

async function pageSummary(page) {
  return page.evaluate(() => {
    const inputs = [...document.querySelectorAll("input, textarea, select")].map((el) => ({
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute("type") ?? "",
      name: el.getAttribute("name") ?? "",
      id: el.id ?? "",
      placeholder: el.getAttribute("placeholder") ?? "",
      visible: Boolean(el.offsetParent),
    }));
    const actions = [...document.querySelectorAll("button, a, input[type=submit]")]
      .map((el) => ({
        tag: el.tagName.toLowerCase(),
        text: (el.innerText || el.value || "").trim().slice(0, 40),
        href: el.getAttribute("href") ?? "",
        visible: Boolean(el.offsetParent),
      }))
      .filter((item) => item.visible && item.text);
    return { title: document.title, url: location.href, inputs, actions: actions.slice(0, 60) };
  });
}

export function resolveHeadless(options) {
  // `--login` must always open a real window, even though headless is the
  // default for every other mode: otherwise the interactive wait is skipped and
  // the script reports "no saved session" without ever showing a login form.
  if (options.login) return false;
  return options.headless !== false;
}

function looksLikeLogin(url, bodyText) {
  return /\/login|signin|sign-in|passport/i.test(url) || /登录|Sign in|Log in/i.test(bodyText);
}

async function bodyText(page) {
  try {
    return (await page.locator("body").innerText({ timeout: 5_000 })) ?? "";
  } catch {
    return "";
  }
}

async function ensureLoggedIn(context, page, options) {
  const headless = resolveHeadless(options);
  const { loginWaitSeconds } = options;
  await page.goto(CREATE_URL, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT_MS });
  let text = await bodyText(page);
  if (!looksLikeLogin(page.url(), text)) return { loggedIn: true };

  const email = options.email || process.env.ABLESCI_EMAIL || "";
  const password = options.password || keychainPassword(email);
  const emailField = await firstVisible(page, SELECTORS.emailField, { timeout: 3_000 });
  const passwordField = await firstVisible(page, SELECTORS.passwordField, { timeout: 3_000 });

  if (emailField && passwordField && email && password) {
    await emailField.fill(email);
    await passwordField.fill(password);
    const submit = await firstVisible(page, SELECTORS.loginButton, { timeout: 3_000 });
    if (submit) await submit.click();
    await page.waitForTimeout(3_000);
    text = await bodyText(page);
    if (!looksLikeLogin(page.url(), text)) return { loggedIn: true, via: "env-credentials" };
    if (/验证码|captcha|滑块|扫码|动态码|OTP/i.test(text)) {
      if (headless) {
        return {
          loggedIn: false,
          reason:
            "login needs a CAPTCHA/OTP that cannot be solved headlessly; run `--login --headful` once to save a session",
        };
      }
    }
  }

  if (headless) {
    return {
      loggedIn: false,
      reason:
        "no saved AbleSci session in this profile. Run `node scripts/ablesci_batch.mjs --login` once (headful) to sign in and save the session.",
    };
  }

  // Headful: let the user complete login (including CAPTCHA) in the window.
  process.stderr.write(
    `\nAbleSci login required. Complete sign-in in the opened window (CAPTCHA/OTP included).\nWaiting up to ${loginWaitSeconds}s for ${CREATE_URL} ...\n`,
  );
  // Do not navigate while the user is typing: watch for the URL leaving the
  // login page or, for QR/same-page sign-in, for logged-in chrome in the DOM,
  // then confirm the create page loads without a login redirect.
  const deadline = Date.now() + loginWaitSeconds * 1000;
  let windowClosed = false;
  let loggedInText = "";
  while (Date.now() < deadline) {
    try {
      await page.waitForTimeout(2_000);
      if (page.isClosed()) {
        windowClosed = true;
        break;
      }
      const onLoginUrl = /\/site\/login|\/login/i.test(page.url());
      if (onLoginUrl) {
        const current = await bodyText(page);
        const signedIn = /退出登录|退出系统|我的求助|个人中心|我的账号/.test(current) && !/登录密码|登录邮箱/.test(current);
        if (!signedIn) continue;
      }
      await page.goto(CREATE_URL, { waitUntil: "domcontentloaded", timeout: 20_000 });
      loggedInText = await bodyText(page);
      if (!looksLikeLogin(page.url(), loggedInText)) return { loggedIn: true, via: "interactive" };
    } catch (error) {
      if (/Target closed|has been closed|Protocol error|Session closed/i.test(String(error))) {
        windowClosed = true;
        break;
      }
      // transient navigation errors while the user steps through the form: keep waiting
    }
  }
  return {
    loggedIn: false,
    reason: windowClosed
      ? "login window closed before sign-in finished; run --login again and leave the window open until it reports success"
      : "timed out waiting for interactive login; raise --login-wait or finish sign-in in the window",
  };
}

export function countPages(buffer) {
  const text = buffer.toString("latin1");
  const plain = (text.match(/\/Type\s*\/Page\b(?!s)/g) || []).length;
  if (plain > 0) return plain;
  const countField = text.match(/\/Count\s+(\d+)/);
  return countField ? Number.parseInt(countField[1], 10) : 0;
}

export function validatePdf(buffer) {
  const problems = [];
  if (buffer.length < MIN_PDF_BYTES) problems.push(`file too small (${buffer.length} bytes)`);
  if (buffer.subarray(0, 1024).toString("latin1").indexOf("%PDF-") === -1) problems.push("missing %PDF- header");
  const tail = buffer.subarray(Math.max(0, buffer.length - 4096)).toString("latin1");
  if (!/%%EOF/.test(tail)) problems.push("missing %%EOF trailer");
  const pages = countPages(buffer);
  return { ok: problems.length === 0, problems, pages, sha256: createHash("sha256").update(buffer).digest("hex") };
}

async function submitDoi(page, item, { publish, log }) {
  const doi = normalizeDoi(item.doi);
  const record = { doi, title: item.title ?? "", status: "pending" };

  await page.goto(CREATE_URL, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT_MS });
  const createText = await bodyText(page);
  if (looksLikeLogin(page.url(), createText)) {
    record.status = "login_required";
    return record;
  }
  if (/只能.*(一篇|1 篇)|同时只能|仅能求助/.test(createText)) {
    record.status = "blocked_by_existing_request";
    record.detail = "account already has an active request; run --download (and --accept) first";
    return record;
  }

  const input = await firstVisible(page, SELECTORS.doiInput, { timeout: 10_000 });
  if (!input) {
    record.status = "selector_failed";
    record.detail = "could not find the DOI input; run --inspect to list form elements";
    return record;
  }
  await input.fill(doi);

  const extract = await firstVisible(page, SELECTORS.extractButton, { timeout: 10_000 });
  if (!extract) {
    record.status = "selector_failed";
    record.detail = "could not find 智能提取文献信息; run --inspect";
    return record;
  }
  await extract.click();
  await page.waitForTimeout(4_000);
  const extracted = await bodyText(page);
  if (!extracted.toUpperCase().includes(doi.toUpperCase())) {
    record.status = "metadata_mismatch";
    record.detail = "extracted metadata does not show the requested DOI";
    return record;
  }
  record.extracted = true;

  if (!publish) {
    record.status = "dry_run_not_published";
    return record;
  }

  const publishButton = await firstVisible(page, SELECTORS.publishButton, { timeout: 10_000 });
  if (!publishButton) {
    record.status = "selector_failed";
    record.detail = "could not find 信息正确，直接发布; run --inspect";
    return record;
  }
  await publishButton.click();
  await page.waitForTimeout(4_000);
  record.status = "published";

  const detail = await firstVisible(page, SELECTORS.detailLink, { timeout: 5_000 });
  if (detail) {
    const href = await detail.getAttribute("href");
    if (href) record.detailUrl = new URL(href, BASE).toString();
  }
  log(`published ${doi}`);
  return record;
}

async function collectUploadedRows(page, log) {
  await page.goto(UPLOADED_URL, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT_MS });
  const text = await bodyText(page);
  if (looksLikeLogin(page.url(), text)) return { rows: [], reason: "login_required" };

  const rows = await page.evaluate(() => {
    const anchors = [...document.querySelectorAll('a[href*="assist"]')];
    return anchors
      .map((a) => ({ text: (a.innerText || "").trim().slice(0, 120), href: a.getAttribute("href") ?? "" }))
      .filter((item) => item.href && /detail|assist-my|download/i.test(item.href));
  });
  log(`uploaded list: ${rows.length} candidate links`);
  return { rows, reason: null };
}

async function downloadFromDetail(context, page, detailUrl, outDir, log) {
  const record = { detailUrl, file: null, status: "pending" };
  await page.goto(detailUrl, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT_MS });
  const text = await bodyText(page);
  if (looksLikeLogin(page.url(), text)) return { ...record, status: "login_required" };
  if (/48 小时内|请.*审核/.test(text)) {
    const confirm = await firstVisible(page, SELECTORS.confirmButton, { timeout: 3_000 });
    if (confirm) await confirm.click().catch(() => {});
  }

  const pdfLink = await firstVisible(page, SELECTORS.pdfLink, { timeout: 8_000 });
  if (!pdfLink) return { ...record, status: "no_uploaded_file" };

  const href = (await pdfLink.getAttribute("href")) ?? "";
  const downloadUrl = href ? new URL(href, BASE).toString() : "";
  if (!downloadUrl) return { ...record, status: "no_download_url" };

  // Prefer an explicit click so the site's own token/nodes logic runs, then
  // fall back to a cookie-authenticated request for the PDF bytes.
  const downloadPagePromise = context.waitForEvent("page", { timeout: 20_000 }).catch(() => null);
  await pdfLink.click().catch(() => {});
  const downloadPage = await downloadPagePromise;
  let buffer = null;
  let filename = null;

  if (downloadPage) {
    await downloadPage.waitForLoadState("domcontentloaded").catch(() => {});
    const line = await firstVisible(downloadPage, SELECTORS.lineLink, { timeout: 6_000 });
    const downloadPromise = downloadPage.waitForEvent("download", { timeout: 30_000 }).catch(() => null);
    if (line) await line.click().catch(() => {});
    const download = await downloadPromise;
    if (download) {
      filename = download.suggestedFilename();
      const tempPath = await download.path();
      if (tempPath) buffer = await readFile(tempPath);
    }
    if (!buffer) {
      // Fall back to the tokenized URL visible on the download page.
      const pdfHref = await downloadPage.evaluate(() => {
        const link = document.querySelector('a[href$=".pdf"], a[href*="download"]');
        return link ? link.getAttribute("href") : null;
      });
      if (pdfHref) {
        const absolute = new URL(pdfHref, downloadPage.url()).toString();
        const response = await context.request.get(absolute);
        if (response.ok()) buffer = Buffer.from(await response.body());
      }
    }
    await downloadPage.close().catch(() => {});
  }

  if (!buffer) {
    const response = await context.request.get(downloadUrl);
    if (response.ok()) buffer = Buffer.from(await response.body());
  }
  if (!buffer) return { ...record, status: "download_failed" };

  const check = validatePdf(buffer);
  if (!check.ok) return { ...record, status: "invalid_pdf", problems: check.problems };

  await mkdir(outDir, { recursive: true });
  const safeName = filename && /\.pdf$/i.test(filename) ? filename : `${doiSlug(detailUrl.split("/").pop() || "ablesci")}.pdf`;
  const file = path.join(outDir, safeName.replace(/[^\w.\-]+/g, "_"));
  await writeFile(file, buffer);
  log(`saved ${file} (${buffer.length} bytes, ~${check.pages} pages)`);
  return {
    ...record,
    status: "downloaded_verified",
    file,
    bytes: buffer.length,
    pages: check.pages,
    sha256: check.sha256,
  };
}

async function acceptAll(page, log) {
  const batch = await firstVisible(page, SELECTORS.batchAccept, { timeout: 8_000 });
  if (!batch) return { accepted: false, reason: "no 批量采纳 control found" };
  // Select every row checkbox before batch accepting.
  await page.evaluate(() => {
    for (const box of document.querySelectorAll('input[type="checkbox"]')) {
      if (!box.disabled && !box.checked) box.click();
    }
  });
  await batch.click().catch(() => {});
  await page.waitForTimeout(1_500);
  const confirm = await firstVisible(page, SELECTORS.confirmButton, { timeout: 6_000 });
  if (confirm) await confirm.click().catch(() => {});
  await page.waitForTimeout(3_000);
  const text = await bodyText(page);
  const accepted = /批量采纳处理完毕|成功|已采纳/.test(text) && !/失败：[1-9]/.test(text);
  log(accepted ? "batch accept reported success" : "batch accept result unclear; check the page");
  return { accepted, message: redact(text.slice(0, 400)) };
}

async function loadDois(options) {
  const items = options.dois.map((value) => ({ doi: normalizeDoi(value) }));
  if (options.doiFile) {
    const raw = await readFile(options.doiFile, "utf8");
    for (const line of raw.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const [doi, ...title] = trimmed.split(",");
      items.push({ doi: normalizeDoi(doi), title: title.join(",").trim() });
    }
  }
  const seen = new Set();
  return items
    .filter((item) => item.doi && !seen.has(item.doi.toUpperCase()) && seen.add(item.doi.toUpperCase()))
    .slice(0, options.max);
}

function runSelfTest() {
  const checks = [];
  const assert = (name, condition) => checks.push({ name, ok: Boolean(condition) });

  assert("normalizeDoi strips resolver prefix", normalizeDoi("https://doi.org/10.1/ABC") === "10.1/ABC");
  assert("doiSlug is filesystem safe", doiSlug("10.1056/NEJMoa2034577") === "10.1056_NEJMoa2034577");
  assert("validatePdf rejects html", validatePdf(Buffer.from("<html>nope</html>")).ok === false);

  const pdf = Buffer.concat([
    Buffer.from("%PDF-1.7\n1 0 obj<</Type/Page>>endobj\n"),
    Buffer.alloc(20_000, 32),
    Buffer.from("\n%%EOF"),
  ]);
  const good = validatePdf(pdf);
  assert("validatePdf accepts a minimal PDF", good.ok);
  assert("countPages finds one page", good.pages === 1);
  assert("sha256 is computed", /^[0-9a-f]{64}$/.test(good.sha256));
  assert("--login always runs headful", resolveHeadless({ login: true, headless: true }) === false);
  assert("default mode is headless", resolveHeadless({ login: false, headless: true }) === true);
  assert("--headful is honoured", resolveHeadless({ login: false, headless: false }) === false);

  const failed = checks.filter((check) => !check.ok);
  console.log(JSON.stringify({ ok: failed.length === 0, checks }, null, 2));
  if (failed.length > 0) process.exitCode = 1;
}

async function main() {
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
  if (options.help) {
    console.log(`usage: node ablesci_batch.mjs [--login] [--inspect] [--download] [--accept]
       [--doi <doi> ...] [--dois <file>] [--out <dir>] [--publish]
       [--headful] [--profile <dir>] [--max N] [--login-wait <seconds>] [--json]
       [--self-test]

Safety: requests are only posted with --publish; files are only accepted with --accept.
Headless runs need a saved session: run --login once (headful).`);
    return;
  }

  if (options.selfTest) {
    runSelfTest();
    return;
  }

  const outDir = options.out ?? path.join(process.cwd(), "literature_pdfs", "AbleSci");
  await mkdir(options.profile, { recursive: true });
  const log = (message) => {
    if (!options.json) process.stderr.write(`${message}\n`);
  };

  const context = await chromium.launchPersistentContext(options.profile, {
    headless: resolveHeadless(options),
    acceptDownloads: true,
    viewport: { width: 1440, height: 900 },
    args: ["--disable-blink-features=AutomationControlled"],
  });
  const result = { mode: [], profile: options.profile, requests: [], downloads: [], accepted: null };

  try {
    const page = context.pages()[0] ?? (await context.newPage());

    // --inspect works without a session on purpose: it is how selectors and the
    // login state get diagnosed on a fresh machine.
    if (options.inspect) {
      result.mode.push("inspect");
      await page.goto(CREATE_URL, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT_MS });
      const create = await pageSummary(page);
      await page.goto(UPLOADED_URL, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT_MS });
      const uploaded = await pageSummary(page);
      result.inspect = { create, uploaded };
      result.loggedIn = !looksLikeLogin(create.url, create.title);
      console.log(JSON.stringify(result, null, 2));
      return;
    }

    const auth = await ensureLoggedIn(context, page, options);
    result.loggedIn = auth.loggedIn;
    if (!auth.loggedIn) {
      result.reason = auth.reason;
      console.log(JSON.stringify(result, null, 2));
      process.exitCode = 2;
      return;
    }

    if (options.login) {
      result.mode.push("login");
      result.message = "session saved; later runs can use --headless";
      console.log(JSON.stringify(result, null, 2));
      return;
    }

    if (options.download) {
      result.mode.push("download");
      const { rows, reason } = await collectUploadedRows(page, log);
      if (reason) {
        result.reason = reason;
        process.exitCode = 2;
        return;
      }
      const detailUrls = [...new Set(rows.map((row) => row.href).filter((href) => /detail/i.test(href)))];
      const targets = detailUrls.length > 0 ? detailUrls.slice(0, options.max) : [UPLOADED_URL];
      for (const href of targets) {
        const url = new URL(href, BASE).toString();
        result.downloads.push(await downloadFromDetail(context, page, url, outDir, log));
      }
      if (options.accept) {
        await page.goto(UPLOADED_URL, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT_MS });
        result.accepted = await acceptAll(page, log);
      }
    }

    const items = await loadDois(options);
    if (items.length > 0) {
      result.mode.push("submit");
      for (const item of items) {
        result.requests.push(await submitDoi(page, item, { publish: options.publish, log }));
      }
    }

    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    await mkdir(outDir, { recursive: true });
    const logPath = path.join(outDir, `ablesci-run-${stamp}.json`);
    await writeFile(logPath, JSON.stringify(result, null, 2));
    result.log = logPath;

    if (options.json) console.log(JSON.stringify(result, null, 2));
    else {
      const ok = result.downloads.filter((item) => item.status === "downloaded_verified").length;
      const published = result.requests.filter((item) => item.status === "published").length;
      console.log(
        `ablesci: ${published} published, ${ok}/${result.downloads.length} downloads verified, log ${logPath}`,
      );
    }
    const failed =
      result.downloads.some((item) => item.status !== "downloaded_verified") ||
      result.requests.some((item) => !["published", "dry_run_not_published"].includes(item.status));
    if (failed) process.exitCode = 2;
  } finally {
    await context.close().catch(() => {});
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error.stack || error.message);
    process.exit(1);
  });
}
