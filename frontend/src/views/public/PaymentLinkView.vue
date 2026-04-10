<template>
  <div class="checkout-shell min-h-screen text-white">
    <div class="checkout-noise"></div>

    <div class="checkout-container relative mx-auto max-w-[1360px] px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
      <div
        v-if="loading"
        class="glass-panel rounded-[32px] border border-white/10 px-6 py-16 text-center text-sm text-white/70"
      >
        Carregando checkout...
      </div>

      <div
        v-else-if="errorMessage"
        class="rounded-[32px] border border-rose-500/30 bg-rose-500/10 px-6 py-16 text-center text-sm text-rose-100"
      >
        {{ errorMessage }}
      </div>

      <div
        v-else-if="sale"
        class="payment-grid grid grid-cols-1 items-start gap-3 xl:gap-4"
      >
        <div class="payment-main space-y-3 xl:space-y-4">
          <section class="hero-card overflow-hidden rounded-[32px] border border-white/10">
            <div class="relative h-[240px] sm:h-[272px] lg:h-[288px]">
              <div class="absolute inset-0 bg-cover bg-center" :style="heroBackgroundStyle"></div>
            </div>
          </section>

          <section class="section-card">
            <header class="section-header">
              <div>
                <p class="eyebrow">Comprador</p>
                <h2 class="section-title">Informações pessoais</h2>
                <p class="section-subtitle">Preencha os dados para finalizar sua compra com segurança.</p>
              </div>
            </header>

            <div class="mt-6 grid gap-4 md:grid-cols-2">
              <div class="form-field md:col-span-2">
                <label>Nome completo</label>
                <input
                  v-model="buyer.name"
                  :disabled="isPaid"
                  type="text"
                  placeholder="Nome e sobrenome"
                />
              </div>

              <div class="form-field">
                <label>E-mail</label>
                <input
                  v-model="buyer.email"
                  :disabled="isPaid"
                  type="email"
                  placeholder="voce@exemplo.com"
                />
              </div>

              <div class="form-field">
                <label>Telefone / WhatsApp</label>
                <input
                  v-model="buyer.phone"
                  :disabled="isPaid"
                  type="tel"
                  placeholder="(11) 99999-0000"
                />
              </div>

              <div class="form-field">
                <label>CPF</label>
                <input
                  v-model="buyer.document"
                  :disabled="isPaid"
                  type="text"
                  placeholder="000.000.000-00"
                />
              </div>

              <div class="form-field">
                <label>Data de nascimento</label>
                <input
                  v-model="buyer.birthdate"
                  :disabled="isPaid"
                  type="date"
                />
              </div>

              <div class="form-field md:col-span-2">
                <label>Endereço (opcional)</label>
                <input
                  v-model="buyer.address"
                  :disabled="isPaid"
                  type="text"
                  placeholder="Rua, número, cidade"
                />
              </div>
            </div>
          </section>

          <section class="section-card">
            <header class="section-header">
              <div>
                <p class="eyebrow">Pagamento</p>
                <h2 class="section-title">Escolha como deseja pagar</h2>
                <p class="section-subtitle">Selecione o método com que deseja concluir esta compra.</p>
              </div>
            </header>

            <div class="mt-6 grid gap-3 md:grid-cols-3">
              <button
                v-for="method in paymentOptions"
                :key="method.value"
                type="button"
                class="payment-tab"
                :class="{ 'payment-tab-active': selectedMethod === method.value }"
                @click="selectMethod(method.value)"
                :disabled="isPaid"
              >
                <div class="payment-tab-top">
                  <span class="payment-icon">{{ method.icon }}</span>
                  <span class="payment-title">{{ method.label }}</span>
                </div>
                <p class="payment-description">{{ method.description }}</p>
              </button>
            </div>

            <div v-if="showCreditCard" class="payment-panel mt-6">
              <div class="grid gap-4 md:grid-cols-2">
                <div class="form-field">
                  <label>Número do cartão</label>
                  <input
                    v-model="cardForm.number"
                    :disabled="isPaid"
                    type="text"
                    inputmode="numeric"
                    placeholder="0000 0000 0000 0000"
                  />
                </div>

                <div class="form-field">
                  <label>Nome impresso</label>
                  <input
                    v-model="cardForm.holder"
                    :disabled="isPaid"
                    type="text"
                    placeholder="Titular do cartão"
                  />
                </div>

                <div class="form-field">
                  <label>CPF do titular</label>
                  <input
                    v-model="cardForm.document"
                    :disabled="isPaid"
                    type="text"
                    inputmode="numeric"
                    placeholder="000.000.000-00"
                  />
                </div>

                <div class="grid gap-4 md:grid-cols-3 md:col-span-2">
                  <div class="form-field md:col-span-1">
                    <label>Validade</label>
                    <input
                      v-model="cardForm.expiry"
                      :disabled="isPaid"
                      type="text"
                      inputmode="numeric"
                      placeholder="MM/AA"
                    />
                  </div>

                  <div class="form-field md:col-span-1">
                    <label>CVV</label>
                    <input
                      v-model="cardForm.cvv"
                      :disabled="isPaid"
                      type="text"
                      inputmode="numeric"
                      placeholder="123"
                    />
                  </div>

                  <div class="form-field md:col-span-1">
                    <label>Parcelas</label>
                    <select v-model.number="cardForm.installments" :disabled="isPaid">
                      <option v-for="qty in installmentOptions" :key="qty" :value="qty">
                        {{ qty }}x de {{ formatCurrency((sale?.amount_cents || 0) / qty, sale?.currency || "BRL") }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <div class="info-strip mt-4">
                <span class="info-dot"></span>
                Seus dados de pagamento são protegidos e criptografados.
              </div>
            </div>

            <div v-if="selectedMethod === 'pix'" class="payment-panel payment-panel-emerald mt-6">
              <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-base font-semibold text-white">Pagamento via Pix</p>
                  <p class="mt-1 text-sm text-emerald-100/90">
                    A confirmação costuma acontecer automaticamente poucos segundos após o envio.
                  </p>
                </div>
                <span class="mini-badge mini-badge-emerald">Instantâneo</span>
              </div>

              <ul class="mt-4 space-y-2 text-sm text-emerald-100/90">
                <li>• Geraremos o QR Code e o código copia e cola após a confirmação.</li>
                <li>• O código Pix terá validade limitada para pagamento.</li>
                <li>• Assim que aprovado, o status será atualizado automaticamente.</li>
              </ul>
            </div>

            <div v-if="selectedMethod === 'boleto'" class="payment-panel payment-panel-amber mt-6">
              <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-base font-semibold text-white">Pagamento via boleto</p>
                  <p class="mt-1 text-sm text-amber-100/90">
                    O pagamento por boleto pode levar até 48 horas úteis para compensar.
                  </p>
                </div>
                <span class="mini-badge mini-badge-amber">Até 48h</span>
              </div>

              <div class="mt-4 grid gap-4 md:grid-cols-2">
                <div class="form-field">
                  <label>CPF/CNPJ</label>
                  <input
                    v-model="boletoForm.document"
                    :disabled="isPaid"
                    type="text"
                    placeholder="000.000.000-00"
                  />
                </div>

                <div class="form-field">
                  <label>CEP</label>
                  <input
                    v-model="boletoForm.zipcode"
                    :disabled="isPaid"
                    type="text"
                    placeholder="00000-000"
                  />
                </div>
              </div>

              <p class="mt-4 text-sm text-amber-100/90">
                Após gerar, o boleto ficará disponível para visualização e download.
              </p>
            </div>
          </section>

          <section class="section-card">
            <header class="section-header">
              <div>
                <p class="eyebrow">Resumo do pedido</p>
                <h2 class="section-title">Confira sua compra</h2>
                <p class="section-subtitle">Revise os itens selecionados antes de concluir o pagamento.</p>
              </div>

              <span class="summary-count">
                {{ sale.items.length }} {{ sale.items.length === 1 ? "item" : "itens" }}
              </span>
            </header>

            <div class="mt-6 space-y-3">
              <article
                v-for="item in sale.items"
                :key="item.id"
                class="item-card"
              >
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <p class="text-base font-semibold text-white">
                      {{ item.quantity }}x {{ item.variation_name }}
                    </p>
                    <p class="mt-1 text-sm text-white/55">
                      Inclui {{ item.people_count }}
                      {{ item.people_count === 1 ? "passageiro" : "passageiros" }}
                      • Ocupação {{ item.consumed_capacity }}
                    </p>
                  </div>

                  <span class="text-base font-bold text-white">
                    {{ formatCurrency(item.total_price + item.child_extra_amount_cents, sale.currency) }}
                  </span>
                </div>

                <ul v-if="item.child_breakdown.length" class="mt-3 space-y-1 text-xs text-white/45">
                  <li v-for="child in item.child_breakdown" :key="child.key">
                    + {{ child.quantity }}x {{ child.label }} ·
                    {{ formatCurrency(child.total_amount_cents, sale.currency) }}
                  </li>
                </ul>
              </article>
            </div>

            <div class="summary-box mt-6">
              <dl class="space-y-3 text-sm text-white/70">
                <div class="flex items-center justify-between gap-4">
                  <dt>Subtotal</dt>
                  <dd class="font-medium text-white/90">{{ formatCurrency(subtotalAmount, sale.currency) }}</dd>
                </div>

                <div class="flex items-center justify-between gap-4">
                  <dt>Taxas e encargos</dt>
                  <dd class="font-medium text-white/90">{{ formatCurrency(feeAmount, sale.currency) }}</dd>
                </div>
              </dl>

              <div class="mt-5 flex items-end justify-between gap-4 border-t border-white/10 pt-5">
                <div>
                  <p class="text-xs uppercase tracking-[0.28em] text-white/45">Total a pagar</p>
                  <p class="mt-1 text-sm text-white/60">Forma selecionada: {{ paymentMethodLabel }}</p>
                </div>
                <span class="summary-total">
                  {{ formatCurrency(sale.amount_cents, sale.currency) }}
                </span>
              </div>
            </div>

            <button
              type="button"
              class="checkout-button mt-6"
              :disabled="isPaid || confirming || submitDisabled"
              @click="confirmPayment"
            >
              {{ confirmButtonLabel }}
            </button>

            <div class="trust-box mt-4">
              <div class="trust-icon">🔒</div>
              <div>
                <p class="text-sm font-semibold text-white">Ambiente protegido</p>
                <p class="mt-1 text-xs leading-5 text-white/60">
                  Transação processada em ambiente seguro pelas soluções do Roteiro Online.
                  Seus dados são protegidos e criptografados.
                </p>
              </div>
            </div>

            <p v-if="confirmError" class="mt-4 text-center text-sm text-rose-300">
              {{ confirmError }}
            </p>
          </section>

          <section
            v-if="success || isPaid"
            class="rounded-[28px] border border-white/12 bg-black/70 p-6 text-white shadow-[0_24px_80px_rgba(0,0,0,0.55)]"
          >
            <p class="text-lg font-semibold">Pagamento confirmado!</p>
            <p class="mt-2 text-sm text-white/70">
              <template v-if="requiresPassengers">
                {{
                  success
                    ? "Recebemos sua confirmacao. Utilize o link abaixo para preencher os dados dos passageiros."
                    : "Este pedido ja estava confirmado pela agencia responsavel."
                }}
              </template>
              <template v-else>
                Pagamento confirmado! Este produto não exige o preenchimento de formulários adicionais.
              </template>
            </p>
            <p
              v-if="sale?.has_rooms && !requiresPassengers"
              class="mt-2 text-xs uppercase tracking-wide text-white/60"
            >
              A agência organizará a hospedagem automaticamente após a confirmação.
            </p>

            <div v-if="requiresPassengers && passengerFormLink" class="passenger-card mt-5">
              <p class="passenger-card-label">Formulario de passageiros</p>
              <a
                :href="passengerFormLink"
                class="passenger-card-link"
                target="_blank"
                rel="noopener"
              >
                Acessar formulario
              </a>
            </div>

            <p v-else-if="requiresPassengers" class="mt-4 text-sm text-white/60">
              A agencia responsavel enviara o formulario de passageiros em breve.
            </p>

            <button type="button" class="open-modal-button mt-6" @click="openSuccessModal">
              Ver confirmacao em destaque
            </button>
          </section>
        </div>

        <aside class="payment-side space-y-4 lg:sticky lg:top-8">
          <section class="sidebar-panel overflow-hidden">
            <div class="sidebar-topline"></div>

            <div class="p-5 sm:p-6">
              <div class="flex items-start gap-4">
                <div class="product-thumb h-20 w-20 shrink-0">
                  <img
                    v-if="productImage"
                    :src="productImage"
                    alt="Produto"
                    class="h-full w-full object-cover"
                  />
                  <div
                    v-else
                    class="flex h-full w-full items-center justify-center bg-gradient-to-br from-emerald-500/35 via-slate-800 to-slate-950 text-[10px] font-bold uppercase tracking-[0.22em] text-white/60"
                  >
                    Produto
                  </div>
                </div>

                <div class="min-w-0 flex-1">
                  <p class="eyebrow">Produto</p>
                  <h3 class="truncate text-xl font-bold text-white">{{ sale.product_title }}</h3>
                  <p class="mt-2 text-sm leading-6 text-white/62">
                    {{ productDescription }}
                  </p>
                </div>
              </div>

              <div class="price-card mt-6">
                <p class="text-xs uppercase tracking-[0.28em] text-white/45">Valor desta compra</p>
                <p class="mt-3 text-3xl font-black tracking-tight text-emerald-400">
                  {{ formatCurrency(sale.amount_cents, sale.currency) }}
                </p>

                <div class="mt-4 grid gap-3 text-sm text-white/68">
                  <div class="flex items-center justify-between gap-4">
                    <span>Forma de pagamento</span>
                    <span class="font-semibold text-white">{{ paymentMethodLabel }}</span>
                  </div>

                  <div class="flex items-center justify-between gap-4">
                    <span>Parcelamento</span>
                    <span class="font-semibold text-white">{{ parcelLabel }}</span>
                  </div>

                  <div class="flex items-center justify-between gap-4">
                    <span>Status do pedido</span>
                    <span class="font-semibold" :class="isPaid ? 'text-emerald-300' : 'text-amber-300'">
                      {{ isPaid ? "Pago" : "Aguardando pagamento" }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="mini-summary mt-6">
                <p class="text-xs uppercase tracking-[0.28em] text-white/45">Compra resumida</p>

                <div class="mt-4 space-y-3">
                  <div
                    v-for="item in sale.items"
                    :key="item.id"
                    class="flex items-start justify-between gap-3 text-sm"
                  >
                    <div>
                      <p class="font-semibold text-white">{{ item.quantity }}x {{ item.variation_name }}</p>
                      <p class="mt-1 text-xs text-white/45">
                        {{ item.people_count }} {{ item.people_count === 1 ? "passageiro" : "passageiros" }}
                      </p>
                    </div>

                    <span class="whitespace-nowrap font-semibold text-white/85">
                      {{ formatCurrency(item.total_price + item.child_extra_amount_cents, sale.currency) }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="trust-side mt-6">
                <div class="flex flex-wrap items-center gap-3">
                  <p class="text-sm font-semibold text-white">Desenvolvido pelo</p>
                  <img :src="brandLogo" alt="Roteiro Online" class="h-[4.16rem] w-auto" />
                </div>
                <p class="mt-2 text-sm leading-6 text-white/58">
                  Sua compra está sendo processada em ambiente seguro, com criptografia,
                  proteção de dados e fluxo profissional para a agência responsável.
                </p>

                <div class="mt-4 flex flex-wrap gap-2">
                  <span class="side-chip">Privacidade</span>
                  <span class="side-chip">Segurança</span>
                  <span class="side-chip">Confiável</span>
                </div>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </div>

    <transition name="fade">
      <div
        v-if="showSuccessModal && (success || isPaid)"
        class="success-modal-overlay"
      >
        <div class="success-modal-panel">
          <button type="button" class="modal-close" @click="closeSuccessModal">&times;</button>
          <p class="modal-eyebrow">Pagamento confirmado</p>
          <h3 class="modal-title">{{ isPaid ? "Pedido pago" : "Pagamento aprovado" }}</h3>
          <p class="modal-text">
            <template v-if="requiresPassengers">
              {{
                success
                  ? "Tudo certo! A compra foi registrada e agora voce pode preencher os dados dos passageiros no link abaixo."
                  : "Este pedido ja estava confirmado anteriormente, mas mantivemos os detalhes disponiveis para consulta."
              }}
            </template>
            <template v-else>
              Pagamento confirmado! Este produto não exige o preenchimento de formulários de passageiros.
            </template>
          </p>
          <p
            v-if="sale?.has_rooms && !requiresPassengers"
            class="mt-2 text-xs uppercase tracking-wide text-white/65"
          >
            A agência organizará automaticamente a acomodação conforme sua compra.
          </p>
          <div v-if="requiresPassengers && passengerFormLink" class="passenger-card modal-passenger-card">
            <p class="passenger-card-label">Formulario de passageiros</p>
            <a
              :href="passengerFormLink"
              class="passenger-card-link"
              target="_blank"
              rel="noopener"
            >
              Acessar formulario
            </a>
          </div>

          <p v-else-if="requiresPassengers" class="modal-text text-white/65">
            A agencia responsavel entrara em contato com o formulario para complementar os dados.
          </p>

          <div class="success-modal-actions">
            <button type="button" class="modal-primary" @click="closeSuccessModal">Fechar</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { confirmPublicSale, getPublicPaymentLinkDetails, getPublicProductDetail } from "../../services/finance";
import type { ProductDetail, PublicCheckoutResponse, SaleDetail } from "../../types/finance";
import BrandLogo from "../../assets/Logo Branco - Roteiro Online.png";

const route = useRoute();
const brandLogo = BrandLogo;

const sale = ref<SaleDetail | null>(null);
const productDetail = ref<ProductDetail | null>(null);
const loading = ref(true);
const errorMessage = ref<string | null>(null);
const success = ref<PublicCheckoutResponse | null>(null);
const selectedMethod = ref<"credit_card" | "pix" | "boleto">("credit_card");
const confirming = ref(false);
const confirmError = ref<string | null>(null);
const showSuccessModal = ref(false);

const buyer = reactive({
  name: "",
  email: "",
  phone: "",
  document: "",
  birthdate: "",
  address: "",
});

const cardForm = reactive({
  number: "",
  holder: "",
  document: "",
  expiry: "",
  cvv: "",
  installments: 1,
});

const boletoForm = reactive({
  document: "",
  zipcode: "",
});

const paymentOptions = [
  {
    value: "credit_card",
    label: "Cartão de crédito",
    description: "Aprovação imediata",
    icon: "💳",
  },
  {
    value: "pix",
    label: "Pix",
    description: "Pagamento instantâneo",
    icon: "⚡",
  },
  {
    value: "boleto",
    label: "Boleto",
    description: "Compensação em até 48h",
    icon: "📄",
  },
] as const;

const installmentOptions = Array.from({ length: 6 }).map((_, index) => index + 1);

const token = computed(() => {
  const raw = route.params.token;
  return Array.isArray(raw) ? raw[0] : raw || "";
});

const isPaid = computed(() => sale.value?.payment_status === "paid");
const requiresPassengers = computed(() => !!sale.value?.requires_passengers);

const passengerFormLink = computed(() => {
  if (!requiresPassengers.value) {
    return null;
  }
  if (success.value?.passenger_token) {
    return `/passageiros/${success.value.passenger_token}`;
  }
  return null;
});

const subtotalAmount = computed(() => sale.value?.base_amount_cents || sale.value?.amount_cents || 0);
const feeAmount = computed(() => (sale.value?.gross_amount_cents || 0) - subtotalAmount.value);

const showCreditCard = computed(() => selectedMethod.value === "credit_card");

const productImage = computed(() => productDetail.value?.checkout_product_image_url || null);

const heroBackgroundStyle = computed(() => {
  const banner = productDetail.value?.checkout_banner_url;
  if (banner) {
    return {
      backgroundImage: `url(${banner})`,
      backgroundSize: "cover",
      backgroundPosition: "center",
    };
  }

  return {
    backgroundImage:
      "radial-gradient(circle at top left, rgba(16,185,129,0.22), transparent 28%), linear-gradient(135deg, #020617 0%, #0f172a 48%, #020617 100%)",
    backgroundSize: "cover",
    backgroundPosition: "center",
  };
});

const heroSubtitle = computed(() => {
  if (productDetail.value?.description) return productDetail.value.description;
  if (sale.value?.product_description) return sale.value.product_description;
  return "Finalize sua compra com segurança em um checkout premium, protegido e confiável.";
});

const productDescription = computed(() => {
  if (sale.value?.product_description) return sale.value.product_description;
  if (productDetail.value?.description) return productDetail.value.description;
  return "Experiência organizada por especialistas para uma compra segura e profissional.";
});

const paymentMethodLabel = computed(() => {
  const option = paymentOptions.find(option => option.value === selectedMethod.value);
  return option ? option.label : "Pagamento";
});

const parcelLabel = computed(() => {
  if (!showCreditCard.value) return "Pagamento único";
  return `${cardForm.installments}x`;
});

const confirmButtonLabel = computed(() => {
  if (isPaid.value) return "Pagamento confirmado";
  if (confirming.value) return "Processando...";
  if (selectedMethod.value === "pix") return "Gerar Pix";
  if (selectedMethod.value === "boleto") return "Gerar boleto";
  return "Pagar com cartão";
});

const submitDisabled = computed(() => {
  if (!buyer.name.trim() || !buyer.email.trim() || !buyer.phone.trim()) {
    return true;
  }

  if (showCreditCard.value) {
    return !cardForm.number || !cardForm.holder || !cardForm.document || !cardForm.expiry || !cardForm.cvv;
  }

  if (selectedMethod.value === "boleto") {
    return !boletoForm.document || !boletoForm.zipcode;
  }

  return false;
});

const formatCurrency = (amountCents: number, currency = "BRL") => {
  const value = (amountCents || 0) / 100;

  try {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency,
    }).format(value);
  } catch {
    return `R$ ${value.toFixed(2)}`;
  }
};

const hydrateBuyer = (detail: SaleDetail) => {
  buyer.name = detail.customer_name || "";
  buyer.email = detail.customer_email || "";
  buyer.phone = detail.customer_phone || "";
};

const loadProductAppearance = async (productPublicId?: string | null) => {
  if (!productPublicId) return;

  try {
    const { data } = await getPublicProductDetail(productPublicId);
    productDetail.value = data;
  } catch {
    productDetail.value = null;
  }
};

const loadPaymentLink = async () => {
  if (!token.value) {
    errorMessage.value = "Link inválido.";
    loading.value = false;
    return;
  }

  try {
    const { data } = await getPublicPaymentLinkDetails(token.value);
    sale.value = data;
    selectedMethod.value = (data.payment_method as typeof selectedMethod.value) || "credit_card";
    cardForm.installments = data.installments || 1;
    hydrateBuyer(data);
    await loadProductAppearance(data.product_public_id);
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Link indisponível ou expirado.";
  } finally {
    loading.value = false;
  }
};

const selectMethod = (value: typeof selectedMethod.value) => {
  if (isPaid.value) return;
  selectedMethod.value = value;
};

const buildCustomerPayload = () => ({
  name: buyer.name.trim() || sale.value?.customer_name || "",
  email: buyer.email.trim() || sale.value?.customer_email || "",
  phone: buyer.phone.trim() || sale.value?.customer_phone || "",
});

const confirmPayment = async () => {
  if (!sale.value || isPaid.value) return;

  confirming.value = true;
  confirmError.value = null;

  try {
    const customerPayload = buildCustomerPayload();

    const { data } = await confirmPublicSale(sale.value.id, {
      payment_method: selectedMethod.value,
      installments: showCreditCard.value ? cardForm.installments : sale.value.installments || 1,
      customer: customerPayload,
    });

    success.value = data;
    sale.value = {
      ...sale.value,
      payment_status: "paid",
      customer_name: customerPayload.name,
      customer_email: customerPayload.email,
      customer_phone: customerPayload.phone,
    } as SaleDetail;
    showSuccessModal.value = true;
  } catch (err: any) {
    confirmError.value = err?.response?.data?.detail || "Não foi possível confirmar o pagamento.";
  } finally {
    confirming.value = false;
  }
};

const openSuccessModal = () => {
  if (success.value || isPaid.value) {
    showSuccessModal.value = true;
  }
};

const closeSuccessModal = () => {
  showSuccessModal.value = false;
};

onMounted(() => {
  loadPaymentLink();
});
</script>

<style scoped>
.checkout-shell {
  position: relative;
  background:
    radial-gradient(circle at top left, rgba(16, 185, 129, 0.05), transparent 22%),
    linear-gradient(180deg, #000000 0%, #030303 35%, #050505 100%);
}

.checkout-noise {
  pointer-events: none;
  position: absolute;
  inset: 0;
  opacity: 0.22;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: linear-gradient(to bottom, black, transparent 92%);
}

.checkout-container {
  width: 70%;
  margin-left: auto;
  margin-right: auto;
}

.payment-grid {
  width: 100%;
}

.payment-main,
.payment-side {
  min-width: 0;
}

@media (min-width: 1024px) {
  .payment-grid {
    grid-template-columns: minmax(0, 1.6fr) minmax(320px, 420px);
  }
}

.glass-panel {
  backdrop-filter: blur(16px);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.72), rgba(2, 6, 23, 0.82));
}

.hero-card {
  background: linear-gradient(180deg, rgba(10, 10, 10, 0.9), rgba(4, 4, 4, 0.96));
  box-shadow: 0 30px 100px rgba(0, 0, 0, 0.45);
}

.section-card {
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(180deg, rgba(8, 8, 8, 0.96), rgba(12, 12, 12, 0.98));
  padding: 1.5rem;
  box-shadow:
    0 26px 70px rgba(0, 0, 0, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(8px);
}

@media (min-width: 1024px) {
  .section-card {
    padding: 1.75rem;
  }
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.section-title {
  margin-top: 0.35rem;
  font-size: 1.25rem;
  line-height: 1.2;
  font-weight: 800;
  color: #ffffff;
}

.section-subtitle {
  margin-top: 0.55rem;
  max-width: 42rem;
  font-size: 0.85rem;
  line-height: 1.6;
  color: rgba(248, 250, 252, 0.58);
}

.eyebrow {
  font-size: 0.72rem;
  letter-spacing: 0.34em;
  text-transform: uppercase;
  color: rgba(248, 250, 252, 0.5);
}

.eyebrow-hero {
  font-size: 0.74rem;
  letter-spacing: 0.34em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.72);
}

.hero-chip {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.08);
  padding: 0.55rem 0.8rem;
  border-radius: 999px;
  backdrop-filter: blur(8px);
}

.status-paid,
.status-pending {
  border-radius: 999px;
}

.status-paid {
  background: rgba(16, 185, 129, 0.18);
  color: #86efac;
  border: 1px solid rgba(16, 185, 129, 0.18);
}

.status-pending {
  background: rgba(245, 158, 11, 0.16);
  color: #fcd34d;
  border: 1px solid rgba(245, 158, 11, 0.14);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.form-field label {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: rgba(248, 250, 252, 0.7);
}

.form-field input,
.form-field select {
  min-height: 3rem;
  width: 100%;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background:
    linear-gradient(180deg, rgba(6, 6, 6, 0.96), rgba(10, 10, 10, 0.98));
  padding: 0.75rem 0.95rem;
  color: #f8fafc;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease,
    background-color 0.2s ease;
}

.form-field input::placeholder,
.form-field select::placeholder {
  color: rgba(248, 250, 252, 0.28);
}

.form-field input:focus,
.form-field select:focus {
  border-color: rgba(16, 185, 129, 0.7);
  box-shadow:
    0 0 0 3px rgba(16, 185, 129, 0.15),
    0 10px 30px rgba(16, 185, 129, 0.06);
}

.form-field input:disabled,
.form-field select:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.form-field select option {
  color: #0f172a;
  background-color: #f8fafc;
}

.form-field select option:disabled {
  color: #94a3b8;
}

.payment-tab {
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.015));
  padding: 1rem 1rem 0.95rem;
  text-align: left;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    background-color 0.18s ease,
    box-shadow 0.18s ease;
}

.payment-tab:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(255, 255, 255, 0.22);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
}

.payment-tab:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.payment-tab-active {
  border-color: rgba(16, 185, 129, 0.75);
  background:
    linear-gradient(180deg, rgba(16, 185, 129, 0.18), rgba(16, 185, 129, 0.08));
  box-shadow:
    0 16px 40px rgba(16, 185, 129, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.payment-tab-top {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.payment-icon {
  display: inline-flex;
  height: 2.1rem;
  width: 2.1rem;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 1rem;
}

.payment-title {
  font-size: 0.98rem;
  font-weight: 700;
  color: #ffffff;
}

.payment-description {
  margin-top: 0.55rem;
  font-size: 0.8rem;
  line-height: 1.5;
  color: rgba(248, 250, 252, 0.58);
}

.payment-panel {
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(180deg, rgba(12, 12, 12, 0.96), rgba(18, 18, 18, 0.98));
  padding: 1rem;
}

@media (min-width: 768px) {
  .payment-panel {
    padding: 1.15rem;
  }
}

.payment-panel-emerald {
  border-color: rgba(16, 185, 129, 0.28);
  background:
    linear-gradient(180deg, rgba(16, 185, 129, 0.16), rgba(16, 185, 129, 0.07));
}

.payment-panel-amber {
  border-color: rgba(245, 158, 11, 0.26);
  background:
    linear-gradient(180deg, rgba(245, 158, 11, 0.14), rgba(245, 158, 11, 0.06));
}

.info-strip {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  font-size: 0.82rem;
  color: rgba(248, 250, 252, 0.6);
}

.info-dot {
  height: 0.55rem;
  width: 0.55rem;
  border-radius: 999px;
  background: #34d399;
  box-shadow: 0 0 12px rgba(52, 211, 153, 0.8);
}

.mini-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.5rem 0.8rem;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.mini-badge-emerald {
  background: rgba(16, 185, 129, 0.18);
  color: #a7f3d0;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.mini-badge-amber {
  background: rgba(245, 158, 11, 0.18);
  color: #fde68a;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.summary-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  padding: 0.55rem 0.85rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: #fff;
}

.item-card {
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(180deg, rgba(12, 12, 12, 0.96), rgba(18, 18, 18, 0.98));
  padding: 1rem 1rem 0.95rem;
}

.summary-box {
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(180deg, rgba(10, 10, 10, 0.97), rgba(16, 16, 16, 0.99));
  padding: 1.1rem 1rem 1.05rem;
}

.summary-total {
  font-size: 1.8rem;
  line-height: 1;
  font-weight: 900;
  letter-spacing: -0.03em;
  color: #34d399;
  text-shadow: 0 0 18px rgba(52, 211, 153, 0.16);
}

@media (min-width: 640px) {
  .summary-total {
    font-size: 2.1rem;
  }
}

.checkout-button {
  width: 100%;
  border: none;
  border-radius: 22px;
  background: linear-gradient(180deg, #34d399 0%, #10b981 100%);
  padding: 1rem 1.25rem;
  font-size: 1.05rem;
  font-weight: 900;
  color: #ffffff;
  box-shadow:
    0 18px 45px rgba(16, 185, 129, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    filter 0.18s ease;
}

.checkout-button:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.04);
  box-shadow:
    0 22px 55px rgba(16, 185, 129, 0.34),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.checkout-button:disabled {
  cursor: not-allowed;
  opacity: 0.58;
  transform: none;
  box-shadow: none;
}

.passenger-card {
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background:
    linear-gradient(180deg, rgba(6, 6, 6, 0.98), rgba(10, 10, 10, 0.98));
  padding: 1rem 1.25rem;
}

.passenger-card-label {
  font-size: 0.72rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: rgba(248, 250, 252, 0.6);
}

.passenger-card-link {
  display: inline-flex;
  margin-top: 0.8rem;
  font-size: 0.95rem;
  font-weight: 700;
  color: #ffffff;
  text-decoration: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.25);
  padding-bottom: 0.15rem;
}

.passenger-card-link:hover {
  color: #a7f3d0;
  border-color: rgba(167, 243, 208, 0.8);
}

.open-modal-button {
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  padding: 0.7rem 1.4rem;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(248, 250, 252, 0.82);
  transition:
    border-color 0.2s ease,
    background-color 0.2s ease;
}

.open-modal-button:hover {
  border-color: rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.success-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: rgba(0, 0, 0, 0.82);
  backdrop-filter: blur(6px);
}

.success-modal-panel {
  width: min(560px, 100%);
  border-radius: 32px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background:
    linear-gradient(180deg, rgba(6, 6, 6, 0.98), rgba(2, 2, 2, 0.98));
  box-shadow:
    0 40px 120px rgba(0, 0, 0, 0.65),
    inset 0 1px 0 rgba(255, 255, 255, 0.03);
  padding: 2.2rem;
  position: relative;
}

.modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  border: none;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 999px;
  width: 2.2rem;
  height: 2.2rem;
  color: rgba(248, 250, 252, 0.8);
  font-size: 1.4rem;
}

.modal-eyebrow {
  font-size: 0.68rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: rgba(248, 250, 252, 0.65);
}

.modal-title {
  margin-top: 0.8rem;
  font-size: 1.9rem;
  font-weight: 800;
  color: #ffffff;
}

.modal-text {
  margin-top: 0.9rem;
  font-size: 0.95rem;
  line-height: 1.6;
  color: rgba(248, 250, 252, 0.72);
}

.modal-passenger-card {
  margin-top: 1.6rem;
}

.success-modal-actions {
  margin-top: 1.8rem;
}

.modal-primary {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  padding: 0.85rem 1.25rem;
  font-size: 0.95rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.modal-primary:hover {
  background: rgba(255, 255, 255, 0.2);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.trust-box {
  display: flex;
  gap: 0.9rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.015));
  padding: 1rem;
}

.trust-icon {
  display: flex;
  height: 2.4rem;
  width: 2.4rem;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: rgba(16, 185, 129, 0.14);
  font-size: 1rem;
}

.sidebar-panel {
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(180deg, rgba(10, 10, 10, 0.98), rgba(4, 4, 4, 0.99));
  box-shadow:
    0 28px 80px rgba(0, 0, 0, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.sidebar-topline {
  height: 6px;
  width: 100%;
  background: linear-gradient(90deg, #10b981, #34d399, #10b981);
}

.product-thumb {
  overflow: hidden;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
}

.price-card {
  border-radius: 24px;
  border: 1px solid rgba(16, 185, 129, 0.14);
  background:
    radial-gradient(circle at top left, rgba(16, 185, 129, 0.06), transparent 26%),
    linear-gradient(180deg, rgba(12, 12, 12, 0.97), rgba(18, 18, 18, 0.99));
  padding: 1rem;
}

.mini-summary {
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.015));
  padding: 1rem;
}

.trust-side {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 1.2rem;
}

.side-chip {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  padding: 0.45rem 0.7rem;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(248, 250, 252, 0.65);
}
</style>
