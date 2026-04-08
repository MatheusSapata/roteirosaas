
<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center gap-3">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        type="button"
        class="rounded-full px-4 py-2 text-sm font-semibold transition"
        :class="activeTab === tab.value ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <section v-if="activeTab === 'products'" class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 class="text-xl font-semibold text-slate-900">Central comercial</h2>
          <p class="text-sm text-slate-500">Cadastre viagens, gerencie estoque e acione o PDV interno.</p>
        </div>
        <div class="flex flex-wrap gap-3">
          <button type="button" class="pill" :disabled="productsLoading || !products.length" @click="openPosModal()">
            Nova venda
          </button>
          <button type="button" class="pill" :disabled="productsLoading || !products.length" @click="openPaymentLinkModal()">
            Gerar link
          </button>
          <button type="button" class="btn-primary" @click="openProductModal()">Criar produto</button>
        </div>
      </div>

      <div v-if="productsLoading" class="placeholder-card">Carregando produtos...</div>
      <div v-else-if="!products.length" class="placeholder-card">
        Nenhum produto cadastrado. Clique em <strong>Criar produto</strong> para começar.
      </div>
      <div v-else class="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="product in products"
          :key="product.public_id"
          class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
        >
          <header class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Produto #{{ product.id }}</p>
              <h3 class="text-xl font-semibold text-slate-900">{{ product.name }}</h3>
              <p v-if="product.description" class="text-sm text-slate-500">{{ product.description }}</p>
              <p class="text-xs text-slate-500">{{ tripDateLabel(product) }}</p>
            </div>
            <div class="flex flex-col items-end gap-2 text-xs font-semibold">
              <span :class="['rounded-full px-3 py-1', productStatusClass(product.status)]">
                {{ productStatusLabel(product.status) }}
              </span>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-slate-600">{{ inventoryBadge(product) }}</span>
            </div>
          </header>

          <dl class="grid grid-cols-2 gap-3 text-center text-sm font-semibold md:grid-cols-4">
            <div class="stat-card">
              <dt>Totais</dt>
              <dd>{{ product.total_slots }}</dd>
            </div>
            <div class="stat-card">
              <dt>Disponíveis</dt>
              <dd class="text-emerald-600">{{ product.available_slots }}</dd>
            </div>
            <div class="stat-card">
              <dt>Reservadas</dt>
              <dd class="text-amber-600">{{ product.reserved_slots }}</dd>
            </div>
            <div class="stat-card">
              <dt>Vendidas</dt>
              <dd class="text-emerald-800">{{ product.sold_slots }}</dd>
            </div>
          </dl>

          <div class="space-y-2 rounded-2xl border border-slate-100 p-3">
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Pacotes</p>
            <div
              v-for="variation in product.variations"
              :key="variation.public_id"
              class="flex flex-wrap items-start justify-between gap-3 rounded-xl bg-slate-50 p-3"
            >
              <div>
                <p class="text-sm font-semibold text-slate-900">
                  {{ variation.name }}
                  <span
                    class="ml-2 rounded-full px-2 py-0.5 text-[11px] font-semibold"
                    :class="variation.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'"
                  >
                    {{ variation.status === 'active' ? 'Ativo' : 'Inativo' }}
                  </span>
                </p>
                <p v-if="variation.description" class="text-xs text-slate-500">{{ variation.description }}</p>
                <p class="text-xs text-slate-500">Inclui {{ variation.people_included }} pessoa(s)</p>
              </div>
              <div class="text-right text-sm font-semibold text-slate-900">
                {{ formatCurrency(variation.price_cents) }}
                <p class="text-xs text-slate-500">
                  Estoque:
                  <span v-if="variation.stock_mode === 'variant'">
                    {{ variation.available_slots ?? 0 }} / {{ variation.total_slots ?? 0 }}
                  </span>
                  <span v-else>herda produto</span>
                </p>
              </div>
            </div>
          </div>

          <div class="flex flex-wrap gap-2">
            <button class="pill" @click="openProductModal(product)">Editar</button>
            <button class="pill" @click="openInventoryModal(product)">Ajustar estoque</button>
            <button class="pill" @click="openPosModal(product)">Nova venda</button>
            <button class="pill" @click="openPaymentLinkModal(product)">Link pagamento</button>
            <button class="pill text-rose-600" @click="openDeleteModal(product)">Excluir</button>
          </div>
        </article>
      </div>
    </section>
    <section v-else-if="activeTab === 'sales'" class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <p class="text-sm text-slate-500">Total de vendas: {{ salesPagination.total }}</p>
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center rounded-full border border-slate-200 bg-slate-100 p-1 text-xs font-semibold text-slate-500">
            <button
              v-for="option in salesViewOptions"
              :key="option.value"
              type="button"
              class="rounded-full px-3 py-1 transition"
              :class="salesViewMode === option.value ? 'bg-white text-slate-900 shadow' : 'hover:text-slate-700'"
              @click="salesViewMode = option.value"
            >
              {{ option.label }}
            </button>
          </div>
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
        <div v-if="salesViewMode === 'cards'" class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <article
            v-for="sale in filteredSales"
            :key="sale.id"
            class="h-full rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Venda #{{ sale.id }} • {{ saleChannelLabel(sale.channel) }}
                  <span v-if="salePageLabel(sale)">• {{ salePageLabel(sale) }}</span>
                </p>
                <h3 class="text-lg font-semibold text-slate-900">{{ sale.product_title }}</h3>
                <p class="text-sm text-slate-500">
                  {{ formatCurrency(sale.amount_cents) }} • {{ sale.installments }}x •
                  {{ sale.customer_name || 'Cliente' }}
                </p>
              </div>
              <div class="flex flex-wrap gap-2 text-xs font-semibold">
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
            </div>
            <div class="mt-4 flex flex-wrap gap-2">
              <button class="pill" @click="openSaleDetails(sale.id)">Detalhes</button>
              <button class="pill" @click="openPassengerModal(sale.id)">Passageiros</button>
              <button class="pill" :disabled="sale.payment_status !== 'paid'" @click="copyPassengerLink(sale.id)">
                Copiar link passageiros
              </button>
            </div>
          </article>
        </div>
        <div v-else class="overflow-x-auto rounded-3xl border border-slate-200 bg-white">
          <table class="min-w-full divide-y divide-slate-200 text-sm text-center">
            <thead class="bg-slate-50 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              <tr>
                <th class="px-3 py-2">ID</th>
                <th class="px-3 py-2">Produto</th>
                <th class="px-3 py-2">Fonte</th>
                <th class="px-3 py-2">Cliente</th>
                <th class="px-3 py-2">Status</th>
                <th class="px-3 py-2">Pagamento</th>
                <th class="px-3 py-2">Ações</th>
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
                    <button class="pill" @click="openPassengerModal(sale.id)">Passageiros</button>
                    <button class="pill" :disabled="sale.payment_status !== 'paid'" @click="copyPassengerLink(sale.id)">
                      Copiar link
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    
    <!-- Product modal -->
    <div v-if="productModalVisible" class="modal-overlay !mt-0">
      <div class="modal-card modal-card--product">
        <header class="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              {{ editingProductId ? 'Editar produto' : 'Novo produto' }}
            </p>
            <h3 class="text-lg font-semibold text-slate-900">{{ productForm.name || 'Nova viagem' }}</h3>
          </div>
          <button class="text-slate-500 hover:text-slate-900" @click="productModalVisible = false">×</button>
        </header>

        <div class="modal-body custom-scroll space-y-4">
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label class="input-label">Nome</label>
              <input v-model="productForm.name" class="input" placeholder="Expedição Amazônia" />
            </div>
            <div>
              <label class="input-label">Status</label>
              <select v-model="productForm.status" class="input">
                <option value="draft">Rascunho</option>
                <option value="active">Ativo</option>
                <option value="inactive">Inativo</option>
              </select>
            </div>
          </div>
          <div>
            <label class="input-label">Descrição</label>
            <textarea v-model="productForm.description" rows="2" class="input" placeholder="Resumo da viagem"></textarea>
          </div>
          <div class="grid gap-4 md:grid-cols-3">
            <div>
              <label class="input-label">Data da viagem</label>
              <input type="date" v-model="productForm.trip_date" class="input" />
            </div>
            <div class="flex items-center gap-2">
              <label class="input-label">Sem data definida</label>
              <input type="checkbox" v-model="productForm.date_is_flexible" class="h-4 w-4" />
            </div>
            <div>
              <label class="input-label">Estratégia de estoque</label>
              <select v-model="productForm.inventory_strategy" class="input">
                <option value="manual">Manual</option>
                <option value="unlimited">Ilimitado</option>
              </select>
            </div>
          </div>
          <div class="grid gap-4 md:grid-cols-3">
            <div>
              <label class="input-label">Vagas totais</label>
              <input type="number" min="0" class="input" v-model.number="productForm.total_slots" :disabled="productForm.inventory_strategy === 'unlimited'" />
            </div>
            <div>
              <label class="input-label">Disponíveis</label>
              <input type="number" min="0" class="input" v-model.number="productForm.available_slots" :disabled="productForm.inventory_strategy === 'unlimited'" />
            </div>
            <div class="flex items-center gap-2">
              <label class="input-label">Permitir overbooking</label>
              <input type="checkbox" v-model="productForm.allow_oversell" class="h-4 w-4" />
            </div>
          </div>
          <div class="space-y-3 rounded-2xl border border-slate-100 p-3">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-semibold text-slate-900">Pacotes</p>
                <p class="text-xs text-slate-500">Defina variações de preço e estoque.</p>
              </div>
              <button type="button" class="text-xs font-semibold text-emerald-600" @click="addVariation">+ Adicionar</button>
            </div>
            <div v-for="(variation, index) in productForm.variations" :key="index" class="space-y-2 rounded-xl bg-slate-50/80 p-3">
              <div class="flex items-center justify-between">
                <p class="text-sm font-semibold text-slate-900">Pacote {{ index + 1 }}</p>
                <button type="button" class="text-xs text-rose-500" @click="removeVariation(index)" :disabled="productForm.variations.length === 1">
                  Remover
                </button>
              </div>
              <div class="grid gap-4 md:grid-cols-2">
                <div>
                  <label class="input-label">Nome</label>
                  <input v-model="variation.name" class="input" placeholder="Pacote premium" />
                </div>
                <div>
                  <label class="input-label">Preço (R$)</label>
                  <input type="number" min="0" step="0.01" class="input" v-model.number="variation.price" />
                </div>
              </div>
              <div class="grid gap-4 md:grid-cols-3">
                <div>
                  <label class="input-label">Pessoas incluídas</label>
                  <input type="number" min="1" class="input" v-model.number="variation.people_included" />
                </div>
                <div>
                  <label class="input-label">Status</label>
                  <select v-model="variation.status" class="input">
                    <option value="active">Ativo</option>
                    <option value="inactive">Inativo</option>
                  </select>
                </div>
                <div>
                  <label class="input-label">Controle</label>
                  <select v-model="variation.stock_mode" class="input">
                    <option value="shared">Herda produto</option>
                    <option value="variant">Próprio</option>
                  </select>
                </div>
              </div>
              <div v-if="variation.stock_mode === 'variant'" class="grid gap-4 md:grid-cols-2">
                <div>
                  <label class="input-label">Total</label>
                  <input type="number" min="0" class="input" v-model.number="variation.total_slots" />
                </div>
                <div>
                  <label class="input-label">Disponíveis</label>
                  <input type="number" min="0" class="input" v-model.number="variation.available_slots" />
                </div>
              </div>
              <div>
                <label class="input-label">Descrição</label>
                <textarea v-model="variation.description" rows="2" class="input" placeholder="Detalhes do pacote"></textarea>
              </div>
            </div>
          </div>
        </div>
        <footer class="modal-footer">
          <button type="button" class="pill" @click="productModalVisible = false">Cancelar</button>
          <button type="button" class="btn-primary" :disabled="productSaving" @click="saveProduct">
            {{ productSaving ? 'Salvando...' : 'Salvar produto' }}
          </button>
        </footer>
      </div>
    </div>
    <div v-if="inventoryModalVisible && inventoryProduct" class="modal-overlay !mt-0">
      <div class="modal-card max-w-md">
        <header class="mb-4 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Ajustar estoque</p>
            <h3 class="text-lg font-semibold text-slate-900">{{ inventoryProduct.name }}</h3>
          </div>
          <button class="text-slate-500" @click="inventoryModalVisible = false">×</button>
        </header>
        <div class="space-y-3">
          <div>
            <label class="input-label">Vagas totais</label>
            <input type="number" min="0" class="input" v-model.number="inventoryForm.total_slots" />
          </div>
          <div>
            <label class="input-label">Disponíveis</label>
            <input type="number" min="0" class="input" v-model.number="inventoryForm.available_slots" />
          </div>
          <div>
            <label class="input-label">Observação</label>
            <textarea rows="2" class="input" v-model="inventoryForm.note" placeholder="Motivo do ajuste"></textarea>
          </div>
        </div>
        <footer class="mt-6 flex justify-end gap-3">
          <button class="pill" @click="inventoryModalVisible = false">Cancelar</button>
          <button class="btn-primary" :disabled="inventorySaving" @click="saveInventoryAdjustment">
            {{ inventorySaving ? 'Aplicando...' : 'Aplicar' }}
          </button>
        </footer>
      </div>
    </div>

    <div v-if="posModalVisible" class="modal-overlay !mt-0">
      <div class="modal-card max-w-3xl">
        <header class="mb-4 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Nova venda assistida</p>
            <h3 class="text-lg font-semibold text-slate-900">{{ posProduct?.name || 'Selecione um produto' }}</h3>
          </div>
          <button class="text-slate-500" @click="closePosModal">×</button>
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
              <p class="text-2xl font-semibold text-slate-900">{{ formatCurrency(posTotal) }}</p>
              <div
                v-if="posResult"
                class="mt-3 space-y-1 rounded-2xl bg-emerald-50 p-3 text-xs text-emerald-900"
              >
                <p class="text-sm font-semibold">Cobrança criada!</p>
                <p>Venda #{{ posResult.sale_id }} • {{ paymentStatusLabel(posResult.provider_status) }}</p>
                <p>Ref: {{ posResult.checkout_reference }}</p>
                <p>{{ posResult.breakdown.installments }}x de {{ formatCurrency(posResult.breakdown.installment_amount_cents) }}</p>
                <button
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
          <div v-if="posProduct" class="space-y-2 rounded-2xl border border-slate-100 p-3">
            <p class="text-sm font-semibold text-slate-900">Pacotes</p>
            <div
              v-for="variation in posProduct.variations"
              :key="variation.public_id"
              class="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2"
            >
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ variation.name }}</p>
                <p class="text-xs text-slate-500">{{ formatCurrency(variation.price_cents) }}</p>
              </div>
              <input type="number" min="0" class="w-24 rounded-full border border-slate-200 px-3 py-1 text-center text-sm" v-model.number="posSelections[variation.public_id]" />
            </div>
          </div>
        </div>
        <footer class="mt-6 flex justify-end gap-3">
          <button class="pill" @click="closePosModal">Cancelar</button>
          <button class="btn-primary" :disabled="posSaving || !posProduct || !posItems.length" @click="submitPosSale">
            {{ posSaving ? 'Processando...' : 'Gerar cobrança' }}
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
          <button class="text-slate-500" @click="closePaymentLinkModal">×</button>
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
          <div v-if="paymentLinkProduct" class="space-y-2 rounded-2xl border border-slate-100 p-3">
            <p class="text-sm font-semibold text-slate-900">Pacotes</p>
            <div
              v-for="variation in paymentLinkProduct.variations"
              :key="variation.public_id"
              class="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2"
            >
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ variation.name }}</p>
                <p class="text-xs text-slate-500">{{ formatCurrency(variation.price_cents) }}</p>
              </div>
              <input type="number" min="0" class="w-24 rounded-full border border-slate-200 px-3 py-1 text-center text-sm" v-model.number="paymentLinkSelections[variation.public_id]" />
            </div>
          </div>
          <div v-if="paymentLinkResult" class="rounded-2xl bg-emerald-50 p-3 text-sm text-emerald-800">
            <p class="font-semibold">Link pronto!</p>
            <p class="break-all">{{ paymentLinkResult.url }}</p>
            <button class="text-xs font-semibold text-emerald-700 underline" @click="copyText(paymentLinkResult.url)">Copiar</button>
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
          <button class="text-slate-500" @click="closeDeleteModal">×</button>
        </header>
        <p class="text-sm text-slate-600">
          Essa ação removerá o produto e suas variações do módulo financeiro. Vendas já registradas não serão apagadas.
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
      <div class="modal-card max-w-2xl">
        <header class="mb-4 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Venda #{{ selectedSale.id }}</p>
            <h3 class="text-lg font-semibold text-slate-900">{{ selectedSale.product_title }}</h3>
          </div>
          <button class="text-slate-500" @click="saleDetailsVisible = false">×</button>
        </header>
        <div class="space-y-4 text-sm">
          <div class="flex flex-wrap gap-2 text-xs font-semibold">
            <span :class="['badge', statusClasses.payment[paymentStatusKey(selectedSale.payment_status)]]">
              {{ paymentStatusLabel(selectedSale.payment_status) }}
            </span>
            <span :class="['badge', statusClasses.payout[payoutStatusKey(selectedSale.payout_status)]]">
              {{ payoutStatusLabel(selectedSale.payout_status) }}
            </span>
            <span :class="['badge', statusClasses.passengers[passengerStatusKey(selectedSale.passenger_status)]]">
              {{ passengerStatusLabel(selectedSale.passenger_status) }}
            </span>
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <div class="rounded-2xl border border-slate-100 p-3">
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Cliente</p>
              <p class="mt-1"><span class="font-semibold text-slate-600">Nome:</span> {{ selectedSale.customer_name || "Não informado" }}</p>
              <p><span class="font-semibold text-slate-600">E-mail:</span> {{ selectedSale.customer_email || "Não informado" }}</p>
              <p><span class="font-semibold text-slate-600">Telefone:</span> {{ selectedSale.customer_phone || "Não informado" }}</p>
              <p><span class="font-semibold text-slate-600">Canal:</span> {{ saleChannelLabel(selectedSale.channel) }}</p>
              <p v-if="salePageLabel(selectedSale)"><span class="font-semibold text-slate-600">Página:</span> {{ salePageLabel(selectedSale) }}</p>
              <p><span class="font-semibold text-slate-600">Criada em:</span> {{ formatDateTime(selectedSale.created_at) }}</p>
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
                <dt class="text-xs text-slate-500">Repasse agência</dt>
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
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Itens</p>
            <ul class="mt-2 space-y-2">
              <li v-for="item in selectedSale.items" :key="item.id" class="rounded-xl border border-slate-100 p-3 text-sm">
                <p class="font-semibold text-slate-900">{{ item.variation_name }}</p>
                <p class="text-slate-500">
                  {{ item.quantity }} x {{ formatCurrency(item.unit_price) }} = {{ formatCurrency(item.total_price) }}
                </p>
                <p class="text-xs text-slate-500">Status: {{ item.status }}</p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>


    <div v-if="passengerModalVisible && passengerSale" class="modal-overlay !mt-0">
      <div class="modal-card max-w-3xl">
        <header class="mb-4 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              Passageiros venda #{{ passengerSale.id }}
            </p>
            <h3 class="text-lg font-semibold text-slate-900">{{ passengerSale.product_title }}</h3>
          </div>
          <button class="text-slate-500" @click="closePassengerModal">×</button>
        </header>
        <div class="max-h-[65vh] space-y-4 overflow-y-auto">
          <div class="rounded-3xl border border-slate-100 bg-slate-50/60 p-4">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Resumo da venda</p>
                <h4 class="text-lg font-semibold text-slate-900">{{ passengerSale.product_title }}</h4>
                <p class="text-sm text-slate-500">
                  Venda #{{ passengerSale.id }} • {{ saleChannelLabel(passengerSale.channel) }}
                </p>
                <p class="text-sm text-slate-500">
                  Cliente: <span class="font-semibold text-slate-900">{{ passengerSale.customer_name || "Não informado" }}</span>
                </p>
              </div>
            </div>
            <div class="mt-4 grid gap-4 text-sm sm:grid-cols-2">
              <div class="space-y-2">
                <div>
                  <p class="text-xs uppercase tracking-wide text-slate-400">Descrição do produto</p>
                  <p class="text-base font-semibold text-slate-900">
                    {{ passengerSale.product_description || "Sem descrição" }}
                  </p>
                </div>
                <div>
                  <p class="text-xs uppercase tracking-wide text-slate-400">Passageiros previstos</p>
                  <p class="text-base font-semibold text-slate-900">{{ passengerSale.passengers_required }}</p>
                </div>
                <div>
                  <p class="text-xs uppercase tracking-wide text-slate-400">Canal</p>
                  <p class="text-base font-semibold text-slate-900">{{ saleChannelLabel(passengerSale.channel) }}</p>
                </div>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide text-slate-400">Pacotes e variações</p>
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
                  <li v-if="!passengerSale.items.length" class="text-xs text-slate-500">
                    Nenhum item associado.
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-100 p-4">
            <div class="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Dados dos passageiros</p>
                <p class="text-sm text-slate-500">Informe todos os passageiros para liberar a viagem.</p>
              </div>
              <div v-if="canManagePassengers" class="flex flex-wrap gap-2">
                <button type="button" class="pill" @click="addManualPassenger">+ Passageiro</button>
                <button
                  type="button"
                  class="pill"
                  :disabled="!passengerSale"
                  @click="passengerSale && copyPassengerLink(passengerSale.id)"
                >
                  Enviar link
                </button>
              </div>
            </div>
            <div v-if="passengerForm.length" class="space-y-4 pt-4">
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="(passenger, index) in passengerForm"
                  :key="`tab-${index}`"
                  type="button"
                  class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                  :class="
                    activePassengerTab === index
                      ? 'border-emerald-500 bg-emerald-500 text-white'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                  "
                  @click="activePassengerTab = index"
                >
                  Passageiro {{ index + 1 }}
                </button>
              </div>
              <div
                v-for="(passenger, index) in passengerForm"
                v-show="activePassengerTab === index"
                :key="`panel-${index}`"
                class="space-y-4 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
              >
                <div class="flex items-center justify-between">
                  <p class="text-sm font-semibold text-slate-900">Passageiro {{ index + 1 }}</p>
                  <button
                    v-if="canManagePassengers && passengerForm.length > 1"
                    type="button"
                    class="text-xs font-semibold text-rose-500"
                    @click="removeManualPassenger(index)"
                  >
                    Remover
                  </button>
                </div>
                <div class="grid gap-3 md:grid-cols-2">
                  <div class="md:col-span-2">
                    <label class="input-label">Nome completo</label>
                    <input v-model="passenger.name" class="input mt-1" placeholder="Nome completo" />
                  </div>
                  <div>
                    <label class="input-label">CPF</label>
                    <input v-model="passenger.cpf" class="input mt-1" placeholder="000.000.000-00" />
                  </div>
                  <div>
                    <label class="input-label">Nascimento</label>
                    <input v-model="passenger.birthdate" type="date" class="input mt-1" />
                  </div>
                  <div>
                    <label class="input-label">Telefone</label>
                    <input v-model="passenger.phone" class="input mt-1" placeholder="(00) 00000-0000" />
                  </div>
                  <div>
                    <label class="input-label">WhatsApp</label>
                    <input v-model="passenger.whatsapp" class="input mt-1" placeholder="(00) 00000-0000" />
                  </div>
                  <div class="md:col-span-2">
                    <label class="input-label">Local de embarque</label>
                    <input v-model="passenger.boarding_location" class="input mt-1" placeholder="Ponto de encontro" />
                  </div>
                </div>
                <div>
                  <label class="input-label">Observações</label>
                  <textarea
                    v-model="passenger.extras"
                    rows="3"
                    class="input mt-1"
                    placeholder="Informações importantes"
                  ></textarea>
                </div>
              </div>
            </div>
            <div v-else class="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
              <p>Nenhum passageiro cadastrado ainda.</p>
              <p class="mt-1 text-xs text-slate-400">Use os botões acima para adicionar manualmente ou enviar o link.</p>
              <div v-if="canManagePassengers" class="mt-4 flex flex-wrap justify-center gap-2">
                <button type="button" class="pill" @click="startManualPassengerInput">Adicionar passageiros</button>
                <button
                  type="button"
                  class="pill"
                  :disabled="!passengerSale"
                  @click="passengerSale && copyPassengerLink(passengerSale.id)"
                >
                  Enviar link para o cliente
                </button>
              </div>
            </div>
          </div>
        </div>
        <footer class="mt-4 flex justify-end gap-3">
          <button class="pill" @click="closePassengerModal">Cancelar</button>
          <button class="btn-primary" :disabled="passengerSaving || !passengerForm.length" @click="savePassengers">
            {{ passengerSaving ? 'Salvando...' : 'Salvar passageiros' }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import {
  listSales,
  getSaleDetails,
  saveSalePassengers,
  getPassengerLink,
  listProducts,
  getProductDetail,
  createProduct,
  updateProduct,
  adjustProductInventory,
  createPosCheckout,
  createProductPaymentLink,
  deleteProduct,
  simulateSaleStatus,
} from "../../services/finance";
import type {
  CheckoutCartItem,
  InventoryAdjustmentPayload,
  Passenger,
  PaymentLinkResponse,
  PublicCheckoutResponse,
  ProductDetail,
  ProductPayload,
  ProductSummary,
  SaleDetail,
  SaleSummary,
  SalePaymentStatus,
} from "../../types/finance";

type ActiveTab = "products" | "sales";
type SalesViewMode = "cards" | "table";

type ProductVariationForm = {
  public_id: string | null;
  name: string;
  description: string | null;
  price: number;
  people_included: number;
  status: string;
  stock_mode: string;
  total_slots: number | null;
  available_slots: number | null;
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
  variations: ProductVariationForm[];
};

const tabs: { label: string; value: ActiveTab }[] = [
  { label: "Produtos", value: "products" },
  { label: "Vendas", value: "sales" },
];
const salesViewOptions: { label: string; value: SalesViewMode }[] = [
  { label: "Cards", value: "cards" },
  { label: "Tabela", value: "table" },
];

const activeTab = ref<ActiveTab>("products");
const salesViewMode = ref<SalesViewMode>("cards");
const sales = ref<SaleSummary[]>([]);
const salesPagination = ref({ total: 0, page: 1, pageSize: 20 });
const selectedSale = ref<SaleDetail | null>(null);
const saleDetailsVisible = ref(false);

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
const passengerForm = ref<Passenger[]>([]);
const passengerSaving = ref(false);
const activePassengerTab = ref(0);
const canManagePassengers = computed(() => passengerSale.value?.payment_status === "paid");

const manualPassengerTemplate = (): Passenger => ({
  id: Date.now() * -1,
  name: "",
  cpf: "",
  birthdate: "",
  phone: "",
  whatsapp: "",
  boarding_location: "",
  extras: "",
});

const startManualPassengerInput = () => {
  if (!canManagePassengers.value || passengerForm.value.length) return;
  const count = Math.max(passengerSale.value?.passengers_required || 1, 1);
  passengerForm.value = Array.from({ length: count }, () => manualPassengerTemplate());
  activePassengerTab.value = 0;
};

const addManualPassenger = () => {
  if (!canManagePassengers.value) return;
  passengerForm.value.push(manualPassengerTemplate());
  activePassengerTab.value = passengerForm.value.length - 1;
};

const removeManualPassenger = (index: number) => {
  if (!canManagePassengers.value) return;
  if (passengerForm.value.length <= 1) return;
  passengerForm.value.splice(index, 1);
};

const products = ref<ProductSummary[]>([]);
const productsLoading = ref(false);

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
  total_slots: null,
  available_slots: null,
});

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
  variations: [defaultVariation()],
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
const posSelections = reactive<Record<string, number>>({});
const posSaving = ref(false);
const posResult = ref<PublicCheckoutResponse | null>(null);

const paymentLinkModalVisible = ref(false);
const paymentLinkProduct = ref<ProductSummary | null>(null);
const paymentLinkProductId = ref<string>("");
const paymentLinkCustomer = reactive({ name: "", email: "", phone: "" });
const paymentLinkSelections = reactive<Record<string, number>>({});
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
  productForm.variations = [defaultVariation()];
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
  productForm.variations = detail.variations.map(variation => ({
    public_id: variation.public_id,
    name: variation.name,
    description: variation.description ?? null,
    price: variation.price_cents / 100,
    people_included: variation.people_included,
    status: variation.status,
    stock_mode: variation.stock_mode,
    total_slots: variation.total_slots ?? null,
    available_slots: variation.available_slots ?? null,
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
  variations: productForm.variations.map(variation => ({
    public_id: variation.public_id || undefined,
    name: variation.name.trim(),
    description: variation.description,
    price_cents: Math.round((variation.price || 0) * 100),
    currency: "BRL",
    people_included: variation.people_included || 1,
    status: variation.status,
    stock_mode: variation.stock_mode,
    total_slots: variation.stock_mode === "variant" ? variation.total_slots ?? 0 : undefined,
    available_slots: variation.stock_mode === "variant" ? variation.available_slots ?? 0 : undefined,
  })),
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
  if (target) {
    target.variations.forEach(variation => {
      posSelections[variation.public_id] = 0;
    });
  }
  posModalVisible.value = true;
};

const closePosModal = () => {
  posModalVisible.value = false;
};

const syncPosProduct = () => {
  const next = products.value.find(item => item.public_id === posProductId.value) || null;
  posProduct.value = next;
  Object.keys(posSelections).forEach(key => delete posSelections[key]);
  if (next) {
    next.variations.forEach(variation => {
      posSelections[variation.public_id] = 0;
    });
  }
};

const posItems = computed<CheckoutCartItem[]>(() =>
  Object.entries(posSelections)
    .filter(([, quantity]) => quantity && quantity > 0)
    .map(([variation_id, quantity]) => ({ variation_id, quantity })),
);

const posTotal = computed(() => {
  if (!posProduct.value) return 0;
  return posProduct.value.variations.reduce((total, variation) => {
    const quantity = posSelections[variation.public_id] || 0;
    return total + variation.price_cents * quantity;
  }, 0);
});

const posPassengers = computed(() => {
  if (!posProduct.value) return 0;
  return posProduct.value.variations.reduce((total, variation) => {
    const quantity = posSelections[variation.public_id] || 0;
    return total + quantity * (variation.people_included || 1);
  }, 0);
});

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
  if (target) {
    target.variations.forEach(variation => {
      paymentLinkSelections[variation.public_id] = 0;
    });
  }
  paymentLinkModalVisible.value = true;
};

const closePaymentLinkModal = () => {
  paymentLinkModalVisible.value = false;
};

const syncPaymentLinkProduct = () => {
  const next = products.value.find(item => item.public_id === paymentLinkProductId.value) || null;
  paymentLinkProduct.value = next;
  Object.keys(paymentLinkSelections).forEach(key => delete paymentLinkSelections[key]);
  if (next) {
    next.variations.forEach(variation => {
      paymentLinkSelections[variation.public_id] = 0;
    });
  }
};

const paymentLinkItems = computed<CheckoutCartItem[]>(() =>
  Object.entries(paymentLinkSelections)
    .filter(([, quantity]) => quantity && quantity > 0)
    .map(([variation_id, quantity]) => ({ variation_id, quantity })),
);

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
  try {
    const { data } = await getSaleDetails(saleId);
    passengerSale.value = data;
    passengerForm.value = data.passengers || [];
    passengerModalVisible.value = true;
  } catch (err) {
    console.error("Erro ao carregar passageiros", err);
  }
};

const closePassengerModal = () => {
  passengerModalVisible.value = false;
  passengerForm.value = [];
  passengerSale.value = null;
};

const savePassengers = async () => {
  if (!passengerSale.value) return;
  passengerSaving.value = true;
  try {
    const { data } = await saveSalePassengers(passengerSale.value.id, passengerForm.value);
    passengerSale.value = data;
    passengerForm.value = data.passengers || [];
    await loadSales();
    closePassengerModal();
  } catch (err) {
    console.error("Erro ao salvar passageiros", err);
  } finally {
    passengerSaving.value = false;
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
  const paymentStatus = await resolveSalePaymentStatus(saleId);
  if (paymentStatus !== "paid") {
    if (typeof window !== "undefined" && window.alert) {
      window.alert("O formulário de passageiros só é liberado após confirmação do pagamento.");
    }
    return;
  }
  try {
    const { data } = await getPassengerLink(saleId);
    await copyText(data.url);
  } catch (err) {
    console.error("Erro ao copiar link", err);
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
  if (!value) return "Não informado";
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
    return product.date_is_flexible ? `${base} (flexível)` : base;
  }
  return "Sem data definida";
};

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
  return `Manual • ${product.available_slots}/${product.total_slots} vagas`;
};

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

watch(
  () => selectedSale.value,
  value => {
    simulationStatus.value = (value?.payment_status as SalePaymentStatus) || "pending";
  },
);

watch(
  () => passengerForm.value.length,
  length => {
    if (!length) {
      activePassengerTab.value = 0;
    } else if (activePassengerTab.value >= length) {
      activePassengerTab.value = length - 1;
    }
  },
);

watch(
  () => passengerModalVisible.value,
  visible => {
    if (!visible) {
      activePassengerTab.value = 0;
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
  await Promise.all([loadSales(), loadProducts()]);
});
</script>

<style scoped>
.pill {
  @apply rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-slate-300;
}
.pill:disabled {
  @apply cursor-not-allowed border-slate-100 text-slate-400 opacity-60 hover:border-slate-100;
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
.badge {
  @apply rounded-full px-3 py-1;
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
@media (min-width: 1024px) {
  .modal-card--product {
    width: 50vw;
  }
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
