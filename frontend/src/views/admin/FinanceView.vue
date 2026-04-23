
<template>
  <div class="space-y-6">
    <section v-if="activeTab === 'products'" class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 class="text-xl font-semibold text-slate-900">Central comercial</h2>
          <p class="text-sm text-slate-500">Cadastre viagens, gerencie estoque e acione o PDV interno.</p>
        </div>
        <div class="flex flex-wrap gap-3">
          <button
            type="button"
            class="pill"
            :disabled="productsLoading || inventoryRebuildLoading || !products.length"
            @click="handleRebuildProductInventory"
          >
            {{ inventoryRebuildLoading ? "Reprocessando..." : "Reprocessar estoque" }}
          </button>
          <button type="button" class="pill" :disabled="productsLoading || !products.length" @click="openPosModal()">
            Nova venda
          </button>
          <button type="button" class="pill" :disabled="productsLoading || !products.length" @click="openPaymentLinkModal()">
            Gerar link
          </button>
          <router-link class="btn-primary" :to="{ name: 'product-create' }">Criar produto</router-link>
        </div>
      </div>

      <div v-if="productsLoading" class="placeholder-card">Carregando produtos...</div>
      <div v-else-if="!products.length" class="placeholder-card">
        Nenhum produto cadastrado. Clique em <strong>Criar produto</strong> para comear.
      </div>
      <div v-else class="space-y-4">
        <div class="products-toolbar">
          <div class="products-toolbar__filters">
            <label class="products-toolbar__search">
              <span class="sr-only">Buscar produto</span>
              <input
                v-model.trim="productSearch"
                type="search"
                class="input products-toolbar__input"
                placeholder="Buscar produto..."
              />
            </label>
            <label class="products-toolbar__select">
              <span class="sr-only">Filtrar por status</span>
              <select v-model="productStatusFilter" class="input products-toolbar__input">
                <option v-for="option in productStatusOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
            <label class="products-toolbar__select">
              <span class="sr-only">Ordenar produtos</span>
              <select v-model="productSort" class="input products-toolbar__input">
                <option v-for="option in productSortOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
          </div>
          <p class="products-toolbar__count">
            {{ filteredProducts.length }} {{ filteredProducts.length === 1 ? "produto" : "produtos" }}
          </p>
        </div>

        <div v-if="!filteredProducts.length" class="placeholder-card">
          Nenhum produto encontrado com os filtros atuais.
        </div>
        <div v-else class="products-list-surface">
        <div class="products-list-scroll">
          <div class="products-list-header product-list-grid">
            <span class="products-list-header__cell products-list-header__cell-product">Produto</span>
            <span class="products-list-header__cell products-list-header__cell-date">Data</span>
            <span class="products-list-header__cell products-list-header__cell-metric">Totais</span>
            <span class="products-list-header__cell products-list-header__cell-metric">Disponíveis</span>
            <span class="products-list-header__cell products-list-header__cell-metric">Reservadas</span>
            <span class="products-list-header__cell products-list-header__cell-metric">Vendidas</span>
            <span class="products-list-header__cell products-list-header__cell-status">Status</span>
            <span class="products-list-header__cell products-list-header__cell-actions">Ações</span>
          </div>

          <article
            v-for="product in filteredProducts"
            :key="product.public_id"
            class="products-row product-list-grid"
          >
            <div class="products-row__product">
              <div class="products-row__thumb-wrap">
                <img
                  v-if="productImageUrl(product)"
                  :src="productImageUrl(product) || undefined"
                  :alt="product.name"
                  class="products-row__thumb"
                />
                <div v-else class="products-row__thumb products-row__thumb--fallback">
                  {{ product.name.slice(0, 1) }}
                </div>
              </div>
              <div class="products-row__identity">
                <h3 class="products-row__title">{{ product.name }}</h3>
              </div>
            </div>

            <div class="products-row__metric">
              <span class="products-row__date">{{ tripDateLabel(product) }}</span>
            </div>
            <div class="products-row__metric">
              <span class="products-row__metric-value">{{ product.total_slots }}</span>
            </div>
            <div class="products-row__metric products-row__metric--available">
              <span class="products-row__metric-value">{{ product.available_slots }}</span>
            </div>
            <div class="products-row__metric products-row__metric--reserved">
              <span class="products-row__metric-value">{{ product.reserved_slots }}</span>
            </div>
            <div class="products-row__metric products-row__metric--sold">
              <span class="products-row__metric-value">{{ product.sold_slots }}</span>
            </div>

            <div class="products-row__status">
              <span class="status-pill" :class="productStatusClass(product.status)">
                {{ productStatusLabel(product.status) }}
              </span>
            </div>

            <div class="products-row__actions">
              <router-link
                class="products-row__link"
                :to="{ name: 'product-detail', params: { productId: product.public_id } }"
              >
                Ver produto
              </router-link>
            </div>
          </article>
        </div>
      </div>
      </div>
    </section>
    <section v-else-if="activeTab === 'sales'" class="space-y-4">
      <div class="flex flex-wrap items-center gap-2">
        <button
          type="button"
          class="sales-tab"
          :class="{ 'sales-tab-active': salesTab === 'overview' }"
          @click="salesTab = 'overview'"
        >
          Geral
        </button>
        <button
          type="button"
          class="sales-tab"
          :class="{ 'sales-tab-active': salesTab === 'settings' }"
          @click="salesTab = 'settings'"
        >
          Configurações
        </button>
      </div>
      <template v-if="salesTab === 'overview'">
        <div class="flex flex-wrap items-center justify-between gap-3">
        <p class="text-sm text-slate-500">Total de vendas: {{ salesPagination.total }}</p>
        <div class="flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="pill"
            :disabled="productsLoading || !products.length"
            @click="openPaymentLinkModal()"
          >
            Gerar link
          </button>
          <button
            type="button"
            class="btn-primary"
            :disabled="productsLoading || !products.length"
            @click="openPosModal()"
          >
            Nova venda
          </button>
          <button class="pill" @click="loadSales">Atualizar</button>
        </div>
      </div>
      <div class="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Status pagamento</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <button
                v-for="option in paymentFilterOptions"
                :key="option.value"
                type="button"
                class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                :class="
                  paymentFilter === option.value
                    ? 'border-emerald-500 bg-emerald-500 text-white'
                    : 'border-slate-200 bg-slate-100 text-slate-600 hover:border-slate-300'
                "
                @click="paymentFilter = option.value"
              >
                {{ option.label }}
              </button>
            </div>
          </div>
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Passageiros</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <button
                v-for="option in passengerFilterOptions"
                :key="option.value"
                type="button"
                class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                :class="
                  passengerFilter === option.value
                    ? 'border-emerald-500 bg-emerald-500 text-white'
                    : 'border-slate-200 bg-slate-100 text-slate-600 hover:border-slate-300'
                "
                @click="passengerFilter = option.value"
              >
                {{ option.label }}
              </button>
            </div>
          </div>
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Fonte</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <button
                v-for="option in channelFilterOptions"
                :key="option.value"
                type="button"
                class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                :class="
                  channelFilter === option.value
                    ? 'border-emerald-500 bg-emerald-500 text-white'
                    : 'border-slate-200 bg-slate-100 text-slate-600 hover:border-slate-300'
                "
                @click="channelFilter = option.value"
              >
                {{ option.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
      <div v-if="!filteredSales.length" class="placeholder-card">Nenhuma venda encontrada.</div>
      <div v-else>
        <div class="overflow-x-auto rounded-3xl border border-slate-200 bg-white">
          <table class="min-w-full divide-y divide-slate-200 text-sm text-center">
            <thead class="bg-slate-50 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              <tr>
                <th class="px-3 py-2">ID</th>
                <th class="px-3 py-2">Produto</th>
                <th class="px-3 py-2">Fonte</th>
                <th class="px-3 py-2">Cliente</th>
                <th class="px-3 py-2">Status</th>
                <th class="px-3 py-2">Pagamento</th>
                <th class="px-3 py-2">Aes</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="sale in filteredSales" :key="sale.id">
                <td class="px-3 py-3 align-middle text-sm font-semibold text-slate-900">#{{ sale.id }}</td>
                <td class="px-3 py-3 align-middle">
                  <p class="text-sm font-semibold text-slate-900">{{ sale.product_title }}</p>
                </td>
                <td class="px-3 py-3 align-middle text-sm text-slate-600">
                  <p class="font-semibold text-slate-900">{{ saleChannelLabel(sale.channel) }}</p>
                  <p class="text-xs text-slate-500" v-if="salePageLabel(sale)">
                    {{ salePageLabel(sale) }}
                  </p>
                </td>
                <td class="px-3 py-3 align-middle text-sm text-slate-600">
                  {{ sale.customer_name || 'Cliente' }}
                </td>
                <td class="px-3 py-3 align-middle">
                  <div class="flex flex-wrap justify-center gap-2 text-xs font-semibold">
                    <span :class="['badge', statusClasses.payment[paymentStatusKey(sale.payment_status)]]">
                      {{ paymentStatusLabel(sale.payment_status) }}
                    </span>
                    <span :class="['badge', statusClasses.payout[payoutStatusKey(sale.payout_status)]]">
                      {{ payoutStatusLabel(sale.payout_status) }}
                    </span>
                    <span :class="['badge', statusClasses.passengers[passengerStatusKey(sale.passenger_status)]]">
                      {{ passengerStatusLabel(sale.passenger_status) }}
                    </span>
                  </div>
                </td>
                <td class="px-3 py-3 align-middle text-sm text-slate-600">
                  <p class="font-semibold text-slate-900">{{ formatCurrency(sale.amount_cents) }}</p>
                  <p class="text-xs text-slate-500">{{ sale.installments }}x</p>
                </td>
                <td class="px-3 py-3 align-middle">
                  <div class="flex flex-wrap justify-center gap-2">
                    <button class="pill" @click="openSaleDetails(sale.id)">Detalhes</button>
                    <button
                      class="pill"
                      :disabled="!sale.requires_passengers"
                      :title="sale.requires_passengers ? 'Gerenciar passageiros' : 'Este produto não exige passageiros.'"
                      @click="sale.requires_passengers && openPassengerModal(sale.id)"
                    >
                      Passageiros
                    </button>
                    <button
                      class="pill"
                      :disabled="sale.payment_status !== 'paid' || !sale.requires_passengers"
                      :title="sale.requires_passengers ? 'Copiar link público' : 'Este produto não exige formulário de passageiros.'"
                      @click="copyPassengerLink(sale.id)"
                    >
                      Copiar link
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
          </template>
            <div v-else class="space-y-4">
        <div class="sales-settings-card">
          <div class="sales-settings-header">
            <div>
              <p class="sales-eyebrow">Integração Blimboo</p>
              <h3 class="text-xl font-semibold text-slate-900">Conecte sua conta Blimboo</h3>
              <p class="mt-2 text-sm text-slate-600">
                Use o token da sua conta para gerar cobrancas diretamente pelo painel e liberar o checkout.
              </p>
            </div>
            <div class="text-right text-xs text-slate-500">
              <p class="font-semibold" :class="blimbooState.hasToken ? 'text-emerald-600' : 'text-slate-500'">
                {{ blimbooState.hasToken ? "Token conectado" : "Nenhum token conectado" }}
              </p>
              <p v-if="blimbooUpdatedLabel">Atualizado em {{ blimbooUpdatedLabel }}</p>
            </div>
          </div>
          <div class="sales-settings-actions">
            <button type="button" class="pill">Criar conta na Blimboo</button>
            <span class="text-xs text-slate-500">Precisa de uma conta? Clique acima e finalize em instantes.</span>
          </div>
          <div class="sales-settings-form">
            <input
              v-model="blimbooState.token"
              type="text"
              class="input flex-1"
              :disabled="blimbooLoading || blimbooSaving"
              placeholder="Cole aqui o token da sua conta Blimboo"
            />
            <button
              type="button"
              class="btn-primary min-w-[220px]"
              :disabled="blimbooSaving"
              @click="connectBlimbooAccount"
            >
              {{ blimbooSaving ? "Salvando..." : "Conectar minha conta" }}
            </button>
          </div>
          <div class="sales-settings-note">
            <p class="text-xs text-slate-500">
              Esse token sera usado como Bearer em todas as cobrancas desta agencia. Insira novamente se precisar trocar.
            </p>
            <p
              v-if="blimbooFeedback"
              class="text-sm font-semibold transition"
              :class="blimbooFeedback.type === 'success' ? 'text-emerald-600' : 'text-rose-600'"
            >
              {{ blimbooFeedback.message }}
            </p>
            <p v-else-if="blimbooLoading" class="text-sm text-slate-500">Carregando configuracoes...</p>
            <p v-else-if="blimbooState.hasToken" class="text-sm text-emerald-600">Token ativo para esta agencia.</p>
          </div>
        </div>
      </div>
    </section>

    
    <div v-if="posModalVisible" class="modal-overlay !mt-0">
      <div class="modal-card max-w-3xl">
        <header class="mb-4 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Nova venda assistida</p>
            <h3 class="text-lg font-semibold text-slate-900">{{ posProduct?.name || 'Selecione um produto' }}</h3>
          </div>
          <button class="text-slate-500" @click="closePosModal"></button>
        </header>
        <div class="space-y-4">
          <div>
            <label class="input-label">Produto</label>
            <select v-model="posProductId" class="input" @change="syncPosProduct">
              <option disabled value="">Selecione</option>
              <option v-for="product in products" :key="product.public_id" :value="product.public_id">{{ product.name }}</option>
            </select>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label class="input-label">Cliente</label>
              <input v-model="posCustomer.name" class="input mb-2" placeholder="Nome completo" />
              <input v-model="posCustomer.email" class="input mb-2" placeholder="email@cliente.com" />
              <input v-model="posCustomer.phone" class="input" placeholder="(11) 99999-0000" />
            </div>
            <div class="rounded-2xl border border-slate-100 p-3">
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Resumo</p>
              <p class="text-sm text-slate-500">Passageiros estimados: <span class="font-semibold text-slate-900">{{ posPassengers }}</span></p>
              <p class="text-sm text-slate-500">Ocupao estimada: <span class="font-semibold text-slate-900">{{ posCapacity }}</span></p>
              <p class="text-2xl font-semibold text-slate-900">{{ formatCurrency(posTotal) }}</p>
              <div
                v-if="posResult"
                class="mt-3 space-y-1 rounded-2xl bg-emerald-50 p-3 text-xs text-emerald-900"
              >
                <p class="text-sm font-semibold">Cobrana criada!</p>
                <p>Venda #{{ posResult.sale_id }}  {{ paymentStatusLabel(posResult.provider_status) }}</p>
                <p>Ref: {{ posResult.checkout_reference }}</p>
                <p>{{ posResult.breakdown.installments }}x de {{ formatCurrency(posResult.breakdown.installment_amount_cents) }}</p>
                <button
                  v-if="posResult.passenger_token"
                  type="button"
                  class="text-[11px] font-semibold text-emerald-700 underline"
                  :disabled="posResult.provider_status !== 'paid'"
                  @click="copyPassengerLink(posResult.sale_id)"
                >
                  Copiar link de passageiros
                </button>
              </div>
            </div>
          </div>
          <div v-if="posProduct" class="space-y-3 rounded-2xl border border-slate-100 p-3">
            <p class="text-sm font-semibold text-slate-900">Pacotes</p>
            <template v-for="variation in (posProduct?.variations || [])" :key="variation.public_id">
              <div
                v-if="posSelections[variation.public_id]"
                class="space-y-3 rounded-xl bg-slate-50 px-3 py-3"
              >
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-slate-900">{{ variation.name }}</p>
                  <p class="text-xs text-slate-500">
                    {{ formatCurrency(variation.price_cents) }}  Inclui {{ variation.people_included }} pessoa(s)
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs font-semibold text-slate-500">Quantidade</span>
                  <input
                    type="number"
                    min="0"
                    class="w-24 rounded-full border border-slate-200 px-3 py-1 text-center text-sm"
                    v-model.number="posSelections[variation.public_id].quantity"
                    @input="handlePosQuantityInput(variation)"
                  />
                </div>
              </div>
              <div
                v-if="hasEnabledChildRules(variation)"
                class="space-y-2 rounded-2xl border border-slate-100 bg-white/80 p-3"
              >
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">crian&ccedil;as</p>
                <div
                  v-for="rule in enabledChildRules(variation)"
                  :key="`${variation.public_id}-${rule.key}`"
                  class="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2"
                >
                  <div>
                    <p class="text-sm font-semibold text-slate-900">{{ describeChildRange(rule) }}</p>
                    <p class="text-[11px] text-slate-500">
                      {{ rule.min_age }}-{{ rule.max_age }} anos 
                      {{ rule.pricing_mode === "free" ? "Gratuito" : `+${formatCurrency(rule.extra_amount_cents)}` }} 
                      {{ rule.counts_towards_capacity ? "Consome vaga" : "No consome vaga" }}
                    </p>
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="grid h-7 w-7 place-items-center rounded-full border border-slate-200 text-sm font-semibold text-slate-700 disabled:opacity-40"
                      @click="adjustPosChild(variation, rule.key, -1)"
                      :disabled="(posSelections[variation.public_id].children[rule.key] || 0) <= 0"
                    >
                      &minus;
                    </button>
                    <span class="min-w-[2ch] text-center font-semibold text-slate-900">
                      {{ posSelections[variation.public_id].children[rule.key] || 0 }}
                    </span>
                    <button
                      type="button"
                      class="grid h-7 w-7 place-items-center rounded-full border border-slate-200 bg-white text-sm font-semibold text-slate-900 disabled:opacity-40"
                      @click="adjustPosChild(variation, rule.key, 1)"
                      :disabled="!canIncrementPosChild(variation, rule.key)"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
              <div class="text-[11px] text-slate-500">
                <template v-if="posSelections[variation.public_id].quantity > 0">
                  <span>
                    Passageiros: {{
                      selectionComposition(variation, posSelections[variation.public_id]).totalPassengers
                    }}
                  </span>
                  
                  <span>
                    Ocupao: {{ selectionComposition(variation, posSelections[variation.public_id]).totalCapacity }}
                  </span>
                  
                  <span>
                    Total: {{ formatCurrency(selectionComposition(variation, posSelections[variation.public_id]).totalPriceCents) }}
                  </span>
                </template>
                <template v-else>Defina a quantidade para ver o resumo.</template>
              </div>
              </div>
            </template>
          </div>
        </div>
        <footer class="mt-6 flex justify-end gap-3">
          <button class="pill" @click="closePosModal">Cancelar</button>
          <button class="btn-primary" :disabled="posSaving || !posProduct || !posItems.length" @click="submitPosSale">
            {{ posSaving ? 'Processando...' : 'Gerar cobrana' }}
          </button>
        </footer>
      </div>
    </div>
    <div v-if="paymentLinkModalVisible" class="modal-overlay !mt-0">
      <div class="modal-card max-w-xl">
        <header class="mb-4 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Link de pagamento</p>
            <h3 class="text-lg font-semibold text-slate-900">{{ paymentLinkProduct?.name || 'Selecione um produto' }}</h3>
          </div>
          <button class="text-slate-500" @click="closePaymentLinkModal"></button>
        </header>
        <div class="space-y-4">
          <div>
            <label class="input-label">Produto</label>
            <select v-model="paymentLinkProductId" class="input" @change="syncPaymentLinkProduct">
              <option disabled value="">Selecione</option>
              <option v-for="product in products" :key="product.public_id" :value="product.public_id">{{ product.name }}</option>
            </select>
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <div>
              <label class="input-label">Nome</label>
              <input v-model="paymentLinkCustomer.name" class="input" placeholder="Cliente" />
            </div>
            <div>
              <label class="input-label">E-mail</label>
              <input v-model="paymentLinkCustomer.email" class="input" placeholder="email@cliente.com" />
            </div>
            <div>
              <label class="input-label">Telefone</label>
              <input v-model="paymentLinkCustomer.phone" class="input" placeholder="(11) 99999-0000" />
            </div>
            <div>
              <label class="input-label">Expira (min)</label>
              <input type="number" min="5" class="input" v-model.number="paymentLinkExpires" />
            </div>
          </div>
          <div v-if="paymentLinkProduct" class="space-y-3 rounded-2xl border border-slate-100 p-3">
            <p class="text-sm font-semibold text-slate-900">Pacotes</p>
            <template v-for="variation in (paymentLinkProduct?.variations || [])" :key="variation.public_id">
              <div
                v-if="paymentLinkSelections[variation.public_id]"
                class="space-y-3 rounded-xl bg-slate-50 px-3 py-3"
              >
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-slate-900">{{ variation.name }}</p>
                  <p class="text-xs text-slate-500">
                    {{ formatCurrency(variation.price_cents) }}  Inclui {{ variation.people_included }} pessoa(s)
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs font-semibold text-slate-500">Quantidade</span>
                  <input
                    type="number"
                    min="0"
                    class="w-24 rounded-full border border-slate-200 px-3 py-1 text-center text-sm"
                    v-model.number="paymentLinkSelections[variation.public_id].quantity"
                    @input="handlePaymentQuantityInput(variation)"
                  />
                </div>
              </div>
              <div
                v-if="hasEnabledChildRules(variation)"
                class="space-y-2 rounded-2xl border border-slate-100 bg-white/80 p-3"
              >
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">crian&ccedil;as</p>
                <div
                  v-for="rule in enabledChildRules(variation)"
                  :key="`${variation.public_id}-${rule.key}`"
                  class="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2"
                >
                  <div>
                    <p class="text-sm font-semibold text-slate-900">{{ describeChildRange(rule) }}</p>
                    <p class="text-[11px] text-slate-500">
                      {{ rule.min_age }}-{{ rule.max_age }} anos 
                      {{ rule.pricing_mode === "free" ? "Gratuito" : `+${formatCurrency(rule.extra_amount_cents)}` }} 
                      {{ rule.counts_towards_capacity ? "Consome vaga" : "No consome vaga" }}
                    </p>
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="grid h-7 w-7 place-items-center rounded-full border border-slate-200 text-sm font-semibold text-slate-700 disabled:opacity-40"
                      @click="adjustPaymentChild(variation, rule.key, -1)"
                      :disabled="(paymentLinkSelections[variation.public_id].children[rule.key] || 0) <= 0"
                    >
                      &minus;
                    </button>
                    <span class="min-w-[2ch] text-center font-semibold text-slate-900">
                      {{ paymentLinkSelections[variation.public_id].children[rule.key] || 0 }}
                    </span>
                    <button
                      type="button"
                      class="grid h-7 w-7 place-items-center rounded-full border border-slate-200 bg-white text-sm font-semibold text-slate-900 disabled:opacity-40"
                      @click="adjustPaymentChild(variation, rule.key, 1)"
                      :disabled="!canIncrementPaymentChild(variation, rule.key)"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
              </div>
            </template>
          </div>
          <div v-if="paymentLinkResult" class="rounded-2xl bg-emerald-50 p-3 text-sm text-emerald-800">
            <p class="font-semibold">Link pronto!</p>
            <p class="break-all">{{ paymentLinkDisplayUrl }}</p>
            <button class="text-xs font-semibold text-emerald-700 underline" @click="copyText(paymentLinkDisplayUrl)">Copiar</button>
          </div>
        </div>
        <footer class="mt-6 flex justify-end gap-3">
          <button class="pill" @click="closePaymentLinkModal">Cancelar</button>
          <button class="btn-primary" :disabled="paymentLinkSaving || !paymentLinkProduct || !paymentLinkItems.length" @click="submitPaymentLink">
            {{ paymentLinkSaving ? 'Gerando...' : 'Gerar link' }}
          </button>
        </footer>
      </div>
    </div>

    <div v-if="deleteModalVisible && deleteTarget" class="modal-overlay !mt-0">
      <div class="modal-card max-w-md">
        <header class="mb-4 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Excluir produto</p>
            <h3 class="text-lg font-semibold text-slate-900">{{ deleteTarget.name }}</h3>
          </div>
          <button class="text-slate-500" @click="closeDeleteModal"></button>
        </header>
        <p class="text-sm text-slate-600">
          Essa ao remover o produto e suas variaes do mdulo Produtos. Vendas j registradas no sero apagadas.
          Deseja continuar?
        </p>
        <footer class="mt-6 flex justify-end gap-3">
          <button class="pill" @click="closeDeleteModal">Cancelar</button>
          <button class="btn-primary bg-rose-500 hover:bg-rose-600 disabled:bg-rose-300" :disabled="deleteLoading" @click="confirmDeleteProduct">
            {{ deleteLoading ? 'Excluindo...' : 'Excluir produto' }}
          </button>
        </footer>
      </div>
    </div>

    <div v-if="saleDetailsVisible && selectedSale" class="modal-overlay !mt-0">
      <div class="modal-card modal-card--sale">
        <header class="mb-4 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Venda #{{ selectedSale.id }}</p>
            <h3 class="text-lg font-semibold text-slate-900">{{ selectedSale.product_title }}</h3>
          </div>
          <button
            class="h-9 w-9 rounded-full border border-slate-200 text-lg font-semibold text-slate-500 transition hover:border-slate-300 hover:text-slate-900"
            type="button"
            aria-label="Fechar detalhes da venda"
            @click="saleDetailsVisible = false"
          >
            &times;
          </button>
        </header>
        <div class="modal-scroll space-y-4 text-sm">
          <div class="flex flex-wrap gap-2 text-xs font-semibold">
            <span :class="['badge', statusClasses.payment[paymentStatusKey(selectedSale.payment_status)]]">
              {{ paymentStatusLabel(selectedSale.payment_status) }}
            </span>
            <span :class="['badge', statusClasses.payout[payoutStatusKey(selectedSale.payout_status)]]">
              {{ payoutStatusLabel(selectedSale.payout_status) }}
            </span>
            <span
              v-if="selectedSale.requires_passengers"
              :class="['badge', statusClasses.passengers[passengerStatusKey(selectedSale.passenger_status)]]"
            >
              {{ passengerStatusLabel(selectedSale.passenger_status) }}
            </span>
          </div>
          <div class="mt-2 flex flex-wrap gap-2 text-[11px] font-semibold text-slate-500">
            <span v-if="selectedSale.is_road_trip" class="badge badge-muted">Excursão rodoviária</span>
            <span v-if="selectedSale.has_rooms" class="badge badge-muted">Hospedagem</span>
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <div class="rounded-2xl border border-slate-100 p-3">
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Cliente</p>
              <p class="mt-1"><span class="font-semibold text-slate-600">Nome:</span> {{ selectedSale.customer_name || "No informado" }}</p>
              <p><span class="font-semibold text-slate-600">E-mail:</span> {{ selectedSale.customer_email || "No informado" }}</p>
              <p><span class="font-semibold text-slate-600">Telefone:</span> {{ selectedSale.customer_phone || "No informado" }}</p>
              <p><span class="font-semibold text-slate-600">Canal:</span> {{ saleChannelLabel(selectedSale.channel) }}</p>
              <p v-if="salePageLabel(selectedSale)"><span class="font-semibold text-slate-600">Pgina:</span> {{ salePageLabel(selectedSale) }}</p>
              <p><span class="font-semibold text-slate-600">Criada em:</span> {{ formatDateTime(selectedSale.created_at) }}</p>
              <p>
                <span class="font-semibold text-slate-600">Passageiros previstos:</span>
                {{ selectedSale.requires_passengers ? selectedSale.passengers_required : "No aplicvel" }}
              </p>
              <p><span class="font-semibold text-slate-600">Ocupao consumida:</span> {{ selectedSale.consumed_capacity }}</p>
            </div>
            <div class="rounded-2xl border border-slate-100 p-3">
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Provedor</p>
              <p class="mt-1"><span class="font-semibold text-slate-600">Gateway:</span> {{ selectedSale.provider }}</p>
              <p><span class="font-semibold text-slate-600">Charge ID:</span> {{ selectedSale.provider_charge_id }}</p>
              <p><span class="font-semibold text-slate-600">Status:</span> {{ paymentStatusLabel(selectedSale.provider_status) }}</p>
              <p><span class="font-semibold text-slate-600">Parcelas:</span> {{ selectedSale.installments }}x de {{ formatCurrency(selectedSale.installment_amount_cents) }}</p>
            </div>
          </div>
          <div class="rounded-2xl border border-slate-100 p-3">
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Resumo financeiro</p>
            <dl class="mt-2 grid gap-3 sm:grid-cols-2">
              <div>
                <dt class="text-xs text-slate-500">Valor base</dt>
                <dd class="text-lg font-semibold text-slate-900">{{ formatCurrency(selectedSale.base_amount_cents) }}</dd>
              </div>
              <div>
                <dt class="text-xs text-slate-500">Valor bruto</dt>
                <dd class="text-lg font-semibold text-slate-900">{{ formatCurrency(selectedSale.gross_amount_cents) }}</dd>
              </div>
              <div>
                <dt class="text-xs text-slate-500">Taxa plataforma</dt>
                <dd class="text-lg font-semibold text-slate-900">{{ formatCurrency(selectedSale.platform_fee_amount_cents) }}</dd>
              </div>
              <div>
                <dt class="text-xs text-slate-500">Taxa gateway</dt>
                <dd class="text-lg font-semibold text-slate-900">{{ formatCurrency(selectedSale.gateway_fee_estimated_cents) }}</dd>
              </div>
              <div>
                <dt class="text-xs text-slate-500">Repasse agncia</dt>
                <dd class="text-lg font-semibold text-slate-900">{{ formatCurrency(selectedSale.agency_net_amount_cents) }}</dd>
              </div>
              <div>
                <dt class="text-xs text-slate-500">Parcelamento</dt>
                <dd class="text-lg font-semibold text-slate-900">
                  {{ selectedSale.installments }}x de {{ formatCurrency(selectedSale.installment_amount_cents) }}
                </dd>
              </div>
            </dl>
            <p class="mt-2 text-xs text-slate-500">Spread estimado: {{ formatPercent(selectedSale.spread_percentage) }}</p>
          </div>
          <div class="rounded-2xl border border-slate-100 p-3">
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Simular status</p>
            <div class="mt-2 flex flex-wrap gap-3">
              <select v-model="simulationStatus" class="input w-full max-w-xs">
                <option v-for="option in saleStatusOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <button class="btn-primary" :disabled="simulatingStatus" @click="applySimulatedStatus">
                {{ simulatingStatus ? 'Aplicando...' : 'Aplicar' }}
              </button>
            </div>
            <p class="mt-2 text-xs text-slate-500">Use para testar o fluxo de webhook simulado.</p>
          </div>
          <div class="pb-2">
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Itens</p>
            <ul class="mt-2 space-y-2">
              <li v-for="item in selectedSale.items" :key="item.id" class="rounded-xl border border-slate-100 p-3 text-sm">
                <p class="font-semibold text-slate-900">{{ item.variation_name }}</p>
                <p class="text-slate-500">
                  {{ item.quantity }} x {{ formatCurrency(item.unit_price) }} = {{ formatCurrency(item.total_price) }}
                </p>
                <p class="text-xs text-slate-500">
                  Passageiros: {{ item.people_count }}  Ocupao: {{ item.consumed_capacity }}
                </p>
                <ul v-if="item.child_breakdown.length" class="mt-1 text-[11px] text-slate-500">
                  <li v-for="child in item.child_breakdown" :key="child.key">
                    {{ child.quantity }}x {{ child.label }}  +{{ formatCurrency(child.total_amount_cents) }}
                  </li>
                </ul>
                <p class="text-xs text-slate-500 mt-1">Status: {{ item.status }}</p>
              </li>
            </ul>
          </div>
          <div
            v-if="!selectedSale.requires_passengers"
            class="rounded-2xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-600"
          >
            Este produto não exige lista de passageiros. Nenhuma ação pós-venda é necessária.
          </div>
        </div>
      </div>
    </div>


    <div v-if="passengerModalVisible && passengerSale" class="modal-overlay !mt-0">
      <div class="modal-card modal-card--passengers max-w-4xl">
        <header class="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 px-6 py-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              Passageiros venda #{{ passengerSale.id }}
            </p>
            <h3 class="text-xl font-semibold text-slate-900">{{ passengerSale.product_title }}</h3>
            <div class="mt-2 flex flex-wrap gap-2 text-xs font-semibold">
              <span :class="['badge', statusClasses.payment[paymentStatusKey(passengerSale.payment_status)]]">
                {{ paymentStatusLabel(passengerSale.payment_status) }}
              </span>
              <span :class="['badge', statusClasses.payout[payoutStatusKey(passengerSale.payout_status)]]">
                {{ payoutStatusLabel(passengerSale.payout_status) }}
              </span>
              <span :class="['badge', statusClasses.passengers[passengerStatusKey(passengerSale.passenger_status)]]">
                {{ passengerStatusLabel(passengerSale.passenger_status) }}
              </span>
            </div>
          </div>
          <button class="pill" @click="closePassengerModal">Fechar</button>
        </header>
        <div class="modal-scroll space-y-6 p-6">
          <section class="rounded-3xl border border-slate-100 bg-slate-50/60 p-4 shadow-inner">
            <div class="grid gap-4 text-sm md:grid-cols-2">
              <div class="space-y-2">
                <div>
                  <p class="text-xs uppercase tracking-wide text-slate-400">Descri&ccedil;&atilde;o do produto</p>
                  <p class="text-base font-semibold text-slate-900">
                    {{ passengerSale.product_description || "Sem descrição" }}
                  </p>
                </div>
                <div>
                  <p class="text-xs uppercase tracking-wide text-slate-400">Cliente</p>
                  <p class="text-base font-semibold text-slate-900">{{ passengerSale.customer_name || "No informado" }}</p>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <p class="text-xs uppercase tracking-wide text-slate-400">Passageiros previstos</p>
                    <p class="text-base font-semibold text-slate-900">{{ passengerSale.passengers_required }}</p>
                  </div>
                  <div>
                    <p class="text-xs uppercase tracking-wide text-slate-400">Canal</p>
                    <p class="text-base font-semibold text-slate-900">{{ saleChannelLabel(passengerSale.channel) }}</p>
                  </div>
                </div>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide text-slate-400">Pacotes e variaes</p>
                <ul class="mt-2 space-y-1 text-slate-600">
                  <li
                    v-for="item in passengerSale.items"
                    :key="item.id"
                    class="rounded-xl border border-slate-100 bg-white px-3 py-2 text-sm"
                  >
                    <p class="font-semibold text-slate-900">{{ item.variation_name }}</p>
                    <p>
                      {{ item.quantity }} x {{ formatCurrency(item.unit_price) }}
                      <span class="text-xs text-slate-500">
                        ({{ item.people_count * item.quantity }} passageiros)
                      </span>
                    </p>
                  </li>
                  <li v-if="!passengerSale.items.length" class="text-xs text-slate-500">Nenhum item associado.</li>
                </ul>
              </div>
            </div>
          </section>

          <section class="rounded-3xl border border-slate-100 p-4 shadow-sm">
            <div class="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Grupos de passageiros</p>
                <p class="text-sm text-slate-500">
                  Cada unidade do pacote gera um grupo independente. Preencha cada passageiro dentro do seu grupo.
                </p>
              </div>
              <div class="flex flex-wrap gap-2">
                <button
                  class="pill"
                  type="button"
                  :disabled="!passengerSale || !passengerSale.requires_passengers || passengerSale.payment_status !== 'paid'"
                  @click="passengerSale && copyPassengerLink(passengerSale.id)"
                >
                  Enviar link
                </button>
                <button
                  class="pill"
                  type="button"
                  :disabled="passengerGroupsLoading || !passengerSale"
                  @click="passengerSale && refreshPassengerGroups()"
                >
                  Atualizar grupos
                </button>
              </div>
            </div>

            <div v-if="passengerGroupsLoading" class="flex items-center justify-center p-6 text-sm text-slate-500">
              Carregando grupos...
            </div>
            <template v-else>
              <div v-if="passengerGroupForms.length" class="space-y-4 pt-4">
                <div class="flex gap-2 overflow-x-auto pb-2">
                  <button
                    v-for="(group, index) in passengerGroupForms"
                    :key="group.id"
                    type="button"
                    class="group-chip"
                    :class="index === activePassengerGroupIndex ? 'group-chip-active' : ''"
                    @click="selectPassengerGroup(index)"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div>
                        <p class="text-sm font-semibold text-slate-900">{{ group.label }}</p>
                        <p class="text-xs text-slate-500">
                          {{ group.occupied_slots }} / {{ group.capacity }} preenchidos
                        </p>
                      </div>
                      
                    </div>
                  </button>
                </div>

                <div v-if="activePassengerGroup" class="space-y-4 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                  <div class="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p class="text-xs uppercase tracking-wide text-slate-400">Resumo do grupo</p>
                      <p class="text-sm font-semibold text-slate-900">{{ activePassengerGroup.product_name }}</p>
                      <p class="text-xs text-slate-500">
                        Passageiros previstos: {{ activePassengerGroup.passengers.length }}
                      </p>
                    </div>
                    <div class="rounded-full bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-600">
                      {{ activePassengerGroup.occupied_slots }} / {{ activePassengerGroup.capacity }} ocupados
                    </div>
                  </div>

                  <div class="flex flex-wrap gap-2 overflow-x-auto border-b border-slate-100 pb-3">
                    <button
                      v-for="(passenger, index) in activePassengerGroup.passengers"
                      :key="`passenger-slot-${passenger.passenger_index}`"
                      type="button"
                      class="passenger-chip flex flex-col items-center text-center"
                      :class="[
                        passengerChipState(passengerSlotState(passenger)),
                        index === activePassengerIndex ? 'passenger-chip-active' : '',
                      ]"
                      @click="selectPassengerSlot(index)"
                    >
                      <span>Passageiro {{ passenger.passenger_index }}</span>
                      <span class="text-[10px] uppercase tracking-wide">
                        {{ passengerSlotLabel(passengerSlotState(passenger)) }}
                      </span>
                    </button>
                  </div>

                  <div v-if="activePassenger" class="space-y-4">
                    <div class="grid gap-3 md:grid-cols-2">
                      <div>
                        <label class="input-label">Tipo</label>
                        <select v-model="activePassenger.type" class="input mt-1" :disabled="!canManagePassengers">
                          <option value="adult">Adulto</option>
                          <option value="child_paid">crian&ccedil;a paga</option>
                          <option value="child_free">crian&ccedil;a gratuita</option>
                        </select>
                      </div>
                      <div class="md:col-span-2">
                        <label class="input-label">Nome completo</label>
                        <input
                          v-model="activePassenger.name"
                          class="input mt-1"
                          placeholder="Nome completo"
                          :disabled="!canManagePassengers"
                        />
                      </div>
                      <div>
                        <label class="input-label">CPF</label>
                        <input
                          v-model="activePassenger.cpf"
                          class="input mt-1"
                          placeholder="000.000.000-00"
                          :disabled="!canManagePassengers"
                        />
                      </div>
                      <div>
                        <label class="input-label">Nascimento</label>
                        <input
                          v-model="activePassenger.birthdate"
                          type="date"
                          class="input mt-1"
                          :disabled="!canManagePassengers"
                        />
                      </div>
                      <div>
                        <label class="input-label">Telefone</label>
                        <input
                          v-model="activePassenger.phone"
                          class="input mt-1"
                          placeholder="(00) 00000-0000"
                          :disabled="!canManagePassengers"
                        />
                      </div>
                      <div>
                        <label class="input-label">WhatsApp</label>
                        <input
                          v-model="activePassenger.whatsapp"
                          class="input mt-1"
                          placeholder="(00) 00000-0000"
                          :disabled="!canManagePassengers"
                        />
                      </div>
                      <div class="md:col-span-2">
                        <label class="input-label">Local de embarque</label>
                        <select
                          v-model="activePassenger.boarding_location"
                          class="input mt-1"
                          :disabled="!canManagePassengers"
                        >
                          <option value="">No definir</option>
                          <option v-for="location in passengerBoardingOptions" :key="location" :value="location">
                            {{ location }}
                          </option>
                        </select>
                        <p v-if="!passengerBoardingOptions.length" class="mt-1 text-xs text-slate-500">
                          Nenhum local cadastrado para este produto.
                        </p>
                      </div>
                    </div>
                    <div>
                      <label class="input-label">Observaes</label>
                      <textarea
                        v-model="activePassenger.extras"
                        rows="3"
                        class="input mt-1"
                        placeholder="Informaes importantes"
                        :disabled="!canManagePassengers"
                      ></textarea>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
                Nenhum grupo de passageiros disponível para esta venda.
              </div>
            </template>
          </section>
        </div>
        <footer class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-6 py-4">
          <p class="text-xs text-slate-500">
            Status geral:
            <span class="font-semibold text-slate-900">{{ passengerStatusLabel(passengerSale.passenger_status) }}</span>
          </p>
          <div class="flex flex-wrap gap-2">
            <button class="pill" type="button" @click="closePassengerModal">Cancelar</button>
            <button
              class="pill"
              type="button"
              :disabled="passengerSaving || !canManagePassengers || !activePassengerGroup"
              @click="saveCurrentGroup"
            >
              {{ passengerSaving ? "Salvando..." : "Salvar grupo" }}
            </button>
            <button
              class="pill"
              type="button"
              :disabled="passengerSaving || !canManagePassengers || !activePassengerGroup"
              @click="saveGroupAndNext"
            >
              Salvar e prximo
            </button>
            <button
              class="btn-primary"
              type="button"
              :disabled="passengerSaving || !allPassengerGroupsComplete"
              @click="finalizePassengerModal"
            >
              Finalizar passageiros
            </button>
          </div>
        </footer>
      </div>
    </div>

  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch, watchEffect } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  listSales,
  getSaleDetails,
  getPassengerLink,
  getSalePassengerGroups,
  savePassengerGroupPassengers,
  listProducts,
  rebuildProductInventory,
  getProductDetail,
  createProduct,
  updateProduct,
  updateProductBoardingLocations,
  adjustProductInventory,
  createPosCheckout,
  createProductPaymentLink,
  deleteProduct,
  simulateSaleStatus,
  getBlimbooSettings,
  saveBlimbooSettings,
} from "../../services/finance";
import { listLegalTemplates } from "../../services/legal";
import { calculatePackageComposition, emptyChildSelection, sanitizeChildSelection } from "../../utils/packagePricing";
import { resolveMediaUrl } from "../../utils/media";
import type {
  CheckoutChildSelection,
  ChildPricingRule,
  ChildPricingRulePayload,
  CheckoutCartItem,
  InventoryAdjustmentPayload,
  Passenger,
  PassengerGroup,
  PassengerGroupListResponse,
  PassengerGroupSavePayload,
  PassengerType,
  PaymentLinkResponse,
  PublicCheckoutResponse,
  ProductDetail,
  ProductPayload,
  ProductSummary,
  SaleDetail,
  SaleSummary,
  SalePaymentStatus,
  AgencyBlimbooSettings,
  AgencyBlimbooSettingsPayload,
} from "../../types/finance";
import type { LegalTemplateSummary } from "../../types/legal";

type ActiveTab = "products" | "sales";
type SalesTab = "overview" | "settings";
type CardInterestMode = "merchant" | "customer";

type ChildPricingRuleForm = {
  key: "under_5" | "age_5_12";
  label: string;
  min_age: number;
  max_age: number;
  enabled: boolean;
  pricing_mode: "free" | "extra";
  extra_amount: number;
  counts_towards_capacity: boolean;
  counts_as_passenger: boolean;
  max_quantity: number | null;
};

type ProductVariationForm = {
  public_id: string | null;
  name: string;
  description: string | null;
  price: number;
  people_included: number;
  status: string;
  stock_mode: string;
  has_accommodation: boolean;
  accommodation_mode: "private" | "shared";
  room_capacity: number;
  slots_per_unit: number;
  total_slots: number | null;
  available_slots: number | null;
  child_policy_enabled: boolean;
  child_pricing_rules: ChildPricingRuleForm[];
};

type PassengerFormState = {
  id?: number | null;
  passenger_group_id?: number | null;
  passenger_index: number;
  type: PassengerType;
  name: string;
  cpf?: string | null;
  birthdate?: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  boarding_location?: string | null;
  extras?: string | null;
};

type PassengerGroupFormState = PassengerGroup & {
  passengers: PassengerFormState[];
};

type ProductFormState = {
  name: string;
  description: string | null;
  status: string;
  trip_date: string | null;
  date_is_flexible: boolean;
  inventory_strategy: "manual" | "unlimited";
  total_slots: number;
  available_slots: number;
  allow_oversell: boolean;
  card_interest_mode: CardInterestMode;
  template_contract_id: number | null;
  checkout_banner_url: string | null;
  checkout_product_image_url: string | null;
  variations: ProductVariationForm[];
  boarding_locations: string[];
  is_road_trip: boolean;
  allowed_payment_methods: Array<"pix" | "credit_card" | "boleto">;
};

type PackageSelectionState = {
  quantity: number;
  children: Record<string, number>;
};

const CHILD_RULE_KEYS: ChildPricingRuleForm["key"][] = ["under_5", "age_5_12"];

const defaultChildRules = (): ChildPricingRuleForm[] => [
  {
    key: "under_5",
    label: "Menores de 5 anos",
    min_age: 0,
    max_age: 4,
    enabled: false,
    pricing_mode: "free",
    extra_amount: 0,
    counts_towards_capacity: false,
    counts_as_passenger: true,
    max_quantity: null,
  },
  {
    key: "age_5_12",
    label: "De 5 a 12 anos",
    min_age: 5,
    max_age: 12,
    enabled: false,
    pricing_mode: "extra",
    extra_amount: 0,
    counts_towards_capacity: true,
    counts_as_passenger: true,
    max_quantity: null,
  },
];

type ChildRuleLike = { min_age: number; max_age: number; label?: string | null };

const describeChildRange = (rule: ChildRuleLike): string => {
  const min = Math.max(0, rule.min_age ?? 0);
  const max = Math.max(min, rule.max_age ?? min);
  if (min === 0) {
    return `At ${max} anos`;
  }
  if (min === max) {
    return `${min} anos`;
  }
  return `De ${min} a ${max} anos`;
};

const childRuleSubtitle = (rule: ChildRuleLike): string => `${rule.min_age} a ${rule.max_age} anos`;

const sanitizeRuleAges = (rule: ChildPricingRuleForm) => {
  rule.min_age = Math.max(0, Math.floor(rule.min_age ?? 0));
  rule.max_age = Math.max(rule.min_age, Math.floor(rule.max_age ?? 0));
};

const toRuleForm = (rule?: ChildPricingRule): ChildPricingRuleForm => {
  if (!rule) {
    return { ...defaultChildRules()[0] };
  }
  const form: ChildPricingRuleForm = {
    key: (rule.key as ChildPricingRuleForm["key"]) || "under_5",
    label: rule.label || "",
    min_age: rule.min_age ?? 0,
    max_age: rule.max_age ?? 0,
    enabled: !!rule.enabled,
    pricing_mode: rule.pricing_mode === "extra" ? "extra" : "free",
    extra_amount: Math.max(0, (rule.extra_amount_cents || 0) / 100),
    counts_towards_capacity: !!rule.counts_towards_capacity,
    counts_as_passenger: rule.counts_as_passenger ?? true,
    max_quantity: typeof rule.max_quantity === "number" ? Math.max(0, rule.max_quantity) : null,
  };
  sanitizeRuleAges(form);
  return form;
};

const resolveRuleForms = (rules?: ChildPricingRule[]): ChildPricingRuleForm[] => {
  const map = new Map<string, ChildPricingRule>();
  (rules || []).forEach(rule => map.set(rule.key, rule));
  return CHILD_RULE_KEYS.map(key => {
    const base = defaultChildRules().find(rule => rule.key === key);
    return toRuleForm(map.get(key) || base);
  });
};

const serializeRuleForm = (rule: ChildPricingRuleForm): ChildPricingRulePayload => {
  sanitizeRuleAges(rule);
  return {
    key: rule.key,
    label: describeChildRange(rule),
    min_age: rule.min_age,
    max_age: rule.max_age,
    enabled: rule.enabled,
    pricing_mode: rule.pricing_mode,
    extra_amount_cents: rule.pricing_mode === "extra" ? Math.round(Math.max(rule.extra_amount, 0) * 100) : 0,
    counts_towards_capacity: rule.counts_towards_capacity,
    counts_as_passenger: rule.counts_as_passenger,
    max_quantity: typeof rule.max_quantity === "number" ? Math.max(0, rule.max_quantity) : null,
  };
};

const route = useRoute();
const activeTab = ref<ActiveTab>("products");
watch(
  () => route.name,
  name => {
    activeTab.value = name === "sales" ? "sales" : "products";
  },
  { immediate: true },
);
const salesTab = ref<SalesTab>("overview");
const sales = ref<SaleSummary[]>([]);
const salesPagination = ref({ total: 0, page: 1, pageSize: 20 });
const selectedSale = ref<SaleDetail | null>(null);
const saleDetailsVisible = ref(false);

const findSaleSummary = (saleId: number) => sales.value.find(sale => sale.id === saleId) || null;
const saleRequiresPassengers = (saleId: number) => {
  const summary = findSaleSummary(saleId);
  if (summary) return !!summary.requires_passengers;
  if (selectedSale.value && selectedSale.value.id === saleId) {
    return !!selectedSale.value.requires_passengers;
  }
  return true;
};

const blimbooState = reactive({ token: "", hasToken: false, updatedAt: "" });
const blimbooLoading = ref(false);
const blimbooSaving = ref(false);
const blimbooFeedback = ref<{ type: "success" | "error"; message: string } | null>(null);
const blimbooUpdatedLabel = computed(() => {
  if (!blimbooState.updatedAt) return "";
  try {
    return new Date(blimbooState.updatedAt).toLocaleString("pt-BR");
  } catch (_err) {
    return "";
  }
});

type PaymentFilter = "all" | SalePaymentStatus;
type PassengerFilter = "all" | "not_started" | "partial" | "completed";
type ChannelFilter = "all" | "pos" | "checkout";

const paymentFilterOptions: { label: string; value: PaymentFilter }[] = [
  { label: "Todos", value: "all" },
  { label: "Pagos", value: "paid" },
  { label: "Processando", value: "processing" },
  { label: "Pendentes", value: "pending" },
  { label: "Cancelados", value: "canceled" },
  { label: "Reembolsados", value: "refunded" },
];

const passengerFilterOptions: { label: string; value: PassengerFilter }[] = [
  { label: "Todos", value: "all" },
  { label: "Sem passageiros", value: "not_started" },
  { label: "Parcial", value: "partial" },
  { label: "Completos", value: "completed" },
];
const channelFilterOptions: { label: string; value: ChannelFilter }[] = [
  { label: "Todos", value: "all" },
  { label: "PDV", value: "pos" },
  { label: "Checkout", value: "checkout" },
];

const paymentFilter = ref<PaymentFilter>("all");
const passengerFilter = ref<PassengerFilter>("all");
const channelFilter = ref<ChannelFilter>("all");
const channelFilterKey = (channel: string): ChannelFilter => (channel === "pos" ? "pos" : "checkout");

const filteredSales = computed(() =>
  sales.value.filter(s => {
    const paymentMatch = paymentFilter.value === "all" || s.payment_status === paymentFilter.value;
    const passengerMatch = passengerFilter.value === "all" || s.passenger_status === passengerFilter.value;
    const channelMatch = channelFilter.value === "all" || channelFilter.value === channelFilterKey(s.channel);
    return paymentMatch && passengerMatch && channelMatch;
  }),
);

const passengerSale = ref<SaleDetail | null>(null);
const passengerModalVisible = ref(false);
const passengerGroupForms = ref<PassengerGroupFormState[]>([]);
const passengerGroupsLoading = ref(false);
const passengerSaving = ref(false);
const activePassengerGroupIndex = ref(0);
const activePassengerIndex = ref(0);
const canManagePassengers = computed(
  () => !!passengerSale.value?.requires_passengers && passengerSale.value.payment_status === "paid",
);
const allPassengerGroupsComplete = computed(
  () => passengerGroupForms.value.length > 0 && passengerGroupForms.value.every(group => group.status === "complete"),
);
const activePassengerGroup = computed(() => passengerGroupForms.value[activePassengerGroupIndex.value] || null);
const activePassenger = computed(() => activePassengerGroup.value?.passengers[activePassengerIndex.value] || null);
const passengerBoardingOptions = ref<string[]>([]);

const boardingLocationsModalVisible = ref(false);
const boardingLocationsForm = ref<string[]>([""]);
const boardingLocationsLoading = ref(false);
const boardingLocationsSaving = ref(false);

const passengerSlotHasData = (passenger?: PassengerFormState | null) => {
  if (!passenger) return false;
  return Boolean(
    passenger.name?.trim() ||
      passenger.cpf?.trim() ||
      passenger.phone?.trim() ||
      passenger.whatsapp?.trim() ||
      passenger.boarding_location?.trim() ||
      passenger.extras?.trim(),
  );
};

const passengerSlotState = (passenger?: PassengerFormState | null): "empty" | "partial" | "complete" => {
  if (!passengerSlotHasData(passenger)) return "empty";
  if (passenger?.name && passenger?.cpf) return "complete";
  return "partial";
};

const passengerSlotLabel = (state: "empty" | "partial" | "complete") => {
  if (state === "complete") return "Completo";
  if (state === "partial") return "Incompleto";
  return "Livre";
};

const passengerChipState = (state: "empty" | "partial" | "complete") => {
  if (state === "complete") return "passenger-chip-complete";
  if (state === "partial") return "passenger-chip-partial";
  return "passenger-chip-empty";
};

const createPassengerSlot = (
  groupId: number,
  slotIndex: number,
  passenger?: Passenger,
  defaultType: PassengerType = "adult",
): PassengerFormState => ({
  id: passenger?.id ?? undefined,
  passenger_group_id: groupId,
  passenger_index: slotIndex,
  type: (passenger?.type as PassengerType) || defaultType,
  name: passenger?.name || "",
  cpf: passenger?.cpf || "",
  birthdate: passenger?.birthdate || "",
  phone: passenger?.phone || "",
  whatsapp: passenger?.whatsapp || "",
  boarding_location: passenger?.boarding_location || "",
  extras: passenger?.extras || "",
});

const normalizePassengerGroup = (group: PassengerGroup): PassengerGroupFormState => {
  const slotTypes =
    (group.slot_types && group.slot_types.length ? group.slot_types : Array.from({ length: group.capacity }, () => "adult")) as PassengerType[];
  const passengers: PassengerFormState[] = slotTypes.map((slotType, idx) => {
    const existing = (group.passengers || []).find(entry => entry.passenger_index === idx + 1);
    return createPassengerSlot(group.id, idx + 1, existing, slotType);
  });
  return { ...group, passengers, slot_types: slotTypes };
};

const selectPassengerGroup = (index: number) => {
  if (index < 0 || index >= passengerGroupForms.value.length) return;
  activePassengerGroupIndex.value = index;
  const group = passengerGroupForms.value[index];
  const targetIndex = group.passengers.findIndex(passenger => passengerSlotState(passenger) !== "complete");
  activePassengerIndex.value = targetIndex >= 0 ? targetIndex : 0;
};

const selectPassengerSlot = (index: number) => {
  const group = activePassengerGroup.value;
  if (!group) return;
  if (index < 0 || index >= group.passengers.length) return;
  activePassengerIndex.value = index;
};

const applyPassengerGroupResponse = (response: PassengerGroupListResponse) => {
  passengerGroupForms.value = response.groups.map(normalizePassengerGroup);
  if (passengerSale.value) {
    passengerSale.value.passenger_status = response.passenger_status;
    passengerSale.value.passengers_required = response.passengers_required;
  }
  if (passengerGroupForms.value.length) {
    const nextGroupIndex = passengerGroupForms.value.findIndex(group => group.status !== "complete");
    selectPassengerGroup(nextGroupIndex >= 0 ? nextGroupIndex : 0);
  } else {
    activePassengerGroupIndex.value = 0;
    activePassengerIndex.value = 0;
  }
};

const refreshPassengerGroups = async () => {
  if (!passengerSale.value) return;
  passengerGroupsLoading.value = true;
  try {
    const { data } = await getSalePassengerGroups(passengerSale.value.id);
    applyPassengerGroupResponse(data);
  } catch (err) {
    console.error("Erro ao carregar grupos de passageiros", err);
  } finally {
    passengerGroupsLoading.value = false;
  }
};

const buildGroupPayload = (group: PassengerGroupFormState): PassengerGroupSavePayload => ({
  passengers: group.passengers
    .filter(passengerSlotHasData)
    .map(passenger => ({
      passenger_index: passenger.passenger_index,
      type: passenger.type,
      name: passenger.name,
      cpf: passenger.cpf || "",
      birthdate: passenger.birthdate || null,
      phone: passenger.phone || "",
      whatsapp: passenger.whatsapp || "",
      boarding_location: passenger.boarding_location || "",
      extras: passenger.extras || "",
    })),
});

const saveCurrentGroup = async () => {
  if (!passengerSale.value || !activePassengerGroup.value) return;
  passengerSaving.value = true;
  try {
    const payload = buildGroupPayload(activePassengerGroup.value);
    await savePassengerGroupPassengers(activePassengerGroup.value.id, payload);
    await refreshPassengerGroups();
    await loadSales();
  } catch (err) {
    console.error("Erro ao salvar passageiros do grupo", err);
  } finally {
    passengerSaving.value = false;
  }
};

const saveGroupAndNext = async () => {
  await saveCurrentGroup();
  if (!passengerGroupForms.value.length) return;
  const nextIndex = (activePassengerGroupIndex.value + 1) % passengerGroupForms.value.length;
  selectPassengerGroup(nextIndex);
};

const finalizePassengerModal = () => {
  closePassengerModal();
};

const products = ref<ProductSummary[]>([]);
const productsLoading = ref(false);
const inventoryRebuildLoading = ref(false);
const productSearch = ref("");
const productStatusFilter = ref<"all" | "active" | "draft" | "inactive">("all");
const productSort = ref<"date-desc" | "date-asc" | "name-asc" | "available-desc">("date-desc");
const contractTemplates = ref<LegalTemplateSummary[]>([]);
const contractTemplatesLoading = ref(false);

const productStatusOptions = [
  { label: "Todos os status", value: "all" },
  { label: "Ativos", value: "active" },
  { label: "Rascunhos", value: "draft" },
  { label: "Inativos", value: "inactive" },
] as const;

const productSortOptions = [
  { label: "Mais recentes", value: "date-desc" },
  { label: "Data mais antiga", value: "date-asc" },
  { label: "Nome A-Z", value: "name-asc" },
  { label: "Mais disponibilidade", value: "available-desc" },
] as const;

const productModalVisible = ref(false);
const productSaving = ref(false);
const editingProductId = ref<string | null>(null);

const defaultVariation = (): ProductVariationForm => ({
  public_id: null,
  name: "",
  description: null,
  price: 0,
  people_included: 1,
  status: "active",
  stock_mode: "shared",
  has_accommodation: false,
  accommodation_mode: "private",
  room_capacity: 2,
  slots_per_unit: 2,
  total_slots: null,
  available_slots: null,
  child_policy_enabled: false,
  child_pricing_rules: defaultChildRules(),
});

const clampPositiveInt = (value: number | null | undefined, fallback = 1) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  const normalized = Math.floor(numeric);
  return normalized >= 1 ? normalized : fallback;
};

const sanitizeRoomCapacity = (variation: ProductVariationForm) => {
  variation.room_capacity = clampPositiveInt(variation.room_capacity, 1);
  if (variation.accommodation_mode === "private") {
    variation.slots_per_unit = variation.room_capacity;
    return;
  }
  variation.slots_per_unit = Math.min(clampPositiveInt(variation.slots_per_unit, 1), variation.room_capacity);
};

const sanitizeSlotsPerUnit = (variation: ProductVariationForm) => {
  if (variation.accommodation_mode === "private") {
    variation.slots_per_unit = variation.room_capacity;
    return;
  }
  variation.slots_per_unit = Math.min(clampPositiveInt(variation.slots_per_unit, 1), variation.room_capacity);
};

const handleAccommodationModeChange = (variation: ProductVariationForm) => {
  if (variation.accommodation_mode === "private") {
    variation.slots_per_unit = variation.room_capacity || 1;
  } else {
    variation.slots_per_unit = Math.min(
      clampPositiveInt(variation.slots_per_unit, 1),
      clampPositiveInt(variation.room_capacity, 1),
    );
  }
};

const resetAccommodationFields = (variation: ProductVariationForm) => {
  variation.accommodation_mode = "private";
  variation.room_capacity = 1;
  variation.slots_per_unit = 1;
};

const ensureAccommodationDefaults = (variation: ProductVariationForm) => {
  sanitizeRoomCapacity(variation);
  sanitizeSlotsPerUnit(variation);
};

const handleHasAccommodationToggle = (variation: ProductVariationForm) => {
  if (!variation.has_accommodation) {
    resetAccommodationFields(variation);
    return;
  }
  if (!variation.accommodation_mode) {
    variation.accommodation_mode = "private";
  }
  ensureAccommodationDefaults(variation);
};

const productVariations = (product?: ProductSummary | null): ProductVariation[] => {
  if (!product) return [];
  return Array.isArray(product.variations) ? product.variations : [];
};

const createSelectionState = (variation: ProductVariation): PackageSelectionState => ({
  quantity: 0,
  children: emptyChildSelection(variation),
});

const syncSelectionChildren = (selection: PackageSelectionState, variation: ProductVariation) => {
  const sanitized = sanitizeChildSelection(variation, selection.quantity, selection.children);
  Object.keys(selection.children).forEach(key => delete selection.children[key]);
  Object.entries(sanitized).forEach(([key, value]) => {
    selection.children[key] = value;
  });
};

const ensureSelectionState = (
  selections: Record<string, PackageSelectionState>,
  variation: ProductVariation,
): PackageSelectionState => {
  if (!selections[variation.public_id]) {
    selections[variation.public_id] = createSelectionState(variation);
  }
  return selections[variation.public_id];
};

const selectionChildrenPayload = (selection: PackageSelectionState): CheckoutChildSelection[] =>
  Object.entries(selection.children)
    .filter(([, quantity]) => quantity && quantity > 0)
    .map(([key, quantity]) => ({ key, quantity }));

const updateSelectionQuantityFor = (
  selections: Record<string, PackageSelectionState>,
  variation: ProductVariation,
) => {
  const selection = ensureSelectionState(selections, variation);
  selection.quantity = Math.max(0, Math.floor(selection.quantity || 0));
  syncSelectionChildren(selection, variation);
};

const adjustSelectionChild = (
  selections: Record<string, PackageSelectionState>,
  variation: ProductVariation,
  ruleKey: string,
  delta: number,
) => {
  const selection = ensureSelectionState(selections, variation);
  const current = selection.children[ruleKey] || 0;
  selection.children[ruleKey] = Math.max(0, current + delta);
  syncSelectionChildren(selection, variation);
};

const selectionChildCount = (selection: PackageSelectionState, key: string) => selection.children[key] || 0;

const ruleMaxForSelection = (variation: ProductVariation, selection: PackageSelectionState, key: string) => {
  const rules = variation.child_pricing_rules || [];
  const rule = rules.find(r => r.key === key);
  if (!rule || !rule.enabled) return 0;
  if (!selection.quantity) return 0;
  if (rule.max_quantity === null || typeof rule.max_quantity === "undefined") {
    return Number.POSITIVE_INFINITY;
  }
  return Math.max(0, rule.max_quantity) * selection.quantity;
};

const canIncrementChild = (variation: ProductVariation, selection: PackageSelectionState, key: string) => {
  const limit = ruleMaxForSelection(variation, selection, key);
  if (!Number.isFinite(limit)) return true;
  return selectionChildCount(selection, key) < limit;
};

const productForm = reactive<ProductFormState>({
  name: "",
  description: null,
  status: "draft",
  trip_date: null,
  date_is_flexible: false,
  inventory_strategy: "manual",
  total_slots: 0,
  available_slots: 0,
  allow_oversell: false,
  card_interest_mode: "merchant",
  template_contract_id: null,
  checkout_banner_url: null,
  checkout_product_image_url: null,
  variations: [defaultVariation()],
  boarding_locations: [],
  is_road_trip: false,
  allowed_payment_methods: ["pix", "credit_card", "boleto"],
});

const childPolicyCollapseState = reactive<Record<string, boolean>>({});
const accommodationCollapseState = reactive<Record<string, boolean>>({});
const variationCollapseKey = (variation: ProductVariationForm, index: number) => variation.public_id ?? `new-${index}`;
const isChildPolicyCollapsed = (variation: ProductVariationForm, index: number) =>
  !!childPolicyCollapseState[variationCollapseKey(variation, index)];
const toggleChildPolicyCollapse = (variation: ProductVariationForm, index: number) => {
  const key = variationCollapseKey(variation, index);
  childPolicyCollapseState[key] = !childPolicyCollapseState[key];
};
const isAccommodationCollapsed = (variation: ProductVariationForm, index: number) =>
  !!accommodationCollapseState[variationCollapseKey(variation, index)];
const toggleAccommodationCollapse = (variation: ProductVariationForm, index: number) => {
  const key = variationCollapseKey(variation, index);
  accommodationCollapseState[key] = !accommodationCollapseState[key];
};

const syncCollapseState = (state: Record<string, boolean>) => {
  const keys = productForm.variations.map((variation, index) => variationCollapseKey(variation, index));
  const active = new Set(keys);
  keys.forEach(key => {
    if (!(key in state)) {
      state[key] = false;
    }
  });
  Object.keys(state).forEach(key => {
    if (!active.has(key)) {
      delete state[key];
    }
  });
};

watchEffect(() => {
  syncCollapseState(childPolicyCollapseState);
  syncCollapseState(accommodationCollapseState);
});

const inventoryModalVisible = ref(false);
const inventoryProduct = ref<ProductSummary | null>(null);
const inventoryForm = reactive<InventoryAdjustmentPayload>({
  total_slots: 0,
  available_slots: 0,
  note: "",
});
const inventorySaving = ref(false);

const posModalVisible = ref(false);
const posProduct = ref<ProductSummary | null>(null);
const posProductId = ref<string>("");
const posCustomer = reactive({ name: "", email: "", phone: "" });
const posSelections = reactive<Record<string, PackageSelectionState>>({});
const posSaving = ref(false);
const posResult = ref<PublicCheckoutResponse | null>(null);

const paymentLinkModalVisible = ref(false);
const paymentLinkProduct = ref<ProductSummary | null>(null);
const paymentLinkProductId = ref<string>("");
const paymentLinkCustomer = reactive({ name: "", email: "", phone: "" });
const paymentLinkSelections = reactive<Record<string, PackageSelectionState>>({});
const paymentLinkExpires = ref(60);
const paymentLinkSaving = ref(false);
const paymentLinkResult = ref<PaymentLinkResponse | null>(null);

const deleteModalVisible = ref(false);
const deleteTarget = ref<ProductSummary | null>(null);
const deleteLoading = ref(false);

const saleStatusOptions: { label: string; value: SalePaymentStatus }[] = [
  { label: "Pendente", value: "pending" },
  { label: "Processando", value: "processing" },
  { label: "Pago", value: "paid" },
  { label: "Cancelado", value: "canceled" },
  { label: "Reembolsado", value: "refunded" },
];
const simulationStatus = ref<SalePaymentStatus>("pending");
const simulatingStatus = ref(false);

const statusClasses = {
  payment: {
    paid: "bg-emerald-100 text-emerald-700",
    processing: "bg-amber-100 text-amber-700",
    canceled: "bg-rose-100 text-rose-600",
    refunded: "bg-sky-100 text-sky-700",
    pending: "bg-slate-100 text-slate-600",
  },
  payout: {
    pending: "bg-slate-100 text-slate-600",
    available: "bg-emerald-100 text-emerald-700",
    payout_paid: "bg-emerald-100 text-emerald-700",
    payout_failed: "bg-rose-100 text-rose-600",
  },
  passengers: {
    not_started: "bg-slate-100 text-slate-600",
    partial: "bg-amber-100 text-amber-700",
    completed: "bg-emerald-100 text-emerald-700",
  },
};

const upsertSaleSummary = (detail: SaleDetail) => {
  const { passengers, items, ...summary } = detail;
  const summaryData = summary as SaleSummary;
  const index = sales.value.findIndex(item => item.id === summaryData.id);
  if (index >= 0) {
    sales.value[index] = summaryData;
  } else {
    sales.value.unshift(summaryData);
  }
};

const resetProductForm = () => {
  productForm.name = "";
  productForm.description = null;
  productForm.status = "draft";
  productForm.trip_date = null;
  productForm.date_is_flexible = false;
  productForm.inventory_strategy = "manual";
  productForm.total_slots = 0;
  productForm.available_slots = 0;
  productForm.allow_oversell = false;
  productForm.card_interest_mode = "merchant";
  productForm.template_contract_id = null;
  productForm.checkout_banner_url = null;
  productForm.checkout_product_image_url = null;
  productForm.variations = [defaultVariation()];
  productForm.boarding_locations = [];
  productForm.is_road_trip = false;
  productForm.allowed_payment_methods = ["pix", "credit_card", "boleto"];
};

const mapDetailToForm = (detail: ProductDetail) => {
  productForm.name = detail.name;
  productForm.description = detail.description ?? null;
  productForm.status = detail.status;
  productForm.trip_date = detail.trip_date ?? null;
  productForm.date_is_flexible = detail.date_is_flexible;
  productForm.inventory_strategy = detail.inventory_strategy;
  productForm.total_slots = detail.total_slots;
  productForm.available_slots = detail.available_slots;
  productForm.allow_oversell = detail.allow_oversell;
  productForm.card_interest_mode = detail.card_interest_mode || "merchant";
  productForm.template_contract_id = detail.template_contract_id ?? null;
  productForm.checkout_banner_url = detail.checkout_banner_url ?? null;
  productForm.checkout_product_image_url = detail.checkout_product_image_url ?? null;
  productForm.boarding_locations = detail.boarding_locations ? [...detail.boarding_locations] : [];
  productForm.is_road_trip = detail.is_road_trip;
  productForm.allowed_payment_methods = Array.isArray(detail.allowed_payment_methods) && detail.allowed_payment_methods.length
    ? [...detail.allowed_payment_methods]
    : ["pix", "credit_card", "boleto"];
  productForm.variations = detail.variations.map(variation => ({
    public_id: variation.public_id,
    name: variation.name,
    description: variation.description ?? null,
    price: variation.price_cents / 100,
    people_included: variation.people_included,
    status: variation.status,
    stock_mode: variation.stock_mode,
    has_accommodation: variation.has_accommodation ?? false,
    accommodation_mode: variation.accommodation_mode ?? "private",
    room_capacity: variation.room_capacity ?? variation.people_included ?? 1,
    slots_per_unit: variation.slots_per_unit ?? variation.people_included ?? 1,
    total_slots: variation.total_slots ?? null,
    available_slots: variation.available_slots ?? null,
    child_policy_enabled: variation.child_policy_enabled,
    child_pricing_rules: resolveRuleForms(variation.child_pricing_rules || []),
  }));
  if (!productForm.variations.length) {
    productForm.variations = [defaultVariation()];
  }
};

const buildProductPayload = (): ProductPayload => ({
  name: productForm.name.trim(),
  description: productForm.description,
  status: productForm.status,
  trip_date: productForm.trip_date || undefined,
  date_is_flexible: productForm.date_is_flexible,
  inventory_strategy: productForm.inventory_strategy,
  total_slots: productForm.total_slots,
  available_slots: productForm.available_slots,
  allow_oversell: productForm.allow_oversell,
  card_interest_mode: productForm.card_interest_mode,
  template_contract_id: productForm.template_contract_id ?? undefined,
  checkout_banner_url: productForm.checkout_banner_url || undefined,
  checkout_product_image_url: productForm.checkout_product_image_url || undefined,
  variations: productForm.variations.map(variation => {
    const hasAccommodation = !!variation.has_accommodation;
    const roomCapacity = hasAccommodation ? Math.max(1, Math.floor(variation.room_capacity || 1)) : 1;
    const slotsPerUnit = hasAccommodation
      ? variation.accommodation_mode === "private"
        ? roomCapacity
        : Math.min(Math.max(1, Math.floor(variation.slots_per_unit || 1)), roomCapacity)
      : 1;
    return {
      public_id: variation.public_id || undefined,
      name: variation.name.trim(),
      description: variation.description,
      price_cents: Math.round((variation.price || 0) * 100),
      currency: "BRL",
      people_included: variation.people_included || 1,
      status: variation.status,
      stock_mode: variation.stock_mode,
      has_accommodation: hasAccommodation,
      accommodation_mode: hasAccommodation ? variation.accommodation_mode : "private",
      room_capacity: roomCapacity,
      slots_per_unit: slotsPerUnit,
      total_slots: variation.stock_mode === "variant" ? Math.max(0, variation.total_slots ?? 0) : undefined,
      available_slots: variation.stock_mode === "variant" ? Math.max(0, variation.available_slots ?? 0) : undefined,
      child_policy_enabled: variation.child_policy_enabled,
      child_pricing_rules: (variation.child_pricing_rules || []).map(serializeRuleForm),
    };
  }),
  boarding_locations: [...productForm.boarding_locations],
  has_rooms: productForm.variations.some(variation => variation.has_accommodation),
  is_road_trip: productForm.is_road_trip,
  allowed_payment_methods: productForm.allowed_payment_methods,
  rooms: [],
});

const addVariation = () => {
  productForm.variations.push(defaultVariation());
};
const removeVariation = (index: number) => {
  if (productForm.variations.length === 1) return;
  productForm.variations.splice(index, 1);
};

const openProductModal = async (product?: ProductSummary) => {
  productModalVisible.value = true;
  productSaving.value = false;
  if (product) {
    editingProductId.value = product.public_id;
    const { data } = await getProductDetail(product.public_id);
    mapDetailToForm(data);
  } else {
    editingProductId.value = null;
    resetProductForm();
  }
};

const saveProduct = async () => {
  productSaving.value = true;
  try {
    const payload = buildProductPayload();
    if (editingProductId.value) {
      await updateProduct(editingProductId.value, payload);
    } else {
      await createProduct(payload);
    }
    await loadProducts();
    productModalVisible.value = false;
  } catch (err) {
    console.error("Erro ao salvar produto", err);
  } finally {
    productSaving.value = false;
  }
};

const loadProducts = async () => {
  productsLoading.value = true;
  try {
    const { data } = await listProducts();
    products.value = data.items;
  } catch (err) {
    console.error("Erro ao carregar produtos", err);
  } finally {
    productsLoading.value = false;
  }
};

const handleRebuildProductInventory = async () => {
  inventoryRebuildLoading.value = true;
  try {
    const { data } = await rebuildProductInventory();
    await loadProducts();
    if (typeof window !== "undefined" && window.alert) {
      window.alert(
        `Estoque reprocessado. ${data.updated_products} de ${data.scanned_products} produto(s) foram atualizados.`,
      );
    }
  } catch (err) {
    console.error("Erro ao reprocessar estoque", err);
    if (typeof window !== "undefined" && window.alert) {
      window.alert("Não foi possível reprocessar o estoque agora.");
    }
  } finally {
    inventoryRebuildLoading.value = false;
  }
};

const loadContractTemplates = async () => {
  contractTemplatesLoading.value = true;
  try {
    const { data } = await listLegalTemplates();
    contractTemplates.value = data.items;
  } catch (err) {
    console.error("Erro ao carregar templates de contrato", err);
  } finally {
    contractTemplatesLoading.value = false;
  }
};

const loadBlimbooSettings = async () => {
  blimbooLoading.value = true;
  blimbooFeedback.value = null;
  try {
    const { data } = await getBlimbooSettings();
    const config: AgencyBlimbooSettings = data;
    blimbooState.token = config.token || "";
    blimbooState.hasToken = !!config.has_token;
    blimbooState.updatedAt = config.updated_at || "";
  } catch (err) {
    console.error("Erro ao carregar configuracoes Blimboo", err);
  } finally {
    blimbooLoading.value = false;
  }
};

const connectBlimbooAccount = async () => {
  if (blimbooSaving.value) return;
  blimbooSaving.value = true;
  blimbooFeedback.value = null;
  try {
    const normalized = blimbooState.token?.trim();
    const payload: AgencyBlimbooSettingsPayload = { token: normalized ? normalized : null };
    const { data } = await saveBlimbooSettings(payload);
    const config: AgencyBlimbooSettings = data;
    blimbooState.token = config.token || "";
    blimbooState.hasToken = !!config.has_token;
    blimbooState.updatedAt = config.updated_at || "";
    blimbooFeedback.value = { type: "success", message: "Token salvo com sucesso." };
  } catch (err) {
    console.error("Erro ao salvar token Blimboo", err);
    blimbooFeedback.value = { type: "error", message: "Nao foi possivel salvar o token." };
  } finally {
    blimbooSaving.value = false;
  }
};

const openInventoryModal = (product: ProductSummary) => {
  inventoryProduct.value = product;
  inventoryForm.total_slots = product.total_slots;
  inventoryForm.available_slots = product.available_slots;
  inventoryForm.note = "";
  inventoryModalVisible.value = true;
};

const saveInventoryAdjustment = async () => {
  if (!inventoryProduct.value) return;
  inventorySaving.value = true;
  try {
    await adjustProductInventory(inventoryProduct.value.public_id, inventoryForm);
    await loadProducts();
    inventoryModalVisible.value = false;
  } catch (err) {
    console.error("Erro ao ajustar estoque", err);
  } finally {
    inventorySaving.value = false;
  }
};

const openPosModal = (product?: ProductSummary) => {
  const target = product || products.value[0] || null;
  posProduct.value = target;
  posProductId.value = target?.public_id || "";
  posCustomer.name = "";
  posCustomer.email = "";
  posCustomer.phone = "";
  posResult.value = null;
  Object.keys(posSelections).forEach(key => delete posSelections[key]);
  productVariations(target).forEach(variation => {
    posSelections[variation.public_id] = createSelectionState(variation);
  });
  posModalVisible.value = true;
};

const closePosModal = () => {
  posModalVisible.value = false;
};

const syncPosProduct = () => {
  const next = products.value.find(item => item.public_id === posProductId.value) || null;
  posProduct.value = next;
  Object.keys(posSelections).forEach(key => delete posSelections[key]);
  productVariations(next).forEach(variation => {
    posSelections[variation.public_id] = createSelectionState(variation);
  });
};

const posItems = computed<CheckoutCartItem[]>(() =>
  Object.entries(posSelections)
    .filter(([, selection]) => selection.quantity > 0)
    .map(([variation_id, selection]) => ({
      variation_id,
      quantity: selection.quantity,
      children: selectionChildrenPayload(selection),
    })),
);

const posTotal = computed(() => {
  if (!posProduct.value) return 0;
  return productVariations(posProduct.value).reduce((total, variation) => {
    const selection = posSelections[variation.public_id];
    if (!selection || selection.quantity <= 0) return total;
    const composition = calculatePackageComposition(variation, selection.quantity, selection.children);
    return total + composition.totalPriceCents;
  }, 0);
});

const posPassengers = computed(() => {
  if (!posProduct.value) return 0;
  return productVariations(posProduct.value).reduce((total, variation) => {
    const selection = posSelections[variation.public_id];
    if (!selection || selection.quantity <= 0) return total;
    const composition = calculatePackageComposition(variation, selection.quantity, selection.children);
    return total + composition.totalPassengers;
  }, 0);
});

const posCapacity = computed(() => {
  if (!posProduct.value) return 0;
  return productVariations(posProduct.value).reduce((total, variation) => {
    const selection = posSelections[variation.public_id];
    if (!selection || selection.quantity <= 0) return total;
    const composition = calculatePackageComposition(variation, selection.quantity, selection.children);
    return total + composition.totalCapacity;
  }, 0);
});

const getPosSelection = (variation: ProductVariation) => ensureSelectionState(posSelections, variation);
const getPaymentSelection = (variation: ProductVariation) => ensureSelectionState(paymentLinkSelections, variation);

const handlePosQuantityInput = (variation: ProductVariation) => updateSelectionQuantityFor(posSelections, variation);
const handlePaymentQuantityInput = (variation: ProductVariation) =>
  updateSelectionQuantityFor(paymentLinkSelections, variation);

const adjustPosChild = (variation: ProductVariation, key: string, delta: number) =>
  adjustSelectionChild(posSelections, variation, key, delta);
const adjustPaymentChild = (variation: ProductVariation, key: string, delta: number) =>
  adjustSelectionChild(paymentLinkSelections, variation, key, delta);

const canIncrementPosChild = (variation: ProductVariation, key: string) => {
  const selection = getPosSelection(variation);
  return canIncrementChild(variation, selection, key);
};

const canIncrementPaymentChild = (variation: ProductVariation, key: string) => {
  const selection = getPaymentSelection(variation);
  return canIncrementChild(variation, selection, key);
};

const selectionComposition = (variation: ProductVariation, selection: PackageSelectionState) =>
  calculatePackageComposition(variation, selection.quantity, selection.children);

const variationChildRules = (variation: ProductVariation) => {
  const rules = variation.child_pricing_rules;
  return Array.isArray(rules) ? rules : [];
};
const enabledChildRules = (variation: ProductVariation) => variationChildRules(variation).filter(rule => rule.enabled);
const hasEnabledChildRules = (variation: ProductVariation) =>
  variation.child_policy_enabled && enabledChildRules(variation).length > 0;

const submitPosSale = async () => {
  if (!posProduct.value || !posItems.value.length) return;
  posSaving.value = true;
  try {
    const payload = {
      product_id: posProduct.value.public_id,
      items: posItems.value,
      customer: { ...posCustomer },
      channel: 'pos'
    };
    const { data } = await createPosCheckout(posProduct.value.public_id, payload);
    posResult.value = data;
    await loadSales();
  } catch (err) {
    console.error("Erro ao criar venda assistida", err);
  } finally {
    posSaving.value = false;
  }
};
const openPaymentLinkModal = (product?: ProductSummary) => {
  const target = product || products.value[0] || null;
  paymentLinkProduct.value = target;
  paymentLinkProductId.value = target?.public_id || "";
  paymentLinkCustomer.name = "";
  paymentLinkCustomer.email = "";
  paymentLinkCustomer.phone = "";
  paymentLinkExpires.value = 60;
  paymentLinkResult.value = null;
  Object.keys(paymentLinkSelections).forEach(key => delete paymentLinkSelections[key]);
  productVariations(target).forEach(variation => {
    paymentLinkSelections[variation.public_id] = createSelectionState(variation);
  });
  paymentLinkModalVisible.value = true;
};

const closePaymentLinkModal = () => {
  paymentLinkModalVisible.value = false;
};

const syncPaymentLinkProduct = () => {
  const next = products.value.find(item => item.public_id === paymentLinkProductId.value) || null;
  paymentLinkProduct.value = next;
  Object.keys(paymentLinkSelections).forEach(key => delete paymentLinkSelections[key]);
  productVariations(next).forEach(variation => {
    paymentLinkSelections[variation.public_id] = createSelectionState(variation);
  });
};

const paymentLinkItems = computed<CheckoutCartItem[]>(() =>
  Object.entries(paymentLinkSelections)
    .filter(([, selection]) => selection.quantity > 0)
    .map(([variation_id, selection]) => ({
      variation_id,
      quantity: selection.quantity,
      children: selectionChildrenPayload(selection),
    })),
);

const resolvePaymentLinkHost = (): string | null => {
  const override = import.meta.env.VITE_PAYMENT_LINK_HOST || null;
  if (override) return override;
  if (import.meta.env.DEV && typeof window !== "undefined") {
    return window.location.origin;
  }
  return null;
};

const normalizePaymentLinkUrl = (url: string): string => {
  const overrideOrigin = resolvePaymentLinkHost();
  if (!overrideOrigin) return url;
  try {
    const target = new URL(url);
    const override = new URL(overrideOrigin);
    target.protocol = override.protocol;
    target.host = override.host;
    return target.toString();
  } catch (err) {
    console.error("Erro ao ajustar URL do link de pagamento", err);
    return url;
  }
};

const paymentLinkDisplayUrl = computed(() => {
  if (!paymentLinkResult.value?.url) return "";
  return normalizePaymentLinkUrl(paymentLinkResult.value.url);
});

const submitPaymentLink = async () => {
  if (!paymentLinkProduct.value || !paymentLinkItems.value.length) return;
  paymentLinkSaving.value = true;
  try {
    const payload = {
      product_id: paymentLinkProduct.value.public_id,
      items: paymentLinkItems.value,
      customer: { ...paymentLinkCustomer },
      expires_in_minutes: paymentLinkExpires.value,
      channel: "pos",
    };
    const { data } = await createProductPaymentLink(paymentLinkProduct.value.public_id, payload);
    paymentLinkResult.value = data;
    await loadSales();
  } catch (err) {
    console.error("Erro ao gerar link de pagamento", err);
  } finally {
    paymentLinkSaving.value = false;
  }
};

const openDeleteModal = (product: ProductSummary) => {
  deleteTarget.value = product;
  deleteModalVisible.value = true;
};

const closeDeleteModal = () => {
  deleteModalVisible.value = false;
  deleteTarget.value = null;
};

const confirmDeleteProduct = async () => {
  if (!deleteTarget.value) return;
  deleteLoading.value = true;
  try {
    await deleteProduct(deleteTarget.value.public_id);
    await loadProducts();
    closeDeleteModal();
  } catch (err) {
    console.error("Erro ao excluir produto", err);
  } finally {
    deleteLoading.value = false;
  }
};

const loadSales = async () => {
  try {
    const { data } = await listSales(salesPagination.value.page, salesPagination.value.pageSize);
    sales.value = data.items;
    salesPagination.value.total = data.total;
  } catch (err) {
    console.error("Erro ao carregar vendas", err);
  }
};

const openSaleDetails = async (saleId: number) => {
  try {
    const { data } = await getSaleDetails(saleId);
    selectedSale.value = data;
    saleDetailsVisible.value = true;
  } catch (err) {
    console.error("Erro ao carregar venda", err);
  }
};

const openPassengerModal = async (saleId: number) => {
  passengerGroupsLoading.value = true;
  try {
    const { data: saleData } = await getSaleDetails(saleId);
    if (!saleData.requires_passengers) {
      if (typeof window !== "undefined" && window.alert) {
        window.alert("Este produto não exige formulário de passageiros.");
      }
      return;
    }
    passengerSale.value = saleData;
    let boardingOptions = saleData.boarding_locations || [];
    if ((!boardingOptions || !boardingOptions.length) && saleData.product_public_id) {
      try {
        const { data } = await getProductDetail(saleData.product_public_id);
        boardingOptions = data.boarding_locations || [];
      } catch (err) {
        console.error("Erro ao buscar locais de embarque do produto", err);
      }
    }
    passengerBoardingOptions.value = boardingOptions || [];
    const { data: groupsData } = await getSalePassengerGroups(saleId);
    applyPassengerGroupResponse(groupsData);
    passengerModalVisible.value = true;
  } catch (err) {
    console.error("Erro ao carregar passageiros", err);
  } finally {
    passengerGroupsLoading.value = false;
  }
};

const closePassengerModal = () => {
  passengerModalVisible.value = false;
  passengerSale.value = null;
  passengerGroupForms.value = [];
  activePassengerGroupIndex.value = 0;
  activePassengerIndex.value = 0;
  passengerBoardingOptions.value = [];
};

const router = useRouter();
const openRoadTripConfig = () => {
  if (!productForm.is_road_trip) return;
  if (!editingProductId.value) {
    if (typeof window !== "undefined" && window.alert) {
      window.alert("Salve o produto para configurar o transporte rodoviário.");
    }
    return;
  }
  router.push({ name: "product-seats", params: { productId: editingProductId.value } });
};
const goToProductPassengers = (product: ProductSummary) => {
  if (!product.is_road_trip) {
    if (typeof window !== "undefined" && window.alert) {
      window.alert("Este produto não exige lista de passageiros.");
    }
    return;
  }
  router.push({ name: "product-passengers", params: { productId: product.public_id } });
};
const goToRoomingList = (product: ProductSummary) => {
  if (!product.has_rooms) {
    if (typeof window !== "undefined" && window.alert) {
      window.alert("Este produto não possui hospedagem para gerenciar.");
    }
    return;
  }
  router.push({ name: "product-rooming-list", params: { productId: product.public_id } });
};

const resetBoardingForm = () => {
  boardingLocationsForm.value = [""];
};

const openBoardingLocationsModal = async () => {
  boardingLocationsModalVisible.value = true;
  if (editingProductId.value) {
    boardingLocationsLoading.value = true;
    try {
      const { data } = await getProductDetail(editingProductId.value);
      boardingLocationsForm.value = data.boarding_locations?.length ? [...data.boarding_locations] : [""];
    } catch (err) {
      console.error("Erro ao carregar locais de embarque", err);
      resetBoardingForm();
    } finally {
      boardingLocationsLoading.value = false;
    }
  } else {
    boardingLocationsForm.value =
      productForm.boarding_locations && productForm.boarding_locations.length
        ? [...productForm.boarding_locations]
        : [""];
  }
};

const closeBoardingLocationsModal = () => {
  boardingLocationsModalVisible.value = false;
  resetBoardingForm();
};

const addBoardingLocationField = () => {
  boardingLocationsForm.value.push("");
};

const removeBoardingLocationField = (index: number) => {
  if (boardingLocationsForm.value.length === 1) {
    boardingLocationsForm.value[0] = "";
    return;
  }
  boardingLocationsForm.value.splice(index, 1);
};

const saveBoardingLocations = async () => {
  const locations = boardingLocationsForm.value.map(item => item.trim()).filter(Boolean);
  if (editingProductId.value) {
    boardingLocationsSaving.value = true;
    try {
      await updateProductBoardingLocations(editingProductId.value, { locations });
      productForm.boarding_locations = [...locations];
      await loadProducts();
      closeBoardingLocationsModal();
    } catch (err) {
      console.error("Erro ao salvar locais de embarque", err);
    } finally {
      boardingLocationsSaving.value = false;
    }
  } else {
    productForm.boarding_locations = [...locations];
    closeBoardingLocationsModal();
  }
};

const getCachedPaymentStatus = (saleId: number): string | null => {
  if (passengerSale.value?.id === saleId) return passengerSale.value.payment_status;
  if (selectedSale.value?.id === saleId) return selectedSale.value.payment_status;
  const summary = sales.value.find(item => item.id === saleId);
  return summary ? summary.payment_status : null;
};

const resolveSalePaymentStatus = async (saleId: number): Promise<string | null> => {
  const cached = getCachedPaymentStatus(saleId);
  if (cached) return cached;
  try {
    const { data } = await getSaleDetails(saleId);
    upsertSaleSummary(data);
    return data.payment_status;
  } catch (err) {
    console.error("Erro ao verificar status da venda", err);
    return null;
  }
};

const copyPassengerLink = async (saleId: number) => {
  if (!saleRequiresPassengers(saleId)) {
    if (typeof window !== "undefined" && window.alert) {
      window.alert("Este produto não exige formulário de passageiros.");
    }
    return;
  }
  const paymentStatus = await resolveSalePaymentStatus(saleId);
  if (paymentStatus !== "paid") {
    if (typeof window !== "undefined" && window.alert) {
      window.alert("O formulrio de passageiros s  liberado aps confirmao do pagamento.");
    }
    return;
  }
  try {
    const { data } = await getPassengerLink(saleId);
    await copyText(data.url);
  } catch (err: any) {
    console.error("Erro ao copiar link", err);
    const detail = err?.response?.data?.detail;
    if (detail && typeof window !== "undefined" && window.alert) {
      window.alert(detail);
    }
  }
};

const applySimulatedStatus = async () => {
  if (!selectedSale.value) return;
  simulatingStatus.value = true;
  try {
    const { data } = await simulateSaleStatus(selectedSale.value.id, simulationStatus.value);
    selectedSale.value = data;
    upsertSaleSummary(data);
  } catch (err) {
    console.error("Erro ao simular status", err);
  } finally {
    simulatingStatus.value = false;
  }
};
const formatCurrency = (value?: number | null) => {
  const cents = typeof value === "number" ? value : 0;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
};

const formatDateTime = (value?: string | null) => {
  if (!value) return "No informado";
  try {
    return new Date(value).toLocaleString("pt-BR");
  } catch {
    return value;
  }
};

const formatPercent = (value?: number | null) => {
  if (typeof value !== "number") return "0%";
  return `${value.toFixed(2)}%`;
};

const saleChannelLabel = (channel: string) => {
  if (channel === "pos") return "PDV";
  if (channel === "link") return "Link";
  return "Checkout";
};

const salePageLabel = (sale?: SaleSummary | SaleDetail | null) => {
  if (!sale) return "";
  return sale.page_title || sale.page_slug || "";
};

const tripDateLabel = (product: ProductSummary) => {
  if (product.trip_date) {
    const base = new Date(product.trip_date).toLocaleDateString("pt-BR");
    return product.date_is_flexible ? `${base} (flexvel)` : base;
  }
  return "Sem data definida";
};

const productImageUrl = (product: ProductSummary) =>
  resolveMediaUrl(product.checkout_product_image_url || product.checkout_banner_url || "");

const productContractLabel = (product: ProductSummary) =>
  product.template_contract_name || "Sem contrato vinculado";

const productStatusLabel = (status: string) => ({
  draft: "Rascunho",
  active: "Ativo",
  inactive: "Inativo",
}[status] || status);

const productStatusClass = (status: string) => {
  if (status === "active") return "bg-emerald-100 text-emerald-700";
  if (status === "draft") return "bg-slate-100 text-slate-600";
  return "bg-rose-100 text-rose-600";
};

const inventoryBadge = (product: ProductSummary) => {
  if (product.inventory_strategy === "unlimited") return "Estoque ilimitado";
  return `Manual  ${product.available_slots}/${product.total_slots} vagas`;
};

const productDateSortValue = (product: ProductSummary) => {
  if (!product.trip_date) return Number.NEGATIVE_INFINITY;
  const timestamp = new Date(product.trip_date).getTime();
  return Number.isFinite(timestamp) ? timestamp : Number.NEGATIVE_INFINITY;
};

const filteredProducts = computed(() => {
  const search = productSearch.value.trim().toLowerCase();
  const filtered = products.value.filter(product => {
    const matchesSearch =
      !search ||
      product.name.toLowerCase().includes(search) ||
      String(product.id).includes(search) ||
      tripDateLabel(product).toLowerCase().includes(search);
    const matchesStatus = productStatusFilter.value === "all" || product.status === productStatusFilter.value;
    return matchesSearch && matchesStatus;
  });

  return [...filtered].sort((a, b) => {
    if (productSort.value === "name-asc") {
      return a.name.localeCompare(b.name, "pt-BR", { sensitivity: "base" });
    }
    if (productSort.value === "available-desc") {
      return b.available_slots - a.available_slots;
    }
    const left = productDateSortValue(a);
    const right = productDateSortValue(b);
    if (productSort.value === "date-asc") return left - right;
    return right - left;
  });
});

const paymentStatusLabel = (status: string) => ({
  pending: "Pendente",
  processing: "Processando",
  paid: "Pago",
  canceled: "Cancelado",
  refunded: "Reembolsado",
}[status] || status);

const payoutStatusLabel = (status: string) => ({
  pending: "Aguardando",
  available: "Disponível",
  payout_paid: "Recebido",
  payout_failed: "Falha",
}[status] || status);

const passengerStatusLabel = (status: string) => ({
  not_started: "Pendentes",
  partial: "Parcial",
  completed: "Completo",
}[status] || status);

const paymentStatusKey = (status: string) => {
  if (status === "paid") return "paid";
  if (status === "processing") return "processing";
  if (status === "canceled") return "canceled";
  if (status === "refunded") return "refunded";
  return "pending";
};

const payoutStatusKey = (status: string) => {
  if (status === "payout_paid") return "payout_paid";
  if (status === "payout_failed") return "payout_failed";
  if (status === "available") return "available";
  return "pending";
};

const passengerStatusKey = (status: string) => {
  if (status === "completed") return "completed";
  if (status === "partial") return "partial";
  return "not_started";
};

const groupStatusBadge = (status: string) => statusClasses.passengers[passengerStatusKey(status)];

watch(
  () => selectedSale.value,
  value => {
    simulationStatus.value = (value?.payment_status as SalePaymentStatus) || "pending";
  },
);

watch(
  () => passengerGroupForms.value.length,
  length => {
    if (!length) {
      activePassengerGroupIndex.value = 0;
      activePassengerIndex.value = 0;
      return;
    }
    if (activePassengerGroupIndex.value >= length) {
      activePassengerGroupIndex.value = length - 1;
    }
    const group = passengerGroupForms.value[activePassengerGroupIndex.value];
    if (group && activePassengerIndex.value >= group.passengers.length) {
      activePassengerIndex.value = group.passengers.length - 1;
    }
  },
);

watch(
  () => passengerModalVisible.value,
  visible => {
    if (!visible) {
      activePassengerGroupIndex.value = 0;
      activePassengerIndex.value = 0;
    }
  },
);

const copyText = async (text: string) => {
  if (!text) return;
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    throw new Error("Clipboard API indisponível");
  } catch (err) {
    try {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    } catch (fallbackErr) {
      console.error("Erro ao copiar texto", fallbackErr || err);
    }
  }
};

onMounted(async () => {
  await Promise.all([loadSales(), loadProducts(), loadContractTemplates(), loadBlimbooSettings()]);
});
</script>

<style scoped>
.pill {
  @apply rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-slate-300;
}
.pill:disabled {
  @apply cursor-not-allowed border-slate-100 text-slate-400 opacity-60 hover:border-slate-100;
}
.sales-tab {
  @apply rounded-full border border-slate-200 px-4 py-1.5 text-sm font-semibold text-slate-600 transition hover:border-slate-300;
}
.sales-tab-active {
  @apply border-emerald-500 bg-emerald-500 text-white shadow;
}
.sales-settings-card {
  @apply rounded-3xl border border-slate-200 bg-white p-6 shadow-sm;
}
.sales-settings-header {
  @apply flex flex-col gap-4 border-b border-slate-100 pb-4 md:flex-row md:items-start md:justify-between;
}
.sales-settings-actions {
  @apply mt-4 flex flex-wrap items-center gap-3;
}
.sales-settings-form {
  @apply mt-6 flex flex-col gap-3 md:flex-row md:items-center;
}
.sales-settings-note {
  @apply mt-4 space-y-2;
}
.sales-eyebrow {
  @apply text-xs font-semibold uppercase tracking-[0.3em] text-slate-400;
}
.group-chip {
  @apply w-full min-w-[180px] rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left transition hover:border-slate-300;
}
.group-chip-active {
  @apply border-emerald-400 bg-emerald-50;
}
.passenger-chip {
  @apply rounded-full border border-slate-200 px-5 py-2 text-xs font-semibold text-slate-600 transition leading-none;
}
.passenger-chip span:first-child {
  @apply mb-0.5;
}
.passenger-chip-active {
  @apply border-emerald-500 bg-emerald-50 text-emerald-700 shadow-[0_0_0_2px_rgba(16,185,129,0.15)];
}
.passenger-chip-complete {
  @apply border-emerald-200 bg-emerald-50 text-emerald-700;
}
.passenger-chip-partial {
  @apply border-amber-200 bg-amber-50 text-amber-700;
}
.passenger-chip-empty {
  @apply border-slate-200 bg-white text-slate-500;
}
.btn-primary {
  @apply rounded-full bg-emerald-500 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:-translate-y-0.5 disabled:bg-emerald-300;
}
.placeholder-card {
  @apply rounded-3xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500;
}
.stat-card {
  @apply rounded-2xl bg-slate-50 p-3;
}
.stat-card dt {
  @apply text-xs uppercase tracking-wide text-slate-400;
}
.stat-card dd {
  @apply text-lg text-slate-900;
}
.products-toolbar {
  @apply flex flex-wrap items-center justify-between gap-3 rounded-[28px] border border-slate-200/80 bg-white px-4 py-4 shadow-[0_3px_14px_rgba(15,23,42,0.04)];
}
.products-toolbar__filters {
  @apply flex min-w-0 flex-1 flex-wrap items-center gap-3;
}
.products-toolbar__search {
  @apply min-w-[280px] flex-[1.3];
}
.products-toolbar__select {
  @apply min-w-[180px];
}
.products-toolbar__input {
  @apply h-11 rounded-full border-slate-200 bg-slate-50/70 px-4 text-sm text-slate-700 shadow-none focus:border-emerald-500 focus:bg-white;
}
.products-toolbar__count {
  @apply text-sm font-medium text-slate-500;
}
.products-list-surface {
  @apply rounded-[30px] border border-slate-200/80 bg-white p-3 shadow-[0_10px_30px_rgba(15,23,42,0.05)];
}
.products-list-scroll {
  @apply overflow-x-auto;
}
.product-list-grid {
  display: grid;
  grid-template-columns:
    minmax(320px, 2.2fr)
    minmax(132px, 0.9fr)
    minmax(92px, 0.7fr)
    minmax(118px, 0.9fr)
    minmax(118px, 0.9fr)
    minmax(118px, 0.9fr)
    minmax(140px, 0.9fr)
    minmax(168px, 0.95fr);
  gap: 1rem;
  align-items: center;
  min-width: 1220px;
}
.products-list-header {
  @apply px-5 pb-3 pt-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400;
}
.products-list-header__cell {
  @apply block;
}
.products-list-header__cell-product {
  @apply text-left;
}
.products-list-header__cell-date,
.products-list-header__cell-metric,
.products-list-header__cell-status {
  @apply text-center;
}
.products-list-header__cell-actions {
  @apply text-right;
}
.products-row {
  @apply rounded-[24px] border border-slate-200/80 bg-white px-5 py-3 shadow-[0_3px_12px_rgba(15,23,42,0.04)];
}
.products-row + .products-row {
  @apply mt-3;
}
.products-row__product {
  @apply flex min-w-0 items-center gap-4;
}
.products-row__thumb-wrap {
  @apply flex-shrink-0;
}
.products-row__thumb {
  @apply h-16 w-16 rounded-2xl border border-slate-200 bg-white object-contain p-1 shadow-sm;
}
.products-row__thumb--fallback {
  @apply flex items-center justify-center bg-slate-100 text-lg font-bold uppercase text-slate-500;
}
.products-row__identity {
  @apply flex min-w-0 items-center;
}
.products-row__title {
  @apply truncate text-[18px] font-semibold tracking-[-0.01em] text-slate-950;
}
.products-row__metric {
  @apply text-center;
}
.products-row__metric-value {
  @apply text-[20px] font-semibold text-slate-950;
}
.products-row__metric--available .products-row__metric-value {
  @apply text-sky-600;
}
.products-row__metric--reserved .products-row__metric-value {
  color: #ca8a04;
}
.products-row__metric--sold .products-row__metric-value {
  @apply text-emerald-600;
}
.products-row__date {
  @apply text-sm font-semibold text-slate-700;
}
.products-row__status {
  @apply flex items-center justify-center;
}
.products-row__actions {
  @apply flex items-center justify-end;
}
.products-row__link {
  @apply inline-flex min-w-[144px] items-center justify-center rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold text-slate-700 transition-all duration-200 hover:-translate-y-[1px] hover:border-slate-300 hover:text-slate-950;
}
.status-pill {
  @apply rounded-full px-3 py-1;
}
.inventory-pill {
  @apply rounded-full bg-slate-100 px-3 py-1 text-slate-600;
}
.badge {
  @apply rounded-full px-3 py-1;
}
.badge-muted {
  @apply bg-slate-100 text-slate-600;
}
.modal-overlay {
  @apply fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4;
}
.modal-card {
  @apply w-full rounded-3xl bg-white p-6 shadow-2xl;
}
.modal-card--product {
  width: 90vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}
.modal-card--sale {
  max-width: 42rem;
  width: min(90vw, 42rem);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}
.modal-card--passengers {
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}
@media (min-width: 1024px) {
  .modal-card--product {
    width: 50vw;
  }
}
.modal-card--passengers .modal-scroll {
  flex: 1;
  overflow-y: auto;
}
.modal-card--sale .modal-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 0.5rem;
  margin-right: -0.5rem;
}
.modal-card--sale .modal-scroll::-webkit-scrollbar {
  width: 6px;
}
.modal-card--sale .modal-scroll::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.4);
  border-radius: 999px;
}
.modal-body {
  @apply mt-4 flex-1 overflow-y-auto;
  padding-right: 0.5rem;
  margin-right: -0.5rem;
  scrollbar-gutter: stable both-edges;
}
@media (min-width: 1024px) {
  .modal-body {
    padding-right: 0.75rem;
    margin-right: -0.75rem;
  }
}
.modal-footer {
  @apply mt-6 flex justify-end gap-3;
  flex-shrink: 0;
}
.modal-card--product .modal-footer {
  @apply border-t border-slate-100 pt-4;
}
.custom-scroll {
  scrollbar-width: thin;
  scrollbar-color: #94a3b8 transparent;
}
.custom-scroll::-webkit-scrollbar {
  width: 6px;
}
.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scroll::-webkit-scrollbar-thumb {
  background-color: #94a3b8;
  border-radius: 9999px;
}
.input {
  @apply w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none;
}
.input-label {
  @apply text-xs font-semibold text-slate-500;
}
</style>













