const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [dir, outdir] = process.argv.slice(2);
fs.mkdirSync(outdir, { recursive: true });
const V = {
  escuro: { bg: '#0A110E', glow: 'rgba(10,99,70,.55)', logo: 'fundo-escuro', icon: 'fundo-escuro', txt: 'rgba(255,255,255,.78)', route: '#90EE8F', ro: .28 },
  verde:  { bg: '#0A6346', glow: 'rgba(144,238,143,.22)', logo: 'fundo-verde', icon: 'fundo-verde', txt: 'rgba(255,255,255,.85)', route: '#90EE8F', ro: .30 },
  claro:  { bg: '#EFF3ED', glow: 'rgba(144,238,143,.45)', logo: 'principal', icon: 'principal', txt: '#3E5247', route: '#15915C', ro: .30 },
};
const svg = (f) => fs.readFileSync(path.join(dir, f), 'utf8').replace(/<\?xml[^>]*>/, '').replace(/width="\d+" height="\d+"/, '');
(async () => {
  const b = await chromium.launch();
  for (const [name, v] of Object.entries(V)) {
    const logo = svg(`roteiro-online-horizontal-${v.logo}.svg`);
    const pin = svg(`roteiro-online-icone-${v.icon}.svg`);
    const html = `<!doctype html><html><head><style>
      html,body{margin:0}
      .c{position:relative;width:1200px;height:630px;overflow:hidden;background:${v.bg};font-family:Inter,sans-serif}
      .glow{position:absolute;inset:0;background:radial-gradient(60% 75% at 50% 46%, ${v.glow}, transparent 70%)}
      .route{position:absolute;inset:0}
      .pinA{position:absolute;width:64px;left:104px;top:418px;opacity:.9}
      .pinB{position:absolute;width:64px;right:96px;top:58px;opacity:.9}
      .logo{position:absolute;left:50%;top:248px;transform:translate(-50%,-50%);width:760px}
      .logo svg,.pinA svg,.pinB svg{display:block;width:100%;height:auto}
      .t{position:absolute;left:0;right:0;top:372px;text-align:center;color:${v.txt};font-size:36px;font-weight:500;letter-spacing:-.01em}
    </style></head><body><div class="c">
      <div class="glow"></div>
      <svg class="route" viewBox="0 0 1200 630"><path d="M136 470 C 150 600, 420 600, 520 560 S 760 470, 900 520 S 1180 420, 1130 300 S 1010 150, 1072 118"
        fill="none" stroke="${v.route}" stroke-opacity="${v.ro}" stroke-width="4" stroke-linecap="round" stroke-dasharray="2 16"/></svg>
      <div class="pinA">${pin}</div><div class="pinB">${pin}</div>
      <div class="logo">${logo}</div>
      <div class="t">Descreva a viagem. A IA monta a página.</div>
    </div></body></html>`;
    for (const sc of [1, 2]) {
      const pg = await b.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: sc });
      await pg.setContent(html); await pg.waitForTimeout(150);
      await pg.screenshot({ path: path.join(outdir, `roteiro-online-compartilhamento-${name}${sc === 2 ? '@2x' : ''}.png`) });
      await pg.close();
    }
  }
  await b.close();
})();
