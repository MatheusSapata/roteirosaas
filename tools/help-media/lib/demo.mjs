// Ajudas para os roteiros: estado da agência de demonstração (ids de seed.mjs) e limpeza
// do que os roteiros criam, para cada gravação começar igual.
import fs from 'fs';
import { DEMO, login, req } from './api.mjs';

export const demo = () => JSON.parse(fs.readFileSync(new URL('../out/demo.json', import.meta.url)));

/** Apaga as páginas que os roteiros criaram (as da demonstração ficam). */
export async function limparPaginasNovas() {
  const { agencyId, pages } = demo();
  const token = await login(DEMO.email, DEMO.password);
  const fixas = new Set(Object.values(pages));
  for (const page of await req(token, 'GET', `/pages?agency_id=${agencyId}`)) {
    if (!fixas.has(page.id)) await req(token, 'DELETE', `/pages/${page.id}`).catch(() => {});
  }
}

/** Id da página da demonstração pelo link (slug). */
export const pagina = slug => demo().pages[slug];

/** Volta a página ao conteúdo e à situação (publicada ou rascunho) da demonstração. */
export async function restaurarPagina(slug) {
  const { paginas } = await import('./paginas.mjs');
  const dados = demo();
  const def = paginas(dados.fotos, dados.forms.espera).find(p => p.slug === slug);
  const token = await login(DEMO.email, DEMO.password);
  const id = dados.pages[slug];
  await req(token, 'PUT', `/pages/${id}`, { title: def.title, slug: def.slug, config_json: { sections: def.sections } });
  await req(token, 'POST', `/pages/${id}/publish`, { publish: !!def.publish });
}
