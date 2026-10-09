// Cria (ou atualiza) a agência de demonstração da Central de Ajuda: "Rota Sul Viagens",
// com páginas no visual novo, formulários, leads em várias etapas, clientes, pixels e
// visitas dos últimos 30 dias. Usa a API do sistema rodando (veja README.md).
//
//   HELP_ADMIN_EMAIL=... HELP_ADMIN_PASSWORD=... node seed.mjs
//
// Pode rodar de novo: páginas, formulários, clientes e pixels são recriados.
import fs from 'fs';
import { execFileSync } from 'child_process';
import { chromium } from 'playwright';
import { gerarFotos } from './lib/fotos.mjs';
import { API, DEMO, chromiumPath, login, req } from './lib/api.mjs';
import { paginas } from './lib/paginas.mjs';

const ADMIN_EMAIL = process.env.HELP_ADMIN_EMAIL;
const ADMIN_PASSWORD = process.env.HELP_ADMIN_PASSWORD;
const OUT = new URL('./out/', import.meta.url).pathname;

import { dia } from './lib/paginas.mjs';

async function garantirUsuaria() {
  try {
    return await login(DEMO.email, DEMO.password);
  } catch {
    if (!ADMIN_EMAIL || !ADMIN_PASSWORD) throw new Error('Defina HELP_ADMIN_EMAIL e HELP_ADMIN_PASSWORD (superusuário local) para criar a conta de demonstração.');
    const admin = await login(ADMIN_EMAIL, ADMIN_PASSWORD);
    await req(admin, 'POST', '/admin/users', {
      name: DEMO.name,
      email: DEMO.email,
      whatsapp: '48999990000',
      password: DEMO.password,
      plan: 'infinity',
      valid_until: dia(365 * 3),
    });
    return login(DEMO.email, DEMO.password);
  }
}

async function enviarFoto(token, agencyId, arquivo) {
  const form = new FormData();
  form.append('file', new Blob([fs.readFileSync(arquivo)], { type: 'image/jpeg' }), arquivo.split('/').pop());
  const res = await fetch(`${API}/media/upload?agency_id=${agencyId}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form });
  if (!res.ok) throw new Error(`upload ${res.status} ${await res.text()}`);
  return (await res.json()).url;
}

const NOMES = [
  ['Juliana Prado', 'Florianópolis'], ['Ricardo Mendes', 'Curitiba'], ['Camila Rocha', 'Porto Alegre'],
  ['Fernando Lima', 'São Paulo'], ['Patrícia Alves', 'Joinville'], ['Bruno Carvalho', 'Blumenau'],
  ['Aline Moreira', 'Campinas'], ['Thiago Nunes', 'Belo Horizonte'], ['Larissa Costa', 'Londrina'],
  ['Gustavo Ribeiro', 'Criciúma'], ['Mariana Teixeira', 'Itajaí'], ['Rafael Duarte', 'Chapecó'],
  ['Beatriz Martins', 'Balneário Camboriú'], ['Eduardo Pires', 'Maringá'],
];
const fone = i => `4899${String(1234567 + i * 7919).slice(0, 7)}`;
const email = nome => nome.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/\s+/g, '.') + '@email.com';

async function main() {
  const browser = await chromium.launch({ executablePath: chromiumPath() });
  const fotos = await gerarFotos(browser, `${OUT}fotos`);
  await browser.close();

  const token = await garantirUsuaria();
  const [agency] = await req(token, 'GET', '/agencies/me');
  const agencyId = agency.id;
  await req(token, 'PUT', `/agencies/${agencyId}`, {
    name: 'Rota Sul Viagens', slug: 'rotasul', primary_color: '#0b8059', contact_email: 'contato@rotasulviagens.com.br',
    cta_whatsapp: '48999990000', description: 'Roteiros em grupo pelo Brasil e América do Sul, com guia e grupos pequenos.',
    social_links: [{ network: 'instagram', url: 'https://instagram.com/rotasulviagens' }, { network: 'facebook', url: 'https://facebook.com/rotasulviagens' }],
  });

  const f = {};
  for (const [nome, arquivo] of Object.entries(fotos)) f[nome] = await enviarFoto(token, agencyId, arquivo);

  // Formulários e etapas das oportunidades.
  for (const form of await req(token, 'GET', `/lead-forms?agencyId=${agencyId}`)) await req(token, 'DELETE', `/lead-forms/${form.id}`).catch(() => {});
  let statuses = await req(token, 'GET', `/lead-forms/statuses?agencyId=${agencyId}`);
  const ETAPAS = [['Novo contato', '#2563EB'], ['Em atendimento', '#D97706'], ['Proposta enviada', '#7C3AED'], ['Fechado', '#059669']];
  for (const [name, color] of ETAPAS) {
    const atual = statuses.find(s => s.name === name);
    if (atual) await req(token, 'PUT', `/lead-forms/statuses/${atual.id}`, { name, color });
    else await req(token, 'POST', '/lead-forms/statuses', { agencyId, name, color });
  }
  statuses = await req(token, 'GET', `/lead-forms/statuses?agencyId=${agencyId}`);
  const etapa = nome => statuses.find(s => s.name === nome)?.id;
  const campos = [
    { id: 'nome', type: 'name', label: 'Nome', required: true },
    { id: 'whatsapp', type: 'phone', label: 'WhatsApp', required: true },
    { id: 'email', type: 'email', label: 'E-mail', required: false },
    { id: 'cidade', type: 'city', label: 'Cidade', required: false },
  ];
  const espera = await req(token, 'POST', '/lead-forms', { agencyId, name: 'Lista de espera Jalapão', title: 'Entre na lista de espera', subtitle: 'Avisamos você primeiro.', buttonLabel: 'Quero ser avisado', showLogo: true, fields: campos, defaultStatusId: etapa('Novo contato'), autoWhatsAppEnabled: false });
  const orcamento = await req(token, 'POST', '/lead-forms', { agencyId, name: 'Orçamento personalizado', title: 'Peça seu orçamento', buttonLabel: 'Enviar', showLogo: true, fields: [...campos.slice(0, 3), { id: 'viagem', type: 'textarea', label: 'Conte sobre a viagem', required: false }], defaultStatusId: etapa('Novo contato'), autoWhatsAppEnabled: false });

  // Páginas (recria as da agência).
  for (const page of await req(token, 'GET', `/pages?agency_id=${agencyId}`)) await req(token, 'DELETE', `/pages/${page.id}`).catch(() => {});
  const criadas = {};
  for (const p of paginas(f, espera.id)) {
    const page = await req(token, 'POST', '/pages', { agency_id: agencyId, title: p.title, slug: p.slug, status: 'draft', config_json: { sections: p.sections } });
    if (p.publish) await req(token, 'POST', `/pages/${page.id}/publish`, { publish: true });
    if (p.principal) await req(token, 'POST', `/pages/${page.id}/set-default`);
    criadas[p.slug] = page.id;
  }

  // Leads: inscrições pelos formulários, distribuídas nas etapas.
  const ordem = ['Novo contato', 'Novo contato', 'Em atendimento', 'Novo contato', 'Proposta enviada', 'Em atendimento', 'Fechado', 'Novo contato', 'Proposta enviada', 'Em atendimento', 'Novo contato', 'Fechado', 'Novo contato', 'Em atendimento'];
  for (const [i, [nome, cidade]] of NOMES.entries()) {
    const form = i % 3 === 2 ? orcamento : espera;
    const values = [
      { fieldId: 'nome', type: 'name', value: nome },
      { fieldId: 'whatsapp', type: 'phone', value: fone(i) },
      { fieldId: 'email', type: 'email', value: email(nome) },
      ...(form === espera ? [{ fieldId: 'cidade', type: 'city', value: cidade }] : [{ fieldId: 'viagem', type: 'textarea', value: 'Casal, quero ir em julho e ficar em pousada.' }]),
    ];
    await req(null, 'POST', `/public/lead-forms/${form.id}/submit`, { values, source: 'page', pageId: criadas['jalapao-6-dias'], pageSlug: 'jalapao-6-dias', pageTitle: 'Jalapão 6 dias' });
  }
  const contatos = await req(token, 'GET', `/lead-forms/contacts?agencyId=${agencyId}`);
  for (const [i, contato] of contatos.entries()) {
    const alvo = etapa(ordem[i % ordem.length]);
    if (alvo) await req(token, 'PUT', `/lead-forms/contacts/${contato.id}/status`, { statusId: alvo });
  }

  // Clientes.
  for (const c of await req(token, 'GET', `/clients?agencyId=${agencyId}`).catch(() => [])) await req(token, 'DELETE', `/clients/${c.id}`).catch(() => {});
  for (const [nome, cidade] of NOMES.slice(0, 7)) await req(token, 'POST', '/clients', { agencyId, name: nome, phone: fone(NOMES.findIndex(n => n[0] === nome)), email: email(nome), city: cidade, state: 'SC', tags: ['Jalapão'] }).catch(e => console.log('  cliente:', e.message.slice(0, 120)));

  // Pixels de rastreamento.
  for (const px of await req(token, 'GET', '/pixels/').catch(() => [])) await req(token, 'DELETE', `/pixels/${px.id}`).catch(() => {});
  await req(token, 'POST', '/pixels/', { name: 'Meta Rota Sul', type: 'meta', value: '1234567890123456' }).catch(e => console.log('  pixel:', e.message.slice(0, 120)));
  await req(token, 'POST', '/pixels/', { name: 'Google Analytics', type: 'ga', value: 'G-ROTASUL26' }).catch(e => console.log('  pixel:', e.message.slice(0, 120)));

  // Visitas dos últimos 30 dias (direto no banco, só se HELP_PSQL_URL estiver definido).
  if (process.env.HELP_PSQL_URL) {
    const linhas = [];
    for (const [slug, id] of Object.entries(criadas)) {
      const peso = { 'jalapao-6-dias': 1, 'chile-santiago-vinicolas': 0.55, 'reveillon-porto-de-galinhas': 0.7 }[slug] || 0.1;
      for (let d = 29; d >= 0; d--) {
        const v = Math.round((60 + 40 * Math.sin(d / 3) + (29 - d) * 2.2) * peso);
        linhas.push(`(${id}, current_date - ${d}, ${v}, ${Math.round(v * 0.08)}, ${Math.round(v * 0.12)})`);
      }
    }
    const ids = Object.values(criadas).join(',');
    execFileSync('psql', [process.env.HELP_PSQL_URL, '-q', '-c', `delete from page_visit_stats where page_id in (${ids}); insert into page_visit_stats (page_id, date, visits, clicks_whatsapp, clicks_cta) values ${linhas.join(',')};`]);
  }

  fs.writeFileSync(`${OUT}demo.json`, JSON.stringify({ agencyId, agencySlug: 'rotasul', pages: criadas, forms: { espera: espera.id, orcamento: orcamento.id }, fotos: f }, null, 2));
  console.log('Agência de demonstração pronta:', JSON.stringify({ agencyId, pages: criadas }));
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
