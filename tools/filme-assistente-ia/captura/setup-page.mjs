// Upload the PD photos to the local stack and create the "Gramado e Canela" page (blank).
import fs from 'fs';
const HM = '/home/user/roteirosaas/tools/help-media';
const { API, DEMO, login, req } = await import(`${HM}/lib/api.mjs`);
const demo = JSON.parse(fs.readFileSync(`${HM}/out/demo.json`));
const token = await login(DEMO.email, DEMO.password);
const fotos = {};
for (const n of ['catedral', 'ruacoberta', 'cascata', 'snowland', 'chocolate', 'lagonegro', 'igreja']) {
  const form = new FormData();
  form.append('file', new Blob([fs.readFileSync(`../photos/full/${n}.jpg`)], { type: 'image/jpeg' }), `${n}.jpg`);
  const res = await fetch(`${API}/media/upload?agency_id=${demo.agencyId}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form });
  const j = await res.json(); fotos[n] = j.url || j.path || j; console.log(n, res.status, JSON.stringify(j).slice(0, 120));
}
const existing = (await req(token, 'GET', `/pages?agency_id=${demo.agencyId}`)).find(p => p.slug === 'gramado-e-canela');
if (existing) await req(token, 'DELETE', `/pages/${existing.id}`);
const page = await req(token, 'POST', '/pages', { agency_id: demo.agencyId, title: 'Gramado e Canela', slug: 'gramado-e-canela', status: 'draft', config_json: { sections: [] } });
fs.writeFileSync('film-state.json', JSON.stringify({ pageId: page.id, fotos, agencySlug: demo.agencySlug }, null, 1));
console.log('page', page.id);
