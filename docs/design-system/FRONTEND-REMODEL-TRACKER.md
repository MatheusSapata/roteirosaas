# Roteiro Online — Inventário e acompanhamento da remodelação

Atualizado em: 08/10/2026  
Fonte de verdade das rotas: `frontend/src/router/index.ts`

Este documento acompanha a adoção do design system Viajeon no frontend do Roteiro Online.
Uma mesma `View` pode representar várias telas quando seu conteúdo muda conforme a rota.

## Legenda

- `MAPEADA`: tela identificada, ainda sem remodelação.
- `EM ESPECIFICAÇÃO`: estrutura visual sendo definida.
- `EM IMPLEMENTAÇÃO`: alteração em andamento.
- `EM QA`: implementação concluída, aguardando validações.
- `CONCLUÍDA`: passou pelos critérios de conclusão.
- `FORA DO ESCOPO`: não deve receber o design da plataforma.

## Critérios para marcar uma tela como concluída

- [ ] Usa tokens semânticos em vez de cores fixas da plataforma.
- [ ] Usa os componentes canônicos aplicáveis.
- [ ] Está consistente em desktop e mobile.
- [ ] Foi validada nos temas claro e escuro, quando pertence à área logada.
- [ ] Possui foco visível e nomes acessíveis nos botões de ícone.
- [ ] Tem estados de carregamento, vazio, erro, sucesso e bloqueio revisados.
- [ ] Preserva permissões, regras de plano e comportamento funcional existente.
- [ ] Não altera a identidade configurável das páginas publicadas pelos clientes.

## Resumo de progresso

| Grupo | Total | Em QA | Concluídas |
|---|---:|---:|---:|
| Fundação e shell | 2 | 2 | 0 |
| Acesso, convite e compra | 7 | 7 | 0 |
| Operação da agência | 19 | 18 | 1 |
| Admin Master | 15 | 15 | 0 |
| Página pública | 1 | 1 | 0 |
| **Total de telas/experiências** | **42** | **41** | **1** |

> Fundação e shell são acompanhados à parte e não entram no total de 41 telas.

---

## 0. Fundação e shell

| ID | Superfície | Arquivo principal | Status | Observações |
|---|---|---|---|---|
| F01 | Tokens globais, tipografia, temas, radius e sombras | `frontend/src/styles/main.css` | EM QA | Tokens do Viaje On; painel sem zoom (100%), tokens âmbar do Admin Master. Conferido claro/escuro em 08/10/2026. |
| F02 | Shell administrativo, sidebar desktop/mobile e modais globais | `frontend/src/layouts/AdminLayout.vue` | EM QA | Menu com as medidas e tempos do Viaje On, contêiner único das telas, Admin Master com menu âmbar e menu do celular em cartão. Conferido em 1440, 1280, 1024 e 390 px, claro e escuro, em 08/10/2026. |

### Componentes canônicos a criar

- [ ] `AppButton`
- [ ] `AppBadge`
- [ ] `AppCard`
- [ ] `AppInput`
- [ ] `AppTextarea`
- [ ] `AppSelect`
- [ ] `AppFormField`
- [ ] `AppPageHeader`
- [ ] `AppEmptyState`
- [ ] `AppDialog`
- [ ] `AppDrawer`
- [ ] `AppDataTable`
- [ ] `AppRowActions`
- [ ] `AppKpiCard`
- [ ] `AppSkeleton`
- [ ] `AppToast`
- [x] Utilitário central de status semânticos
- [x] Formatadores brasileiros centralizados
- [x] Integração de `lucide-vue-next` (ícones padronizados no painel, traço único em `styles/main.css`)
- [ ] Rota interna de catálogo do design system

---

## 1. Acesso, convite e compra

| ID | Tela | Rota | View | Status | Prioridade |
|---|---|---|---|---|---|
| A01 | Login | `/` e `/login` | `views/admin/LoginView.vue` | EM QA | Painéis, formulário, campos e estados alinhados ao design system. |
| A02 | Esqueci minha senha | `/forgot-password` | `views/admin/ForgotPasswordView.vue` | EM QA | Identidade, formulário e feedbacks alinhados aos tokens semânticos. |
| A03 | Redefinir senha | `/reset-password` | `views/admin/ResetPasswordView.vue` | EM QA | Formulário, token inválido e estados de envio alinhados aos tokens. |
| A04 | Criar senha | `/create-password` | `views/admin/CreatePasswordView.vue` | EM QA | Etapas, validações, campos e feedbacks alinhados ao design system. |
| A05 | Aceitar convite | `/accept-invite` | `views/public/AcceptInviteView.vue` | EM QA | Convite válido, inválido e utilizado alinhados ao design system. |
| A06 | Processamento do pedido | `/pedido` | `views/public/CheckoutProcessingView.vue` | EM QA | Processamento, sucesso e erro alinhados aos tokens semânticos. |
| A07 | Checkout personalizado | `/checkout/:offerKey` | `views/public/CustomCheckoutView.vue` | EM QA | Temas, foco, pagamento, aprovação e responsividade preservados e refinados. |

### Estados que precisam ser conferidos

- [ ] Login padrão
- [ ] Login carregando
- [ ] Credenciais inválidas
- [ ] Recuperação enviada
- [ ] Token de redefinição inválido/expirado
- [ ] Senha criada com sucesso
- [ ] Convite válido, inválido e já utilizado
- [ ] Pedido processando, aprovado, pendente e com erro
- [ ] Checkout desktop e mobile
- [ ] Checkout com dados bloqueados/preenchidos

---

## 2. Operação da agência

| ID | Tela | Rota | View | Status | Prioridade |
|---|---|---|---|---|---|
| O01 | Dashboard | `/admin/dashboard` | `views/admin/DashboardView.vue` | CONCLUÍDA | Aprovada visualmente pelo usuário em 16/07/2026. |
| O02 | Lista de páginas | `/admin/pages` | `views/admin/PagesListView.vue` | EM QA | Resumo, filtros, tabela, criação, templates e duplicação remodelados; aguardando aprovação visual. |
| O03 | Editor de página | `/admin/pages/:id/edit` | `views/admin/PageEditorView.vue` | EM QA | Shell, configurações, preview, catálogo, modais e assistente IA remodelados; contraste do tema escuro refinado e editores de seção seguem no ciclo de QA. |
| O04 | Central de aulas | `/admin/aulas` | `views/admin/AulasView.vue` | EM QA | Trilha, progresso, player, módulos e estados ajustados aos temas. |
| O05 | Formulários | `/admin/leads/forms` | `views/admin/LeadsView.vue` | EM QA | Piloto remodelado; campos livres e prévia preservados, aguardando aprovação visual. |
| O06 | Oportunidades | `/admin/leads/opportunities` | `views/admin/LeadsView.vue` | EM QA | Piloto remodelado; respostas dos campos livres preservadas no detalhe, aguardando aprovação visual. |
| O07 | Clientes | `/admin/leads/clients` | `views/admin/LeadsView.vue` + `views/admin/ClientsView.vue` | EM QA | Listagem, KPIs, filtros, cards mobile e criação remodelados; aguardando aprovação visual. |
| O08 | Detalhe do cliente | `/admin/leads/clients/:id` | `views/admin/ClientDetailView.vue` | EM QA | Cabeçalho, métricas, abas, oportunidades, notas, documentos, histórico e dados remodelados; aguardando aprovação visual. |
| O09 | Configurações de leads | `/admin/leads/settings` | `views/admin/LeadsView.vue` | EM QA | Gerenciador do funil, ordenação e modal de etapas remodelados; aguardando aprovação visual. |
| O10 | Caixa de entrada WhatsApp | `/admin/inbox` | `views/admin/InboxView.vue` | EM QA | Conversas, atendimento, compositor, oportunidades e modais remodelados; aguardando aprovação visual. |
| O11 | Caixa de entrada indisponível | `/admin/inbox-unavailable` | `views/admin/InboxUnavailableView.vue` | EM QA | Estado indisponível remodelado; aguardando aprovação visual. |
| O12 | Configurações da agência | `/admin/agency` | `views/admin/AgencySettingsView.vue` | EM QA | Identidade, contato, endereço, marca, redes sociais e aviso de alterações remodelados; aguardando aprovação visual. |
| O13 | Faturas da agência | `/admin/agency/invoices` | `views/admin/AgencyInvoicesView.vue` | EM QA | Resumo financeiro, filtros, cobranças, status e paginação remodelados; aguardando aprovação visual. |
| O14 | Equipe da agência | `/admin/agency/team` | `views/admin/AgencyTeamView.vue` | EM QA | Resumo do plano, membros, convites, menus e permissões remodelados; aguardando aprovação visual. |
| O15 | Domínios personalizados | `/admin/domains` | `views/admin/AgencyDomainsView.vue` | EM QA | Cadastro, favicon, DNS, SSL, ações e guias remodelados; aguardando aprovação visual. |
| O16 | Planos | `/admin/planos` | `views/public/PlansView.vue` | EM QA | Planos, ciclos, alertas e ações alinhados aos tokens semânticos. |
| O17 | Integrações de rastreamento | `/admin/integracoes/rastreamento` | `views/admin/IntegrationsView.vue` | EM QA | Resumo, pixels e conexão segura com o Viajeon alinhados aos dois temas. |
| O18 | Integrações de atendimento | `/admin/integracoes/atendimento` | `views/admin/ConnectionsView.vue` | EM QA | Canal, conexão, QR Code, modais e estados alinhados aos dois temas. |
| O19 | Perfil | `/admin/perfil` | `views/admin/ProfileView.vue` | EM QA | Assinatura, dados pessoais, segurança e uploads migrados para tokens semânticos. |

### Superfícies internas críticas da operação

| ID | Superfície | Componente/local | Tela relacionada | Status |
|---|---|---|---|---|
| S01 | Cabeçalho do dashboard | `components/admin/dashboard/DashboardHeader.vue` | O01 | CONCLUÍDA |
| S02 | Cards de KPI | `components/admin/dashboard/KpiCard.vue` | O01 | CONCLUÍDA |
| S03 | Gráfico de desempenho | `components/admin/dashboard/PerformanceChart.vue` | O01 | CONCLUÍDA |
| S04 | Pipeline | `components/admin/dashboard/PipelineCard.vue` | O01 | CONCLUÍDA |
| S05 | Alertas | `components/admin/dashboard/AlertsPanel.vue` | O01 | CONCLUÍDA |
| S06 | Leads recentes | `components/admin/dashboard/LeadsRecentTable.vue` | O01 | CONCLUÍDA |
| S07 | Construtor de formulário | `components/admin/leads/LeadFormBuilderModal.vue` | O05 | EM QA |
| S08 | Prévia de formulário | `components/admin/leads/LeadFormPreview.vue` | O05/O03 | EM QA |
| S09 | Drawer/modal da oportunidade | `components/admin/leads/OpportunityDrawer.vue` | O06 | EM QA |
| S10 | Gerenciador de etapas | `components/admin/leads/LeadStatusManagerPanel.vue` | O09 | EM QA |
| S11 | Banner do sistema | `components/admin/SystemBanner.vue` | O01–O19 | EM QA |
| S12 | Seletor de CTA | `components/admin/inputs/CtaActionPicker.vue` | O03 | EM QA |
| S13 | Upload de imagem | `components/admin/inputs/ImageUploadField.vue` | O03 | EM QA |
| S14 | Upload múltiplo | `components/admin/inputs/MultiImageUploadField.vue` | O03 | EM QA |
| S15 | Editor de texto rico | `components/admin/inputs/RichTextEditor.vue` | O03/Admin Master | EM QA |
| S16 | Controles de título de seção | `components/admin/inputs/SectionHeadingControls.vue` | O03 | EM QA |

### Formulários internos do editor de páginas

| ID | Formulário de seção | Componente | Status | Observação |
|---|---|---|---|---|
| E01 | Banner principal | `components/admin/SectionHeroForm.vue` | EM QA | Textos, destaques, mídia e CTA refinados; revisar editor de imagem. |
| E02 | Banner em card | `components/admin/SectionBannerCardForm.vue` | EM QA | Textos, destaques, mídia, CTA, dropdowns e ações refinados nos dois temas. |
| E03 | Foto destacada | `components/admin/SectionPhotoForm.vue` | EM QA | Mídia, layouts, cores e ações refinados; revisar editor de imagem. |
| E04 | Biografia | `components/admin/SectionBiographyForm.vue` | EM QA | Textos, tipografia, editor rico, controles e uploads refinados nos dois temas. |
| E05 | Preços | `components/admin/SectionPricesForm.vue` | EM QA | Planos, valores, destaque, chips, campos e ações refinados nos dois temas. |
| E06 | Itinerário | `components/admin/SectionItineraryForm.vue` | EM QA | Dias, ordenação, editor rico, mídia e ações refinados nos dois temas. |
| E07 | Perguntas frequentes | `components/admin/SectionFaqForm.vue` | EM QA | Perguntas, chips, ordenação, editor rico e estados vazios refinados. |
| E08 | Depoimentos | `components/admin/SectionTestimonialsForm.vue` | EM QA | Lista, ordenação, avatares, campos e estados vazios refinados nos dois temas. |
| E09 | Vídeo em destaque | `components/admin/SectionFeaturedVideoForm.vue` | EM QA | Textos, vídeo, CTA, seletores e dropdowns refinados nos dois temas. |
| E10 | Chamada para ação | `components/admin/SectionCtaForm.vue` | EM QA | Conteúdo, botão, destaque, editor rico e estados ativos refinados. |
| E11 | História | `components/admin/SectionStoryForm.vue` | EM QA | Galeria, vídeo, tipografia, modais, CTA e ações refinados nos dois temas. |
| E12 | Motivos e benefícios | `components/admin/SectionReasonsForm.vue` | EM QA | Itens, chips, seletor e popover de ícones refinados nos temas claro e escuro. |
| E13 | Contagem regressiva | `components/admin/SectionCountdownForm.vue` | EM QA | Data, tempo, cores e seletores refinados nos dois temas. |
| E14 | Detalhes dos voos | `components/admin/SectionFlightDetailsForm.vue` | EM QA | Trechos, companhias, aeroportos, chips e busca refinados nos dois temas. |
| E15 | Rodapé da agência | `components/admin/SectionAgencyFooterForm.vue` | EM QA | Cores, dados herdados, campos e estados informativos refinados. |
| E16 | Pacotes Viajeon | `components/admin/SectionViajeonCheckoutForm.vue` | EM QA | Operação, textos e cores configuráveis; imagens da operação deliberadamente omitidas. |

---

## 3. Admin Master

| ID | Tela | Rota | View | Status | Prioridade |
|---|---|---|---|---|---|
| M01 | Painel | `/admin/administracao/dashboard` | `views/admin/AdminManagementView.vue` | EM QA | Redesign 10/2026: período em pílulas, números com formato brasileiro, gráfico com tokens de gráfico, planos ativos em barras e "Precisa de atenção". |
| M02 | Ao vivo | `/admin/administracao/monitor` | `views/admin/AdminManagementView.vue` | EM QA | Redesign 10/2026: números (online, computador/celular, no editor) e tabela com "onde está" em português. |
| M03 | Usuários | `/admin/administracao/usuarios` | `views/admin/AdminManagementView.vue` | EM QA | Redesign 10/2026: filtros rápidos (pagantes, em teste, vencem em 7 dias, vencidos, cancelados), "Mais filtros", menu "⋯" e detalhes na própria linha. |
| M04 | Admins globais | `/admin/administracao/admin-global` | `views/admin/AdminGlobalAgencyAdminView.vue` | EM QA | Redesign 10/2026: lista com busca e formulário em painel lateral. |
| M05 | Aulas | `/admin/administracao/aulas` | `views/admin/AdminManagementView.vue` | EM QA | Redesign 10/2026: módulos em cartões, ordenação por setas e formulário em painel lateral. |
| M06 | Modelos de página | `/admin/administracao/templates` | `views/admin/AdminManagementView.vue` | EM QA | Redesign 10/2026: abas Publicados / Criar a partir de uma página, cartões com capa e painel lateral. |
| M07 | APIs de voo | `/admin/administracao/apis-voo` | `components/admin/FlightApiKeysPanel.vue` | EM QA | Redesign 10/2026: números, barra de uso por chave, menu "⋯" e formulários em painel lateral. |
| M08 | Banners | `/admin/administracao/banners` | `views/admin/BannerManagementView.vue` | EM QA | Redesign 10/2026: números (no ar, vistas, cliques, taxa), filtros em pílulas, resultado por banner e interruptor "No ar". |
| M09 | WhatsApp | `/admin/administracao/whatsapp` | `views/admin/AdminWhatsAppManagementView.vue` | EM QA | Redesign 10/2026: números, abas, filtro "Com problema" e situação em português. |
| M10 | Ofertas e checkout | `/admin/administracao/ofertas` | `views/admin/AdminCheckoutSettingsView.vue` | EM QA | Redesign 10/2026: topo, abas com contadores, interruptor do checkout e tabela de ofertas; formulários internos pela camada de compatibilidade. |
| M11 | Webhooks e push | `/admin/administracao/webhooks` | `views/admin/WebhookNotificationsView.vue` | EM QA | Redesign 10/2026: lista de eventos, editor com interruptor e prévia "como chega no celular". |
| M12 | Previsão de receita | `/admin/administracao/receita-previsao` | `views/admin/AdminManagementView.vue` | EM QA | Redesign 10/2026: calendário com intensidade por valor e detalhe do dia. |
| M13 | LTV por cliente | `/admin/administracao/ltv-clientes` | `views/admin/AdminLtvCustomersView.vue` | EM QA | Redesign 10/2026: busca, filtros, ordenação, barra de valor e exportação CSV. |
| M14 | Prompt do construtor | `/admin/administracao/prompt-construtor` | `views/admin/PromptConstructorView.vue` | EM QA | Redesign 10/2026: prompt e teste lado a lado, aviso de alterações não salvas e tabela de versões. |
| M15 | Conciliação | `/admin/administracao/conciliacao` | `views/admin/AdminReconciliationView.vue` | EM QA | Redesign 10/2026: segue os tokens do tema (antes ficava clara no modo escuro), topo e botões no padrão. |

Peças comuns: menu interno agrupado (`components/admin/master/AdminMasterNav.vue`, lista em `nav.ts`), topo (`AdminMasterHeader.vue`), número (`AdminMasterKpi.vue`), painel lateral (`AdminMasterDrawer.vue`) e classes `am-*` em `styles/admin-master.css`. A mesma folha tem a camada de compatibilidade que converte as cores fixas antigas dentro de `.admin-master-surface`.

### Estados críticos do Admin Master

- [ ] Tabelas densas e ações por linha
- [ ] Filtros e busca
- [ ] Modais de assinatura, validade, reembolso e exclusão
- [ ] Monitor carregando, operacional e com erro
- [ ] Formulários de aulas e templates
- [ ] Calendário/previsão de receita
- [ ] Configuração de ofertas e checkout
- [ ] Logs e detalhes de webhook
- [ ] Estados sem dados
- [ ] Permissão de superusuário preservada

---

## 4. Página pública publicada

| ID | Tela | Rotas | View | Status | Regra |
|---|---|---|---|---|---|
| P01 | Página pública da agência | `/:agencySlug/:pageSlug?`, `/p/:agencySlug/:pageSlug?`, domínio próprio `/` e `/:pageSlug` | `views/public/PublicPageView.vue` | EM QA | Identidade do cliente preservada; foco, controles e formulário receberam revisão técnica de acessibilidade. |

### Seções públicas configuráveis

Estas seções não devem ser visualmente uniformizadas como telas administrativas. A remodelação deve se limitar a consistência técnica, acessibilidade, estados e controles compartilhados.

| ID | Seção | Componente | Status |
|---|---|---|---|
| P01.01 | Hero | `components/public/PublicHeroSection.vue` | EM QA |
| P01.02 | Banner/card | `components/public/PublicBannerCardSection.vue` | EM QA |
| P01.03 | Foto | `components/public/PublicPhotoSection.vue` | EM QA |
| P01.04 | Biografia | `components/public/PublicBiographySection.vue` | EM QA |
| P01.05 | Preços | `components/public/PublicPricesSection.vue` | EM QA |
| P01.06 | Roteiro | `components/public/PublicItinerarySection.vue` | EM QA |
| P01.07 | Perguntas frequentes | `components/public/PublicFaqSection.vue` | EM QA |
| P01.08 | Depoimentos | `components/public/PublicTestimonialsSection.vue` | EM QA |
| P01.09 | Vídeo em destaque | `components/public/PublicFeaturedVideoSection.vue` | EM QA |
| P01.10 | CTA | `components/public/PublicCtaSection.vue` | EM QA |
| P01.11 | História | `components/public/PublicStorySection.vue` | EM QA |
| P01.12 | Motivos | `components/public/PublicReasonsSection.vue` | EM QA |
| P01.13 | Contagem regressiva | `components/public/PublicCountdownSection.vue` | EM QA |
| P01.14 | Detalhes de voo | `components/public/PublicFlightDetailsSection.vue` | EM QA |
| P01.15 | Rodapé gratuito | `components/public/PublicFreeFooterBrandSection.vue` | EM QA |
| P01.16 | Rodapé da agência | `components/public/PublicAgencyFooterSection.vue` | EM QA |
| P01.17 | Formulário de captação | `components/public/PublicLeadCaptureModal.vue` | EM QA |
| P01.18 | Pacotes Viajeon | `components/public/PublicViajeonCheckoutSection.vue` | EM QA |

### Editores de seção no construtor

| ID | Editor | Componente | Status |
|---|---|---|---|
| E01 | Hero | `components/admin/SectionHeroForm.vue` | EM QA |
| E02 | Banner/card | `components/admin/SectionBannerCardForm.vue` | EM QA |
| E03 | Foto | `components/admin/SectionPhotoForm.vue` | EM QA |
| E04 | Biografia | `components/admin/SectionBiographyForm.vue` | EM QA |
| E05 | Preços | `components/admin/SectionPricesForm.vue` | EM QA |
| E06 | Roteiro | `components/admin/SectionItineraryForm.vue` | EM QA |
| E07 | Perguntas frequentes | `components/admin/SectionFaqForm.vue` | EM QA |
| E08 | Depoimentos | `components/admin/SectionTestimonialsForm.vue` | EM QA |
| E09 | Vídeo em destaque | `components/admin/SectionFeaturedVideoForm.vue` | EM QA |
| E10 | CTA | `components/admin/SectionCtaForm.vue` | EM QA |
| E11 | História | `components/admin/SectionStoryForm.vue` | EM QA |
| E12 | Motivos | `components/admin/SectionReasonsForm.vue` | EM QA |
| E13 | Contagem regressiva | `components/admin/SectionCountdownForm.vue` | EM QA |
| E14 | Detalhes de voo | `components/admin/SectionFlightDetailsForm.vue` | EM QA |
| E15 | Rodapé da agência | `components/admin/SectionAgencyFooterForm.vue` | EM QA |
| E16 | Pacotes Viajeon | `components/admin/SectionViajeonCheckoutForm.vue` | EM QA |

Outras superfícies do editor:

- [ ] Catálogo de seções
- [ ] Configurações gerais da página
- [ ] Preview desktop
- [ ] Preview mobile
- [ ] Seleção de template
- [ ] Prévia do formulário de captação
- [ ] Assistente de IA
- [ ] Uploads e recortes de imagem
- [ ] Confirmações de exclusão e descarte
- [ ] Avisos de plano e permissões

---

## 5. Views existentes sem rota ativa

Esses arquivos existem no código, mas não representam telas navegáveis no roteador atual.
Antes de remodelá-los, é necessário decidir se serão removidos ou reativados.

| View | Situação atual | Decisão | Status |
|---|---|---|---|
| `views/admin/RegisterView.vue` | `/register` usa apenas um placeholder e redireciona para site externo. | Pendente | NÃO CONTABILIZADA |
| `views/public/MarketingLandingView.vue` | A rota `/` usa `LoginView.vue`. | Pendente | NÃO CONTABILIZADA |
| `views/admin/ClientsView.vue` | As rotas de clientes usam `LeadsView.vue`; rotas antigas redirecionam. | Provável legado | NÃO CONTABILIZADA |

---

## 6. Rotas de redirecionamento — sem tela própria

Não precisam de remodelação enquanto continuarem apenas redirecionando:

- `/register`
- `/profissionalmensal`
- `/profissionalanual`
- `/agenciamensal`
- `/agenciaanual`
- `/escalamensal`
- `/escalaanual`
- `/profissional`
- `/agencia`
- `/escala`
- `/planos`
- `/admin/leads`
- `/admin/clientes`
- `/admin/clientes/:id`
- `/admin/integracoes`
- `/admin/conexoes`
- `/admin/administracao`
- `/admin/administracao/checkout`

---

## 7. Ordem de trabalho sugerida

Esta ordem minimiza retrabalho porque cada etapa fornece componentes para a seguinte:

1. Fundação visual e catálogo do design system.
2. Shell administrativo.
3. Dashboard como tela-piloto.
4. Formulários e oportunidades como módulo-piloto.
5. Clientes e detalhes.
6. Lista de páginas.
7. Configurações, equipe, domínios e integrações.
8. Inbox.
9. Editor de páginas e seus editores de seção.
10. Admin Master.
11. Login, recuperação, convite e compra.
12. Revisão técnica das páginas públicas.

---

## 8. Histórico de atualização

| Data | Alteração |
|---|---|
| 16/07/2026 | Inventário inicial criado a partir do roteador, views e componentes reais do frontend. |
| 16/07/2026 | F01 implementada: tokens semânticos, Inter + Sora, temas, status, radius, sombras e formatadores. |
| 16/07/2026 | F02 implementada: sidebar semântica, topbar, drawer mobile, seletor de tema e avisos globais remodelados. |
| 16/07/2026 | O01 implementada como piloto: dashboard, componentes S01–S06 e banner S11 alinhados ao design system. |
| 16/07/2026 | O01 e S01–S06 concluídos após aprovação visual do usuário; O05/O06 iniciados. |
| 16/07/2026 | O05/O06 e S07–S09 implementados: formulários, campos personalizados, oportunidades e respostas livres alinhados ao design system. |
| 16/07/2026 | O06 ajustada no modo escuro: tabela, agrupamentos, textos secundários, estados ganho/perda e ações receberam contraste consistente. |
| 16/07/2026 | S09 ajustado no modo escuro: o fundo do drawer da oportunidade agora permanece contínuo até o final da tela. |
| 16/07/2026 | O06 corrigida na origem: removidas regras dark compiladas incorretamente e substituídos fundos fixos da tabela por tokens semânticos. |
| 16/07/2026 | S09 refinado: divisórias claras do drawer substituídas por bordas semânticas mais discretas. |
| 16/07/2026 | O07/O08 implementadas: listagem e detalhe de clientes alinhados ao design system nos temas claro e escuro. |
| 16/07/2026 | S09 corrigido no estilo-base: corpo flexível do drawer passa a usar o fundo do card em toda a altura, eliminando o rodapé branco. |
| 16/07/2026 | O07 refinada no dark: divisórias claras da tabela de clientes substituídas pela borda semântica do tema. |
| 16/07/2026 | O07 refinada novamente: divisórias internas entre clientes removidas, preservando apenas cabeçalho e contorno da tabela. |
| 16/07/2026 | F02 refinada: topbar administrativa removida e seletor de tema movido para a sidebar, acima do perfil, em desktop e mobile. |
| 16/07/2026 | O07 recebeu divisórias internas sutis, com baixa opacidade, para organizar as linhas sem contraste excessivo no dark. |
| 16/07/2026 | O09/S10 implementadas: configurações do funil, cartões de etapas, ordenação e modal de criação/edição alinhados ao design system. |
| 16/07/2026 | O10/O11 implementadas: Inbox WhatsApp, painel de oportunidades, modais e estado indisponível alinhados aos temas claro e escuro. |
| 16/07/2026 | O12 implementada: configurações da agência e editor de logo alinhados ao design system nos temas claro e escuro. |
| 16/07/2026 | O12 refinada: divisórias internas mantidas com baixa opacidade para organizar os cards sem contraste excessivo. |
| 16/07/2026 | O13 implementada: faturas, resumo por status, filtros, paginação e ações financeiras alinhados aos temas claro e escuro. |
| 16/07/2026 | O14 implementada: equipe, limites do plano, convites e modal detalhado de permissões alinhados aos temas claro e escuro. |
| 16/07/2026 | O15 implementada: domínios personalizados, instruções DNS, SSL, favicon e ações alinhados aos temas claro e escuro. |
| 16/07/2026 | O02 implementada: lista de páginas, indicadores, filtros, ações, criação, templates e duplicação alinhados aos temas claro e escuro. |
| 16/07/2026 | O03 implementada no nível estrutural: toolbar, configurações, preview, catálogo de seções, modais e assistente IA alinhados ao design system. |
| 16/07/2026 | O03 refinada no tema escuro: configurações usam os tokens do tema e a moldura externa do preview não permanece branca. |
| 16/07/2026 | E01–E15 iniciados: modal e base compartilhada dos formulários de seção alinhados aos tokens dos temas claro e escuro; revisão individual permanece em QA. |
| 16/07/2026 | S15 remodelado: barra, área editável, placeholder, ícones e foco do editor de texto rico agora acompanham os tokens dos temas claro e escuro. |
| 16/07/2026 | E01–E15 refinados: ícones e SVGs das abas selecionadas receberam contraste explícito usando a cor de primeiro plano do tema. |
| 16/07/2026 | E12 refinado: removidos fundos brancos fixos dos chips, botão de adição, seletor de ícone, popover e estado vazio. |
| 16/07/2026 | O03 refinado: ações dos avisos de alterações não salvas receberam estados neutro, destrutivo e primário com hover semântico. |
| 16/07/2026 | E01 refinado: barra de texto rico, botão de adição e chips de destaques deixaram de usar fundos brancos fixos. |
| 16/07/2026 | E01 refinado em mídia e CTA: botões brancos substituídos por superfícies semânticas e seleções azul-marinho pelo verde primário. |
| 16/07/2026 | E01–E15 receberam regra visual: seleções e tooltips internos não usam azul-marinho fixo no tema escuro. |
| 16/07/2026 | E01 reforçado no dark: toolbar, botão de adicionar, caixa e chips de destaques receberam regras prioritárias contra estilos claros legados. |
| 16/07/2026 | E02–E04 refinados na origem: formulários de banner em card, foto e biografia passaram a usar tokens semânticos em navegação, campos, mídia, seleções e ações. |
| 16/07/2026 | E05–E07 refinados na origem: Preços, Itinerário e FAQ receberam tokens semânticos em cards, listas, ordenação, mídia, editores e ações. |
| 16/07/2026 | E08–E10 refinados na origem: Depoimentos, Vídeo em destaque e CTA receberam tokens semânticos em listas, mídia, seletores, dropdowns e ações. |
| 21/07/2026 | E11 e E13–E15 finalizados no código; S12, S14 e S16 remodelados e todo o bloco de editores de seção movido para EM QA após validação técnica. |
| 21/07/2026 | O04 e O16–O19 remodelados no código e movidos para EM QA após validação dos componentes Vue. |
| 21/07/2026 | A01–A07 remodelados no código e movidos para EM QA após validação de login, recuperação, convite, pedido e checkout. |
| 21/07/2026 | M01–M14 receberam a camada semântica compartilhada e ajustes nas views especializadas; os oito componentes Vue envolvidos foram compilados e movidos para EM QA. |
| 21/07/2026 | P01.01–P01.17 revisadas tecnicamente sem substituir a identidade dos clientes; foco visível, expansores e formulário acessível foram implementados e todas as seções públicas compiladas. |
| 21/07/2026 | Ciclo geral encerrado para QA: build de produção validado com 770 módulos e todas as 41 telas/experiências em QA ou já concluídas. |
| 21/07/2026 | O03 refinado: o Assistente IA agora persiste cada conversa por página e usuário, restaura o histórico após atualização e evita duplicação de mensagens. |
| 21/07/2026 | O17/E16/P01.18: integração Viajeon implementada com credenciais criptografadas, operações ativas, seleção de pacotes e redirecionamento por sessão; imagens da operação não são enviadas nem exibidas. |
| 05/10/2026 | Visual novo das seções (v2), lote 1: Capa, Contagem, Sobre a viagem, Diferenciais, Roteiro, Galeria, Foto, Preços, Depoimentos, Dúvidas, Outros roteiros e Faixa de chamada em `components/public/v2`. Liberado só para agências com superusuário (`PAGE_DESIGN_V2_ROLLOUT=superusers`; `all` libera para todos, `off` desliga). Cada página pode voltar com "Usar visual antigo" (Cores), salvo em `config.design = "legacy"`. As demais seções seguem no visual antigo até serem portadas. |
| 05/10/2026 | Visual novo (v2), lote 2: Menu do topo, Capa com card, Vídeo, Vídeo de vendas (mesma lógica de liberação), Artigo e Rodapé reescritos; Voos, Compra online e Formulário mantêm o componente atual com as cores do v2 (destaque da página e texto pelo fundo). Com isso todas as seções têm versão v2; só o Selo da plataforma segue igual. |
| 08/10/2026 | F01/F02, fase 1 do alinhamento com o Viaje On: o painel deixou o zoom de 90% e passou a 100%. Menu lateral com cartão de 244px (64px recolhido) solto 12px da borda, cantos de 20px sem borda, itens de 40px com texto de 14px e ícones de 16px, logo maior e botão de fixar no topo mostrando o estado (alfinete verde = fixado). Abre ao passar o mouse em 120ms, fecha em 180ms e anima em 200ms; compacta abaixo de 820px e 680px de altura. |
| 08/10/2026 | F02: as telas comuns ficam num contêiner único (largura máxima de 1400px; o espaçamento externo vem só do layout), então o título começa no mesmo ponto em todas. Páginas, Leads, Cliente, Minha agência, Faturas, Equipe, Domínios, Integrações, Atendimento, Aulas e Perfil deixaram o espaçamento próprio. |
| 08/10/2026 | M01–M14: no Admin Master o menu principal fica recolhido e o menu do Admin vira um cartão âmbar com "Voltar ao painel"; o fundo ganha o degradê âmbar do Viaje On. |
| 08/10/2026 | F02 no celular: menu em cartão solto da borda, com "Nova página" no topo e os mesmos itens do computador; o botão do WhatsApp some com o menu aberto. Fade global dos modais passou a 200ms. |
| 08/10/2026 | F02: menu recolhido mostra um traço no lugar do título de cada grupo, na mesma altura do título; os itens ficam na mesma posição aberto ou recolhido (conferido em 900, 760 e 640px de altura). |
| 08/10/2026 | F01: selects do painel com a seta própria (a do Viaje On), 12px da borda e 36px de folga; a seta nativa ficava colada na borda dos campos arredondados ("Mais recentes", filtros do Dashboard, Formulários, Agência, Clientes e Admin Master). A prévia das páginas públicas fica de fora. |
| 08/10/2026 | Visual novo (v2), revisão das seções: Outros roteiros volta a seguir a seção antiga (até 4 cards lado a lado; do 5º em diante, carrossel com setas no padrão da galeria; carrossel desligado vira grade centralizada de 3 ou 4 por linha; no celular, desliza com o dedo). Capa, Capa com card e títulos de seção com texto longo diminuem a letra e alargam o cartão em vez de esticar a seção (`useCopyFit`). Diferenciais, Depoimentos e Galeria em grade centralizam a última linha; o mosaico da galeria monta blocos de 5 fotos sem buracos (no celular, 2 colunas). Banner com sombra no celular deixa o texto sempre sobre a parte escura. |
| 08/10/2026 | Visual novo (v2): nova opção "Alinhamento" (Esquerda/Centro) no cabeçalho da seção em Dúvidas, Vídeo, Roteiro, Outros roteiros, Preços, Diferenciais e Depoimentos (`headingAlign`; padrão: centro, Outros roteiros à esquerda). Alinhado à esquerda, o título começa junto com o conteúdo da seção. |
| 09/10/2026 | Outros roteiros (v2): setas nas laterais, fora dos cards (somem no celular, onde o carrossel desliza com o dedo). Título e texto ficam com a altura do maior card da linha e datas, preço e botão ficam na base, alinhados entre os cards. No card estreito a data de volta desce de linha em vez de ser cortada. |
| 09/10/2026 | Outros roteiros (v2): preço no mesmo desenho das datas, com "a partir de" pequeno em cima e o valor com "por pessoa" ao lado; o complemento desce inteiro quando não cabe, nunca quebrado no meio. Em card estreito (menos de 220px de conteúdo) o valor diminui um pouco para caber com "por pessoa" na mesma linha. |
| 09/10/2026 | Outros roteiros (v2): ícones iguais aos da seção antiga, em contorno fino e sem fundo: calendário em cada data (ao lado de "Ida" e "Volta") e etiqueta no preço. Ficam visíveis em qualquer largura de card. |
| 09/10/2026 | Editor novo (v2): na aba Conteúdo os grupos do formulário da seção vêm todos recolhidos; em Aparência só o primeiro vem aberto. Dentro das listas o primeiro item continua aberto e o item novo abre para preencher. |
| 09/10/2026 | A seção "Outros roteiros" passou a se chamar "Links/roteiros" no editor (camadas, título do formulário, catálogo de seções e editor antigo); no formulário, o grupo e os itens também viraram "Links/roteiros". Na página, ida e volta descem uma embaixo da outra quando o card não tem espaço para as duas. |
| 09/10/2026 | Links/roteiros (v2): no carrossel, a área de rolagem ganhou folga em cima e embaixo para a subida do card e a sombra do hover não serem cortadas; nas laterais não há folga, para não aparecer uma tira dos cards vizinhos. |
| 09/10/2026 | O03 (editor): clicar em outra seção com alterações não salvas abre o aviso em vez de descartar: "Salvar e abrir a outra", "Descartar e abrir a outra" ou "Continuar editando". Clicar na seção que já está aberta não recarrega o rascunho. |
| 09/10/2026 | O03 (editor novo): Menu do topo transparente fica por cima da seção seguinte na prévia, como na página publicada, mostrando a foto, a sombra e o degradê da capa atrás dele (antes aparecia numa faixa separada com o topo da foto). O selo e as ações da seção de baixo descem para logo abaixo do menu. No Menu do topo, selo e ações ficam centralizados na altura dele e mais compactos, cabendo dentro da área. |
