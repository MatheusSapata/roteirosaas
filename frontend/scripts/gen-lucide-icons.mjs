// Gera src/utils/generated/lucideIcons.json com o desenho de todos os ícones do Lucide
// (licença ISC), para o seletor de ícones e para as páginas carregarem só quando usam.
// Rodar de novo depois de atualizar o lucide-vue-next: node scripts/gen-lucide-icons.mjs
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import vm from "node:vm";

const dir = "node_modules/lucide-vue-next/dist/esm/icons/";
const out = {};
for (const file of readdirSync(dir).sort()) {
  if (!file.endsWith(".js")) continue;
  const source = readFileSync(dir + file, "utf8");
  const match = source.match(/createLucideIcon\("([^"]+)",\s*(\[[\s\S]*\])\);/);
  if (!match) continue;
  const nodes = vm.runInNewContext(match[2]);
  out[match[1]] = nodes.map(([tag, attrs]) => {
    const { key, ...rest } = attrs;
    return [tag, rest];
  });
}
writeFileSync("src/utils/generated/lucideIcons.json", JSON.stringify(out));
console.log(`${Object.keys(out).length} ícones`);
