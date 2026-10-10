// Gera .gz e .br ao lado dos arquivos do build (JS, CSS, HTML, SVG, JSON). Com
// `gzip_static on` (e `brotli_static on`, se o nginx tiver o módulo), o servidor entrega
// a versão comprimida sem gastar CPU a cada visita.
import { readdir, readFile, writeFile, stat } from "node:fs/promises";
import { join, extname } from "node:path";
import { brotliCompressSync, constants, gzipSync } from "node:zlib";

const DIST = new URL("../dist/", import.meta.url).pathname;
const TYPES = new Set([".js", ".css", ".html", ".svg", ".json", ".txt"]);
const MIN_BYTES = 1024;

const walk = async dir => (await Promise.all((await readdir(dir, { withFileTypes: true })).map(entry => {
  const path = join(dir, entry.name);
  return entry.isDirectory() ? walk(path) : [path];
}))).flat();

let before = 0;
let after = 0;
for (const file of await walk(DIST)) {
  if (!TYPES.has(extname(file)) || (await stat(file)).size < MIN_BYTES) continue;
  const data = await readFile(file);
  const gz = gzipSync(data, { level: 9 });
  const br = brotliCompressSync(data, { params: { [constants.BROTLI_PARAM_QUALITY]: 11, [constants.BROTLI_PARAM_SIZE_HINT]: data.length } });
  await writeFile(`${file}.gz`, gz);
  await writeFile(`${file}.br`, br);
  before += data.length;
  after += br.length;
}
console.log(`compress-dist: ${Math.round(before / 1024)} KB -> ${Math.round(after / 1024)} KB (brotli)`);
