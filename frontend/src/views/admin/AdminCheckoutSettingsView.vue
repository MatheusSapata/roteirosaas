<template>
  <div class="admin-master-surface w-full space-y-6 px-4 py-8 md:px-8">
    <section class="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.35em] text-slate-400">Admin master</p>
          <h1 class="mt-2 text-2xl font-bold text-slate-900">Ofertas</h1>
          <p class="mt-2 text-sm text-slate-500">
            Gerencie ofertas, cupons e layouts de checkout usados no checkout transparente.
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <label class="inline-flex items-center gap-3 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700">
            <input v-model="form.is_active" type="checkbox" />
            Módulo ativo
          </label>
          <button
            type="button"
            class="rounded-full bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-slate-800 disabled:opacity-60"
            :disabled="saving"
            @click="save"
          >
            {{ saving ? "Salvando..." : "Salvar alterações" }}
          </button>
        </div>
      </div>
    </section>

    <section class="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100">
      <div class="flex flex-wrap gap-8 border-b border-slate-200">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="-mb-px border-b-2 pb-3 text-sm font-semibold transition"
          :class="activeTab === tab.id ? 'border-slate-900 text-slate-900' : 'border-transparent text-slate-500 hover:text-slate-800'"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <div v-if="activeTab === 'offers'" class="mt-6 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Ofertas</h2>
            <p class="text-sm text-slate-500">Cada oferta resolve o valor, plano e checkout visual usados no link público.</p>
          </div>
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="openOfferModal()">
            + Nova oferta
          </button>
        </div>

        <div class="overflow-hidden rounded-3xl border border-slate-200">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              <tr>
                <th class="px-4 py-3">Oferta</th>
                <th class="px-4 py-3">Key</th>
                <th class="px-4 py-3">Link</th>
                <th class="px-4 py-3">Checkout</th>
                <th class="px-4 py-3">Plano</th>
                <th class="px-4 py-3">Ciclo</th>
                <th class="px-4 py-3">Valor</th>
                <th class="px-4 py-3">Status</th>
                <th class="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-if="!form.offers.length">
                <td colspan="9" class="px-4 py-8 text-center text-sm text-slate-500">Nenhuma oferta cadastrada.</td>
              </tr>
              <tr v-for="offer in form.offers" :key="offer.local_id">
                <td class="px-4 py-4">
                  <div class="font-semibold text-slate-900">{{ offer.title }}</div>
                  <div class="text-xs text-slate-500">{{ offer.footer_product_label }}</div>
                </td>
                <td class="px-4 py-4 font-mono text-xs text-slate-600">{{ offer.key }}</td>
                <td class="px-4 py-4">
                  <div class="max-w-[280px] truncate font-mono text-xs text-slate-500">{{ buildOfferCheckoutUrl(offer.key) || "--" }}</div>
                </td>
                <td class="px-4 py-4 text-slate-600">{{ checkoutNameByKey(offer.checkout_key) }}</td>
                <td class="px-4 py-4 text-slate-600">{{ planLabel(offer.plan_key) }}</td>
                <td class="px-4 py-4 text-slate-600">{{ cycleLabel(offer.billing_cycle) }}</td>
                <td class="px-4 py-4 font-semibold text-slate-900">{{ formatCurrency(offer.amount) }}</td>
                <td class="px-4 py-4">
                  <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="offer.active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'">
                    {{ offer.active ? "Ativa" : "Inativa" }}
                  </span>
                </td>
                <td class="px-4 py-4">
                  <div class="flex justify-end gap-2">
                    <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50" @click="copyOfferLink(offer.key)">
                      Copiar link
                    </button>
                    <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50" @click="openOfferModal(offer)">
                      Editar
                    </button>
                    <button type="button" class="rounded-full border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50" @click="removeOffer(offer.local_id)">
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'pixels'" class="mt-6 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Pixels Meta</h2>
            <p class="text-sm text-slate-500">Cadastre o ID e o access token e defina em quais ofertas cada pixel fica ativo.</p>
          </div>
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="openPixelModal()">
            + Novo pixel
          </button>
        </div>

        <div class="overflow-hidden rounded-3xl border border-slate-200">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              <tr>
                <th class="px-4 py-3">Pixel</th>
                <th class="px-4 py-3">ID</th>
                <th class="px-4 py-3">Token</th>
                <th class="px-4 py-3">Ofertas</th>
                <th class="px-4 py-3">Status</th>
                <th class="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-if="!form.pixels.length">
                <td colspan="6" class="px-4 py-8 text-center text-sm text-slate-500">Nenhum pixel cadastrado.</td>
              </tr>
              <tr v-for="pixel in form.pixels" :key="pixel.local_id">
                <td class="px-4 py-4">
                  <div class="font-semibold text-slate-900">{{ pixel.name }}</div>
                  <div class="text-xs text-slate-500">Meta Pixel</div>
                </td>
                <td class="px-4 py-4 font-mono text-xs text-slate-600">{{ pixel.pixel_id }}</td>
                <td class="px-4 py-4">
                  <div class="max-w-[240px] truncate font-mono text-xs text-slate-500">{{ pixel.access_token || "--" }}</div>
                </td>
                <td class="px-4 py-4 text-slate-600">{{ pixelOfferSummary(pixel.offer_keys) }}</td>
                <td class="px-4 py-4">
                  <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="pixel.active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'">
                    {{ pixel.active ? "Ativo" : "Inativo" }}
                  </span>
                </td>
                <td class="px-4 py-4">
                  <div class="flex justify-end gap-2">
                    <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50" @click="openPixelModal(pixel)">
                      Editar
                    </button>
                    <button type="button" class="rounded-full border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50" @click="removePixel(pixel.local_id)">
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'coupons'" class="mt-6 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Cupons</h2>
            <p class="text-sm text-slate-500">Crie cupons por valor ou percentual e limite em quais ofertas eles podem ser usados.</p>
          </div>
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="openCouponModal()">
            + Novo cupom
          </button>
        </div>

        <div class="overflow-hidden rounded-3xl border border-slate-200">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              <tr>
                <th class="px-4 py-3">Cupom</th>
                <th class="px-4 py-3">Tipo</th>
                <th class="px-4 py-3">Desconto</th>
                <th class="px-4 py-3">Ofertas permitidas</th>
                <th class="px-4 py-3">Usos</th>
                <th class="px-4 py-3">Status</th>
                <th class="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-if="!form.coupons.length">
                <td colspan="7" class="px-4 py-8 text-center text-sm text-slate-500">Nenhum cupom cadastrado.</td>
              </tr>
              <tr v-for="coupon in form.coupons" :key="coupon.local_id">
                <td class="px-4 py-4">
                  <div class="font-semibold text-slate-900">{{ coupon.title }}</div>
                  <div class="font-mono text-xs text-slate-500">{{ coupon.code }}</div>
                </td>
                <td class="px-4 py-4 text-slate-600">{{ coupon.discount_type === 'percent' ? 'Percentual' : 'Valor fixo' }}</td>
                <td class="px-4 py-4 font-semibold text-slate-900">
                  {{ coupon.discount_type === 'percent' ? `${coupon.value}%` : formatCurrency(coupon.value) }}
                </td>
                <td class="px-4 py-4 text-slate-600">
                  {{ couponOfferSummary(coupon.offer_keys) }}
                </td>
                <td class="px-4 py-4 font-semibold text-slate-900">
                  {{ coupon.usage_count ?? 0 }}
                </td>
                <td class="px-4 py-4">
                  <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="coupon.active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'">
                    {{ coupon.active ? "Ativo" : "Inativo" }}
                  </span>
                </td>
                <td class="px-4 py-4">
                  <div class="flex justify-end gap-2">
                    <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50" @click="openCouponModal(coupon)">
                      Editar
                    </button>
                    <button type="button" class="rounded-full border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50" @click="removeCoupon(coupon.local_id)">
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'checkouts'" class="mt-6 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Checkouts</h2>
            <p class="text-sm text-slate-500">Cada checkout define o tema e os banners usados por uma ou mais ofertas.</p>
          </div>
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="openCheckoutModal()">
            + Novo checkout
          </button>
        </div>

        <div class="overflow-hidden rounded-3xl border border-slate-200">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              <tr>
                <th class="px-4 py-3">Checkout</th>
                <th class="px-4 py-3">Key</th>
                <th class="px-4 py-3">Tema</th>
                <th class="px-4 py-3">Imagens</th>
                <th class="px-4 py-3">Status</th>
                <th class="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-if="!form.checkouts.length">
                <td colspan="6" class="px-4 py-8 text-center text-sm text-slate-500">Nenhum checkout cadastrado.</td>
              </tr>
              <tr v-for="checkout in form.checkouts" :key="checkout.local_id">
                <td class="px-4 py-4">
                  <div class="font-semibold text-slate-900">{{ checkout.name }}</div>
                </td>
                <td class="px-4 py-4 font-mono text-xs text-slate-600">{{ checkout.key }}</td>
                <td class="px-4 py-4 text-slate-600">{{ checkout.theme_mode === 'light' ? 'White' : 'Dark' }}</td>
                <td class="px-4 py-4 text-slate-600">
                  {{ imageState(checkout.desktop_image_url) }} desktop • {{ imageState(checkout.mobile_banner_url) }} mobile
                </td>
                <td class="px-4 py-4">
                  <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="checkout.active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'">
                    {{ checkout.active ? "Ativo" : "Inativo" }}
                  </span>
                </td>
                <td class="px-4 py-4">
                  <div class="flex justify-end gap-2">
                    <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50" @click="openCheckoutModal(checkout)">
                      Editar
                    </button>
                    <button type="button" class="rounded-full border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50" @click="removeCheckout(checkout.local_id)">
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'reports'" class="mt-6 space-y-6">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Relatórios</h2>
            <p class="text-sm text-slate-500">Assinaturas e upgrades consolidados por oferta, com leitura visual rápida do volume convertido.</p>
          </div>
        </div>

        <div class="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <div class="flex flex-wrap items-end gap-3">
            <label class="space-y-2 text-sm font-semibold text-slate-700">
              <span>Período</span>
              <select
                v-model="reportPeriodPreset"
                class="min-w-[180px] rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              >
                <option value="7">Últimos 7 dias</option>
                <option value="30">Últimos 30 dias</option>
                <option value="90">Últimos 90 dias</option>
                <option value="custom">Personalizado</option>
              </select>
            </label>
            <label class="space-y-2 text-sm font-semibold text-slate-700">
              <span>De</span>
              <input
                v-model="reportPeriodStart"
                type="date"
                class="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
                :disabled="reportPeriodPreset !== 'custom'"
              />
            </label>
            <label class="space-y-2 text-sm font-semibold text-slate-700">
              <span>Até</span>
              <input
                v-model="reportPeriodEnd"
                type="date"
                class="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
                :disabled="reportPeriodPreset !== 'custom'"
              />
            </label>
            <div class="flex min-w-[180px] flex-1 flex-wrap items-center justify-end gap-3">
              <div class="text-right">
                <p class="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Intervalo ativo</p>
                <p class="mt-1 text-sm font-semibold text-slate-900">{{ reportPeriodLabel }}</p>
              </div>
              <button
                type="button"
                class="rounded-full border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                :disabled="reportsLoading"
                @click="loadReports"
              >
                {{ reportsLoading ? "Atualizando..." : "Aplicar período" }}
              </button>
            </div>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div class="rounded-3xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-5 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Assinaturas</p>
            <div class="mt-2 text-3xl font-black text-slate-900">{{ reportSummary.totalSigned }}</div>
            <p class="mt-1 text-sm text-slate-500">Conversões concluídas em todas as ofertas.</p>
          </div>
          <div class="rounded-3xl border border-amber-200 bg-gradient-to-br from-amber-50 to-white p-5 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.22em] text-amber-700">Upgrades</p>
            <div class="mt-2 text-3xl font-black text-amber-700">{{ reportSummary.totalUpgrades }}</div>
            <p class="mt-1 text-sm text-amber-700/80">Assinaturas migradas pelo fluxo de upgrade.</p>
          </div>
          <div class="rounded-3xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-5 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-700">Ofertas com conversão</p>
            <div class="mt-2 text-3xl font-black text-emerald-700">{{ reportSummary.offersWithSales }}</div>
            <p class="mt-1 text-sm text-emerald-700/80">Ofertas que já geraram alguma assinatura.</p>
          </div>
          <div class="rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-5 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Taxa de upgrade</p>
            <div class="mt-2 text-3xl font-black text-slate-900">{{ reportSummary.upgradeRate }}</div>
            <p class="mt-1 text-sm text-slate-500">Participação de upgrades sobre as conversões.</p>
          </div>
        </div>

        <div class="grid gap-6 xl:grid-cols-[1.7fr_0.95fr]">
          <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 class="text-base font-bold text-slate-900">Conversões por oferta</h3>
                <p class="text-sm text-slate-500">Barras empilhadas mostram diretas e upgrades dentro do total convertido de cada oferta.</p>
              </div>
              <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Total: {{ reportSummary.totalSigned }}
              </div>
            </div>

            <div v-if="reportsLoading" class="mt-6 space-y-3">
              <div v-for="index in 4" :key="index" class="animate-pulse rounded-2xl border border-slate-200 p-4">
                <div class="h-4 w-40 rounded-full bg-slate-100"></div>
                <div class="mt-4 h-3 rounded-full bg-slate-100"></div>
              </div>
            </div>

            <div v-else-if="!reportRows.length" class="mt-6 rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
              Nenhuma conversão encontrada para gerar relatório.
            </div>

            <div v-else class="mt-6 space-y-4">
              <article
                v-for="(row, index) in reportRows"
                :key="row.offer_key"
                class="report-card-animate rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-4 shadow-sm"
                :style="{ animationDelay: `${index * 70}ms` }"
              >
                <div class="flex flex-wrap items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="flex items-center gap-2">
                      <span
                        class="h-2.5 w-2.5 rounded-full"
                        :class="row.is_active ? 'bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.12)]' : 'bg-slate-300'"
                      ></span>
                      <h4 class="truncate text-base font-bold text-slate-900">{{ row.offer_title }}</h4>
                    </div>
                    <p class="mt-1 truncate font-mono text-[11px] uppercase tracking-[0.22em] text-slate-400">{{ row.offer_key }}</p>
                    <p class="mt-2 text-xs text-slate-500">
                      Checkout: <span class="font-semibold text-slate-700">{{ checkoutNameByKey(row.checkout_key) }}</span>
                      <span class="mx-2 text-slate-300">•</span>
                      Última assinatura: <span class="font-semibold text-slate-700">{{ formatDateTime(row.last_signed_at) }}</span>
                    </p>
                  </div>
                  <div class="rounded-full bg-white px-3 py-1.5 text-right text-xs font-semibold text-slate-600 ring-1 ring-slate-200">
                    <div class="text-[11px] uppercase tracking-[0.2em] text-slate-400">Total</div>
                    <div class="mt-0.5 text-sm font-black text-slate-900">{{ row.total_count }}</div>
                  </div>
                </div>

                <div class="mt-4">
                  <div class="flex justify-between text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                    <span>Diretas {{ row.direct_count }}</span>
                    <span>Upgrades {{ row.upgrade_count }}</span>
                  </div>
                  <div class="mt-2 h-3 overflow-hidden rounded-full bg-slate-100">
                    <div
                      class="flex h-full overflow-hidden rounded-full transition-all duration-1000 ease-out"
                      :style="{ width: reportChartWidth(row.total_count), opacity: reportChartReady ? 1 : 0 }"
                    >
                      <div
                        class="h-full bg-gradient-to-r from-sky-500 to-cyan-400 transition-all duration-1000 ease-out"
                        :style="{ width: reportShareWidth(row.direct_count, row.total_count) }"
                      ></div>
                      <div
                        class="h-full bg-gradient-to-r from-amber-400 to-orange-300 transition-all duration-1000 ease-out"
                        :style="{ width: reportShareWidth(row.upgrade_count, row.total_count) }"
                      ></div>
                    </div>
                  </div>
                </div>

                <div class="mt-3 flex flex-wrap items-center gap-2 text-xs">
                  <span class="rounded-full bg-sky-50 px-2.5 py-1 font-semibold text-sky-700">Diretas: {{ row.direct_count }}</span>
                  <span class="rounded-full bg-amber-50 px-2.5 py-1 font-semibold text-amber-700">Upgrades: {{ row.upgrade_count }}</span>
                  <span class="rounded-full bg-slate-100 px-2.5 py-1 font-semibold text-slate-600">Total: {{ row.total_count }}</span>
                </div>
              </article>
            </div>
          </section>

          <aside class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 class="text-base font-bold text-slate-900">Resumo rápido</h3>
            <p class="mt-1 text-sm text-slate-500">Leitura compacta do desempenho por oferta.</p>

            <div class="mt-5 space-y-3">
              <div
                v-for="(row, index) in reportRows.slice(0, 6)"
                :key="`${row.offer_key}-summary-${index}`"
                class="rounded-2xl border border-slate-200 bg-slate-50/80 p-4"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="truncate font-semibold text-slate-900">{{ row.offer_title }}</div>
                    <div class="mt-1 text-xs text-slate-500">{{ row.offer_key }}</div>
                  </div>
                  <div class="text-right">
                    <div class="text-2xl font-black text-slate-900">{{ row.total_count }}</div>
                    <div class="text-[11px] uppercase tracking-[0.18em] text-slate-400">conversões</div>
                  </div>
                </div>
                <div class="mt-3 h-2 rounded-full bg-slate-200">
                  <div class="h-2 rounded-full bg-gradient-to-r from-emerald-500 to-lime-400 transition-all duration-1000 ease-out" :style="{ width: reportChartWidth(row.total_count) }"></div>
                </div>
                <div class="mt-3 flex items-center justify-between text-xs text-slate-500">
                  <span>{{ formatPercent(row.total_count, reportSummary.totalSigned) }} do total</span>
                  <span>{{ row.upgrade_count }} upgrades</span>
                </div>
              </div>
              <div v-if="!reportRows.length && !reportsLoading" class="rounded-2xl border border-dashed border-slate-200 p-6 text-sm text-slate-500">
                Nenhum dado disponível.
              </div>
            </div>
          </aside>
        </div>
      </div>

      <div v-else-if="activeTab === 'tracking'" class="mt-6 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Trackeamento</h2>
            <p class="text-sm text-slate-500">Leads criados na etapa 2 e eventos do funil do checkout.</p>
          </div>
          <div class="flex items-center gap-2">
            <input
              v-model="trackingSearch"
              type="text"
              placeholder="Buscar nome, email ou documento"
              class="w-[260px] rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700"
            />
            <select v-model="trackingFilterStatus" class="rounded-full border border-slate-200 px-3 py-2 text-sm text-slate-700">
              <option value="">Todos status</option>
              <option value="signed">Assinou</option>
              <option value="pending">Em andamento</option>
            </select>
            <select v-model="trackingFilterPaymentMethod" class="rounded-full border border-slate-200 px-3 py-2 text-sm text-slate-700">
              <option value="">Todas formas</option>
              <option value="card">Cartão</option>
              <option value="pix">PIX</option>
              <option value="none">Não definido</option>
            </select>
            <label class="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700">
              <input v-model="trackingOnlyErrors" type="checkbox" />
              Somente com erro
            </label>
            <select v-model="trackingFilterOffer" class="rounded-full border border-slate-200 px-3 py-2 text-sm text-slate-700">
              <option value="">Todas as ofertas</option>
              <option v-for="offer in form.offers" :key="offer.local_id" :value="offer.key">{{ offer.title }}</option>
            </select>
            <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="loadTracking">
              Atualizar
            </button>
          </div>
        </div>

        <div class="overflow-hidden rounded-3xl border border-slate-200">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              <tr>
                <th class="px-4 py-3">Lead</th>
                <th class="px-4 py-3">Oferta</th>
                <th class="px-4 py-3">Forma</th>
                <th class="px-4 py-3">Eventos</th>
                <th class="px-4 py-3">Erros</th>
                <th class="px-4 py-3">Tempo</th>
                <th class="px-4 py-3">Geo/IP</th>
                <th class="px-4 py-3">Status</th>
                <th class="px-4 py-3">Atualizado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-if="trackingLoading">
                <td colspan="9" class="px-4 py-8 text-center text-sm text-slate-500">Carregando tracking...</td>
              </tr>
              <tr v-else-if="!filteredTrackingRows.length">
                <td colspan="9" class="px-4 py-8 text-center text-sm text-slate-500">Sem dados de tracking.</td>
              </tr>
              <tr v-for="row in filteredTrackingRows" :key="row.id" class="cursor-pointer hover:bg-slate-50/70" @click="openTrackingDetail(row)">
                <td class="px-4 py-4">
                  <div class="font-semibold text-slate-900">{{ row.customer_name }}</div>
                  <div class="text-xs text-slate-500">{{ row.customer_email }}</div>
                  <div class="font-mono text-[11px] text-slate-500">{{ row.customer_document || "-" }}</div>
                </td>
                <td class="px-4 py-4 font-mono text-xs text-slate-600">{{ row.offer_key }}</td>
                <td class="px-4 py-4 text-slate-700">{{ row.payment_method_selected || "-" }}</td>
                <td class="px-4 py-4 text-slate-700">{{ row.events_count }} <span class="text-xs text-slate-500">({{ row.sessions_count || 1 }} sess.)</span></td>
                <td class="px-4 py-4 text-slate-700">{{ row.error_events_count }}</td>
                <td class="px-4 py-4 text-slate-700">{{ row.total_time_seconds != null ? `${row.total_time_seconds}s` : "-" }}</td>
                <td class="px-4 py-4 text-xs text-slate-600">
                  <div>{{ row.last_ip_city || "-" }}{{ row.last_ip_region ? `, ${row.last_ip_region}` : "" }}{{ row.last_ip_country ? `, ${row.last_ip_country}` : "" }}</div>
                  <div class="font-mono text-[11px] text-slate-500">{{ row.last_ip_address || "-" }}</div>
                </td>
                <td class="px-4 py-4">
                  <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="row.signed_at ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'">
                    {{ row.signed_at ? "Assinou" : "Em andamento" }}
                  </span>
                </td>
                <td class="px-4 py-4 text-slate-600">{{ formatDateTime(row.updated_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <Teleport to="body">
      <div
        v-if="trackingDetailOpen"
        class="fixed left-0 top-0 z-[9999] h-screen w-screen bg-slate-950/60 backdrop-blur-sm"
        @click="closeTrackingDetail"
      >
        <div class="flex h-full w-full items-center justify-center p-4">
          <div class="max-h-[90vh] w-full max-w-5xl overflow-auto rounded-3xl bg-white p-6 shadow-[0_40px_120px_-35px_rgba(15,23,42,0.55)]" @click.stop>
        <div class="flex items-start justify-between gap-4 border-b border-slate-200/80 pb-4">
          <div>
            <p class="text-[11px] font-semibold uppercase tracking-[0.36em] text-slate-500">Tracking detalhado</p>
            <h3 class="mt-2 text-4xl font-black leading-none text-slate-900">{{ trackingDetail?.customer_name || "Lead" }}</h3>
            <div class="mt-3 flex flex-wrap items-center gap-2 text-sm font-medium text-slate-600">
              <span class="rounded-full bg-slate-100 px-3 py-1">{{ trackingDetail?.customer_email || "-" }}</span>
              <span class="rounded-full bg-slate-100 px-3 py-1">{{ trackingDetail?.customer_phone || "-" }}</span>
              <span class="rounded-full bg-slate-100 px-3 py-1 font-mono">{{ trackingDetail?.customer_document || "-" }}</span>
            </div>
            <div class="mt-3 flex flex-wrap items-center gap-2">
              <span class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                Oferta key: {{ trackingOfferKeys(trackingDetail).join(", ") || "-" }}
              </span>
              <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
                Primeira atividade: {{ formatDateTime(trackingDetail?.first_seen_at) }}
              </span>
              <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
                Última atividade: {{ formatDateTime(trackingDetail?.last_seen_at) }}
              </span>
            </div>
          </div>
          <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-600" @click="closeTrackingDetail">Fechar</button>
        </div>
        <div v-if="trackingDetailLoading" class="mt-6 rounded-2xl border border-slate-200 p-6 text-sm text-slate-600">Carregando detalhes...</div>
        <template v-else-if="trackingDetail">
          <div class="mt-6 grid gap-3 md:grid-cols-5">
            <div class="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-4 shadow-sm"><p class="text-xs uppercase tracking-[0.2em] text-slate-500">Sessoes</p><p class="mt-1 text-2xl font-extrabold text-slate-900">{{ trackingDetail.sessions_count }}</p></div>
            <div class="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-4 shadow-sm"><p class="text-xs uppercase tracking-[0.2em] text-slate-500">Eventos</p><p class="mt-1 text-2xl font-extrabold text-slate-900">{{ trackingDetail.events_count }}</p></div>
            <div class="rounded-2xl border border-rose-200 bg-gradient-to-br from-rose-50 to-white p-4 shadow-sm"><p class="text-xs uppercase tracking-[0.2em] text-rose-500">Erros</p><p class="mt-1 text-2xl font-extrabold text-rose-600">{{ trackingDetail.error_events_count }}</p></div>
            <div class="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm"><p class="text-xs uppercase tracking-[0.2em] text-emerald-600">Assinou</p><p class="mt-1 text-2xl font-extrabold text-emerald-600">{{ trackingDetail.signed_count }}</p></div>
            <div class="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm"><p class="text-xs uppercase tracking-[0.2em] text-emerald-600">Senha</p><p class="mt-1 text-2xl font-extrabold text-emerald-600">{{ trackingDetail.password_defined_count }}</p></div>
          </div>
          <div class="mt-5 overflow-hidden rounded-2xl border border-slate-200">
            <table class="min-w-full divide-y divide-slate-200 text-sm">
              <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                <tr><th class="px-4 py-3">Data/hora</th><th class="px-4 py-3">Sessao</th><th class="px-4 py-3">Evento</th><th class="px-4 py-3">Etapa</th><th class="px-4 py-3">Pagamento</th><th class="px-4 py-3">Duracao</th><th class="px-4 py-3">IP/Geo</th><th class="px-4 py-3">Erro</th></tr>
              </thead>
              <tbody class="divide-y divide-slate-100 bg-white">
                <tr v-for="ev in trackingDetail.events" :key="ev.id">
                  <td class="px-4 py-3 text-slate-700">{{ formatDateTime(ev.created_at) }}</td>
                  <td class="px-4 py-3 font-mono text-xs text-slate-600">{{ ev.token.slice(0, 8) }}...</td>
                  <td class="px-4 py-3 font-semibold text-slate-900">{{ ev.event_name }}</td>
                  <td class="px-4 py-3 text-slate-700">{{ ev.step || "-" }}</td>
                  <td class="px-4 py-3 text-slate-700">{{ ev.payment_method || "-" }}</td>
                  <td class="px-4 py-3 text-slate-700">{{ formatDurationMs(ev.duration_ms) }}</td>
                  <td class="px-4 py-3 text-xs text-slate-600"><div>{{ ev.ip_city || "-" }}{{ ev.ip_region ? `, ${ev.ip_region}` : "" }}{{ ev.ip_country ? `, ${ev.ip_country}` : "" }}</div><div class="font-mono text-[11px] text-slate-500">{{ ev.ip_address || "-" }}</div></td>
                  <td class="px-4 py-3 text-xs" :class="ev.error_message ? 'text-rose-600' : 'text-slate-500'">{{ ev.error_message || "-" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          </template>
          </div>
        </div>
      </div>
    </Teleport>

    <div v-if="offerModal.open" class="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/45 px-4 py-8">
      <div class="max-h-[90vh] w-full max-w-4xl overflow-auto rounded-3xl bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="text-xl font-bold text-slate-900">{{ offerModal.editingId ? "Editar oferta" : "Nova oferta" }}</h3>
            <p class="mt-1 text-sm text-slate-500">Configure o valor, o plano e qual checkout visual esta oferta usa.</p>
          </div>
          <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-600" @click="closeOfferModal">Fechar</button>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Key do link</span>
            <input v-model="offerModal.form.key" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Título</span>
            <input v-model="offerModal.form.title" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Texto do produto no rodapé</span>
            <input v-model="offerModal.form.footer_product_label" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Subtítulo</span>
            <input v-model="offerModal.form.subtitle" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Plano interno</span>
            <select v-model="offerModal.form.plan_key" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm">
              <option value="professional">Profissional</option>
              <option value="agency">Agência</option>
              <option value="scale">Escala</option>
              <option value="test">Teste</option>
            </select>
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Ciclo</span>
            <select v-model="offerModal.form.billing_cycle" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm">
              <option value="monthly">Mensal</option>
              <option value="annual">Anual</option>
            </select>
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Valor</span>
            <input v-model="offerModal.form.amount" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Checkout visual</span>
            <select v-model="offerModal.form.checkout_key" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm">
              <option value="">Selecione</option>
              <option v-for="checkout in form.checkouts" :key="checkout.local_id" :value="checkout.key">{{ checkout.name }}</option>
            </select>
          </label>
          <label class="inline-flex items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700 md:col-span-2">
            <input v-model="offerModal.form.active" type="checkbox" />
            Oferta ativa
          </label>
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" @click="closeOfferModal">Cancelar</button>
          <button type="button" class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white" @click="submitOfferModal">Salvar oferta</button>
        </div>
      </div>
    </div>

    <div v-if="pixelModal.open" class="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/45 px-4 py-8">
      <div class="max-h-[90vh] w-full max-w-4xl overflow-auto rounded-3xl bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="text-xl font-bold text-slate-900">{{ pixelModal.editingId ? "Editar pixel" : "Novo pixel" }}</h3>
            <p class="mt-1 text-sm text-slate-500">Cadastre o pixel da Meta, o token da API e as ofertas em que ele será disparado.</p>
          </div>
          <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-600" @click="closePixelModal">Fechar</button>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <label class="space-y-2 text-sm font-semibold text-slate-700 md:col-span-2">
            <span>Nome</span>
            <input v-model="pixelModal.form.name" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm" placeholder="Pixel principal da campanha" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Pixel ID</span>
            <input v-model="pixelModal.form.pixel_id" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-mono" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Access Token da API</span>
            <input v-model="pixelModal.form.access_token" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-mono" />
          </label>
          <label class="inline-flex items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700 md:col-span-2">
            <input v-model="pixelModal.form.active" type="checkbox" />
            Pixel ativo
          </label>
        </div>

        <div class="mt-5 rounded-2xl border border-slate-200 p-4">
          <div class="text-sm font-semibold text-slate-900">Ofertas permitidas</div>
          <p class="mt-1 text-xs text-slate-500">Se nenhuma oferta for marcada, o pixel não será usado em nenhuma oferta.</p>
          <div class="mt-3 grid gap-3 md:grid-cols-2">
            <label v-for="offer in form.offers" :key="offer.local_id" class="inline-flex items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-700">
              <input v-model="pixelModal.form.offer_keys" type="checkbox" :value="offer.key" />
              <span>{{ offer.title }}</span>
            </label>
          </div>
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" @click="closePixelModal">Cancelar</button>
          <button type="button" class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white" @click="submitPixelModal">Salvar pixel</button>
        </div>
      </div>
    </div>

    <div v-if="couponModal.open" class="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/45 px-4 py-8">
      <div class="max-h-[90vh] w-full max-w-4xl overflow-auto rounded-3xl bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="text-xl font-bold text-slate-900">{{ couponModal.editingId ? "Editar cupom" : "Novo cupom" }}</h3>
            <p class="mt-1 text-sm text-slate-500">Defina o desconto e em quais ofertas este cupom poderá ser aplicado.</p>
          </div>
          <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-600" @click="closeCouponModal">Fechar</button>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Código</span>
            <input v-model="couponModal.form.code" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm uppercase" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Título</span>
            <input v-model="couponModal.form.title" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Tipo de desconto</span>
            <select v-model="couponModal.form.discount_type" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm">
              <option value="fixed">Valor fixo</option>
              <option value="percent">Percentual</option>
            </select>
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Valor</span>
            <input v-model="couponModal.form.value" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm" />
          </label>
          <label class="inline-flex items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700 md:col-span-2">
            <input v-model="couponModal.form.active" type="checkbox" />
            Cupom ativo
          </label>
        </div>

        <div class="mt-5 rounded-2xl border border-slate-200 p-4">
          <div class="text-sm font-semibold text-slate-900">Ofertas permitidas</div>
          <div class="mt-3 grid gap-3 md:grid-cols-2">
            <label v-for="offer in form.offers" :key="offer.local_id" class="inline-flex items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-700">
              <input v-model="couponModal.form.offer_keys" type="checkbox" :value="offer.key" />
              <span>{{ offer.title }}</span>
            </label>
          </div>
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" @click="closeCouponModal">Cancelar</button>
          <button type="button" class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white" @click="submitCouponModal">Salvar cupom</button>
        </div>
      </div>
    </div>

    <div v-if="checkoutModal.open" class="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/45 px-4 py-8">
      <div class="max-h-[90vh] w-full max-w-5xl overflow-auto rounded-3xl bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="text-xl font-bold text-slate-900">{{ checkoutModal.editingId ? "Editar checkout" : "Novo checkout" }}</h3>
            <p class="mt-1 text-sm text-slate-500">Defina tema e banners que serão reutilizados pelas ofertas vinculadas.</p>
          </div>
          <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-600" @click="closeCheckoutModal">Fechar</button>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Key</span>
            <input v-model="checkoutModal.form.key" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Nome</span>
            <input v-model="checkoutModal.form.name" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm" />
          </label>
          <label class="space-y-2 text-sm font-semibold text-slate-700">
            <span>Tema</span>
            <select v-model="checkoutModal.form.theme_mode" class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm">
              <option value="dark">Dark</option>
              <option value="light">White</option>
            </select>
          </label>
          <label class="inline-flex items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700">
            <input v-model="checkoutModal.form.active" type="checkbox" />
            Checkout ativo
          </label>
        </div>

        <div class="mt-5 grid gap-5">
          <ImageUploadField
            v-model="checkoutModal.form.desktop_image_url"
            label="Banner desktop"
            hint="Imagem da coluna lateral no desktop."
            layout="row"
            replace-label="Substituir"
            :enable-crop="true"
            editor-title="Ajuste a imagem desktop do checkout"
          />
          <ImageUploadField
            v-model="checkoutModal.form.mobile_banner_url"
            label="Banner mobile"
            hint="Imagem do topo exibida no checkout mobile."
            layout="row"
            replace-label="Substituir"
            :enable-crop="true"
            editor-title="Ajuste o banner mobile do checkout"
          />
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" @click="closeCheckoutModal">Cancelar</button>
          <button type="button" class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white" @click="submitCheckoutModal">Salvar checkout</button>
        </div>
      </div>
    </div>

    <div
      v-if="snackbar.open"
      class="fixed bottom-6 left-1/2 z-[300] -translate-x-1/2 rounded-full px-5 py-3 text-sm font-semibold text-white shadow-2xl"
      :class="snackbar.tone === 'error' ? 'bg-rose-600' : 'bg-slate-900'"
    >
      {{ snackbar.text }}
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, reactive, ref, watch } from "vue";
import ImageUploadField from "../../components/admin/inputs/ImageUploadField.vue";
import {
  getAdminCheckoutOfferReports,
  getAdminCheckoutTrackingDocument,
  getAdminCheckoutTracking,
  getAdminCheckoutSettings,
  saveAdminCheckoutSettings,
  type CheckoutAppearance,
  type CheckoutCoupon,
  type CheckoutOfferReportItem,
  type CheckoutOffer,
  type CheckoutPixel,
  type CheckoutSettings,
  type CheckoutTrackingItem,
  type CheckoutTrackingDocumentDetail,
} from "../../services/checkout";

type TabId = "offers" | "pixels" | "coupons" | "checkouts" | "reports" | "tracking";

type OfferRow = CheckoutOffer & { local_id: string };
type PixelRow = CheckoutPixel & { local_id: string };
type CouponRow = CheckoutCoupon & { local_id: string };
type CheckoutRow = CheckoutAppearance & { local_id: string };

const tabs: Array<{ id: TabId; label: string }> = [
  { id: "offers", label: "Ofertas" },
  { id: "pixels", label: "Pixels" },
  { id: "coupons", label: "Cupons" },
  { id: "checkouts", label: "Checkouts" },
  { id: "reports", label: "Relatórios" },
  { id: "tracking", label: "Trackeamento" },
];

const activeTab = ref<TabId>("offers");
const loading = ref(true);
const saving = ref(false);
const snackbar = ref<{ open: boolean; text: string; tone: "success" | "error" }>({
  open: false,
  text: "",
  tone: "success",
});
let snackbarTimer: ReturnType<typeof setTimeout> | null = null;
let localSeed = 0;

const nextLocalId = (prefix: string) => `${prefix}-${localSeed++}`;

const blankOffer = (): OfferRow => ({
  local_id: nextLocalId("offer"),
  key: "",
  title: "",
  footer_product_label: "",
  plan_key: "professional",
  billing_cycle: "monthly",
  amount: "49.99",
  active: true,
  subtitle: "",
  checkout_key: "",
});

const blankPixel = (): PixelRow => ({
  local_id: nextLocalId("pixel"),
  name: "",
  pixel_id: "",
  access_token: "",
  active: true,
  offer_keys: [],
});

const blankCoupon = (): CouponRow => ({
  local_id: nextLocalId("coupon"),
  code: "",
  title: "",
  discount_type: "fixed",
  value: "10.00",
  offer_keys: [],
  active: true,
});

const blankCheckout = (): CheckoutRow => ({
  local_id: nextLocalId("checkout"),
  key: "",
  name: "",
  theme_mode: "dark",
  desktop_image_url: null,
  mobile_banner_url: null,
  active: true,
});

const form = reactive<{
  is_active: boolean;
  offers: OfferRow[];
  pixels: PixelRow[];
  coupons: CouponRow[];
  checkouts: CheckoutRow[];
}>({
  is_active: true,
  offers: [],
  pixels: [],
  coupons: [],
  checkouts: [],
});

const offerModal = reactive<{ open: boolean; editingId: string | null; form: OfferRow }>({
  open: false,
  editingId: null,
  form: blankOffer(),
});

const couponModal = reactive<{ open: boolean; editingId: string | null; form: CouponRow }>({
  open: false,
  editingId: null,
  form: blankCoupon(),
});

const pixelModal = reactive<{ open: boolean; editingId: string | null; form: PixelRow }>({
  open: false,
  editingId: null,
  form: blankPixel(),
});

const checkoutModal = reactive<{ open: boolean; editingId: string | null; form: CheckoutRow }>({
  open: false,
  editingId: null,
  form: blankCheckout(),
});
const trackingRows = ref<CheckoutTrackingItem[]>([]);
const reportRows = ref<CheckoutOfferReportItem[]>([]);
const trackingLoading = ref(false);
const reportsLoading = ref(false);
const reportChartReady = ref(false);
const reportPeriodPreset = ref<"7" | "30" | "90" | "custom">("30");
const reportPeriodStart = ref("");
const reportPeriodEnd = ref("");
const trackingFilterOffer = ref("");
const trackingSearch = ref("");
const trackingFilterStatus = ref<"" | "signed" | "pending">("");
const trackingFilterPaymentMethod = ref<"" | "card" | "pix" | "none">("");
const trackingOnlyErrors = ref(false);
const trackingDetailOpen = ref(false);
const trackingDetailLoading = ref(false);
const trackingDetail = ref<CheckoutTrackingDocumentDetail | null>(null);

const reportSummary = computed(() => {
  const totalSigned = reportRows.value.reduce((sum, row) => sum + (row.signed_count || 0), 0);
  const totalUpgrades = reportRows.value.reduce((sum, row) => sum + (row.upgrade_count || 0), 0);
  const offersWithSales = reportRows.value.filter(row => (row.total_count || 0) > 0).length;
  const upgradeRate = totalSigned > 0 ? `${Math.round((totalUpgrades / totalSigned) * 100)}%` : "0%";
  return { totalSigned, totalUpgrades, offersWithSales, upgradeRate };
});

const reportMaxCount = computed(() => Math.max(...reportRows.value.map(row => row.total_count || 0), 1));

const formatDateInputValue = (date: Date) => {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const todayDateInput = () => formatDateInputValue(new Date());

const daysAgoDateInput = (daysAgo: number) => {
  const date = new Date();
  date.setHours(12, 0, 0, 0);
  date.setDate(date.getDate() - daysAgo);
  return formatDateInputValue(date);
};

const syncReportPeriodPreset = (preset: "7" | "30" | "90" | "custom") => {
  reportPeriodPreset.value = preset;
  const today = todayDateInput();
  if (preset === "7") {
    reportPeriodStart.value = daysAgoDateInput(6);
    reportPeriodEnd.value = today;
    return;
  }
  if (preset === "30") {
    reportPeriodStart.value = daysAgoDateInput(29);
    reportPeriodEnd.value = today;
    return;
  }
  if (preset === "90") {
    reportPeriodStart.value = daysAgoDateInput(89);
    reportPeriodEnd.value = today;
    return;
  }
  if (!reportPeriodStart.value) reportPeriodStart.value = daysAgoDateInput(29);
  if (!reportPeriodEnd.value) reportPeriodEnd.value = today;
};

const reportPeriodLabel = computed(() => {
  if (reportPeriodPreset.value === "7") return "Últimos 7 dias";
  if (reportPeriodPreset.value === "30") return "Últimos 30 dias";
  if (reportPeriodPreset.value === "90") return "Últimos 90 dias";
  if (reportPeriodStart.value && reportPeriodEnd.value) {
    return `${reportPeriodStart.value} a ${reportPeriodEnd.value}`;
  }
  return "Período personalizado";
});

const filteredTrackingRows = computed(() => {
  const search = trackingSearch.value.trim().toLowerCase();
  return trackingRows.value.filter(row => {
    if (trackingFilterStatus.value === "signed" && !row.signed_at) return false;
    if (trackingFilterStatus.value === "pending" && row.signed_at) return false;

    const payment = (row.payment_method_selected || "").toLowerCase();
    if (trackingFilterPaymentMethod.value === "card" && payment !== "card") return false;
    if (trackingFilterPaymentMethod.value === "pix" && payment !== "pix") return false;
    if (trackingFilterPaymentMethod.value === "none" && payment) return false;

    if (trackingOnlyErrors.value && (row.error_events_count || 0) <= 0) return false;

    if (search) {
      const haystack = [
        row.customer_name || "",
        row.customer_email || "",
        row.customer_document || "",
        row.offer_key || "",
      ]
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(search)) return false;
    }
    return true;
  });
});

const showSnackbar = (text: string, tone: "success" | "error" = "success") => {
  snackbar.value = { open: true, text, tone };
  if (snackbarTimer) clearTimeout(snackbarTimer);
  snackbarTimer = setTimeout(() => {
    snackbar.value.open = false;
  }, 3200);
};

const normalizeMoneyInput = (value: string) => {
  const normalized = String(value || "").replace(",", ".").trim();
  return normalized || "0";
};

const extractApiErrorMessage = (error: unknown, fallback: string) => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail) && detail.length) {
      const first = detail[0];
      if (typeof first === "string" && first.trim()) return first;
      if (first && typeof first === "object" && "msg" in first && typeof first.msg === "string") {
        return first.msg;
      }
    }
  }
  return fallback;
};

const checkoutNameByKey = (key?: string | null) => {
  const row = form.checkouts.find(item => item.key === key);
  return row?.name || "Sem checkout";
};

const offerTitleByKey = (key: string) => form.offers.find(offer => offer.key === key)?.title || key;

const pixelOfferSummary = (offerKeys: string[]) => {
  if (!offerKeys.length) return "Nenhuma oferta";
  return offerKeys.map(offerTitleByKey).join(", ");
};

const cycleLabel = (cycle: string) => (cycle === "annual" ? "Anual" : "Mensal");

const planLabel = (plan: string) => {
  if (plan === "agency") return "Agência";
  if (plan === "scale") return "Escala";
  if (plan === "test") return "Teste";
  return "Profissional";
};

const formatCurrency = (value: string) => {
  const parsed = Number(String(value || "0").replace(",", "."));
  return Number.isFinite(parsed)
    ? parsed.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
    : value;
};

const couponOfferSummary = (offerKeys: string[]) => {
  if (!offerKeys.length) return "Nenhuma oferta vinculada";
  const titles = offerKeys
    .map(key => form.offers.find(offer => offer.key === key)?.title || key)
    .filter(Boolean);
  return titles.join(", ");
};

const imageState = (url?: string | null) => (url ? "Com" : "Sem");

const formatPercent = (value: number, total: number) => {
  if (!total || value <= 0) return "0%";
  return `${Math.round((value / total) * 100)}%`;
};

const reportChartWidth = (value: number) => {
  if (!value) return "0%";
  const max = reportMaxCount.value || 1;
  return `${Math.max(6, (value / max) * 100)}%`;
};

const reportShareWidth = (value: number, total: number) => {
  if (!value || !total) return "0%";
  return `${(value / total) * 100}%`;
};

const animateReportChart = () => {
  reportChartReady.value = false;
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      reportChartReady.value = true;
    });
  });
};

const buildReportQuery = () => ({
  startDate: reportPeriodStart.value || undefined,
  endDate: reportPeriodEnd.value || undefined,
});

const checkoutPublicBaseUrl = () => {
  if (typeof window === "undefined") return "";
  return import.meta.env.PROD ? "https://roteiroonline.com" : window.location.origin;
};

const buildOfferCheckoutUrl = (offerKey: string) => {
  const normalizedKey = offerKey.trim().toLowerCase();
  if (!normalizedKey) return "";
  return `${checkoutPublicBaseUrl()}/checkout/${normalizedKey}`;
};

const copyOfferLink = async (offerKey: string) => {
  const url = buildOfferCheckoutUrl(offerKey);
  if (!url) {
    showSnackbar("Preencha a key da oferta antes de copiar o link.", "error");
    return;
  }
  try {
    await navigator.clipboard.writeText(url);
    showSnackbar("Link da oferta copiado.");
  } catch (error) {
    console.error(error);
    showSnackbar("Não foi possível copiar o link da oferta.", "error");
  }
};

const applySettings = (data: Partial<CheckoutSettings> & Record<string, any>) => {
  const rawCheckouts = Array.isArray(data.checkouts) ? data.checkouts : [];
  const rawOffers = Array.isArray(data.offers) ? data.offers : [];
  const rawPixels = Array.isArray(data.pixels) ? data.pixels : [];
  const rawCoupons = Array.isArray(data.coupons) ? data.coupons : [];

  const fallbackCheckouts: CheckoutRow[] = rawCheckouts.length
    ? rawCheckouts.map(item => ({ ...item, local_id: nextLocalId("checkout") }))
    : [
        {
          local_id: nextLocalId("checkout"),
          key: "default",
          name: "Checkout padrão",
          theme_mode: data.theme_mode === "light" ? "light" : "dark",
          desktop_image_url: data.desktop_image_url || null,
          mobile_banner_url: data.mobile_banner_url || null,
          active: true,
        },
      ];

  form.is_active = typeof data.is_active === "boolean" ? data.is_active : true;
  form.checkouts = fallbackCheckouts;
  form.offers = rawOffers.map(item => ({
    ...item,
    local_id: nextLocalId("offer"),
    checkout_key: item.checkout_key || fallbackCheckouts[0]?.key || "",
  }));
  form.pixels = rawPixels.map(item => ({
    ...item,
    local_id: nextLocalId("pixel"),
    offer_keys: Array.isArray(item.offer_keys) ? [...item.offer_keys] : [],
  }));
  form.coupons = rawCoupons.map(item => ({ ...item, local_id: nextLocalId("coupon") }));
};

const serializePayload = () => ({
  is_active: form.is_active,
  offers: form.offers.map(({ local_id, ...item }) => ({
    ...item,
    amount: normalizeMoneyInput(item.amount),
    footer_product_label: item.footer_product_label?.trim() || item.title.trim(),
    checkout_key: item.checkout_key?.trim() || null,
  })),
  pixels: form.pixels.map(({ local_id, ...item }) => ({
    ...item,
    name: item.name.trim(),
    pixel_id: item.pixel_id.trim(),
    access_token: item.access_token.trim(),
    offer_keys: item.offer_keys.map(value => value.trim().toLowerCase()).filter(Boolean),
  })),
  coupons: form.coupons.map(({ local_id, ...item }) => ({
    ...item,
    code: item.code.trim().toUpperCase(),
    value: normalizeMoneyInput(item.value),
    offer_keys: item.offer_keys.map(value => value.trim().toLowerCase()).filter(Boolean),
  })),
  checkouts: form.checkouts.map(({ local_id, ...item }) => item),
});

const load = async () => {
  loading.value = true;
  try {
    const data = await getAdminCheckoutSettings();
    applySettings(data);
  } catch (error) {
    console.error(error);
    showSnackbar("Não foi possível carregar as ofertas.", "error");
  } finally {
    loading.value = false;
  }
};

const loadTracking = async () => {
  trackingLoading.value = true;
  try {
    trackingRows.value = await getAdminCheckoutTracking(trackingFilterOffer.value || undefined, 300);
  } catch (error) {
    console.error(error);
    showSnackbar("Nao foi possivel carregar o trackeamento.", "error");
  } finally {
    trackingLoading.value = false;
  }
};

const loadReports = async () => {
  reportsLoading.value = true;
  reportChartReady.value = false;
  try {
    reportRows.value = await getAdminCheckoutOfferReports(buildReportQuery());
    animateReportChart();
  } catch (error) {
    console.error(error);
    showSnackbar("Nao foi possivel carregar os relatórios.", "error");
  } finally {
    reportsLoading.value = false;
  }
};

const openTrackingDetail = async (row: CheckoutTrackingItem) => {
  if (!row.customer_document) {
    showSnackbar("Documento nao encontrado para este lead.", "error");
    return;
  }
  trackingDetailOpen.value = true;
  trackingDetailLoading.value = true;
  trackingDetail.value = null;
  try {
    trackingDetail.value = await getAdminCheckoutTrackingDocument(row.customer_document, trackingFilterOffer.value || undefined);
  } catch (error) {
    console.error(error);
    showSnackbar("Nao foi possivel carregar os detalhes do tracking.", "error");
    trackingDetailOpen.value = false;
  } finally {
    trackingDetailLoading.value = false;
  }
};

const closeTrackingDetail = () => {
  trackingDetailOpen.value = false;
  trackingDetail.value = null;
};

const formatDateTime = (value?: string | null) => {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString("pt-BR");
};

const formatDurationMs = (value?: number | null) => {
  if (value == null) return "-";
  if (value < 1000) return `${value}ms`;
  return `${(value / 1000).toFixed(1)}s`;
};

const trackingOfferKeys = (detail: CheckoutTrackingDocumentDetail | null) => {
  if (!detail) return [];
  const keys = new Set((detail.events || []).map(event => (event.offer_key || "").trim()).filter(Boolean));
  return Array.from(keys);
};

const persistSettings = async (successMessage: string) => {
  saving.value = true;
  try {
    const data = await saveAdminCheckoutSettings(serializePayload());
    applySettings(data);
    showSnackbar(successMessage);
    return true;
  } catch (error) {
    console.error(error);
    showSnackbar(extractApiErrorMessage(error, "Não foi possível salvar as ofertas."), "error");
    return false;
  } finally {
    saving.value = false;
  }
};

const save = async () => {
  await persistSettings("Ofertas salvas com sucesso.");
};

const openOfferModal = (row?: OfferRow) => {
  offerModal.open = true;
  offerModal.editingId = row?.local_id || null;
  offerModal.form = row ? { ...row } : blankOffer();
};

const closeOfferModal = () => {
  offerModal.open = false;
  offerModal.editingId = null;
  offerModal.form = blankOffer();
};

const submitOfferModal = async () => {
  if (!offerModal.form.key.trim() || !offerModal.form.title.trim()) {
    showSnackbar("Preencha key e título da oferta.", "error");
    return;
  }
  offerModal.form.footer_product_label = offerModal.form.footer_product_label?.trim() || offerModal.form.title.trim();
  if (offerModal.editingId) {
    const index = form.offers.findIndex(item => item.local_id === offerModal.editingId);
    if (index >= 0) form.offers[index] = { ...offerModal.form };
  } else {
    form.offers.push({ ...offerModal.form, local_id: nextLocalId("offer") });
  }
  const saved = await persistSettings("Oferta salva com sucesso.");
  if (saved) closeOfferModal();
};

const removeOffer = async (localId: string) => {
  const target = form.offers.find(item => item.local_id === localId);
  form.offers = form.offers.filter(item => item.local_id !== localId);
  form.coupons = form.coupons.map(item => ({
    ...item,
    offer_keys: item.offer_keys.filter(key => form.offers.some(offer => offer.key === key)),
  }));
  if (target) {
    form.pixels = form.pixels.map(item => ({
      ...item,
      offer_keys: item.offer_keys.filter(key => key !== target.key),
    }));
  }
  await persistSettings("Oferta excluída com sucesso.");
};

const openPixelModal = (row?: PixelRow) => {
  pixelModal.open = true;
  pixelModal.editingId = row?.local_id || null;
  pixelModal.form = row ? { ...row, offer_keys: [...row.offer_keys] } : blankPixel();
};

const closePixelModal = () => {
  pixelModal.open = false;
  pixelModal.editingId = null;
  pixelModal.form = blankPixel();
};

const submitPixelModal = async () => {
  if (!pixelModal.form.name.trim() || !pixelModal.form.pixel_id.trim() || !pixelModal.form.access_token.trim()) {
    showSnackbar("Preencha nome, ID e token do pixel.", "error");
    return;
  }
  if (pixelModal.editingId) {
    const index = form.pixels.findIndex(item => item.local_id === pixelModal.editingId);
    if (index >= 0) {
      form.pixels[index] = {
        ...pixelModal.form,
        name: pixelModal.form.name.trim(),
        pixel_id: pixelModal.form.pixel_id.trim(),
        access_token: pixelModal.form.access_token.trim(),
        offer_keys: [...pixelModal.form.offer_keys],
      };
    }
  } else {
    form.pixels.push({
      ...pixelModal.form,
      local_id: nextLocalId("pixel"),
      name: pixelModal.form.name.trim(),
      pixel_id: pixelModal.form.pixel_id.trim(),
      access_token: pixelModal.form.access_token.trim(),
      offer_keys: [...pixelModal.form.offer_keys],
    });
  }
  const saved = await persistSettings("Pixel salvo com sucesso.");
  if (saved) closePixelModal();
};

const removePixel = async (localId: string) => {
  form.pixels = form.pixels.filter(item => item.local_id !== localId);
  await persistSettings("Pixel excluído com sucesso.");
};

const openCouponModal = (row?: CouponRow) => {
  couponModal.open = true;
  couponModal.editingId = row?.local_id || null;
  couponModal.form = row ? { ...row, offer_keys: [...row.offer_keys] } : blankCoupon();
};

const closeCouponModal = () => {
  couponModal.open = false;
  couponModal.editingId = null;
  couponModal.form = blankCoupon();
};

const submitCouponModal = async () => {
  if (!couponModal.form.code.trim() || !couponModal.form.title.trim()) {
    showSnackbar("Preencha código e título do cupom.", "error");
    return;
  }
  const normalizedCouponValue = Number(normalizeMoneyInput(couponModal.form.value));
  if (!Number.isFinite(normalizedCouponValue) || normalizedCouponValue <= 0) {
    showSnackbar("Informe um valor de desconto válido para o cupom.", "error");
    return;
  }
  if (couponModal.editingId) {
    const index = form.coupons.findIndex(item => item.local_id === couponModal.editingId);
    if (index >= 0) form.coupons[index] = { ...couponModal.form, code: couponModal.form.code.trim().toUpperCase(), value: normalizeMoneyInput(couponModal.form.value) };
  } else {
    form.coupons.push({
      ...couponModal.form,
      local_id: nextLocalId("coupon"),
      code: couponModal.form.code.trim().toUpperCase(),
      value: normalizeMoneyInput(couponModal.form.value),
    });
  }
  const saved = await persistSettings("Cupom salvo com sucesso.");
  if (saved) closeCouponModal();
};

const removeCoupon = async (localId: string) => {
  form.coupons = form.coupons.filter(item => item.local_id !== localId);
  await persistSettings("Cupom excluído com sucesso.");
};

const openCheckoutModal = (row?: CheckoutRow) => {
  checkoutModal.open = true;
  checkoutModal.editingId = row?.local_id || null;
  checkoutModal.form = row ? { ...row } : blankCheckout();
};

const closeCheckoutModal = () => {
  checkoutModal.open = false;
  checkoutModal.editingId = null;
  checkoutModal.form = blankCheckout();
};

const submitCheckoutModal = async () => {
  if (!checkoutModal.form.key.trim() || !checkoutModal.form.name.trim()) {
    showSnackbar("Preencha key e nome do checkout.", "error");
    return;
  }
  if (checkoutModal.editingId) {
    const index = form.checkouts.findIndex(item => item.local_id === checkoutModal.editingId);
    if (index >= 0) form.checkouts[index] = { ...checkoutModal.form };
  } else {
    form.checkouts.push({ ...checkoutModal.form, local_id: nextLocalId("checkout") });
  }
  const saved = await persistSettings("Checkout salvo com sucesso.");
  if (saved) closeCheckoutModal();
};

const removeCheckout = async (localId: string) => {
  const target = form.checkouts.find(item => item.local_id === localId);
  form.checkouts = form.checkouts.filter(item => item.local_id !== localId);
  if (target) {
    const fallback = form.checkouts[0]?.key || "";
    form.offers = form.offers.map(item => ({
      ...item,
      checkout_key: item.checkout_key === target.key ? fallback : item.checkout_key,
    }));
  }
  await persistSettings("Checkout excluído com sucesso.");
};

onMounted(async () => {
  syncReportPeriodPreset(reportPeriodPreset.value);
  await load();
  await Promise.all([loadTracking(), loadReports()]);
});

watch(activeTab, value => {
  if (value === "tracking" && !trackingLoading.value) {
    loadTracking();
  }
  if (value === "reports" && !reportsLoading.value) {
    loadReports();
  }
});

watch(reportPeriodPreset, value => {
  syncReportPeriodPreset(value);
});
</script>

<style scoped>
@keyframes report-card-in {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.report-card-animate {
  animation: report-card-in 560ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
</style>
