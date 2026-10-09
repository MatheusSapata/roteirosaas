// Gera a mídia da Central de Ajuda a partir dos roteiros em roteiros/*.mjs:
//   - demonstração interativa: telas de cada passo nos temas claro e escuro + passos.json
//   - vídeo curto (MP4) com cursor e legendas, quando o roteiro tem `video: true`
// A saída vai para frontend/src/help/media/<id>/ e entra no build do painel.
//
//   node gerar.mjs                 todos os roteiros
//   node gerar.mjs criar-pagina    só os roteiros pedidos
//   node gerar.mjs --sem-video     pula os vídeos
import fs from 'fs';
import path from 'path';
import { abrirNavegador } from './lib/sessao.mjs';
import { capturarTour } from './lib/tour.mjs';
import { gravarVideo } from './lib/video.mjs';

const PASTA_ROTEIROS = new URL('./roteiros/', import.meta.url).pathname;
const SAIDA = new URL('../../frontend/src/help/media/', import.meta.url).pathname;
const TMP = new URL('./out/video-tmp/', import.meta.url).pathname;

const args = process.argv.slice(2);
const semVideo = args.includes('--sem-video');
const soVideo = args.includes('--so-video');
const pedidos = args.filter(a => !a.startsWith('--'));

const arquivos = fs.readdirSync(PASTA_ROTEIROS).filter(f => f.endsWith('.mjs') && !f.startsWith('_')).sort();
const roteiros = [];
for (const arquivo of arquivos) {
  const { default: roteiro } = await import(path.join(PASTA_ROTEIROS, arquivo));
  if (!pedidos.length || pedidos.includes(roteiro.id)) roteiros.push(roteiro);
}
if (!roteiros.length) {
  console.error('Nenhum roteiro encontrado para:', pedidos.join(', '));
  process.exit(1);
}

const browser = await abrirNavegador();
let falhas = 0;
for (const roteiro of roteiros) {
  const pasta = `${SAIDA}${roteiro.id}`;
  fs.mkdirSync(pasta, { recursive: true });
  const t = Date.now();
  try {
    if (!soVideo) {
      for (const f of fs.readdirSync(pasta).filter(f => f.endsWith('.webp'))) fs.unlinkSync(`${pasta}/${f}`);
      if (roteiro.antesDeTudo) await roteiro.antesDeTudo();
      const passos = await capturarTour(browser, roteiro, 'light', pasta);
      if (roteiro.antesDeTudo) await roteiro.antesDeTudo();
      await capturarTour(browser, roteiro, 'dark', pasta);
      fs.writeFileSync(`${pasta}/passos.json`, JSON.stringify({ id: roteiro.id, titulo: roteiro.titulo, gerado: new Date().toISOString().slice(0, 10), passos }, null, 2) + '\n');
    }
    if (roteiro.video && !semVideo) {
      if (roteiro.antesDeTudo) await roteiro.antesDeTudo();
      await gravarVideo(browser, roteiro, `${pasta}/video.mp4`, `${TMP}${roteiro.id}`);
    }
    if (roteiro.depoisDeTudo) await roteiro.depoisDeTudo();
    const kb = fs.readdirSync(pasta).reduce((soma, f) => soma + fs.statSync(`${pasta}/${f}`).size, 0) / 1024;
    console.log(`✓ ${roteiro.id} (${roteiro.passos.length} passos, ${Math.round(kb)} KB, ${Math.round((Date.now() - t) / 1000)}s)`);
  } catch (e) {
    if (roteiro.depoisDeTudo) await roteiro.depoisDeTudo().catch(() => {});
    falhas++;
    console.log(`✗ ${roteiro.id}: ${e.message.split('\n')[0]}`);
  }
}
await browser.close();
process.exit(falhas ? 1 : 0);
