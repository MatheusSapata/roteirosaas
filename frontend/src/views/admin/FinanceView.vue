
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
      <div class="flex items-center justify-between">
        <p class="text-sm text-slate-500">Total de vendas: {{ salesPagination.total }}</p>
        <button class="pill" @click="loadSales">Atualizar</button>
      </div>
      <div v-if="!sales.length" class="placeholder-card">Nenhuma venda encontrada.</div>
      <div v-else class="grid gap-4">
        <article
          v-for="sale in sales"
          :key="sale.id"
          class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Venda #{{ sale.id }} • {{ sale.channel === 'pos' ? 'PDV' : sale.channel === 'link' ? 'Link' : 'Checkout' }}
              </p>
              <h3 class="text-lg font-semibold text-slate-900">{{ sale.product_title }}</h3>
              <p class="text-sm text-slate-500">
                {{ formatCurrency(sale.amount_cents) }} • {{ sale.installments }}x • {{ sale.customer_name || 'Cliente' }}
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
            <button class="pill" @click="copyPassengerLink(sale.id)">Copiar link passageiros</button>
          </div>
        </article>
      </div>
    </section>

    <section v-else class="grid gap-4 md:grid-cols-2">
      <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow">
        <h3 class="text-lg font-semibold text-slate-900">Conta Stripe</h3>
        <p class="mt-1 text-sm text-slate-500">Conecte sua conta para o checkout público e PDV.</p>
        <div class="mt-4 space-y-2 text-sm">
          <p>
            <span class="font-semibold text-slate-600">Status:</span>
            <span :class="accountStatus?.connected ? 'text-emerald-600' : 'text-rose-500'">
              {{ accountStatus?.connected ? 'Conectado' : 'Não conectado' }}
            </span>
          </p>
          <p><span class="font-semibold text-slate-600">E-mail:</span> {{ accountStatus?.email || '-' }}</p>
          <p>
            <span class="font-semibold text-slate-600">Cobranças:</span>
            <span :class="accountStatus?.charges_enabled ? 'text-emerald-600' : 'text-rose-500'">
              {{ accountStatus?.charges_enabled ? 'Liberadas' : 'Pendentes' }}
            </span>
          </p>
          <p>
            <span class="font-semibold text-slate-600">Pagamentos:</span>
            <span :class="accountStatus?.payouts_enabled ? 'text-emerald-600' : 'text-rose-500'">
              {{ accountStatus?.payouts_enabled ? 'Liberados' : 'Pendentes' }}
            </span>
          </p>
        </div>
        <div class="mt-6 flex flex-wrap gap-3">
          <button class="btn-primary" :disabled="onboardingLoading" @click="startOnboarding">
            {{ accountStatus?.connected ? 'Atualizar dados' : 'Conectar Stripe' }}
          </button>
          <button type="button" class="text-sm font-semibold text-slate-500" @click="loadAccountStatus">Atualizar status</button>
        </div>
        <div v-if="accountStatus?.requirements?.length" class="mt-4 rounded-2xl bg-amber-50 p-4 text-sm text-amber-700">
          <p class="font-semibold">Pendências</p>
          <ul class="mt-2 list-disc pl-5">
            <li v-for="req in accountStatus.requirements" :key="req">{{ req }}</li>
          </ul>
        </div>
      </div>
      <div class="rounded-3xl border border-emerald-100 bg-emerald-50 p-6 text-slate-800 shadow">
        <h3 class="text-lg font-semibold">Como funciona</h3>
        <ul class="mt-3 space-y-2 text-sm">
          <li>• Checkout Stripe integrado às páginas e ao PDV.</li>
          <li>• Repasse automático com taxa de 1,5%.</li>
          <li>• Controle de estoque centralizado para evitar overbooking.</li>
        </ul>
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
              <p v-if="posResult" class="mt-2 text-xs text-emerald-600">Venda #{{ posResult.sale_id }} criada.</p>
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
        <div class="space-y-3 text-sm">
          <p><span class="font-semibold text-slate-600">Cliente:</span> {{ selectedSale.customer_name || 'Não informado' }}</p>
          <p><span class="font-semibold text-slate-600">Valor:</span> {{ formatCurrency(selectedSale.amount_cents) }}</p>
          <p><span class="font-semibold text-slate-600">Canal:</span> {{ selectedSale.channel }}</p>
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
      <div class="modal-card max-w-2xl">
        <header class="mb-4 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              Passageiros venda #{{ passengerSale.id }}
            </p>
            <h3 class="text-lg font-semibold text-slate-900">{{ passengerSale.product_title }}</h3>
          </div>
          <button class="text-slate-500" @click="closePassengerModal">×</button>
        </header>
        <div class="max-h-[60vh] space-y-3 overflow-y-auto">
          <div v-for="(passenger, index) in passengerForm" :key="index" class="rounded-xl border border-slate-100 p-3">
            <p class="text-sm font-semibold text-slate-900">Passageiro {{ index + 1 }}</p>
            <input v-model="passenger.name" class="input mt-2" placeholder="Nome completo" />
            <input v-model="passenger.cpf" class="input mt-2" placeholder="CPF" />
            <input v-model="passenger.phone" class="input mt-2" placeholder="Telefone" />
            <textarea v-model="passenger.extras" rows="2" class="input mt-2" placeholder="Observações"></textarea>
          </div>
        </div>
        <footer class="mt-4 flex justify-end gap-3">
          <button class="pill" @click="closePassengerModal">Cancelar</button>
          <button class="btn-primary" :disabled="passengerSaving" @click="savePassengers">
            {{ passengerSaving ? 'Salvando...' : 'Salvar passageiros' }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import {
  fetchStripeAccountStatus,
  createStripeOnboardingLink,
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
} from "../../services/finance";
import type {
  CheckoutCartItem,
  InventoryAdjustmentPayload,
  Passenger,
  PaymentLinkResponse,
  ProductDetail,
  ProductPayload,
  ProductSummary,
  SaleDetail,
  SaleSummary,
  StripeAccountStatus,
} from "../../types/finance";

type ActiveTab = "products" | "sales" | "config";

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
  { label: "Configurações", value: "config" },
];

const activeTab = ref<ActiveTab>("products");
const accountStatus = ref<StripeAccountStatus | null>(null);
const onboardingLoading = ref(false);

const sales = ref<SaleSummary[]>([]);
const salesPagination = ref({ total: 0, page: 1, pageSize: 20 });
const selectedSale = ref<SaleDetail | null>(null);
const saleDetailsVisible = ref(false);

const passengerSale = ref<SaleDetail | null>(null);
const passengerModalVisible = ref(false);
const passengerForm = ref<Passenger[]>([]);
const passengerSaving = ref(false);

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
const posResult = ref<{ sale_id: number; client_secret: string; passenger_token: string } | null>(null);

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

const statusClasses = {
  payment: {
    succeeded: "bg-emerald-100 text-emerald-700",
    processing: "bg-amber-100 text-amber-700",
    canceled: "bg-rose-100 text-rose-600",
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

const loadAccountStatus = async () => {
  try {
    const { data } = await fetchStripeAccountStatus();
    accountStatus.value = data;
  } catch (err) {
    console.error("Erro ao carregar status Stripe", err);
  }
};

const startOnboarding = async () => {
  onboardingLoading.value = true;
  try {
    const { data } = await createStripeOnboardingLink();
    window.location.assign(data.url);
  } catch (err) {
    console.error("Erro ao iniciar onboarding", err);
  } finally {
    onboardingLoading.value = false;
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

const copyPassengerLink = async (saleId: number) => {
  try {
    const { data } = await getPassengerLink(saleId);
    await navigator.clipboard.writeText((data as { url: string }).url);
  } catch (err) {
    console.error("Erro ao copiar link", err);
  }
};
const formatCurrency = (value?: number | null) => {
  const cents = typeof value === "number" ? value : 0;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
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
  succeeded: "Pago",
  processing: "Processando",
  requires_payment_method: "Aguardando",
  requires_action: "Ação necessária",
  canceled: "Cancelado",
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
  if (status === "succeeded") return "succeeded";
  if (status === "processing") return "processing";
  if (status === "canceled") return "canceled";
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

const copyText = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
  } catch (err) {
    console.error("Erro ao copiar texto", err);
  }
};

onMounted(async () => {
  await Promise.all([loadAccountStatus(), loadSales(), loadProducts()]);
});
</script>

<style scoped>
.pill {
  @apply rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-slate-300;
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
