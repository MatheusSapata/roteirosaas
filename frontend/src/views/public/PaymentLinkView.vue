<template>
  <div class="checkout-shell min-h-screen">
    <div class="checkout-container mx-auto max-w-6xl px-4 py-8 pb-32 sm:px-6 lg:px-8 lg:py-10 lg:pb-40">
      <div v-if="loading" class="state-card text-center text-sm text-slate-500">
        Carregando checkout...
      </div>

      <div v-else-if="errorMessage" class="state-card border-rose-200 bg-rose-50 text-center text-sm text-rose-700">
        {{ errorMessage }}
      </div>

      <div
        v-else-if="sale"
        class="payment-grid grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.9fr)]"
      >
        <div class="payment-main space-y-6">
          <section class="hero-card">
            <div class="hero-media">
              <div class="hero-image" :style="heroBackgroundStyle"></div>
            </div>
            <div class="hero-content">
              <div class="hero-meta">
                <span class="hero-badge">Ambiente protegido</span>
                <span class="hero-status" :class="isPaid ? 'hero-status-paid' : 'hero-status-pending'">
                  {{ isPaid ? "Pagamento confirmado" : "Aguardando pagamento" }}
                </span>
              </div>
              <div>
                <p class="eyebrow">Checkout seguro</p>
                <h1 class="hero-title">{{ sale.product_title }}</h1>
                <p class="hero-subtitle">{{ heroSubtitle }}</p>
              </div>
            </div>
          </section>

          <section class="section-card">
            <header class="section-header">
              <div>
                <p class="eyebrow">Dados do comprador</p>
                <h2 class="section-title">Informações pessoais</h2>
                <p class="section-subtitle">Preencha seus dados para concluir sua compra com segurança.</p>
              </div>
            </header>

            <div class="form-grid mt-6">
              <div class="form-field form-field-full">
                <label>Nome completo</label>
                <input v-model="buyer.name" :disabled="isPaid" type="text" placeholder="Nome e sobrenome" @input="markTouched('buyer_name')" />
                <p v-if="fieldErrors.buyer_name" class="field-error">{{ fieldErrors.buyer_name }}</p>
              </div>

              <div class="form-field">
                <label>E-mail</label>
                <input v-model="buyer.email" :disabled="isPaid" type="email" placeholder="voce@exemplo.com" @input="markTouched('buyer_email')" />
                <p v-if="fieldErrors.buyer_email" class="field-error">{{ fieldErrors.buyer_email }}</p>
              </div>

              <div class="form-field">
                <label>Telefone / WhatsApp</label>
                <input
                  v-model="buyer.phone"
                  :disabled="isPaid"
                  type="tel"
                  placeholder="(11) 99999-0000"
                  @input="handlePhoneInput"
                />
                <p v-if="fieldErrors.buyer_phone" class="field-error">{{ fieldErrors.buyer_phone }}</p>
              </div>

              <div class="form-field">
                <label>CPF</label>
                <input
                  v-model="buyer.document"
                  :disabled="isPaid"
                  type="text"
                  placeholder="000.000.000-00"
                  inputmode="numeric"
                  @input="handleBuyerCpfInput"
                />
                <p v-if="fieldErrors.buyer_document" class="field-error">{{ fieldErrors.buyer_document }}</p>
              </div>
            </div>
          </section>

          <section class="section-card">
            <header class="section-header">
              <div>
                <p class="eyebrow">Pagamento</p>
                <h2 class="section-title">Escolha como deseja pagar</h2>
                <p class="section-subtitle">Selecione a forma de pagamento mais conveniente para concluir esta compra.</p>
              </div>
            </header>

            <div class="payment-methods mt-6">
              <button
                v-for="method in paymentOptions"
                :key="method.value"
                type="button"
                class="payment-tab"
                :class="{ 'payment-tab-active': selectedMethod === method.value }"
                :disabled="isPaid"
                @click="selectMethod(method.value)"
              >
                <div class="payment-tab-top">
                  <span class="payment-icon">{{ method.icon }}</span>
                  <span class="payment-title">{{ method.label }}</span>
                </div>
                <p class="payment-description">{{ method.description }}</p>
              </button>
            </div>

            <div v-if="showCreditCard" class="payment-panel mt-6">
              <div class="form-grid">
                <div class="form-field form-field-full">
                  <label>Número do cartão</label>
                  <input
                    v-model="cardForm.number"
                    :disabled="isPaid"
                    type="text"
                    inputmode="numeric"
                    placeholder="0000 0000 0000 0000"
                    @input="handleCardNumberInput"
                  />
                  <p v-if="fieldErrors.card_number" class="field-error">{{ fieldErrors.card_number }}</p>
                </div>

                <div class="form-field">
                  <label>Nome impresso</label>
                  <input v-model="cardForm.holder" :disabled="isPaid" type="text" placeholder="Titular do cartão" @input="markTouched('card_holder')" />
                  <p v-if="fieldErrors.card_holder" class="field-error">{{ fieldErrors.card_holder }}</p>
                </div>

                <div class="form-field">
                  <label>CPF do titular</label>
                  <input
                    v-model="cardForm.document"
                    :disabled="isPaid"
                    type="text"
                    inputmode="numeric"
                    placeholder="000.000.000-00"
                    @input="handleCardCpfInput"
                  />
                  <p v-if="fieldErrors.card_document" class="field-error">{{ fieldErrors.card_document }}</p>
                </div>

                <div class="form-field">
                  <label>Validade</label>
                  <input
                    v-model="cardForm.expiry"
                    :disabled="isPaid"
                    type="text"
                    inputmode="numeric"
                    placeholder="MM/AA"
                    @input="handleExpiryInput"
                  />
                  <p v-if="fieldErrors.card_expiry" class="field-error">{{ fieldErrors.card_expiry }}</p>
                </div>

                <div class="form-field">
                  <label>CVV</label>
                  <input
                    v-model="cardForm.cvv"
                    :disabled="isPaid"
                    type="text"
                    inputmode="numeric"
                    placeholder="123"
                    @input="handleCvvInput"
                  />
                  <p v-if="fieldErrors.card_cvv" class="field-error">{{ fieldErrors.card_cvv }}</p>
                </div>

                <div class="form-field form-field-full">
                  <label>Parcelas</label>
                  <select v-model.number="cardForm.installments" :disabled="isPaid || pricingLoading">
                    <option v-for="option in installmentOptions" :key="option.installments" :value="option.installments">
                      {{ option.installments }}x de {{ formatCurrency(option.installment_amount_cents, pricingCurrency) }}
                    </option>
                  </select>
                  <p v-if="pricingLoading" class="field-hint">Consultando parcelas da Blimboo...</p>
                  <p v-else-if="pricingError" class="field-hint">{{ pricingError }}</p>
                </div>
              </div>

              <div class="security-note mt-5">
                <span class="security-note-icon">🔒</span>
                Seus dados de pagamento são protegidos e criptografados.
              </div>
            </div>

            <div v-if="selectedMethod === 'pix'" class="payment-panel payment-panel-accent mt-6">
              <div class="payment-panel-head">
                <div>
                  <p class="payment-panel-title">Pagamento via Pix</p>
                  <p class="payment-panel-text">Gere o Pix agora e receba a confirmação rapidamente após o pagamento.</p>
                </div>
                <span class="method-pill method-pill-success">Instantâneo</span>
              </div>

              <ul class="payment-bullets">
                <li>Você receberá o QR Code e o código copia e cola após gerar o pagamento.</li>
                <li>O código Pix terá validade limitada para pagamento.</li>
                <li>Assim que aprovado, o status será atualizado automaticamente.</li>
              </ul>
            </div>

            <div v-if="selectedMethod === 'boleto'" class="payment-panel payment-panel-warm mt-6">
              <div class="payment-panel-head">
                <div>
                  <p class="payment-panel-title">Pagamento via boleto</p>
                  <p class="payment-panel-text">O boleto pode levar até 48 horas úteis para compensar após o pagamento.</p>
                </div>
                <span class="method-pill method-pill-neutral">Até 48h</span>
              </div>

              <div class="form-grid mt-5">
                <div class="form-field">
                  <label>CPF/CNPJ</label>
                  <input
                    v-model="boletoForm.document"
                    :disabled="isPaid"
                    type="text"
                    placeholder="000.000.000-00"
                    @input="handleBoletoDocumentInput"
                  />
                  <p v-if="fieldErrors.boleto_document" class="field-error">{{ fieldErrors.boleto_document }}</p>
                </div>

                <div class="form-field">
                  <label>CEP</label>
                  <input
                    v-model="boletoForm.zipcode"
                    :disabled="isPaid"
                    type="text"
                    placeholder="00000-000"
                    @input="handleBoletoZipcodeInput"
                  />
                  <p v-if="fieldErrors.boleto_zipcode" class="field-error">{{ fieldErrors.boleto_zipcode }}</p>
                </div>
              </div>

              <p class="payment-panel-foot">Após gerar, o boleto ficará disponível para visualização e download.</p>
            </div>
          </section>
          <section class="section-card">
            <header class="section-header">
              <div>
                <p class="eyebrow">Resumo do pedido</p>
                <h2 class="section-title">Revise sua compra</h2>
                <p class="section-subtitle">Confira os itens selecionados e o valor final antes de concluir o pagamento.</p>
              </div>

              <span class="summary-count">
                {{ sale.items.length }} {{ sale.items.length === 1 ? "item" : "itens" }}
              </span>
            </header>

            <div class="order-items mt-6">
              <article v-for="item in sale.items" :key="item.id" class="item-card">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <p class="item-title">{{ item.quantity }}x {{ item.variation_name }}</p>
                    <p class="item-description">
                      Inclui {{ item.people_count }}
                      {{ item.people_count === 1 ? "passageiro" : "passageiros" }}
                      • Ocupação {{ item.consumed_capacity }}
                    </p>
                  </div>

                  <span class="item-value">
                    {{ formatCurrency(item.total_price + item.child_extra_amount_cents, sale.currency) }}
                  </span>
                </div>

                <ul v-if="item.child_breakdown.length" class="item-children">
                  <li v-for="child in item.child_breakdown" :key="child.key">
                    + {{ child.quantity }}x {{ child.label }} •
                    {{ formatCurrency(child.total_amount_cents, sale.currency) }}
                  </li>
                </ul>
              </article>
            </div>

            <div class="summary-box mt-6">
              <dl class="summary-lines">
                <div class="summary-line">
                  <dt>Subtotal</dt>
                  <dd>{{ formatCurrency(subtotalAmount, sale.currency) }}</dd>
                </div>

                <div class="summary-line">
                  <dt>Taxas e encargos</dt>
                  <dd>{{ formatCurrency(feeAmount, sale.currency) }}</dd>
                </div>
              </dl>

              <div class="summary-total-row">
                <div>
                  <p class="summary-total-label">Total a pagar</p>
                  <p class="summary-total-caption">Forma selecionada: {{ paymentMethodLabel }}</p>
                  <p v-if="showCreditCard" class="summary-installment">
                    Em {{ parcelLabel }} de {{ installmentValueLabel }}
                  </p>
                </div>
                <span class="summary-total">{{ formatCurrency(displayAmountCents, sale.currency) }}</span>
              </div>
            </div>

            <button type="button" class="checkout-button mt-6" :disabled="isPaid || confirming || submitDisabled" @click="confirmPayment">
              {{ confirmButtonLabel }}
            </button>

            <div class="trust-box mt-4">
              <div class="trust-icon">🔒</div>
              <div>
                <p class="trust-title">Ambiente protegido</p>
                <p class="trust-text">Seus dados são criptografados e processados com segurança para concluir a compra com tranquilidade.</p>
              </div>
            </div>

            <p v-if="confirmError" class="mt-4 text-sm text-rose-600">{{ confirmError }}</p>
          </section>

          <section v-if="success || isPaid" class="success-card">
            <p class="success-title">Pagamento confirmado</p>
            <p class="success-text">
              <template v-if="requiresPassengers">
                {{
                  success
                    ? "Recebemos sua confirmação. Utilize o link abaixo para preencher os dados dos passageiros."
                    : "Este pedido já estava confirmado pela agência responsável."
                }}
              </template>
              <template v-else>
                Pagamento confirmado. Este produto não exige o preenchimento de formulários adicionais.
              </template>
            </p>
            <p v-if="sale?.has_rooms && !requiresPassengers" class="success-mini">
              A agência organizará a hospedagem automaticamente após a confirmação.
            </p>

            <div v-if="requiresPassengers && passengerFormLink" class="passenger-card mt-5">
              <p class="passenger-card-label">Formulário de passageiros</p>
              <a :href="passengerFormLink" class="passenger-card-link" target="_blank" rel="noopener">Acessar formulário</a>
            </div>

            <p v-else-if="requiresPassengers" class="success-text">A agência responsável enviará o formulário de passageiros em breve.</p>

            <button type="button" class="secondary-button mt-6" @click="openSuccessModal">Ver confirmação</button>
          </section>
        </div>

        <aside class="payment-side lg:sticky lg:top-8">
          <div class="sidebar-stack">
            <section class="sidebar-card">
              <div class="flex items-start gap-4">
                <div class="product-thumb">
                  <img v-if="productImage" :src="productImage" alt="Produto" class="h-full w-full object-cover" />
                  <div v-else class="product-thumb-fallback">Produto</div>
                </div>

                <div class="min-w-0 flex-1">
                  <p class="eyebrow">Produto</p>
                  <h3 class="sidebar-product-title">{{ sale.product_title }}</h3>
                  <p class="sidebar-product-text">{{ productDescription }}</p>
                </div>
              </div>
            </section>

            <section class="sidebar-card sidebar-card-highlight">
              <p class="eyebrow">Valor da compra</p>
              <p class="sidebar-price">{{ formatCurrency(displayAmountCents, sale.currency) }}</p>

              <div class="sidebar-summary-lines">
                <div class="sidebar-summary-line">
                  <span>Forma de pagamento</span>
                  <span>{{ paymentMethodLabel }}</span>
                </div>

                <div class="sidebar-summary-line">
                  <span>Parcelamento</span>
                  <span>{{ parcelLabel }}</span>
                </div>

                <div class="sidebar-summary-line">
                  <span>Status</span>
                  <span :class="isPaid ? 'text-emerald-600' : 'text-amber-600'">{{ isPaid ? "Pago" : "Aguardando pagamento" }}</span>
                </div>
              </div>
            </section>

            <section class="sidebar-card">
              <p class="eyebrow">Compra resumida</p>

              <div class="sidebar-items">
                <div v-for="item in sale.items" :key="item.id" class="sidebar-item">
                  <div>
                    <p class="sidebar-item-title">{{ item.quantity }}x {{ item.variation_name }}</p>
                    <p class="sidebar-item-text">{{ item.people_count }} {{ item.people_count === 1 ? "passageiro" : "passageiros" }}</p>
                  </div>

                  <span class="sidebar-item-value">{{ formatCurrency(item.total_price + item.child_extra_amount_cents, sale.currency) }}</span>
                </div>
              </div>
            </section>

            <section class="sidebar-card">
              <div class="flex items-center gap-3">
                <div class="trust-icon trust-icon-soft">🔒</div>
                <div>
                  <p class="trust-title">Compra segura</p>
                  <p class="trust-text">Seus dados são protegidos e criptografados durante todo o processo de pagamento.</p>
                </div>
              </div>

              <div class="sidebar-brand">
                <p class="sidebar-brand-label">Processado com segurança por</p>
                <img :src="brandLogo" alt="Roteiro Online" class="sidebar-brand-logo" />
              </div>

              <div class="sidebar-chips">
                <span class="side-chip">Ambiente protegido</span>
                <span class="side-chip">Dados criptografados</span>
                <span class="side-chip">Fluxo confiável</span>
              </div>
            </section>
          </div>
        </aside>
      </div>
    </div>

    <div v-if="sale" class="sticky-checkout-bar">
      <div class="sticky-checkout-bar__inner">
        <div class="sticky-checkout-bar__summary">
          <p class="sticky-checkout-bar__label">Total da compra</p>
          <div class="sticky-checkout-bar__value-wrap">
            <span class="sticky-checkout-bar__value">{{ formatCurrency(displayAmountCents, sale.currency) }}</span>
            <span v-if="showCreditCard" class="sticky-checkout-bar__meta">{{ parcelLabel }} de {{ installmentValueLabel }}</span>
            <span v-else class="sticky-checkout-bar__meta">{{ paymentMethodLabel }}</span>
          </div>
        </div>

        <button
          type="button"
          class="checkout-button sticky-checkout-bar__button"
          :disabled="isPaid || confirming || submitDisabled"
          @click="confirmPayment"
        >
          {{ confirmButtonLabel }}
        </button>
      </div>
    </div>

    <transition name="fade">
      <div v-if="showSuccessModal && (success || isPaid)" class="success-modal-overlay">
        <div class="success-modal-panel">
          <button type="button" class="modal-close" @click="closeSuccessModal">&times;</button>
          <p class="modal-eyebrow">Pagamento confirmado</p>
          <h3 class="modal-title">{{ isPaid ? "Pedido pago" : "Pagamento aprovado" }}</h3>
          <p class="modal-text">
            <template v-if="requiresPassengers">
              {{
                success
                  ? "Tudo certo. A compra foi registrada e agora você pode preencher os dados dos passageiros no link abaixo."
                  : "Este pedido já estava confirmado anteriormente, mas mantivemos os detalhes disponíveis para consulta."
              }}
            </template>
            <template v-else>
              Pagamento confirmado. Este produto não exige o preenchimento de formulários de passageiros.
            </template>
          </p>
          <p v-if="sale?.has_rooms && !requiresPassengers" class="modal-mini">A agência organizará automaticamente a acomodação conforme sua compra.</p>
          <div v-if="requiresPassengers && passengerFormLink" class="passenger-card modal-passenger-card">
            <p class="passenger-card-label">Formulário de passageiros</p>
            <a :href="passengerFormLink" class="passenger-card-link" target="_blank" rel="noopener">Acessar formulário</a>
          </div>

          <p v-else-if="requiresPassengers" class="modal-text">A agência responsável entrará em contato com o formulário para complementar os dados.</p>

          <div class="success-modal-actions">
            <button type="button" class="modal-primary" @click="closeSuccessModal">Fechar</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { confirmPublicSale, getPublicPaymentLinkDetails, getPublicPaymentLinkPricing, getPublicProductDetail } from "../../services/finance";
import type { PaymentInstallmentOption, ProductDetail, PublicCheckoutResponse, SaleDetail } from "../../types/finance";
import BrandLogo from "../../assets/Logo Cor - Roteiro Online.png";

const route = useRoute();
const brandLogo = BrandLogo;

const sale = ref<SaleDetail | null>(null);
const productDetail = ref<ProductDetail | null>(null);
const loading = ref(true);
const errorMessage = ref<string | null>(null);
const success = ref<PublicCheckoutResponse | null>(null);
const selectedMethod = ref<"credit_card" | "pix" | "boleto">("pix");
const confirming = ref(false);
const confirmError = ref<string | null>(null);
const showSuccessModal = ref(false);
const pricingLoading = ref(false);
const pricingError = ref<string | null>(null);
const pricingOptions = ref<PaymentInstallmentOption[]>([]);
const pricingLoadedToken = ref<string | null>(null);
const touchedFields = reactive<Record<string, boolean>>({
  buyer_name: false,
  buyer_email: false,
  buyer_phone: false,
  buyer_document: false,
  card_number: false,
  card_holder: false,
  card_document: false,
  card_expiry: false,
  card_cvv: false,
  boleto_document: false,
  boleto_zipcode: false,
});

const buyer = reactive({ name: "", email: "", phone: "", document: "", birthdate: "", address: "" });
const cardForm = reactive({ number: "", holder: "", document: "", expiry: "", cvv: "", installments: 1 });
const boletoForm = reactive({ document: "", zipcode: "" });

const paymentOptions = [
  { value: "pix", label: "Pix", description: "Pagamento instantâneo", icon: "⚡" },
  { value: "credit_card", label: "Cartão de crédito", description: "Aprovação imediata", icon: "💳" },
  { value: "boleto", label: "Boleto", description: "Compensação em até 48h", icon: "📄" },
] as const;

const token = computed(() => {
  const raw = route.params.token;
  return Array.isArray(raw) ? raw[0] : raw || "";
});
const isPaid = computed(() => sale.value?.payment_status === "paid");
const requiresPassengers = computed(() => !!sale.value?.requires_passengers);
const passengerFormLink = computed(() => {
  if (!requiresPassengers.value) return null;
  if (success.value?.passenger_token) return `/passageiros/${success.value.passenger_token}`;
  return null;
});
const showCreditCard = computed(() => selectedMethod.value === "credit_card");
const productImage = computed(() => productDetail.value?.checkout_product_image_url || null);
const pricingCurrency = computed(() => sale.value?.currency || "BRL");
const fallbackInstallmentOptions = computed<PaymentInstallmentOption[]>(() => {
  const maxInstallments = Math.max(1, Math.min(sale.value?.installments || 1, 12));
  const totalAmount = sale.value?.amount_cents || 0;
  return Array.from({ length: maxInstallments }).map((_, index) => {
    const installments = index + 1;
    return {
      installments,
      installment_amount_cents: Math.round(totalAmount / installments),
      total_amount_cents: totalAmount,
      has_interest: false,
    };
  });
});
const installmentOptions = computed<PaymentInstallmentOption[]>(() =>
  pricingOptions.value.length ? pricingOptions.value : fallbackInstallmentOptions.value,
);
const selectedInstallmentOption = computed<PaymentInstallmentOption | null>(() => {
  const option = installmentOptions.value.find(entry => entry.installments === cardForm.installments);
  return option || installmentOptions.value[0] || null;
});
const displayAmountCents = computed(() => {
  if (showCreditCard.value && selectedInstallmentOption.value) return selectedInstallmentOption.value.total_amount_cents;
  return sale.value?.amount_cents || 0;
});
const subtotalAmount = computed(() => sale.value?.base_amount_cents || sale.value?.amount_cents || 0);
const feeAmount = computed(() => Math.max(0, displayAmountCents.value - subtotalAmount.value));

const heroBackgroundStyle = computed(() => {
  const banner = productDetail.value?.checkout_banner_url;
  if (banner) {
    return { backgroundImage: `url(${banner})`, backgroundSize: "cover", backgroundPosition: "center" };
  }
  return {
    backgroundImage:
      "linear-gradient(135deg, rgba(16,185,129,0.12), rgba(255,255,255,0.2)), linear-gradient(135deg, #e2e8f0 0%, #f8fafc 100%)",
    backgroundSize: "cover",
    backgroundPosition: "center",
  };
});

const heroSubtitle = computed(() => {
  if (productDetail.value?.description) return productDetail.value.description;
  if (sale.value?.product_description) return sale.value.product_description;
  return "Finalize sua compra com segurança em um ambiente profissional e confiável.";
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
const parcelLabel = computed(() => (!showCreditCard.value ? "Pagamento único" : `${selectedInstallmentOption.value?.installments || cardForm.installments}x`));
const installmentValueLabel = computed(() =>
  formatCurrency(selectedInstallmentOption.value?.installment_amount_cents || sale.value?.amount_cents || 0, sale.value?.currency || "BRL"),
);

const digitsOnly = (value: string) => value.replace(/\D/g, "");
const formatCpf = (value: string) => {
  const digits = digitsOnly(value).slice(0, 11);
  return digits
    .replace(/^(\d{3})(\d)/, "$1.$2")
    .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/\.(\d{3})(\d)/, ".$1-$2");
};
const formatCardNumber = (value: string) => digitsOnly(value).slice(0, 16).replace(/(\d{4})(?=\d)/g, "$1 ").trim();
const formatExpiry = (value: string) => {
  const digits = digitsOnly(value).slice(0, 4);
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)}/${digits.slice(2)}`;
};
const formatPhone = (value: string) => {
  const digits = digitsOnly(value).slice(0, 11);
  if (digits.length <= 2) return digits ? `(${digits}` : "";
  if (digits.length <= 7) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
};
const isValidEmail = (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
const isValidExpiry = (value: string) => {
  if (!/^\d{2}\/\d{2}$/.test(value)) return false;
  const [month, year] = value.split("/").map(Number);
  return month >= 1 && month <= 12 && year >= 0;
};

const markTouched = (field: keyof typeof touchedFields) => {
  touchedFields[field] = true;
};

const fieldErrors = computed<Record<string, string>>(() => {
  const errors: Record<string, string> = {};

  if (touchedFields.buyer_name && !buyer.name.trim()) errors.buyer_name = "Informe o nome completo.";
  if (touchedFields.buyer_email && !isValidEmail(buyer.email)) errors.buyer_email = "Informe um e-mail válido.";
  if (touchedFields.buyer_phone && digitsOnly(buyer.phone).length < 10) errors.buyer_phone = "Informe um telefone válido.";
  if (touchedFields.buyer_document && digitsOnly(buyer.document).length !== 11) errors.buyer_document = "Informe um CPF válido.";

  if (showCreditCard.value) {
    if (touchedFields.card_number && digitsOnly(cardForm.number).length < 13) errors.card_number = "Informe um cartão válido.";
    if (touchedFields.card_holder && !cardForm.holder.trim()) errors.card_holder = "Informe o nome impresso no cartão.";
    if (touchedFields.card_document && digitsOnly(cardForm.document).length !== 11) errors.card_document = "Informe um CPF válido.";
    if (touchedFields.card_expiry && !isValidExpiry(cardForm.expiry)) errors.card_expiry = "Informe uma validade válida.";
    if (touchedFields.card_cvv && digitsOnly(cardForm.cvv).length < 3) errors.card_cvv = "Informe um CVV válido.";
  }

  if (selectedMethod.value === "boleto") {
    if (touchedFields.boleto_document && digitsOnly(boletoForm.document).length < 11) errors.boleto_document = "Informe um CPF/CNPJ válido.";
    if (touchedFields.boleto_zipcode && digitsOnly(boletoForm.zipcode).length !== 8) errors.boleto_zipcode = "Informe um CEP válido.";
  }

  return errors;
});

const confirmButtonLabel = computed(() => {
  if (isPaid.value) return "Pagamento confirmado";
  if (confirming.value) return "Processando...";
  if (selectedMethod.value === "pix") return "Gerar Pix";
  if (selectedMethod.value === "boleto") return "Gerar boleto";
  return "Pagar com cartão";
});

const submitDisabled = computed(() => {
  if (!buyer.name.trim() || !isValidEmail(buyer.email) || digitsOnly(buyer.phone).length < 10 || digitsOnly(buyer.document).length !== 11) return true;
  if (showCreditCard.value) {
    return (
      digitsOnly(cardForm.number).length < 13 ||
      !cardForm.holder.trim() ||
      digitsOnly(cardForm.document).length !== 11 ||
      !isValidExpiry(cardForm.expiry) ||
      digitsOnly(cardForm.cvv).length < 3
    );
  }
  if (selectedMethod.value === "boleto") return digitsOnly(boletoForm.document).length < 11 || digitsOnly(boletoForm.zipcode).length !== 8;
  return false;
});

const formatCurrency = (amountCents: number, currency = "BRL") => {
  const value = (amountCents || 0) / 100;
  try {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(value);
  } catch {
    return `R$ ${value.toFixed(2)}`;
  }
};

const hydrateBuyer = (detail: SaleDetail) => {
  buyer.name = detail.customer_name || "";
  buyer.email = detail.customer_email || "";
  buyer.phone = detail.customer_phone || "";
  buyer.document = formatCpf(buyer.document);
  buyer.phone = formatPhone(buyer.phone);
};

const handleBuyerCpfInput = () => {
  markTouched("buyer_document");
  buyer.document = formatCpf(buyer.document);
};

const handlePhoneInput = () => {
  markTouched("buyer_phone");
  buyer.phone = formatPhone(buyer.phone);
};

const handleCardNumberInput = () => {
  markTouched("card_number");
  cardForm.number = formatCardNumber(cardForm.number);
};

const handleCardCpfInput = () => {
  markTouched("card_document");
  cardForm.document = formatCpf(cardForm.document);
};

const handleExpiryInput = () => {
  markTouched("card_expiry");
  cardForm.expiry = formatExpiry(cardForm.expiry);
};

const handleCvvInput = () => {
  markTouched("card_cvv");
  cardForm.cvv = digitsOnly(cardForm.cvv).slice(0, 4);
};

const handleBoletoDocumentInput = () => {
  markTouched("boleto_document");
  boletoForm.document = formatCpf(boletoForm.document);
};

const handleBoletoZipcodeInput = () => {
  markTouched("boleto_zipcode");
  boletoForm.zipcode = digitsOnly(boletoForm.zipcode).slice(0, 8).replace(/^(\d{5})(\d)/, "$1-$2");
};

const syncInstallmentSelection = () => {
  const available = installmentOptions.value;
  if (!available.length) {
    cardForm.installments = 1;
    return;
  }
  if (!available.some(option => option.installments === cardForm.installments)) {
    cardForm.installments = available[0].installments;
  }
};

const loadCreditCardPricing = async () => {
  if (!token.value || pricingLoading.value || pricingLoadedToken.value === token.value) {
    syncInstallmentSelection();
    return;
  }
  pricingLoading.value = true;
  pricingError.value = null;
  try {
    const { data } = await getPublicPaymentLinkPricing(token.value);
    pricingOptions.value = (data.options || []).slice().sort((left, right) => left.installments - right.installments);
    pricingLoadedToken.value = token.value;
  } catch (err: any) {
    pricingOptions.value = [];
    pricingError.value = err?.response?.data?.detail || "Nao foi possivel consultar as parcelas da Blimboo agora.";
  } finally {
    pricingLoading.value = false;
    syncInstallmentSelection();
  }
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
    pricingOptions.value = [];
    pricingLoadedToken.value = null;
    pricingError.value = null;
    selectedMethod.value = data.payment_status === "paid"
      ? ((data.payment_method as typeof selectedMethod.value) || "pix")
      : "pix";
    cardForm.installments = data.installments || 1;
    hydrateBuyer(data);
    await loadProductAppearance(data.product_public_id);
    syncInstallmentSelection();
    if (selectedMethod.value === "credit_card") await loadCreditCardPricing();
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
  if (success.value || isPaid.value) showSuccessModal.value = true;
};
const closeSuccessModal = () => {
  showSuccessModal.value = false;
};

onMounted(() => {
  loadPaymentLink();
});

watch(
  () => selectedMethod.value,
  value => {
    if (value === "credit_card") {
      loadCreditCardPricing();
    }
  },
);
</script>
<style scoped>
.checkout-shell {
  background:
    radial-gradient(circle at top left, rgba(16, 185, 129, 0.08), transparent 24%),
    linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}
.checkout-container { width: 100%; }
.state-card,.section-card,.hero-card,.sidebar-card,.success-card,.success-modal-panel {
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}
.state-card { padding: 4rem 1.5rem; }
.hero-card { overflow: hidden; }
.hero-media { padding: 1rem 1rem 0; }
.hero-image { height: 280px; border-radius: 24px; background-color: #e2e8f0; }
.hero-content,.section-card,.sidebar-card,.success-card { padding: 1.5rem; }
.hero-meta,.section-header,.payment-panel-head,.summary-total-row,.summary-line,.sidebar-summary-line,.sidebar-item {
  display: flex; justify-content: space-between; gap: 1rem;
}
.hero-meta,.payment-panel-head { flex-wrap: wrap; align-items: flex-start; }
.section-header,.summary-total-row,.sidebar-summary-line,.sidebar-item { align-items: flex-start; }
.hero-badge,.hero-status,.summary-count,.method-pill,.side-chip {
  display: inline-flex; align-items: center; border-radius: 999px;
}
.hero-badge { padding: 0.55rem 0.9rem; background: #ecfdf5; color: #047857; font-size: 0.75rem; font-weight: 700; }
.hero-status { padding: 0.55rem 0.9rem; font-size: 0.75rem; font-weight: 700; }
.hero-status-paid { background: #ecfdf5; color: #047857; }
.hero-status-pending { background: #fff7ed; color: #c2410c; }
.eyebrow,.passenger-card-label,.modal-eyebrow,.summary-total-label,.sidebar-brand-label {
  font-size: 0.72rem; letter-spacing: 0.24em; text-transform: uppercase; color: #94a3b8; font-weight: 700;
}
.hero-title { margin-top: 0.5rem; font-size: 2rem; line-height: 1.05; font-weight: 600; letter-spacing: -0.03em; color: #0f172a; }
.hero-subtitle,.section-subtitle,.sidebar-product-text,.trust-text,.modal-text,.success-text,.payment-panel-text,.payment-panel-foot,.item-description,.sidebar-item-text,.summary-total-caption,.modal-mini,.success-mini {
  color: #64748b;
}
.hero-subtitle { margin-top: 0.85rem; max-width: 44rem; font-size: 0.98rem; line-height: 1.7; }
.section-title { margin-top: 0.45rem; font-size: 1.4rem; line-height: 1.2; font-weight: 600; color: #0f172a; }
.section-subtitle { margin-top: 0.6rem; max-width: 42rem; font-size: 0.95rem; line-height: 1.65; }
.form-grid,.payment-methods,.order-items,.summary-lines,.sidebar-summary-lines,.sidebar-items,.sidebar-stack {
  display: grid; gap: 1rem;
}
.form-grid { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.payment-methods { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.order-items,.summary-lines,.sidebar-summary-lines,.sidebar-items,.sidebar-stack { grid-template-columns: minmax(0, 1fr); }
@media (min-width: 768px) {
  .form-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .payment-methods { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
.form-field-full { grid-column: 1 / -1; }
.form-field { display: flex; flex-direction: column; gap: 0.55rem; }
.form-field label { font-size: 0.75rem; font-weight: 700; color: #64748b; letter-spacing: 0.06em; text-transform: uppercase; }
.form-field input,.form-field select {
  width: 100%; height: 3rem; border-radius: 1rem; border: 1px solid #cbd5e1; background: #ffffff; padding: 0.75rem 0.95rem; color: #0f172a; outline: none; transition: all 0.2s ease;
}
.form-field input::placeholder,.form-field select::placeholder { color: #94a3b8; }
.form-field input:focus,.form-field select:focus { border-color: #10b981; box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1); }
.form-field input:disabled,.form-field select:disabled { cursor: not-allowed; background: #f8fafc; color: #94a3b8; }
.field-error { font-size: 0.8rem; color: #dc2626; }
.field-hint { font-size: 0.8rem; color: #64748b; }
.payment-tab {
  border-radius: 22px; border: 1px solid rgba(203, 213, 225, 0.95); background: #ffffff; padding: 1rem; text-align: left; transition: all 0.2s ease;
}
.payment-tab:hover:not(:disabled) { transform: translateY(-1px); border-color: #94a3b8; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06); }
.payment-tab-active { border-color: #10b981; background: #ecfdf5; }
.payment-tab:disabled { opacity: 0.6; cursor: not-allowed; }
.payment-tab-top { display: flex; align-items: center; gap: 0.75rem; }
.payment-icon { display: inline-flex; align-items: center; justify-content: center; width: 2.25rem; height: 2.25rem; border-radius: 14px; background: #f1f5f9; font-size: 1rem; }
.payment-title,.item-title,.sidebar-item-title,.success-title,.trust-title,.payment-panel-title { font-weight: 600; color: #0f172a; }
.payment-description { margin-top: 0.6rem; font-size: 0.84rem; line-height: 1.5; color: #64748b; }
.payment-panel { border-radius: 24px; border: 1px solid rgba(203, 213, 225, 0.8); background: #ffffff; padding: 1.1rem; }
.payment-panel-accent { background: #f0fdf4; border-color: rgba(16, 185, 129, 0.24); }
.payment-panel-warm { background: #fff7ed; border-color: rgba(245, 158, 11, 0.24); }
.payment-panel-text,.payment-panel-foot,.trust-text,.item-description,.sidebar-item-text,.summary-total-caption,.modal-text,.success-text { margin-top: 0.4rem; font-size: 0.92rem; line-height: 1.6; }
.payment-bullets { margin-top: 1rem; padding-left: 1.1rem; color: #475569; font-size: 0.92rem; line-height: 1.7; }
.method-pill { padding: 0.5rem 0.85rem; font-size: 0.72rem; font-weight: 700; }
.method-pill-success { background: #dcfce7; color: #15803d; }
.method-pill-neutral { background: #ffedd5; color: #c2410c; }
.security-note,.trust-box,.passenger-card {
  border-radius: 22px; border: 1px solid rgba(226, 232, 240, 0.95); background: #ffffff; padding: 1rem;
}
.security-note { display: flex; align-items: center; gap: 0.75rem; background: #f8fafc; font-size: 0.9rem; color: #475569; }
.summary-count { justify-content: center; background: #f1f5f9; padding: 0.55rem 0.85rem; font-size: 0.82rem; font-weight: 700; color: #334155; }
.item-card,.summary-box { border-radius: 24px; border: 1px solid rgba(226, 232, 240, 0.95); background: #ffffff; padding: 1rem; }
.summary-box { background: #f8fafc; padding: 1.15rem; }
.item-value,.sidebar-item-value { font-size: 1rem; font-weight: 600; color: #0f172a; }
.item-children { margin-top: 0.8rem; color: #64748b; font-size: 0.8rem; line-height: 1.6; }
.summary-line dd,.sidebar-summary-line span:last-child { font-weight: 600; color: #0f172a; }
.summary-total-row { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; align-items: flex-end; }
.summary-total { font-size: 2.25rem; line-height: 1; font-weight: 600; color: #059669; letter-spacing: -0.04em; }
.checkout-button,.modal-primary {
  width: 100%; border: none; border-radius: 18px; background: #059669; color: #ffffff; font-size: 1rem; font-weight: 600; min-height: 3.5rem; transition: all 0.2s ease; box-shadow: 0 10px 30px rgba(16, 185, 129, 0.2);
}
.checkout-button:hover:not(:disabled),.modal-primary:hover { transform: translateY(-1px); background: #047857; }
.checkout-button:disabled { opacity: 0.6; cursor: not-allowed; box-shadow: none; }
.trust-box { display: flex; gap: 0.9rem; }
.trust-icon { display: flex; align-items: center; justify-content: center; width: 2.4rem; height: 2.4rem; border-radius: 16px; background: #ecfdf5; flex-shrink: 0; }
.trust-icon-soft { background: #f8fafc; }
.success-card { background: #f0fdf4; border-color: rgba(16, 185, 129, 0.22); }
.success-title { font-size: 1.1rem; }
.success-mini,.modal-mini { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; }
.secondary-button { border: 1px solid #cbd5e1; border-radius: 18px; background: #ffffff; min-height: 3rem; padding: 0 1.2rem; font-size: 0.95rem; font-weight: 600; color: #334155; transition: all 0.2s ease; }
.secondary-button:hover { transform: translateY(-1px); border-color: #94a3b8; }
.product-thumb { width: 88px; height: 88px; flex-shrink: 0; overflow: hidden; border-radius: 20px; border: 1px solid rgba(226, 232, 240, 0.95); background: #f8fafc; }
.product-thumb-fallback { display: flex; width: 100%; height: 100%; align-items: center; justify-content: center; background: linear-gradient(135deg, #dcfce7, #f8fafc); color: #0f172a; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.18em; }
.sidebar-product-title { margin-top: 0.45rem; font-size: 1.25rem; line-height: 1.2; font-weight: 600; color: #0f172a; }
.sidebar-product-text { margin-top: 0.65rem; font-size: 0.92rem; line-height: 1.65; }
.sidebar-price { margin-top: 0.9rem; font-size: 2.25rem; line-height: 1; font-weight: 600; color: #059669; letter-spacing: -0.04em; }
.sidebar-brand { margin-top: 1.1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }
.sidebar-brand-logo { margin-top: 0.6rem; height: 2.4rem; width: auto; }
.sidebar-chips { margin-top: 1rem; display: flex; flex-wrap: wrap; gap: 0.5rem; }
.side-chip { padding: 0.5rem 0.8rem; background: #f8fafc; border: 1px solid #e2e8f0; font-size: 0.7rem; font-weight: 700; color: #475569; }
.passenger-card-link { display: inline-flex; margin-top: 0.75rem; color: #047857; font-weight: 600; text-decoration: none; }
.passenger-card-link:hover { color: #065f46; }
.success-modal-overlay { position: fixed; inset: 0; z-index: 40; display: flex; align-items: center; justify-content: center; padding: 1.5rem; background: rgba(15, 23, 42, 0.35); backdrop-filter: blur(6px); }
.success-modal-panel { width: min(560px, 100%); padding: 2rem; position: relative; }
.modal-close { position: absolute; top: 1rem; right: 1rem; width: 2.25rem; height: 2.25rem; border: 1px solid #e2e8f0; border-radius: 999px; background: #ffffff; color: #64748b; font-size: 1.35rem; }
.modal-title { margin-top: 0.7rem; font-size: 1.8rem; line-height: 1.1; font-weight: 600; color: #0f172a; }
.modal-passenger-card,.success-modal-actions { margin-top: 1.5rem; }
.fade-enter-active,.fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from,.fade-leave-to { opacity: 0; }
.summary-installment { margin-top: 0.35rem; font-size: 0.88rem; color: #475569; }
.sticky-checkout-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 35;
  padding: 0.85rem 1rem calc(0.85rem + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, rgba(248, 250, 252, 0) 0%, rgba(248, 250, 252, 0.95) 28%, #f8fafc 100%);
  backdrop-filter: blur(10px);
}
.sticky-checkout-bar__inner {
  max-width: 72rem;
  margin: 0 auto;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
  border-radius: 24px;
  padding: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.sticky-checkout-bar__summary { min-width: 0; }
.sticky-checkout-bar__label { font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase; color: #94a3b8; font-weight: 700; }
.sticky-checkout-bar__value-wrap { display: flex; flex-direction: column; gap: 0.15rem; }
.sticky-checkout-bar__value { font-size: 1.55rem; line-height: 1; font-weight: 600; color: #0f172a; letter-spacing: -0.03em; }
.sticky-checkout-bar__meta { font-size: 0.84rem; color: #64748b; }
.sticky-checkout-bar__button { width: auto; min-width: 220px; padding: 0 1.5rem; }
@media (max-width: 767px) {
  .sticky-checkout-bar__inner { flex-direction: column; align-items: stretch; }
  .sticky-checkout-bar__button { width: 100%; min-width: 0; }
}
</style>
