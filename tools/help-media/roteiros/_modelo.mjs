// Modelo de roteiro. Copie para roteiros/<id>.mjs (o id é o mesmo do artigo em
// frontend/src/help/content.ts) e rode `node gerar.mjs <id>`.
//
// Cada passo vira uma tela da demonstração interativa e um trecho do vídeo:
//   legenda   texto curto do passo ("Clique em Nova página")
//   detalhe   explicação opcional, mostrada abaixo da legenda na demonstração
//   alvo      seletor do Playwright (ou função page => Locator) do ponto de clique
//   acao      'clicar' (padrão), 'digitar' (com `texto`), 'selecionar' (com `valor`),
//             'passar' (hover) ou 'nenhuma' (só destaca)
//   antes     função(page) que roda antes da captura (rolar, abrir algo)
//   depois    função(page) que roda depois da ação
//   esperar   ms depois da ação (padrão 1100)
// Último passo sem alvo = tela final, sem ponto de clique.
//
// No roteiro: `rota` (texto ou função), `pronto` (espera a tela), `video` (grava o MP4),
// `antesDeTudo` / `depoisDeTudo` (deixam os dados da demonstração como estavam; veja
// lib/demo.mjs).
export default {
  id: 'exemplo',
  titulo: 'Exemplo',
  rota: '/admin/dashboard',
  video: false,
  pronto: page => page.getByRole('heading', { level: 1 }).first().waitFor(),
  passos: [
    { legenda: 'Clique em Nova página', alvo: 'text=Nova página', acao: 'nenhuma' },
    { legenda: 'Pronto' },
  ],
};
