#!/usr/bin/env node
// Fetch a full-text PDF from Sci-Hub by DOI.
//
// Intended position in the retrieval chain: local EndNote miss -> lawful open
// access / user-authorized institutional access -> Sci-Hub (only when the user
// has authorized this fallback) -> AbleSci mutual aid.
//
// Dependency-free on purpose: Node's global fetch plus a small cookie jar, and
// a built-in solver for Sci-Hub's altcha proof-of-work challenge, so it runs
// headlessly in DeepSeek Harness, Codex, or any other agent runtime without
// npm install, a browser, or a captcha service.
//
// Usage:
//   node scihub_fetch.mjs --doi 10.1056/NEJMoa2034577 --out ./pdfs
//   node scihub_fetch.mjs --doi <doi> --mirrors sci-hub.st,sci-hub.ru --json
//   node scihub_fetch.mjs --batch dois.txt --out ./pdfs
//
// Exit codes: 0 = every requested PDF saved and validated, 2 = at least one
// DOI unresolved, 1 = usage or IO error.

import { createHash } from "node:crypto";
import { inflateSync } from "node:zlib";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const DEFAULT_MIRRORS = ["sci-hub.st", "sci-hub.ru", "sci-hub.se"];
const USER_AGENT =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";
const MIN_PDF_BYTES = 10 * 1024;
const REQUEST_TIMEOUT_MS = 45_000;
const MAX_PAGE_ATTEMPTS = 4;

export function normalizeDoi(value) {
  if (!value) return "";
  return String(value)
    .trim()
    .replace(/^https?:\/\/(dx\.)?doi\.org\//i, "")
    .replace(/^doi:\s*/i, "")
    .replace(/\s+/g, "");
}

export function doiSlug(doi) {
  return (
    normalizeDoi(doi)
      .replace(/[^A-Za-z0-9._-]+/g, "_")
      .slice(0, 120) || "unknown-doi"
  );
}

class Session {
  constructor() {
    this.cookies = new Map();
  }

  cookieHeader() {
    return [...this.cookies.entries()].map(([key, value]) => `${key}=${value}`).join("; ");
  }

  storeCookies(response) {
    const list = response.headers.getSetCookie?.() ?? [];
    for (const raw of list) {
      const [pair] = raw.split(";");
      const index = pair.indexOf("=");
      if (index > 0) this.cookies.set(pair.slice(0, index).trim(), pair.slice(index + 1).trim());
    }
  }

  async fetch(url, init = {}) {
    const headers = {
      "user-agent": USER_AGENT,
      "accept-language": "en-US,en;q=0.9",
      ...(this.cookies.size > 0 ? { cookie: this.cookieHeader() } : {}),
      ...(init.headers ?? {}),
    };
    const response = await fetch(url, {
      redirect: "follow",
      ...init,
      headers,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    this.storeCookies(response);
    return response;
  }
}

function absoluteUrl(candidate, baseUrl) {
  try {
    return new URL(candidate, baseUrl).toString();
  } catch {
    return null;
  }
}

// Sci-Hub serves the article either as an embedded PDF viewer or as a plain
// link to /storage/...; mirror HTML varies, so collect every plausible URL.
export function extractPdfUrls(html, pageUrl) {
  const found = [];
  const push = (raw) => {
    if (!raw) return;
    const decoded = raw
      .replace(/&amp;/g, "&")
      .replace(/&#38;/g, "&")
      .replace(/&quot;/g, '"')
      .trim();
    if (!decoded || decoded.startsWith("data:") || decoded.startsWith("javascript:")) return;
    const url = absoluteUrl(decoded, pageUrl);
    if (!url || !/^https?:/i.test(url)) return;
    if (!found.includes(url)) found.push(url);
  };

  for (const pattern of [
    /<embed[^>]+src\s*=\s*["']([^"']+)["']/gi,
    /<iframe[^>]+src\s*=\s*["']([^"']+)["']/gi,
    /<object[^>]+data\s*=\s*["']([^"']+)["']/gi,
  ]) {
    for (const match of html.matchAll(pattern)) push(match[1]);
  }
  for (const match of html.matchAll(/href\s*=\s*["']([^"']*?\.pdf[^"']*)["']/gi)) push(match[1]);
  for (const match of html.matchAll(/location\.href\s*=\s*['"]([^'"]+)['"]/gi)) {
    if (/\.pdf|download|\/storage\//i.test(match[1])) push(match[1]);
  }
  return found;
}

function countPagesInText(text) {
  return (text.match(/\/Type\s*\/Page\b(?!s)/g) || []).length;
}

// Many publisher PDFs store page objects inside compressed object streams
// (ObjStm), so a plain-text scan finds nothing. Inflate streams with zlib and
// count again; this keeps page counting dependency-free and reasonably exact.
function countPagesInInflatedStreams(buffer) {
  const text = buffer.toString("latin1");
  const chunks = [];
  const pattern = /stream\r?\n/g;
  let match;
  while ((match = pattern.exec(text)) !== null) {
    const start = match.index + match[0].length;
    const end = text.indexOf("endstream", start);
    if (end < 0) continue;
    try {
      chunks.push(inflateSync(buffer.subarray(start, end)).toString("latin1"));
    } catch {
      // Not a Flate stream, or encrypted: ignore.
    }
  }
  return chunks.length > 0 ? countPagesInText(chunks.join("\n")) : 0;
}

export function countPages(buffer) {
  const plain = countPagesInText(buffer.toString("latin1"));
  if (plain > 0) return plain;
  const inflated = countPagesInInflatedStreams(buffer);
  if (inflated > 0) return inflated;
  const countField = buffer.toString("latin1").match(/\/Count\s+(\d+)/);
  return countField ? Number.parseInt(countField[1], 10) : 0;
}

export function validatePdf(buffer) {
  const problems = [];
  if (buffer.length < MIN_PDF_BYTES) problems.push(`file too small (${buffer.length} bytes)`);
  if (buffer.subarray(0, 1024).toString("latin1").indexOf("%PDF-") === -1) {
    problems.push("missing %PDF- header");
  }
  const tail = buffer.subarray(Math.max(0, buffer.length - 4096)).toString("latin1");
  if (!/%%EOF/.test(tail)) problems.push("missing %%EOF trailer (truncated download?)");
  const pages = countPages(buffer);
  // A page count of 0 is reported, not fatal: object streams, encryption, or an
  // unusual producer can hide page dictionaries from a scanner. Identity is
  // still verified downstream by opening the file.
  return { ok: problems.length === 0, problems, pages, pagesKnown: pages > 0 };
}

// altcha proof-of-work: find n where sha256(salt + n) === challenge.
export function solveAltcha({ challenge, salt, maxNumber = 200_000 }) {
  for (let n = 0; n <= maxNumber; n += 1) {
    if (createHash("sha256").update(`${salt}${n}`).digest("hex") === challenge) return n;
  }
  return -1;
}

async function solveCaptcha(session, pageHtml, baseUrl) {
  const id = (pageHtml.match(/\/captcha\/challenge\/(\d+)/) || [])[1];
  if (!id) return { ok: false, reason: "captcha page without challenge id" };
  const response = await session.fetch(`${baseUrl}/captcha/challenge/${id}`, {
    headers: { accept: "application/json" },
  });
  if (!response.ok) return { ok: false, reason: `challenge HTTP ${response.status}` };
  const challenge = await response.json();
  const number = solveAltcha(challenge);
  if (number < 0) return { ok: false, reason: "captcha unsolvable within maxNumber" };
  const payload = Buffer.from(
    JSON.stringify({
      algorithm: challenge.algorithm,
      challenge: challenge.challenge,
      number,
      salt: challenge.salt,
      signature: challenge.signature,
    }),
  ).toString("base64");
  const solution = await session.fetch(`${baseUrl}/captcha/solution/${id}`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({ captcha: payload }),
  });
  const body = await solution.text();
  let success = false;
  try {
    success = JSON.parse(body).success === true;
  } catch {
    success = false;
  }
  return success
    ? { ok: true, number }
    : { ok: false, reason: `solution rejected (HTTP ${solution.status}: ${body.slice(0, 120)})` };
}

async function attemptMirror(doi, mirror, log) {
  const session = new Session();
  const baseUrl = `https://${mirror}`;
  const pageUrl = `${baseUrl}/${encodeURI(doi)}`;
  const attempt = { mirror, pageUrl, ok: false };

  try {
    let html = "";
    for (let round = 0; round < MAX_PAGE_ATTEMPTS; round += 1) {
      const page = await session.fetch(pageUrl);
      if (!page.ok) {
        attempt.reason = `page HTTP ${page.status}`;
        return attempt;
      }
      html = await page.text();
      const isChallenge = /are you are robot|are you a robot/i.test(html);
      if (!isChallenge) break;
      log(`  ${mirror}: robot check, solving proof-of-work`);
      const solved = await solveCaptcha(session, html, baseUrl);
      if (!solved.ok) {
        attempt.reason = solved.reason;
        return attempt;
      }
    }

    const candidates = extractPdfUrls(html, pageUrl);
    if (candidates.length === 0) {
      const title = (html.match(/<title[^>]*>([^<]*)</i) || [])[1] ?? "";
      attempt.reason = `no PDF link (page title: ${title.trim().slice(0, 80)})`;
      return attempt;
    }

    attempt.candidates = candidates.length;
    for (const pdfUrl of candidates) {
      const response = await session.fetch(pdfUrl, {
        headers: { accept: "application/pdf,*/*", referer: pageUrl },
      });
      if (!response.ok) continue;
      const buffer = Buffer.from(await response.arrayBuffer());
      const check = validatePdf(buffer);
      if (!check.ok) {
        attempt.reason = `invalid PDF from ${pdfUrl}: ${check.problems.join("; ")}`;
        continue;
      }
      return { ...attempt, ok: true, pdfUrl, buffer, pages: check.pages };
    }
    attempt.reason ??= "no valid PDF among candidates";
    return attempt;
  } catch (error) {
    attempt.reason = `network error: ${error.message}`;
    return attempt;
  }
}

export async function fetchDoi(doi, { mirrors = DEFAULT_MIRRORS, outDir = ".", log = () => {} } = {}) {
  const normalized = normalizeDoi(doi);
  const attempts = [];
  for (const mirror of mirrors) {
    log(`trying ${mirror} for ${normalized}`);
    const attempt = await attemptMirror(normalized, mirror, log);
    attempts.push({ ...attempt, buffer: undefined });
    if (attempt.ok) {
      await mkdir(outDir, { recursive: true });
      const file = path.join(outDir, `${doiSlug(normalized)}.pdf`);
      await writeFile(file, attempt.buffer);
      const sha256 = createHash("sha256").update(attempt.buffer).digest("hex");
      const text = attempt.buffer.toString("latin1");
      return {
        ok: true,
        doi: normalized,
        mirror,
        source: "sci-hub",
        sourceUrl: attempt.pageUrl,
        file,
        bytes: attempt.buffer.length,
        pages: attempt.pages,
        pagesApprox: true,
        pagesKnown: attempt.pages > 0,
        doiMentionedInPdf: text.includes(normalized),
        sha256,
        attempts: attempts.map(({ buffer, ...rest }) => rest),
      };
    }
    log(`  ${mirror}: ${attempt.reason}`);
  }
  return { ok: false, doi: normalized, attempts, reason: "no mirror produced a valid PDF" };
}

function parseArgs(argv) {
  const options = { dois: [], out: ".", mirrors: DEFAULT_MIRRORS.slice(), json: false, batch: null };
  const commands = ["--doi", "--batch", "--out", "--mirrors"];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--json") options.json = true;
    else if (arg === "--self-test") options.selfTest = true;
    else if (arg === "--help" || arg === "-h") options.help = true;
    else if (commands.includes(arg)) {
      const value = argv[i + 1] ?? "";
      i += 1;
      if (arg === "--doi") options.dois.push(normalizeDoi(value));
      else if (arg === "--batch") options.batch = value;
      else if (arg === "--out") options.out = value;
      else options.mirrors = value.split(",").map((item) => item.trim()).filter(Boolean);
    } else if (arg.startsWith("--")) throw new Error(`unknown flag: ${arg}`);
    else options.dois.push(normalizeDoi(arg));
  }
  options.dois = options.dois.filter(Boolean);
  return options;
}

function runSelfTest() {
  const checks = [];
  const assert = (name, condition) => checks.push({ name, ok: Boolean(condition) });

  assert("normalizeDoi strips doi: prefix", normalizeDoi("doi:10.1/ABC") === "10.1/ABC");
  assert("normalizeDoi strips resolver URL", normalizeDoi("https://doi.org/10.1/ABC") === "10.1/ABC");
  assert("doiSlug is filesystem safe", doiSlug("10.1056/NEJMoa2034577") === "10.1056_NEJMoa2034577");

  const urls = extractPdfUrls(
    '<embed src="//cdn.example.org/pdf/a.pdf#page=1"><iframe src="/storage/x.pdf"></iframe>',
    "https://sci-hub.st/10.1/x",
  );
  assert("extractPdfUrls finds embed and iframe", urls.length === 2);
  assert("extractPdfUrls resolves protocol-relative URL", urls[0].startsWith("https://cdn.example.org/"));

  assert("validatePdf rejects html", validatePdf(Buffer.from("<html>nope</html>")).ok === false);

  const pdf = Buffer.concat([
    Buffer.from("%PDF-1.7\n1 0 obj<</Type/Page>>endobj\n"),
    Buffer.alloc(20_000, 32),
    Buffer.from("\n%%EOF"),
  ]);
  const good = validatePdf(pdf);
  assert("validatePdf accepts a minimal PDF", good.ok);
  assert("validatePdf counts one page", good.pages === 1);

  // altcha proof-of-work solver: sha256(salt + n) === challenge
  const salt = "abc";
  const challenge = createHash("sha256").update(`${salt}7`).digest("hex");
  assert("solveAltcha finds the right number", solveAltcha({ challenge, salt, maxNumber: 1000 }) === 7);

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
    console.log(
      "usage: node scihub_fetch.mjs --doi <doi> [--doi ...] [--batch file] [--out dir] [--mirrors a,b] [--json] [--self-test]",
    );
    return;
  }
  if (options.selfTest) {
    runSelfTest();
    return;
  }
  if (options.batch) {
    const text = await readFile(options.batch, "utf8");
    for (const line of text.split(/\r?\n/)) {
      const doi = normalizeDoi(line.split(/[,\t]/)[0]);
      if (doi && !doi.startsWith("#")) options.dois.push(doi);
    }
  }
  options.dois = [...new Set(options.dois)].filter(Boolean);
  if (options.dois.length === 0) {
    console.error("no DOI given; pass --doi <doi> or --batch <file>");
    process.exit(1);
  }

  const results = [];
  for (const doi of options.dois) {
    const result = await fetchDoi(doi, {
      mirrors: options.mirrors,
      outDir: options.out,
      log: options.json ? () => {} : (message) => console.error(message),
    });
    results.push(result);
    if (!options.json) {
      if (result.ok) {
        console.log(
          `${result.doi} -> ${result.file} (${result.bytes} bytes, ~${result.pages} pages, sha256 ${result.sha256.slice(0, 12)}...)`,
        );
      } else {
        console.log(`${result.doi} -> NOT FOUND (${result.reason})`);
      }
    }
  }

  if (options.json) {
    console.log(JSON.stringify(results.length === 1 ? results[0] : results, null, 2));
  }

  if (results.some((result) => !result.ok)) process.exitCode = 2;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error.stack || error.message);
    process.exit(1);
  });
}
