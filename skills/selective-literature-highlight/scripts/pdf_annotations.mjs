import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.resolve(HERE, "..");

let pdfLibPromise;
let pdfjsPromise;

async function loadPdfLib() {
  if (!pdfLibPromise) pdfLibPromise = import("pdf-lib");
  return pdfLibPromise;
}

async function loadPdfjs() {
  if (!pdfjsPromise) {
    pdfjsPromise = import("pdfjs-dist/legacy/build/pdf.mjs");
  }
  return pdfjsPromise;
}

function standardFontDataPath() {
  const candidates = [
    process.env.DSH_PDF_STANDARD_FONTS,
    path.join(SKILL_DIR, "node_modules/pdfjs-dist/standard_fonts"),
    path.resolve(process.cwd(), "node_modules/pdfjs-dist/standard_fonts"),
  ].filter(Boolean);
  for (const dir of candidates) {
    try {
      if (fs.existsSync(dir) && fs.statSync(dir).isDirectory()) return `${dir}${path.sep}`;
    } catch {
      // Try the next candidate.
    }
  }
  return undefined;
}

export async function readAnnotations(pdfPath) {
  const { PDFDocument, PDFName, PDFNumber, PDFArray } = await loadPdfLib();
  const bytes = fs.readFileSync(pdfPath);
  const doc = await PDFDocument.load(bytes, { updateMetadata: false, ignoreEncryption: false });
  const pages = [];
  let total = 0;
  for (let index = 0; index < doc.getPageCount(); index += 1) {
    const page = doc.getPage(index);
    const annots = page.node.lookupMaybe(PDFName.of("Annots"), PDFArray);
    const items = [];
    if (annots) {
      for (let i = 0; i < annots.size(); i += 1) {
        const ref = annots.get(i);
        const annot = page.doc.context.lookup(ref);
        const subtype = annot?.get(PDFName.of("Subtype"))?.decodeText?.() || "";
        const rect = annot?.get(PDFName.of("Rect"));
        const quad = annot?.get(PDFName.of("QuadPoints"));
        const rectValues = rect ? Array.from({ length: rect.size() }, (_, n) => rect.get(n).asNumber()) : [];
        const quadValues = quad ? Array.from({ length: quad.size() }, (_, n) => quad.get(n).asNumber()) : [];
        const contents = annot?.get(PDFName.of("Contents"))?.decodeText?.() || "";
        const title = annot?.get(PDFName.of("T"))?.decodeText?.() || "";
        items.push({ subtype, rect: rectValues, quadPoints: quadValues, contents, title });
        if (subtype === "Highlight") total += 1;
      }
    }
    pages.push({ page: index + 1, width: page.getWidth(), height: page.getHeight(), annotations: items });
  }
  return { pageCount: pages.length, highlights: total, pages };
}

export async function extractTextItems(pdfPath) {
  const pdfjs = await loadPdfjs();
  const data = new Uint8Array(fs.readFileSync(pdfPath));
  const doc = await pdfjs.getDocument({
    data,
    useSystemFonts: false,
    isEvalSupported: false,
    standardFontDataUrl: standardFontDataPath(),
  }).promise;
  const pages = [];
  for (let index = 1; index <= doc.numPages; index += 1) {
    const page = await doc.getPage(index);
    const viewport = page.getViewport({ scale: 1 });
    const content = await page.getTextContent();
    const items = content.items.filter((item) => typeof item.str === "string" && item.str.length > 0).map((item) => ({
      text: item.str,
      transform: [...item.transform],
      width: item.width,
      height: item.height,
      x: item.transform[4],
      y: item.transform[5],
    }));
    pages.push({ page: index, width: viewport.width, height: viewport.height, items });
  }
  if (typeof doc.destroy === "function") await doc.destroy();
  return { pageCount: pages.length, pages };
}

export function sha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

export function resolvePdfPath(input) {
  return path.resolve(input);
}
