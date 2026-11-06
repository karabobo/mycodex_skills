#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { readAnnotations, sha256 } from "./pdf_annotations.mjs";

function usage() {
  console.error("Usage: node scripts/check_pdf_highlights.mjs SOURCE.pdf OUTPUT.pdf --expected-count N");
}

function nearlyEqual(a, b, epsilon = 0.01) {
  return Math.abs(a - b) <= epsilon;
}

function validQuad(points, width, height) {
  if (!Array.isArray(points) || points.length !== 8 || points.some((n) => !Number.isFinite(n))) return false;
  for (let i = 0; i < points.length; i += 2) {
    if (points[i] < -0.5 || points[i] > width + 0.5 || points[i + 1] < -0.5 || points[i + 1] > height + 0.5) return false;
  }
  return true;
}

async function check(sourcePath, outputPath, expectedCount) {
  const errors = [];
  if (!fs.existsSync(sourcePath) || !fs.existsSync(outputPath)) throw new Error("source and output must exist");
  if (path.resolve(sourcePath) === path.resolve(outputPath)) errors.push("source_output_must_differ");
  const source = await readAnnotations(sourcePath);
  const output = await readAnnotations(outputPath);
  if (source.pageCount !== output.pageCount) errors.push("page_count_changed");
  let total = 0;
  const markedPages = [];
  for (const page of output.pages) {
    let count = 0;
    for (const annot of page.annotations) {
      if (annot.subtype !== "Highlight") {
        errors.push(`page_${page.page}:non_highlight_comment`);
        continue;
      }
      count += 1;
      total += 1;
      if (annot.contents || annot.title) errors.push(`page_${page.page}:comment_metadata`);
      if (annot.rect.length !== 4 || annot.rect.some((n) => !Number.isFinite(n))) errors.push(`page_${page.page}:invalid_rect`);
      if (annot.quadPoints.length === 0 || annot.quadPoints.length % 8 !== 0) errors.push(`page_${page.page}:invalid_quads`);
      for (let i = 0; i < annot.quadPoints.length; i += 8) {
        if (!validQuad(annot.quadPoints.slice(i, i + 8), page.width, page.height)) errors.push(`page_${page.page}:quad_outside_page`);
      }
    }
    if (count) markedPages.push({ page: page.page, highlights: count });
  }
  if (expectedCount !== undefined && total !== expectedCount) errors.push("highlight_count_mismatch");
  if (total === 0 && expectedCount !== 0) errors.push("no_highlights");
  return {
    passed: errors.length === 0,
    errors: [...new Set(errors)].sort(),
    highlights: total,
    marked_pages: markedPages,
    source_sha256: sha256(sourcePath),
    output_sha256: sha256(outputPath),
    manual_checks_required: ["claim_evidence_alignment", "each_highlight_visual_review"],
  };
}

async function main() {
  if (process.argv.length < 3) {
    usage();
    process.exitCode = 2;
    return;
  }
  const source = process.argv[2];
  const output = process.argv[3];
  const expectedIndex = process.argv.indexOf("--expected-count");
  const expected = expectedIndex >= 0 ? Number(process.argv[expectedIndex + 1]) : undefined;
  if (expected !== undefined && (!Number.isInteger(expected) || expected < 0)) throw new Error("--expected-count must be nonnegative");
  const result = await check(source, output, expected);
  console.log(JSON.stringify(result, null, 2));
  if (!result.passed) process.exitCode = 1;
}

main().catch((error) => {
  console.error(JSON.stringify({ passed: false, errors: [error.message] }, null, 2));
  process.exitCode = 1;
});
