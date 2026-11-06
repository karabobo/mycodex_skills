#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { PDFArray, PDFName, PDFNumber } from "pdf-lib";
import { extractTextItems } from "./pdf_annotations.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));

function usage() {
  console.error("Usage: node scripts/highlight_pdf.mjs SOURCE.pdf OUTPUT.pdf SPEC.json");
  console.error('SPEC: {"highlights":[{"page":1,"text":"exact phrase","color":[1,0.8,0],"opacity":0.3}]}');
}

function normalize(value) {
  return value.replace(/\s+/g, " ").trim();
}

function rgb(value) {
  if (!Array.isArray(value) || value.length !== 3 || value.some((n) => !Number.isFinite(n))) {
    return [1, 0.85, 0.2];
  }
  return value.map((n) => Math.max(0, Math.min(1, n)));
}

function locatePhrase(items, phrase) {
  const wanted = normalize(phrase);
  for (let start = 0; start < items.length; start += 1) {
    let combined = "";
    for (let end = start; end < items.length && combined.length <= wanted.length + 80; end += 1) {
      combined = normalize(`${combined} ${items[end].text}`);
      if (combined === wanted || combined.includes(wanted)) return items.slice(start, end + 1);
      if (combined.length > wanted.length && !wanted.startsWith(combined) && !combined.includes(wanted)) break;
    }
  }
  return null;
}

function itemRect(item) {
  const x1 = item.x;
  const y1 = item.y - Math.abs(item.height || 10);
  const x2 = item.x + Math.abs(item.width || 1);
  const y2 = item.y + Math.max(1, Math.abs(item.height || 10) * 0.15);
  return [x1, y1, x2, y2];
}

function unionRect(items) {
  const rects = items.map(itemRect);
  return [
    Math.min(...rects.map((r) => r[0])),
    Math.min(...rects.map((r) => r[1])),
    Math.max(...rects.map((r) => r[2])),
    Math.max(...rects.map((r) => r[3])),
  ];
}

function addHighlight(page, rect, color, opacity) {
  const context = page.doc.context;
  const [x1, y1, x2, y2] = rect;
  const annot = context.obj({
    Type: "Annot",
    Subtype: "Highlight",
    Rect: [x1, y1, x2, y2],
    QuadPoints: [x1, y2, x2, y2, x1, y1, x2, y1],
    C: color,
    F: 4,
    CA: opacity,
    ca: opacity,
  });
  const annots = page.node.lookup(PDFName.of("Annots"), PDFArray) || context.obj([]);
  annots.push(annot);
  page.node.set(PDFName.of("Annots"), annots);
}

async function main() {
  if (process.argv.length !== 5) {
    usage();
    return 2;
  }
  const [, , sourcePath, outputPath, specPath] = process.argv;
  const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
  if (!Array.isArray(spec.highlights)) throw new Error("spec.highlights must be an array");
  const { PDFDocument } = await import("pdf-lib");
  const sourceBytes = fs.readFileSync(sourcePath);
  const text = await extractTextItems(sourcePath);
  const doc = await PDFDocument.load(sourceBytes, { updateMetadata: false });
  const details = [];
  for (const request of spec.highlights) {
    const pageNumber = Number(request.page);
    if (!Number.isInteger(pageNumber) || pageNumber < 1 || pageNumber > text.pageCount) {
      throw new Error(`invalid page: ${request.page}`);
    }
    if (typeof request.text !== "string" || !request.text.trim()) throw new Error("highlight text must be non-empty");
    const match = locatePhrase(text.pages[pageNumber - 1].items, request.text);
    if (!match) throw new Error(`exact passage not found on page ${pageNumber}: ${request.text}`);
    addHighlight(doc.getPage(pageNumber - 1), unionRect(match), rgb(request.color), Number.isFinite(request.opacity) ? request.opacity : 0.3);
    details.push({ page: pageNumber, text: request.text, rects: 1 });
  }
  fs.mkdirSync(path.dirname(path.resolve(outputPath)), { recursive: true });
  fs.writeFileSync(outputPath, await doc.save({ useObjectStreams: false, addDefaultPage: false }));
  console.log(JSON.stringify({ ok: true, output: outputPath, highlights: details.length, details }, null, 2));
  return 0;
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exitCode = 1;
});
