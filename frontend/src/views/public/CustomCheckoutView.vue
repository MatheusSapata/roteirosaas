<template>
  <div class="checkout-shell" :class="themeClass">
    <div class="checkout-layout">
      <aside class="checkout-banner-desktop" :style="desktopBannerStyle"></aside>

      <main class="checkout-main">
        <div v-if="!isPaymentApproved" class="checkout-mobile-banner" :style="mobileBannerStyle"></div>

        <section class="checkout-stage">
          <template v-if="loading">
            <div class="checkout-loader-wrap">
              <div class="checkout-loader"></div>
            </div>
          </template>

          <template v-else-if="errorMessage">
            <div class="checkout-copy">
              <p class="checkout-eyebrow">Erro</p>
              <h1 class="checkout-title">{{ errorMessage }}</h1>
            </div>
          </template>

          <template v-else-if="step === 'details'">
            <div class="checkout-copy">
              <p class="checkout-eyebrow">{{ isUpgradeFlow ? "Vamos fazer seu upgrade!" : "Vamos começar!" }}</p>
              <h1 class="checkout-title">Informe seus dados para continuar</h1>
              <p class="checkout-subtitle">Todos os dados são necessários para a emissão da sua compra.</p>
            </div>

            <form class="checkout-form" @submit.prevent="submitDetails">
              <label class="checkout-field">
                <span>Nome completo</span>
                <input v-model="form.customer_name" :disabled="lockedProfileFields.customer_name" placeholder="Seu nome" />
              </label>
              <label class="checkout-field">
                <span>E-mail</span>
                <input v-model="form.customer_email" :disabled="lockedProfileFields.customer_email" type="email" placeholder="seu@email.com" />
              </label>
              <label class="checkout-field">
                <span>CPF ou CNPJ</span>
                <input
                  v-model="form.customer_document"
                  :disabled="lockedProfileFields.customer_document"
                  :placeholder="documentPlaceholder"
                  @input="form.customer_document = formatDocument(form.customer_document)"
                />
              </label>
              <label class="checkout-field">
                <span>Celular</span>
                <input v-model="form.customer_phone" :disabled="lockedProfileFields.customer_phone" placeholder="(11) 99999-9999" />
              </label>
              <div class="checkout-field-row">
                <label class="checkout-field">
                  <span>CEP</span>
                  <div class="checkout-cep-wrap">
                    <input v-model="form.customer_zipcode" :disabled="lockedProfileFields.customer_zipcode" placeholder="00000-000" />
                    <a
                      class="checkout-link-help checkout-link-help-inside"
                      href="https://buscacepinter.correios.com.br/app/endereco/index.php"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Não sei meu CEP
                    </a>
                  </div>
                </label>
              </div>
              <label class="checkout-field">
                <span>Você possui cupom de desconto?</span>
                <div class="checkout-coupon-wrap">
                  <input v-model="form.coupon_code" placeholder="Digite seu cupom" />
                  <span
                    class="checkout-coupon-apply"
                    :class="{ 'is-disabled': submitting || !form.coupon_code.trim() }"
                    role="button"
                    tabindex="0"
                    @click="(submitting || !form.coupon_code.trim()) ? null : applyCoupon()"
                    @keydown.enter.prevent="(submitting || !form.coupon_code.trim()) ? null : applyCoupon()"
                  >
                    Aplicar Cupom
                  </span>
                </div>
              </label>
              <button class="checkout-primary" type="submit" :disabled="submitting">
                {{ submitting ? "Prosseguindo..." : "Prosseguir" }}
              </button>
            </form>
          </template>

          <template v-else-if="step === 'method'">
            <div class="checkout-copy">
              <p class="checkout-eyebrow">Você está quase lá!</p>
              <h1 class="checkout-title">Agora escolha a forma de pagamento</h1>
            </div>

            <div class="checkout-methods">
              <button class="checkout-method-card" @click="choosePix">
                <div class="checkout-method-icon">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M0 0h24v24H0z" fill="none" />
                    <path fill="currentColor" d="M11.143 3.136a2.77 2.77 0 0 1 1.714 0c.363.118.666.324.959.573c.28.239.599.557.98.938l2.536 2.536h-1.347a2.08 2.08 0 0 0-1.54.697l-1.979 2.176a.63.63 0 0 1-.932 0L9.555 7.88a2.08 2.08 0 0 0-1.54-.697H6.668l2.536-2.536c.381-.381.7-.7.98-.938c.293-.249.596-.455.959-.573" />
                    <path fill="currentColor" d="M5.659 8.192L4.647 9.204c-.381.381-.7.7-.938.98c-.249.293-.455.596-.573.959a2.77 2.77 0 0 0 0 1.714c.118.364.324.666.573.959c.239.28.557.599.938.98l1.012 1.012h2.356c.287 0 .574-.125.794-.367l1.978-2.176a1.64 1.64 0 0 1 2.426 0l1.978 2.176c.22.242.507.367.794.367h2.356l1.012-1.012c.381-.381.7-.7.938-.98c.249-.293.455-.596.573-.959a2.77 2.77 0 0 0 0-1.714c-.118-.363-.324-.666-.573-.959a19 19 0 0 0-.938-.98l-1.012-1.012h-2.356c-.287 0-.574.125-.794.367l-1.978 2.176a1.64 1.64 0 0 1-2.426 0L8.809 8.559a1.07 1.07 0 0 0-.794-.367z" />
                    <path fill="currentColor" d="M17.332 16.817h-1.347a2.08 2.08 0 0 1-1.54-.697l-1.979-2.176a.63.63 0 0 0-.932 0L9.555 16.12c-.4.44-.952.697-1.54.697H6.668l2.536 2.536c.381.381.7.7.98.938c.293.249.596.455.959.573a2.78 2.78 0 0 0 1.714 0c.363-.118.666-.324.959-.573c.28-.239.599-.557.98-.938z" />
                  </svg>
                </div>
                <span>Pagar com PIX</span>
              </button>
              <button class="checkout-method-card" @click="chooseCard">
                <div class="checkout-method-icon">
                  <svg viewBox="0 0 64 64" fill="none">
                    <rect x="10" y="16" width="44" height="32" rx="4" stroke="currentColor" stroke-width="4"/>
                    <path d="M10 26h44" stroke="currentColor" stroke-width="4"/>
                  </svg>
                </div>
                <span>Pagar com Cartão de Crédito</span>
              </button>
            </div>

            <button class="checkout-secondary mt-8" @click="goBackToDetails">Voltar</button>
          </template>

          <template v-else-if="step === 'card'">
            <div class="checkout-copy">
              <p class="checkout-eyebrow">Você está quase lá!</p>
              <h1 class="checkout-title checkout-title-card">Boa! Você escolheu pagar no Cartão!</h1>
            </div>

            <div class="checkout-card-step-shell">
            <form class="checkout-form" @submit.prevent="submitCard">
              <div class="checkout-card-info">
                <div class="checkout-card-info-icon">
                  <svg viewBox="0 0 64 64" fill="none" aria-hidden="true">
                    <rect x="10" y="16" width="44" height="32" rx="4" stroke="currentColor" stroke-width="4"/>
                    <path d="M10 26h44" stroke="currentColor" stroke-width="4"/>
                  </svg>
                </div>
                <p>Preencha os dados do seu cartão de crédito e conclua o pagamento</p>
              </div>

              <label class="checkout-field">
                <span>Número</span>
                <input
                  v-model="card.card_number"
                  inputmode="numeric"
                  maxlength="19"
                  placeholder="0000 0000 0000 0000"
                  @input="card.card_number = formatCardNumber(card.card_number)"
                  @focus="ccvFocused = false"
                />
              </label>
              <label class="checkout-field">
                <span>Nome impresso</span>
                <input v-model="card.holder_name" placeholder="Nome" @focus="ccvFocused = false" />
              </label>
              <div class="checkout-card-grid">
                <label class="checkout-field">
                  <span>Validade</span>
                  <input
                    v-model="card.expiry"
                    inputmode="numeric"
                    maxlength="7"
                    placeholder="MM / AA"
                    @input="card.expiry = formatCardExpiry(card.expiry)"
                    @focus="ccvFocused = false"
                  />
                </label>
                <label class="checkout-field">
                  <span>Código de segurança (CVV)</span>
                  <input
                    v-model="card.ccv"
                    inputmode="numeric"
                    maxlength="4"
                    placeholder="123"
                    @input="card.ccv = formatCardCvv(card.ccv)"
                    @focus="ccvFocused = true"
                    @blur="ccvFocused = false"
                  />
                </label>
              </div>
              <button class="checkout-secondary" type="button" @click="goBackToMethod">Pagar com outro método</button>
              <button class="checkout-primary" type="submit" :disabled="submitting || cardAwaitingConfirmation">
                <span v-if="submitting || cardAwaitingConfirmation" class="checkout-inline-spinner" aria-hidden="true"></span>
                {{ submitting ? "Processando..." : (cardAwaitingConfirmation ? "Aguardando confirmação..." : "Prosseguir") }}
              </button>
            </form>
            </div>
          </template>

          <template v-else-if="step === 'pix'">
            <div class="checkout-copy">
              <p class="checkout-eyebrow">Você está quase lá!</p>
              <h1 class="checkout-title">Boa! Você escolheu pagar no PIX!</h1>
            </div>

            <div class="checkout-pix-card">
              <div class="checkout-pix-qr">
                <img v-if="pixDisplaySrc" :src="pixDisplaySrc" alt="QR Code PIX" />
                <p v-else class="checkout-pix-empty">QR indisponível no momento. Use o código PIX abaixo.</p>
              </div>
              <div class="checkout-pix-copy">
                <p>Escaneie o QR Code com o app do seu banco para realizar o pagamento.</p>
                <button class="checkout-secondary" @click="copyPixCode">Copiar código</button>
              </div>
            </div>

            <div class="checkout-note-box">
              <p>Após o pagamento, você será redirecionado automaticamente.</p>
              <p v-if="session?.pix_expiration_date">O QR Code expira em {{ pixExpirationLabel }}.</p>
            </div>

            <button class="checkout-secondary mt-8" @click="goBackToMethod">Pagar com outro método</button>
          </template>

          <template v-else-if="step === 'success'">
            <div class="checkout-success">
              <div class="checkout-success-icon">✓</div>
              <h1 class="checkout-title center">Pagamento aprovado!</h1>
              <p class="checkout-subtitle center">Sua compra foi realizada com sucesso.</p>
            </div>

            <div class="checkout-summary-card">
              <h3>Detalhes da compra</h3>
              <div class="checkout-summary-row"><span>Produto</span><strong>{{ config?.offer.title }}</strong></div>
              <div class="checkout-summary-row"><span>Valor pago</span><strong>{{ formattedAmount }}</strong></div>
              <div class="checkout-summary-row"><span>Forma de pagamento</span><strong>{{ paymentMethodLabel }}</strong></div>
              <div class="checkout-summary-row"><span>Data e hora</span><strong>{{ paidAtLabel }}</strong></div>
            </div>

            <div class="checkout-success-action">
              <button class="checkout-primary checkout-success-button" :disabled="true" type="button">
                <span v-if="onboardingRedirecting" class="checkout-inline-spinner" aria-hidden="true"></span>
                <span>{{ isUpgradeFlow ? "Realizando seu upgrade..." : "Iniciando seu cadastro..." }}</span>
              </button>
            </div>
          </template>

          <template v-else-if="step === 'password'">
            <div class="checkout-copy">
              <h1 class="checkout-title">Finalize seu cadastro</h1>
              <p class="checkout-subtitle">Para acessar a plataforma, crie uma senha segura para sua conta.</p>
            </div>

            <form class="checkout-form" @submit.prevent="submitPassword">
              <label class="checkout-field">
                <span>E-mail</span>
                <input :value="session?.customer_email || form.customer_email" type="email" disabled />
              </label>
              <label class="checkout-field">
                <span>Digite sua senha</span>
                <div class="checkout-password-wrap">
                  <input v-model="password" :type="showPassword ? 'text' : 'password'" placeholder="••••••••••••" />
                  <button
                    type="button"
                    class="checkout-eye"
                    :aria-label="showPassword ? 'Ocultar senha' : 'Mostrar senha'"
                    @click="showPassword = !showPassword"
                  >
                    <svg v-if="showPassword" viewBox="0 0 24 24" aria-hidden="true">
                      <path
                        d="M3 3l18 18M10.58 10.58A2 2 0 0012 14a2 2 0 001.42-.58M9.88 5.09A10.94 10.94 0 0112 5c5 0 9.27 3.11 11 7M6.1 6.1C4.27 7.36 2.84 9.07 2 11c.56 1.27 1.39 2.43 2.44 3.4C6.39 16.33 9.06 17.5 12 17.5c1.74 0 3.38-.4 4.84-1.12"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.8"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                    </svg>
                    <svg v-else viewBox="0 0 24 24" aria-hidden="true">
                      <path
                        d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7zm10 3a3 3 0 100-6 3 3 0 000 6z"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.8"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                    </svg>
                  </button>
                </div>
              </label>
              <label class="checkout-field">
                <span>Repita sua senha</span>
                <div class="checkout-password-wrap">
                  <input v-model="confirmPassword" :type="showConfirmPassword ? 'text' : 'password'" placeholder="••••••••••••" />
                  <button
                    type="button"
                    class="checkout-eye"
                    :aria-label="showConfirmPassword ? 'Ocultar senha' : 'Mostrar senha'"
                    @click="showConfirmPassword = !showConfirmPassword"
                  >
                    <svg v-if="showConfirmPassword" viewBox="0 0 24 24" aria-hidden="true">
                      <path
                        d="M3 3l18 18M10.58 10.58A2 2 0 0012 14a2 2 0 001.42-.58M9.88 5.09A10.94 10.94 0 0112 5c5 0 9.27 3.11 11 7M6.1 6.1C4.27 7.36 2.84 9.07 2 11c.56 1.27 1.39 2.43 2.44 3.4C6.39 16.33 9.06 17.5 12 17.5c1.74 0 3.38-.4 4.84-1.12"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.8"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                    </svg>
                    <svg v-else viewBox="0 0 24 24" aria-hidden="true">
                      <path
                        d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7zm10 3a3 3 0 100-6 3 3 0 000 6z"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.8"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                    </svg>
                  </button>
                </div>
              </label>

              <div class="checkout-password-rules">
                <div :class="passwordRuleClass(password.length >= 8)">Mínimo de 8 caracteres</div>
                <div :class="passwordRuleClass(/[A-Z]/.test(password))">Pelo menos 1 letra maiúscula</div>
                <div :class="passwordRuleClass(/[0-9]/.test(password))">Pelo menos 1 número</div>
                <div :class="passwordRuleClass(hasSpecialCharacter(password))">Pelo menos 1 caractere especial</div>
              </div>

              <button class="checkout-primary" type="submit" :disabled="submitting">
                {{ submitting ? "Finalizando..." : "Acessar a plataforma" }}
              </button>
            </form>
          </template>

          <div v-if="showAccessTransition" class="checkout-access-transition">
            <div class="checkout-access-spinner"></div>
            <p class="checkout-access-line checkout-access-line-primary">
              {{ isUpgradeFlow ? "Estamos realizando seu upgrade..." : "Estamos finalizando seu cadastro..." }}
            </p>
            <p class="checkout-access-line checkout-access-line-secondary">
              Sua nova maneira de apresentar viagens começa agora.
            </p>
          </div>

          <p v-if="inlineError" class="checkout-inline-error">{{ inlineError }}</p>
        </section>

        <div v-if="step !== 'success' && step !== 'password'" class="checkout-protected checkout-protected-footer">
          <svg viewBox="0 0 20 24" aria-hidden="true">
            <path d="M0 0h20v24H0z" fill="none" />
            <path fill="currentColor" d="M3.5 6.5V10H2a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V12a2 2 0 0 0-2-2h-1.5V6.5a6.5 6.5 0 1 0-13 0M6 10V6.5a4 4 0 0 1 8 0V10zm2 5.5a2 2 0 1 1 3.092 1.676l-.008.005s.195 1.18.415 2.57v.001a.75.75 0 0 1-.749.749H9.248a.75.75 0 0 1-.749-.749v-.001l.415-2.57a2 2 0 0 1-.916-1.68z" />
          </svg>
          <span>Sua compra está protegida. Pagamento processado pelo Asaas</span>
        </div>

        <footer v-if="step !== 'success' && step !== 'password'" class="checkout-footer">
          <div v-if="hasAppliedCoupon" class="checkout-footer-discount-line">
            <div class="checkout-footer-discount-main">
              <svg class="checkout-footer-discount-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2048 2048" aria-hidden="true">
                <path d="M0 0h2048v2048H0z" fill="none" />
                <path
                  fill="currentColor"
                  d="M624 832q0 36-14 68t-38 56t-56 38t-68 14t-68-14t-56-38t-38-56t-14-68t14-68t38-56t56-38t68-14t68 14t56 38t38 56t14 68m-176 80q33 0 56-23t24-57q0-33-23-56t-57-24q-33 0-56 23t-24 57q0 33 23 56t57 24m512 128q36 0 68 14t56 38t38 56t14 68t-14 68t-38 56t-56 38t-68 14t-68-14t-56-38t-38-56t-14-68t14-68t38-56t56-38t68-14m0 256q33 0 56-23t24-57q0-33-23-56t-57-24q-33 0-56 23t-24 57q0 33 23 56t57 24M842 640h108l-384 768H458zm566-256l640 640l-640 640H0V384zm-53 1152l512-512l-512-512H128v1024zm181-576q26 0 45 19t19 45t-19 45t-45 19t-45-19t-19-45t19-45t45-19"
                />
              </svg>
              <div class="checkout-footer-discount-text">
                <div class="checkout-footer-discount-text-top">
                  <span><strong>Cupom aplicado:</strong> {{ appliedCouponLabel.replace("Cupom ", "") }}</span>
                  <button type="button" class="checkout-footer-coupon-remove" @click="removeAppliedCoupon" :disabled="submitting">
                    x
                  </button>
                </div>
                <div class="checkout-footer-discount-text-bottom">
                  <span><strong>Desconto:</strong> {{ discountPercentLabel }}</span>
                  <span><strong>Economia:</strong> {{ discountAmountLabel.replace("Economia ", "") }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="checkout-footer-main-row">
            <div class="checkout-footer-left">
              <div class="checkout-footer-left-main">
                <span class="checkout-footer-dot"></span>
                <span>{{ config?.offer.footer_product_label || "Plano profissional" }}</span>
              </div>
            </div>
            <div class="checkout-footer-right">
              <div class="checkout-footer-total-only">
                <small>Total a pagar</small>
                <div class="checkout-footer-price-row">
                  <span v-if="hasAppliedCoupon && originalAmountLabel" class="checkout-footer-original-price">{{ originalAmountLabel }}</span>
                  <div class="checkout-footer-final-price">
                    <strong>{{ formattedAmount }}</strong>
                    <span class="checkout-footer-cycle-suffix">/ mês</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import {
  createCheckoutSession,
  createUpgradeCheckoutSession,
  finishCheckoutPassword,
  getCheckoutConfig,
  getCheckoutSession,
  previewCheckoutCoupon,
  trackCheckoutEvent,
  refreshCheckoutSession,
  startCardCheckout,
  startPixCheckout,
  updateUpgradeCheckoutSessionDetails,
  type CheckoutCouponPreview,
  type CheckoutPublicConfig,
  type CheckoutSession
} from "../../services/checkout";
import { useAuthStore } from "../../store/useAuthStore";
import { resolveMediaUrl } from "../../utils/media";

type Step = "details" | "method" | "card" | "pix" | "success" | "password";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const offerKey = computed(() => String(route.params.offerKey || route.query.offer || "").trim().toLowerCase());
const isUpgradeFlow = computed(() => String(route.query.upgrade || "") === "1" || Boolean(session.value?.is_upgrade));
const config = ref<CheckoutPublicConfig | null>(null);
const session = ref<CheckoutSession | null>(null);
const couponPreview = ref<CheckoutCouponPreview | null>(null);
const step = ref<Step>("details");
const loading = ref(true);
const submitting = ref(false);
const errorMessage = ref("");
const inlineError = ref("");
const cardAwaitingConfirmation = ref(false);
const password = ref("");
const confirmPassword = ref("");
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const ccvFocused = ref(false);
const onboardingRedirecting = ref(false);
const showAccessTransition = ref(false);
let onboardingRedirectTimer: ReturnType<typeof setTimeout> | null = null;
let pollTimer: ReturnType<typeof setTimeout> | null = null;
let cardAwaitingTimeout: ReturnType<typeof setTimeout> | null = null;
let pollingInFlight = false;
let fastCardChecksLeft = 0;
let stepEnteredAt = Date.now();
let hasTrackedMethodStep = false;
let metaPixelsInitialized = false;

const activeMetaPixels = computed(() => (config.value?.pixels || []).filter(pixel => pixel.active && pixel.pixel_id.trim()));

const metaStandardEventName = (eventName: string, status?: string | null, paymentMethod?: string | null) => {
  const normalized = String(eventName || "").trim().toLowerCase();
  const normalizedStatus = String(status || "").trim().toLowerCase();
  const normalizedPayment = String(paymentMethod || "").trim().toLowerCase();
  if (normalized === "step_method_view") return "InitiateCheckout";
  if (normalized === "payment_method_click" || normalized === "pix_started" || normalized === "card_processing") return "AddPaymentInfo";
  if (normalized === "payment_success" || normalizedStatus === "paid") return "Purchase";
  if (normalized === "details_submit_success" || normalized === "step_details_view") return "Lead";
  if (normalized === "details_submit" || normalized === "details_completed") return "Lead";
  if (normalized === "purchase") return "Purchase";
  if (normalizedPayment === "card" && normalizedStatus === "processing") return "AddPaymentInfo";
  return "";
};

const buildMetaEventId = (eventName: string, step?: string | null, status?: string | null, paymentMethod?: string | null) => {
  const token = session.value?.token || offerKey.value || "checkout";
  return [token, eventName, step || "", status || "", paymentMethod || ""]
    .map(value => String(value || "").trim().toLowerCase() || "-")
    .join("|");
};

const ensureMetaPixelBase = () => {
  if (typeof document === "undefined") return;
  if (document.getElementById("meta-pixel-base")) return;
  const script = document.createElement("script");
  script.id = "meta-pixel-base";
  script.innerHTML = `
    !function(f,b,e,v,n,t,s)
    {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t,s)}(window, document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
  `;
  document.head.appendChild(script);
};

const initializeMetaPixels = () => {
  if (typeof window === "undefined") return;
  const pixels = activeMetaPixels.value;
  if (!pixels.length) return;
  ensureMetaPixelBase();
  if (!(window as any).fbq) return;
  if (!metaPixelsInitialized) {
    pixels.forEach(pixel => {
      (window as any).fbq("init", pixel.pixel_id);
    });
    (window as any).fbq("track", "PageView");
    metaPixelsInitialized = true;
  }
};

const sendMetaCheckoutEvent = (
  eventName: string,
  extra: {
    step?: string | null;
    status?: string | null;
    payment_method?: string | null;
  } = {}
) => {
  if (typeof window === "undefined") return;
  const pixels = activeMetaPixels.value;
  if (!pixels.length || !(window as any).fbq) return;

  const eventId = buildMetaEventId(eventName, extra.step ?? step.value, extra.status ?? session.value?.status ?? null, extra.payment_method ?? session.value?.payment_method ?? null);
  const payload = {
    currency: "BRL",
    value: Number(session.value?.amount ?? couponPreview.value?.amount ?? config.value?.offer.amount ?? 0),
    content_name: config.value?.offer.title || config.value?.offer.key || "Checkout",
    content_ids: [config.value?.offer.key].filter(Boolean),
    checkout_event_name: eventName,
    checkout_step: extra.step ?? step.value,
    checkout_status: extra.status ?? session.value?.status ?? null,
    checkout_payment_method: extra.payment_method ?? session.value?.payment_method ?? null,
    offer_key: config.value?.offer.key || "",
  };

  (window as any).fbq("trackCustom", "CheckoutStatus", payload, { eventID: eventId });
  const standardEvent = metaStandardEventName(eventName, extra.status ?? session.value?.status ?? null, extra.payment_method ?? session.value?.payment_method ?? null);
  if (standardEvent) {
    (window as any).fbq("track", standardEvent, payload, { eventID: eventId });
  }
};

const adminAppOrigin = () => {
  if (typeof window === "undefined") return "";
  if (import.meta.env.PROD) return "https://app.roteiroonline.com";
  return window.location.origin.replace(/\/$/, "");
};

const goToAdminDashboard = (query?: Record<string, string>) => {
  const origin = adminAppOrigin();
  const search = query ? new URLSearchParams(query).toString() : "";
  const target = `${origin}/admin/dashboard${search ? `?${search}` : ""}`;
  if (typeof window !== "undefined") {
    window.location.assign(target);
    return;
  }
  router.push({ path: "/admin/dashboard", query }).catch(() => {});
};

const form = reactive({
  customer_name: "",
  customer_email: "",
  customer_document: "",
  customer_phone: "",
  customer_zipcode: "",
  coupon_code: ""
});

const lockedProfileFields = reactive({
  customer_name: false,
  customer_email: false,
  customer_document: false,
  customer_phone: false,
  customer_zipcode: false,
});

const card = reactive({
  card_number: "",
  holder_name: "",
  expiry: "",
  ccv: "",
  installment_count: 1
});

const themeClass = computed(() => (config.value?.theme_mode === "light" ? "checkout-theme-light" : "checkout-theme-dark"));
const effectiveAmount = computed(() => Number(session.value?.amount ?? couponPreview.value?.amount ?? config.value?.offer.amount ?? 0));
const effectiveOriginalAmount = computed(() => Number(session.value?.original_amount ?? couponPreview.value?.original_amount ?? config.value?.offer.amount ?? 0));
const effectiveDiscountAmount = computed(() => Number(session.value?.discount_amount ?? couponPreview.value?.discount_amount ?? 0));
const effectiveAppliedCouponCode = computed(() => String(session.value?.applied_coupon_code || couponPreview.value?.applied_coupon_code || "").trim());
const formattedAmount = computed(() => {
  const value = effectiveAmount.value;
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
});
const hasAppliedCoupon = computed(() => Boolean(effectiveAppliedCouponCode.value && effectiveDiscountAmount.value > 0));
const appliedCouponLabel = computed(() => {
  if (!effectiveAppliedCouponCode.value) return "";
  return `Cupom ${effectiveAppliedCouponCode.value}`;
});
const discountAmountLabel = computed(() => {
  const value = effectiveDiscountAmount.value;
  if (!Number.isFinite(value) || value <= 0) return "";
  return `Economia ${value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}`;
});
const discountPercentLabel = computed(() => {
  const original = effectiveOriginalAmount.value;
  const discount = effectiveDiscountAmount.value;
  if (!Number.isFinite(original) || !Number.isFinite(discount) || original <= 0 || discount <= 0) return "";
  return `${Math.round((discount / original) * 100)}% off`;
});
const originalAmountLabel = computed(() => {
  const original = effectiveOriginalAmount.value;
  const current = effectiveAmount.value;
  if (!Number.isFinite(original) || !Number.isFinite(current) || original <= current) return "";
  return original.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
});
const paymentMethodLabel = computed(() => (session.value?.payment_method === "card" ? "Cartão de crédito" : "PIX"));
const paidAtLabel = computed(() => {
  if (!session.value?.paid_at) return "--";
  return new Date(session.value.paid_at).toLocaleString("pt-BR");
});
const pixImageSrc = computed(() => {
  const raw = String(session.value?.pix_qr_code_base64 || "").trim();
  if (!raw) return "";
  return raw.startsWith("data:image") ? raw : `data:image/png;base64,${raw}`;
});
const pixDisplaySrc = computed(() => {
  if (pixImageSrc.value) return pixImageSrc.value;
  const payload = String(session.value?.pix_copy_paste || "").trim();
  if (!payload) return "";
  return `https://api.qrserver.com/v1/create-qr-code/?size=320x320&data=${encodeURIComponent(payload)}`;
});
const isCardBackVisible = computed(() => ccvFocused.value || card.ccv.trim().length > 0);
const cardBrandKey = computed(() => {
  const digits = card.card_number.replace(/\D/g, "");
  if (/^4/.test(digits)) return "visa";
  if (/^(5[1-5]|2[2-7])/.test(digits)) return "mastercard";
  if (/^3[47]/.test(digits)) return "amex";
  if (/^(30[0-5]|36|38|39)/.test(digits)) return "diners";
  if (/^(4011|4312|4389)/.test(digits)) return "elo";
  if (/^(6062|3841)/.test(digits)) return "hipercard";
  return "credito";
});
const cardBrandLabel = computed(() => {
  switch (cardBrandKey.value) {
    case "visa":
      return "VISA";
    case "mastercard":
      return "Mastercard";
    case "amex":
      return "AMEX";
    case "diners":
      return "Diners";
    case "elo":
      return "ELO";
    case "hipercard":
      return "Hipercard";
    default:
      return "Crédito";
  }
});
const cardNumberPreview = computed(() => {
  const digits = card.card_number.replace(/\D/g, "").slice(0, 16);
  const padded = digits.padEnd(16, "*");
  return (padded.match(/.{1,4}/g) || []).join(" ");
});
const cardNamePreview = computed(() => {
  const value = card.holder_name.trim();
  return value ? value.toUpperCase() : "SEU NOME";
});
const cardExpiryPreview = computed(() => {
  const value = card.expiry.trim();
  return value || "MM / AA";
});
const documentPlaceholder = computed(() => {
  const digits = form.customer_document.replace(/\D/g, "");
  return digits.length > 11 ? "00.000.000/0000-00" : "000.000.000-00";
});
const cardCvvPreview = computed(() => {
  const digits = card.ccv.replace(/\D/g, "").slice(0, 4);
  return digits.padEnd(3, "*");
});
const pixExpirationLabel = computed(() => {
  if (!session.value?.pix_expiration_date) return "--";
  return new Date(session.value.pix_expiration_date).toLocaleDateString("pt-BR");
});
const desktopBannerStyle = computed(() => {
  const url = resolveMediaUrl(config.value?.desktop_image_url);
  return url
    ? { backgroundImage: `url(${url})` }
    : { backgroundImage: "linear-gradient(180deg, #3d2a7c 0%, #12356f 100%)" };
});
const mobileBannerStyle = computed(() => {
  const url = resolveMediaUrl(config.value?.mobile_banner_url);
  return url
    ? { backgroundImage: `url(${url})` }
    : { backgroundImage: "linear-gradient(90deg, #0c5cc7 0%, #9525c6 100%)" };
});
const isPaymentApproved = computed(() => {
  const status = String(session.value?.status || "").trim().toLowerCase();
  return Boolean(session.value?.paid_at) || status === "paid" || status === "signed";
});
const loadConfig = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    config.value = await getCheckoutConfig(offerKey.value);
    initializeMetaPixels();
  } catch (error) {
    console.error(error);
    errorMessage.value = "Não foi possível carregar este checkout.";
  } finally {
    loading.value = false;
  }
};

const parseExpiry = () => {
  const digits = card.expiry.replace(/\D/g, "");
  if (digits.length < 4) return { month: "", year: "" };
  const month = digits.slice(0, 2);
  const year = digits.length >= 6 ? digits.slice(2, 6) : `20${digits.slice(2, 4)}`;
  return { month, year };
};

const formatCardNumber = (value: string) => {
  const digits = value.replace(/\D/g, "").slice(0, 16);
  return digits.replace(/(\d{4})(?=\d)/g, "$1 ").trim();
};

const formatCardExpiry = (value: string) => {
  const digits = value.replace(/\D/g, "").slice(0, 4);
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)} / ${digits.slice(2)}`;
};

const formatCardCvv = (value: string) => value.replace(/\D/g, "").slice(0, 4);
const formatDocument = (value: string) => {
  const digits = value.replace(/\D/g, "").slice(0, 14);
  if (digits.length <= 11) {
    if (digits.length <= 3) return digits;
    if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`;
    if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
    return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`;
  }
  if (digits.length <= 2) return digits;
  if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`;
  if (digits.length <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`;
  if (digits.length <= 12) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`;
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
};

const validateDetails = () => {
  if (!form.customer_name.trim() || !form.customer_email.trim() || !form.customer_document.trim() || !form.customer_phone.trim() || !form.customer_zipcode.trim()) {
    inlineError.value = "Preencha todos os campos obrigatórios.";
    return false;
  }
  const documentDigits = form.customer_document.replace(/\D/g, "");
  if (documentDigits.length !== 11 && documentDigits.length !== 14) {
    inlineError.value = "Informe um CPF ou CNPJ válido.";
    return false;
  }
  inlineError.value = "";
  return true;
};

const getFriendlyCheckoutError = (error: any, fallback: string) => {
  const detail = error?.response?.data?.detail;
  const serialized =
    typeof detail === "string"
      ? detail
      : typeof detail === "object" && detail
        ? JSON.stringify(detail)
        : "";
  const raw = `${serialized} ${error?.message || ""}`.toLowerCase();

  if (!raw) return fallback;
  if (raw.includes("cadastrado")) {
    return serialized || "Este e-mail ou documento já está cadastrado. Faça login para acessar sua conta.";
  }
  if (raw.includes("cpf") || raw.includes("cnpj") || raw.includes("customer_document")) {
    return "Informe um CPF ou CNPJ válido.";
  }
  if (raw.includes("email") || raw.includes("customer_email")) {
    return "Informe um e-mail válido.";
  }
  if (raw.includes("zipcode") || raw.includes("cep")) {
    return "Informe um CEP válido.";
  }
  if (raw.includes("phone") || raw.includes("telefone")) {
    return "Informe um telefone válido com DDD.";
  }
  if (raw.includes("coupon") || raw.includes("cupom")) {
    return "Não foi possível aplicar este cupom. Verifique o código e tente novamente.";
  }
  if (raw.includes("expirationseconds")) {
    return "Não foi possível gerar o PIX agora. Tente novamente em instantes.";
  }
  if (raw.includes("contract") || raw.includes("autoriza")) {
    return "Não foi possível iniciar o PIX automático agora. Tente novamente.";
  }
  if (raw.includes("card") || raw.includes("credit") || raw.includes("ccv") || raw.includes("cvv")) {
    return "Não foi possível aprovar o cartão. Revise os dados e tente novamente.";
  }
  if (raw.includes("timeout") || raw.includes("gateway") || raw.includes("network")) {
    return "Instabilidade temporária ao processar o pagamento. Tente novamente.";
  }
  if (raw.includes("asaas")) {
    return "Não foi possível processar o pagamento no momento. Tente novamente.";
  }
  return fallback;
};

const trackEvent = async (
  eventName: string,
  extra: {
    step?: string | null;
    status?: string | null;
    payment_method?: string | null;
    error_message?: string | null;
    metadata?: Record<string, unknown>;
  } = {}
) => {
  if (!session.value?.token) return;
  try {
    const now = Date.now();
    const duration = Math.max(0, now - stepEnteredAt);
    sendMetaCheckoutEvent(eventName, {
      step: extra.step ?? step.value,
      status: extra.status ?? session.value?.status ?? null,
      payment_method: extra.payment_method ?? session.value?.payment_method ?? null,
    });
    await trackCheckoutEvent(session.value.token, {
      event_name: eventName,
      step: extra.step ?? step.value,
      status: extra.status ?? session.value?.status ?? null,
      payment_method: extra.payment_method ?? session.value?.payment_method ?? null,
      duration_ms: duration,
      error_message: extra.error_message ?? null,
      metadata: extra.metadata ?? null,
    });
  } catch (error) {
    console.debug("tracking_error", error);
  }
};

const submitDetails = async () => {
  if (!validateDetails() || !config.value) return;
  submitting.value = true;
  inlineError.value = "";
  try {
    const normalizedEmail = form.customer_email.trim().toLowerCase();
    if (isUpgradeFlow.value) {
      if (!session.value?.token) throw new Error("Sessao de upgrade nao encontrada.");
      session.value = await updateUpgradeCheckoutSessionDetails(session.value.token, {
        customer_name: form.customer_name,
        customer_email: normalizedEmail,
        customer_document: form.customer_document,
        customer_phone: form.customer_phone,
        customer_zipcode: form.customer_zipcode,
      });
    } else {
      session.value = await createCheckoutSession({
        offer_key: config.value.offer.key,
        customer_name: form.customer_name,
        customer_email: normalizedEmail,
        customer_document: form.customer_document,
        customer_phone: form.customer_phone,
        customer_zipcode: form.customer_zipcode,
        coupon_code: form.coupon_code
      });
    }
    await trackEvent("details_submit_success", {
      step: "details",
      status: session.value.status,
      metadata: {
        customer_name: session.value.customer_name,
        customer_email: session.value.customer_email,
        customer_phone: session.value.customer_phone,
        customer_zipcode: session.value.customer_zipcode,
        offer_key: session.value.offer_key,
      },
    });
    router.replace({ query: { ...route.query, token: session.value.token } }).catch(() => {});
    step.value = "method";
    stepEnteredAt = Date.now();
    if (!hasTrackedMethodStep) {
      hasTrackedMethodStep = true;
      await trackEvent("step_method_view", {
        step: "method",
        metadata: {
          customer_name: session.value.customer_name,
          customer_email: session.value.customer_email,
          customer_phone: session.value.customer_phone,
          customer_zipcode: session.value.customer_zipcode,
          offer_key: session.value.offer_key,
        },
      });
    }
  } catch (error: any) {
    console.error(error);
    inlineError.value = getFriendlyCheckoutError(error, "Não foi possível iniciar o checkout.");
    await trackEvent("details_submit_error", { step: "details", status: "error", error_message: inlineError.value });
  } finally {
    submitting.value = false;
  }
};

const applyCoupon = async () => {
  if (!config.value) return;
  const coupon = form.coupon_code.trim();
  if (!coupon) return;
  submitting.value = true;
  inlineError.value = "";
  try {
    if (!session.value) {
      couponPreview.value = await previewCheckoutCoupon({
        offer_key: config.value.offer.key,
        coupon_code: coupon,
      });
      form.coupon_code = couponPreview.value.applied_coupon_code || coupon;
      return;
    }
    stopPolling();
    session.value = await createCheckoutSession({
      offer_key: config.value.offer.key,
      customer_name: session.value?.customer_name || form.customer_name,
      customer_email: (session.value?.customer_email || form.customer_email).trim().toLowerCase(),
      customer_document: form.customer_document,
      customer_phone: session.value?.customer_phone || form.customer_phone,
      customer_zipcode: session.value?.customer_zipcode || form.customer_zipcode,
      coupon_code: coupon
    });
    form.coupon_code = session.value.applied_coupon_code || coupon;
    router.replace({ query: { ...route.query, token: session.value.token } }).catch(() => {});
  } catch (error: any) {
    console.error(error);
    inlineError.value = getFriendlyCheckoutError(error, "Não foi possível aplicar este cupom.");
  } finally {
    submitting.value = false;
  }
};

const fillFormFromSession = (data: CheckoutSession) => {
  form.customer_name = data.customer_name || "";
  form.customer_email = data.customer_email || "";
  form.customer_document = formatDocument(data.customer_document || "");
  form.customer_phone = data.customer_phone || "";
  form.customer_zipcode = data.customer_zipcode || "";
  form.coupon_code = data.applied_coupon_code || form.coupon_code || "";
};

const lockUpgradePrefilledFields = (data: CheckoutSession) => {
  if (!isUpgradeFlow.value) return;
  const flags = data.locked_profile_fields || {};
  const hasFlag = (key: string) => Object.prototype.hasOwnProperty.call(flags, key);
  lockedProfileFields.customer_name = hasFlag("customer_name")
    ? Boolean(flags.customer_name)
    : Boolean((data.customer_name || "").trim());
  lockedProfileFields.customer_email = hasFlag("customer_email")
    ? Boolean(flags.customer_email)
    : Boolean((data.customer_email || "").trim());
  lockedProfileFields.customer_document = hasFlag("customer_document")
    ? Boolean(flags.customer_document)
    : Boolean((data.customer_document || "").trim());
  lockedProfileFields.customer_phone = hasFlag("customer_phone")
    ? Boolean(flags.customer_phone)
    : Boolean((data.customer_phone || "").trim());
  lockedProfileFields.customer_zipcode = hasFlag("customer_zipcode")
    ? Boolean(flags.customer_zipcode)
    : Boolean((data.customer_zipcode || "").trim());
};

const choosePix = async () => {
  if (!session.value) return;
  submitting.value = true;
  inlineError.value = "";
  try {
    await trackEvent("payment_method_click", { payment_method: "pix", step: "method" });
    session.value = await startPixCheckout(session.value.token);
    step.value = "pix";
    stepEnteredAt = Date.now();
    router.replace({ query: { ...route.query, step: "pix" } }).catch(() => {});
    await trackEvent("pix_started", { payment_method: "pix", step: "pix" });
    startPolling();
  } catch (error: any) {
    console.error(error);
    inlineError.value = getFriendlyCheckoutError(error, "Não foi possível gerar o PIX.");
    await trackEvent("pix_error", { payment_method: "pix", step: "method", status: "error", error_message: inlineError.value });
  } finally {
    submitting.value = false;
  }
};

const removeAppliedCoupon = async () => {
  if (!config.value) return;
  if (!session.value) {
    form.coupon_code = "";
    couponPreview.value = null;
    inlineError.value = "";
    return;
  }
  if (!session.value.applied_coupon_code) return;
  submitting.value = true;
  inlineError.value = "";
  try {
    form.coupon_code = "";
    couponPreview.value = null;
    stopPolling();
    session.value = await createCheckoutSession({
      offer_key: config.value.offer.key,
      customer_name: session.value.customer_name || form.customer_name,
      customer_email: (session.value.customer_email || form.customer_email).trim().toLowerCase(),
      customer_document: form.customer_document,
      customer_phone: session.value.customer_phone || form.customer_phone,
      customer_zipcode: session.value.customer_zipcode || form.customer_zipcode,
      coupon_code: null
    });
    router.replace({ query: { ...route.query, token: session.value.token } }).catch(() => {});
    if (step.value === "pix" || step.value === "card") step.value = "method";
  } catch (error: any) {
    console.error(error);
    inlineError.value = getFriendlyCheckoutError(error, "Não foi possível remover o cupom.");
  } finally {
    submitting.value = false;
  }
};

const submitCard = async () => {
  if (!session.value) return;
  const { month, year } = parseExpiry();
  if (!month || !year) {
    inlineError.value = "Informe uma validade válida do cartão.";
    return;
  }
  submitting.value = true;
  cardAwaitingConfirmation.value = false;
  inlineError.value = "";
  try {
    await trackEvent("payment_method_click", { payment_method: "card", step: "method" });
    session.value = await startCardCheckout(session.value.token, {
      token: session.value.token,
      holder_name: card.holder_name,
      card_number: card.card_number,
      expiry_month: month,
      expiry_year: year,
      ccv: card.ccv,
      installment_count: 1
    });
    if (session.value.status === "paid") {
      step.value = "success";
      stopPolling();
      cardAwaitingConfirmation.value = false;
      clearCardAwaitingTimeout();
      stepEnteredAt = Date.now();
      await trackEvent("payment_success", { payment_method: "card", step: "success", status: "paid" });
      startSuccessAutoRedirect();
    } else {
      session.value.payment_method = "card";
      if (isAwaitingCheckoutStatus(session.value.status)) {
        fastCardChecksLeft = 3;
        startPolling();
        cardAwaitingConfirmation.value = true;
        startCardAwaitingTimeout();
        inlineError.value = "Pagamento em processamento. Aguarde a confirmação (isso pode levar alguns segundos).";
        await trackEvent("card_processing", { payment_method: "card", step: "card", status: session.value.status });
      } else {
        stopPolling();
        cardAwaitingConfirmation.value = false;
        clearCardAwaitingTimeout();
        inlineError.value = "Pagamento não aprovado. Revise os dados do cartão ou tente outro método.";
        await trackEvent("card_error", {
          payment_method: "card",
          step: "card",
          status: session.value.status,
          error_message: inlineError.value,
        });
      }
    }
  } catch (error: any) {
    console.error(error);
    cardAwaitingConfirmation.value = false;
    clearCardAwaitingTimeout();
    inlineError.value = getFriendlyCheckoutError(error, "Não foi possível processar o cartão.");
    await trackEvent("card_error", { payment_method: "card", step: "card", status: "error", error_message: inlineError.value });
  } finally {
    submitting.value = false;
  }
};

const copyPixCode = async () => {
  if (!session.value?.pix_copy_paste) return;
  await navigator.clipboard.writeText(session.value.pix_copy_paste);
  inlineError.value = "Código PIX copiado.";
};

const goToPasswordStep = async () => {
  if (!session.value) return;
  if (session.value.is_upgrade) {
    await trackEvent("upgrade_redirect_dashboard", { step: "success", status: "paid" });
    try {
      await auth.fetchProfile();
    } catch {}
    goToAdminDashboard();
    return;
  }
  if (!session.value.requires_password_setup) {
    await trackEvent("signup_not_required", { step: "success" });
    router.push("/login").catch(() => {});
    return;
  }
  step.value = "password";
  stepEnteredAt = Date.now();
  await trackEvent("password_step_view", { step: "password" });
};

const chooseCard = () => {
  stopPolling();
  cardAwaitingConfirmation.value = false;
  clearCardAwaitingTimeout();
  step.value = "card";
  stepEnteredAt = Date.now();
  router.replace({ query: { ...route.query, step: "card" } }).catch(() => {});
};

const goBackToMethod = () => {
  stopPolling();
  cardAwaitingConfirmation.value = false;
  clearCardAwaitingTimeout();
  step.value = "method";
  stepEnteredAt = Date.now();
  router.replace({ query: { ...route.query, step: "method" } }).catch(() => {});
};

const goBackToDetails = () => {
  stopPolling();
  cardAwaitingConfirmation.value = false;
  clearCardAwaitingTimeout();
  step.value = "details";
  stepEnteredAt = Date.now();
  router.replace({ query: { ...route.query, step: "details" } }).catch(() => {});
};

const isTerminalCheckoutStatus = (status?: string | null) => {
  const value = String(status || "").trim().toLowerCase();
  return ["paid", "failed", "refused", "canceled", "cancelled", "expired"].includes(value);
};

const isAwaitingCheckoutStatus = (status?: string | null) => {
  const value = String(status || "").trim().toLowerCase();
  if (!value) return true;
  return !isTerminalCheckoutStatus(value);
};

const clearCardAwaitingTimeout = () => {
  if (cardAwaitingTimeout) {
    clearTimeout(cardAwaitingTimeout);
    cardAwaitingTimeout = null;
  }
};

const startCardAwaitingTimeout = () => {
  clearCardAwaitingTimeout();
  cardAwaitingTimeout = setTimeout(() => {
    if (!cardAwaitingConfirmation.value) return;
    cardAwaitingConfirmation.value = false;
    inlineError.value = "A operadora demorou para confirmar este pagamento. Você pode tentar novamente ou usar outro método.";
  }, 25000);
};

const startSuccessAutoRedirect = () => {
  if (!session.value || onboardingRedirectTimer) return;
  onboardingRedirecting.value = true;
  trackEvent("signup_redirect_started", { step: "success", status: session.value.status }).catch(() => {});
  onboardingRedirectTimer = setTimeout(async () => {
    onboardingRedirectTimer = null;
    await goToPasswordStep();
    onboardingRedirecting.value = false;
  }, 3000);
};

const submitPassword = async () => {
  if (!session.value) return;
  if (password.value !== confirmPassword.value) {
    inlineError.value = "As senhas não coincidem.";
    return;
  }
  submitting.value = true;
  inlineError.value = "";
  try {
    const result = await finishCheckoutPassword(session.value.token, password.value);
    await trackEvent("password_defined", { step: "password", status: "success" });
    const params = new URLSearchParams();
    params.set("username", result.email);
    params.set("password", password.value);
    const loginRes = await api.post("/auth/login", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" }
    });
    auth.setTokens(loginRes.data.access_token, loginRes.data.refresh_token);
    await auth.fetchProfile();
    showAccessTransition.value = true;
    await new Promise(resolve => setTimeout(resolve, 6000));
    goToAdminDashboard({ onboarding: "1" });
  } catch (error: any) {
    console.error(error);
    inlineError.value = getFriendlyCheckoutError(error, "Não foi possível finalizar o cadastro.");
  } finally {
    submitting.value = false;
  }
};

const hasSpecialCharacter = (value: string) => /[!@#$%^&*(),.?":{}|<>]/.test(value);
const passwordRuleClass = (ok: boolean) => (ok ? "checkout-rule ok" : "checkout-rule");

const hydrateStepFromSession = (data: CheckoutSession) => {
  const requestedStep = String(route.query.step || "").trim().toLowerCase();
  session.value = data;
  fillFormFromSession(data);
  lockUpgradePrefilledFields(data);
  if (data.password_defined_at) {
    cardAwaitingConfirmation.value = false;
    clearCardAwaitingTimeout();
    step.value = "success";
    startSuccessAutoRedirect();
    return;
  }
  if (data.status === "paid") {
    cardAwaitingConfirmation.value = false;
    clearCardAwaitingTimeout();
    step.value = "success";
    stopPolling();
    stepEnteredAt = Date.now();
    trackEvent("payment_success", { step: "success", status: "paid", payment_method: data.payment_method || null }).catch(() => {});
    startSuccessAutoRedirect();
    return;
  }
  if (data.payment_method === "pix" && data.pix_copy_paste) {
    cardAwaitingConfirmation.value = false;
    clearCardAwaitingTimeout();
    step.value = "pix";
    return;
  }
  if (data.payment_method === "card") {
    cardAwaitingConfirmation.value = isAwaitingCheckoutStatus(data.status);
    if (!cardAwaitingConfirmation.value && String(data.status || "").toLowerCase() !== "paid") {
      stopPolling();
      clearCardAwaitingTimeout();
      inlineError.value = "Pagamento não aprovado. Revise os dados do cartão ou tente outro método.";
    } else if (cardAwaitingConfirmation.value) {
      startCardAwaitingTimeout();
    }
    step.value = "card";
    stepEnteredAt = Date.now();
    return;
  }
  cardAwaitingConfirmation.value = false;
  clearCardAwaitingTimeout();
  if ((requestedStep === "card" || step.value === "card") && data.status !== "paid" && !data.payment_method) {
    cardAwaitingConfirmation.value = isAwaitingCheckoutStatus(data.status);
    if (cardAwaitingConfirmation.value) startCardAwaitingTimeout();
    step.value = "card";
    stepEnteredAt = Date.now();
    return;
  }
  step.value = "method";
  stepEnteredAt = Date.now();
  if (!hasTrackedMethodStep) {
    hasTrackedMethodStep = true;
    trackEvent("step_method_view", {
      step: "method",
      metadata: {
        customer_name: data.customer_name,
        customer_email: data.customer_email,
        customer_phone: data.customer_phone,
        customer_zipcode: data.customer_zipcode,
        offer_key: data.offer_key,
      },
    }).catch(() => {});
  }
};

const refreshCurrentSession = async () => {
  if (!session.value || pollingInFlight) return;
  pollingInFlight = true;
  try {
    const data = await refreshCheckoutSession(session.value.token);
    hydrateStepFromSession(data);
  } catch (error) {
    console.error(error);
  } finally {
    pollingInFlight = false;
  }
};

const startPolling = () => {
  stopPolling();
  const loop = async () => {
    await refreshCurrentSession();
    if (!pollTimer) return;
    if (step.value === "card" && cardAwaitingConfirmation.value && fastCardChecksLeft > 0) {
      fastCardChecksLeft -= 1;
      pollTimer = setTimeout(loop, 1200);
      return;
    }
    pollTimer = setTimeout(loop, step.value === "card" ? 3000 : 15000);
  };
  pollTimer = setTimeout(loop, step.value === "card" ? 1200 : 15000);
};

const stopPolling = () => {
  if (pollTimer) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
  clearCardAwaitingTimeout();
  fastCardChecksLeft = 0;
};

onMounted(async () => {
  await loadConfig();
  const token = String(route.query.token || "");
  let loadedByToken = false;
  if (token) {
    try {
      const data = await getCheckoutSession(token);
      hydrateStepFromSession(data);
      loadedByToken = true;
      if (data.status !== "paid") {
        startPolling();
      }
    } catch (error) {
      console.error(error);
    }
  }

  if (loadedByToken) {
    return;
  }

  if (isUpgradeFlow.value && config.value) {
    try {
      session.value = await createUpgradeCheckoutSession(config.value.offer.key, form.coupon_code || null);
      fillFormFromSession(session.value);
      lockUpgradePrefilledFields(session.value);
      router.replace({ query: { ...route.query, token: session.value.token, upgrade: "1" } }).catch(() => {});
      step.value = "details";
      stepEnteredAt = Date.now();
    } catch (error: any) {
      console.error(error);
      errorMessage.value = getFriendlyCheckoutError(error, "Não foi possível iniciar o checkout de upgrade.");
    }
  }
});

onBeforeUnmount(() => {
  stopPolling();
  clearCardAwaitingTimeout();
  if (onboardingRedirectTimer) {
    clearTimeout(onboardingRedirectTimer);
    onboardingRedirectTimer = null;
  }
});
</script>

<style scoped>
.checkout-shell {
  height: 100vh;
  overflow: hidden;
}

.checkout-theme-dark {
  background: #0d0f12;
  color: #fff;
}

.checkout-theme-light {
  background: #f4f5f9;
  color: #0f172a;
}

.checkout-layout {
  display: grid;
  height: 100vh;
  grid-template-columns: 50vw 50vw;
}

.checkout-banner-desktop {
  background-position: center;
  background-size: cover;
  height: 100vh;
}

.checkout-main {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  min-height: 0;
  height: 100vh;
}

.checkout-mobile-banner {
  display: none;
}

.checkout-stage {
  width: 90%;
  max-width: 90%;
  padding: 24px 28px 20px;
  min-height: 0;
  margin: 0 auto;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  justify-self: center;
  align-self: center;
}

.checkout-copy {
  margin-bottom: 24px;
}

.checkout-eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  opacity: 0.8;
}

.checkout-title {
  margin: 0;
  font-size: 34px;
  line-height: 1.04;
  font-weight: 700;
  letter-spacing: -0.04em;
}

.checkout-title.center,
.checkout-subtitle.center {
  text-align: center;
}

.checkout-subtitle {
  margin: 10px 0 0;
  font-size: 14px;
  line-height: 1.45;
  opacity: 0.82;
}

.checkout-form,
.checkout-methods {
  display: grid;
  gap: 10px;
  width: 90%;
  margin: 0 auto;
}

.checkout-copy,
.checkout-pix-card,
.checkout-note-box,
.checkout-summary-card,
.checkout-success,
.checkout-secondary.mt-8 {
  width: 90%;
  margin-left: auto;
  margin-right: auto;
}

.checkout-field,
.checkout-field-row {
  display: grid;
  gap: 6px;
}

.checkout-field span {
  font-size: 12px;
  opacity: 0.8;
}

.checkout-field input,
.checkout-field select {
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  padding: 0 15px;
  color: inherit;
  font-size: 15px;
}

.checkout-coupon-wrap {
  position: relative;
  width: 100%;
}

.checkout-cep-wrap {
  position: relative;
  width: 100%;
}

.checkout-coupon-wrap input {
  width: 100%;
  padding-right: 118px;
}

.checkout-cep-wrap input {
  width: 100%;
  padding-right: 130px;
}

.checkout-coupon-apply {
  position: absolute;
  top: 50%;
  right: 14px;
  transform: translateY(-50%);
  font-size: 20px;
  font-weight: 800;
  color: #18c269;
  user-select: none;
  cursor: pointer;
  line-height: 1;
}

.checkout-coupon-apply.is-disabled {
  opacity: 0.55;
  pointer-events: none;
}

.checkout-theme-light .checkout-field input,
.checkout-theme-light .checkout-field select {
  border-color: #d7dde6;
  background: #fff;
}

.checkout-field input:disabled {
  opacity: 0.6;
}

.checkout-field-row {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.checkout-link-help {
  color: #18c269;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  align-self: center;
  margin-top: 18px;
}

.checkout-link-help-inside {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  margin-top: 0;
  font-size: 12px;
}

.checkout-protected {
  margin: 10px auto 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 12px;
  text-align: center;
  opacity: 0.72;
}

.checkout-protected svg {
  width: 10px;
  height: 12px;
  flex: 0 0 auto;
}

.checkout-protected-footer {
  width: 90%;
  margin: 6px auto 10px;
}

.checkout-primary,
.checkout-secondary,
.checkout-method-card {
  border-radius: 12px;
  height: 52px;
  font-size: 16px;
  font-weight: 600;
  transition: .2s ease;
}

.checkout-primary {
  border: 0;
  background: #18c269;
  color: #fff;
  margin-top: 8px;
}

.checkout-secondary {
  border: 1px solid rgba(255,255,255,.16);
  background: transparent;
  color: inherit;
}

.checkout-theme-light .checkout-secondary,
.checkout-theme-light .checkout-method-card {
  border-color: #d7dde6;
}

.checkout-methods {
  gap: 18px;
}

.checkout-method-card {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 22px;
  padding: 0 24px;
  border: 1px solid rgba(255,255,255,.14);
  background: transparent;
  color: inherit;
  height: 124px;
  transition: background .24s ease, color .24s ease, border-color .24s ease, box-shadow .24s ease, transform .2s ease;
}

@media (hover: hover) and (pointer: fine) {
  .checkout-method-card:hover {
    background: linear-gradient(180deg, #18c269 0%, #0fa25f 100%);
    color: #ffffff;
    border-color: #18c269;
    box-shadow: 0 14px 30px -18px rgba(24, 194, 105, 0.9);
    transform: translateY(-2px);
  }
}

.checkout-method-card:active {
  transform: scale(0.985);
}

@media (hover: none) {
  .checkout-method-card:active {
    background: linear-gradient(180deg, #18c269 0%, #0fa25f 100%);
    color: #ffffff;
    border-color: #18c269;
    box-shadow: 0 10px 22px -16px rgba(24, 194, 105, 0.9);
  }
}

.checkout-method-icon {
  width: 46px;
  height: 46px;
}

.checkout-method-icon svg {
  width: 100%;
  height: 100%;
}

.checkout-secondary.mt-8 {
  margin-top: 18px;
}

.checkout-card-preview,
.checkout-pix-card,
.checkout-note-box,
.checkout-summary-card {
  border: 1px solid rgba(255,255,255,.12);
  background: rgba(255,255,255,.04);
  border-radius: 14px;
}

.checkout-theme-light .checkout-card-preview,
.checkout-theme-light .checkout-pix-card,
.checkout-theme-light .checkout-note-box,
.checkout-theme-light .checkout-summary-card {
  border-color: #d7dde6;
  background: #fff;
}

.checkout-card-step-shell {
  width: 100%;
}

.checkout-card-info {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  gap: 16px;
  align-items: center;
  border: 1px solid rgba(255,255,255,.12);
  background: rgba(255,255,255,.04);
  border-radius: 14px;
  padding: 18px 20px;
}

.checkout-theme-light .checkout-card-info {
  border-color: #d7dde6;
  background: #fff;
}

.checkout-card-info-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: inherit;
}

.checkout-card-info-icon svg {
  width: 100%;
  height: 100%;
}

.checkout-card-info p {
  margin: 0;
  font-size: 14px;
  line-height: 1.45;
}

.checkout-card-preview {
  padding: 14px;
  width: 80%;
  max-width: 80%;
  margin: 0 auto;
}

.checkout-card-preview-inner {
  position: relative;
  min-height: 184px;
  transform-style: preserve-3d;
  transition: transform .35s ease;
}

.checkout-card-preview.flipped .checkout-card-preview-inner {
  transform: rotateY(180deg);
}

.checkout-card-face {
  position: absolute;
  inset: 0;
  display: grid;
  gap: 16px;
  padding: 18px;
  border-radius: 16px;
  backface-visibility: hidden;
  background: linear-gradient(135deg, #1a2746 0%, #172342 100%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.08);
}

.checkout-theme-light .checkout-card-face {
  background: linear-gradient(135deg, #edf3ff 0%, #d8e4f5 100%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.75);
  color: #10203a;
}

.checkout-card-face-back {
  transform: rotateY(180deg);
  align-content: start;
}

.checkout-card-face-top,
.checkout-card-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: center;
  gap: 14px;
}

.checkout-card-chip {
  width: 52px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(248,211,104,.95), rgba(201,148,34,.95));
  box-shadow: inset 0 0 0 1px rgba(0,0,0,.12);
}

.checkout-card-number {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.checkout-card-meta {
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
}

.checkout-card-meta-left {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  align-items: end;
}

.checkout-card-meta-block {
  display: grid;
  gap: 4px;
}

.checkout-card-meta-block small,
.checkout-card-cvv-area small {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.66;
}

.checkout-card-meta-block strong {
  font-size: 14px;
  font-weight: 700;
}

.checkout-card-brand-badge {
  justify-self: end;
  align-self: end;
  min-width: 92px;
  min-height: 42px;
  padding: 8px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,.08);
  display: grid;
  place-items: center;
}

.checkout-theme-light .checkout-card-brand-badge {
  background: rgba(16,32,58,.08);
}

.checkout-card-brand-image {
  display: block;
  max-width: 74px;
  max-height: 22px;
  width: auto;
  height: auto;
  object-fit: contain;
}

.checkout-card-brand-badge span {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
}

.checkout-card-brand-visa {
  font-style: italic;
}

.checkout-card-brand-mastercard,
.checkout-card-brand-amex,
.checkout-card-brand-elo,
.checkout-card-brand-hipercard {
  letter-spacing: 0.02em;
}

.checkout-card-stripe {
  height: 42px;
  margin: 10px -18px 0;
  background: rgba(6, 8, 14, 0.88);
}

.checkout-card-cvv-area {
  justify-self: end;
  width: 118px;
  display: grid;
  gap: 8px;
}

.checkout-card-cvv-box {
  display: grid;
  align-items: center;
  min-height: 42px;
  padding: 0 14px;
  border-radius: 10px;
  background: rgba(255,255,255,.94);
  color: #17233b;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.24em;
  text-align: right;
}

.checkout-card-back-copy {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  opacity: 0.76;
}

.checkout-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.checkout-pix-card {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
}

.checkout-pix-qr {
  width: 180px;
  height: 180px;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
}

.checkout-pix-qr img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.checkout-pix-empty {
  margin: 0;
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  text-align: center;
  color: #111827;
  font-size: 0.9rem;
  padding: 10px;
}

.checkout-pix-copy {
  display: grid;
  align-content: center;
  gap: 10px;
}

.checkout-note-box,
.checkout-summary-card {
  margin-top: 14px;
  padding: 14px;
}

.checkout-success {
  display: grid;
  justify-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.checkout-success-icon {
  display: grid;
  place-items: center;
  width: 92px;
  height: 92px;
  border-radius: 999px;
  background: #18c269;
  color: #fff;
  font-size: 46px;
  font-weight: 800;
}

.checkout-summary-card h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.checkout-summary-row {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 10px;
  font-size: 14px;
}

.checkout-success-action {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.checkout-success-button {
  min-width: 320px;
  max-width: 420px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.checkout-inline-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #ffffff;
  border-radius: 999px;
  flex-shrink: 0;
  vertical-align: middle;
  animation: spin .8s linear infinite;
}

.checkout-password-wrap {
  position: relative;
}

.checkout-password-wrap input {
  width: 100%;
  padding-right: 50px;
}

.checkout-eye {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  border: 0;
  background: transparent;
  color: inherit;
  opacity: 0.7;
  cursor: pointer;
  padding: 0;
  line-height: 0;
}

.checkout-eye svg {
  width: 20px;
  height: 20px;
}

.checkout-password-rules {
  display: grid;
  gap: 8px;
}

.checkout-rule {
  font-size: 13px;
  opacity: 0.6;
}

.checkout-rule.ok {
  color: #18c269;
  opacity: 1;
}

.checkout-inline-error {
  margin-top: 10px;
  color: #ff6b6b;
  font-size: 13px;
  width: 90%;
  margin-left: auto;
  margin-right: auto;
  text-align: center;
}

.checkout-access-transition {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 24px;
  border-radius: 20px;
  background: rgba(7, 10, 16, 0.96);
  animation: fadeInUp .35s ease-out;
}

.checkout-access-spinner {
  width: 54px;
  height: 54px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: #18c269;
  border-radius: 999px;
  animation: spin .8s linear infinite;
}

.checkout-access-line {
  margin: 0;
  text-align: center;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.checkout-access-line-primary {
  font-size: 24px;
  color: #e7fff2;
}

.checkout-access-line-secondary {
  font-size: 18px;
  background: linear-gradient(90deg, #2fe08a, #84fdbd);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.checkout-theme-light .checkout-access-transition {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #d7dde6;
}

.checkout-theme-light .checkout-access-spinner {
  border-color: rgba(15, 23, 42, 0.2);
  border-top-color: #18c269;
}

.checkout-theme-light .checkout-access-line-primary {
  color: #0f172a;
}

.checkout-theme-light .checkout-access-line-secondary {
  background: linear-gradient(90deg, #16a34a, #0ea5a3);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.checkout-footer {
  display: grid;
  gap: 12px;
  padding: 14px 24px;
  border-top: 1px solid rgba(255,255,255,.08);
  background: rgba(10,11,13,.96);
}

.checkout-theme-light .checkout-footer {
  border-top-color: #d7dde6;
  background: rgba(255,255,255,.96);
}

.checkout-footer-left {
  display: flex;
  align-items: center;
}

.checkout-footer-left-main {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
}

.checkout-footer-dot {
  width: 13px;
  height: 13px;
  border-radius: 999px;
  background: linear-gradient(180deg, #18c269, #0fa25f);
}

.checkout-footer-right {
  text-align: right;
}

.checkout-footer-main-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.checkout-footer-right small {
  display: block;
  font-size: 13px;
  opacity: 0.7;
}

.checkout-footer-discount-line {
  width: 100%;
  padding: 12px 18px;
  border-radius: 12px;
  border: 1px solid rgba(24,255,126,.35);
  background: linear-gradient(90deg, rgba(9,54,30,.96), rgba(8,73,37,.96));
}

.checkout-footer-discount-main,
.checkout-footer-discount-sub {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.checkout-footer-discount-main {
  justify-content: flex-start;
  gap: 10px;
  width: 100%;
  min-width: 0;
}

.checkout-footer-discount-icon {
  width: 18px;
  height: 18px;
  color: #8bffc0;
  flex: 0 0 auto;
}

.checkout-footer-discount-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1 1 auto;
  min-width: 0;
  font-size: 13px;
  color: #d2ffe6;
}

.checkout-footer-discount-text strong {
  color: #8bffc0;
  font-weight: 800;
}

.checkout-footer-discount-text-top,
.checkout-footer-discount-text-bottom {
  display: flex;
  align-items: center;
  gap: 10px 12px;
  min-width: 0;
}

.checkout-footer-discount-text-top {
  justify-content: space-between;
}

.checkout-footer-discount-text-bottom {
  flex-wrap: wrap;
}

.checkout-footer-coupon-remove {
  width: 20px;
  height: 20px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(255,255,255,.72);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.checkout-footer-discount-text span {
  min-width: 0;
  overflow-wrap: anywhere;
}

.checkout-footer-coupon-remove:disabled {
  opacity: 0.45;
  cursor: default;
}

.checkout-footer-total-only {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.checkout-footer-price-row {
  display: flex;
  align-items: baseline;
  gap: 14px;
}

.checkout-footer-final-price {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
}

.checkout-footer-cycle-suffix {
  font-size: 12px;
  font-weight: 600;
  opacity: 0.72;
}

.checkout-footer-original-price {
  font-size: 16px;
  color: rgba(255,255,255,.62);
  text-decoration: line-through;
  text-decoration-thickness: 2px;
}

.checkout-theme-light .checkout-footer-coupon-remove {
  color: rgba(15,23,42,.62);
}

.checkout-theme-light .checkout-footer-discount-line {
  border-color: rgba(24,194,105,.3);
  background: linear-gradient(90deg, rgba(222,255,238,.95), rgba(206,255,228,.95));
}

.checkout-theme-light .checkout-footer-discount-main strong {
  color: #0d8a4d;
}

.checkout-theme-light .checkout-footer-discount-icon {
  color: #0d8a4d;
}

.checkout-theme-light .checkout-footer-discount-text {
  color: rgba(15,23,42,.78);
}

.checkout-theme-light .checkout-footer-discount-text strong {
  color: #0d8a4d;
}

.checkout-theme-light .checkout-footer-original-price {
  color: rgba(15,23,42,.48);
}

.checkout-footer-right strong {
  font-size: 28px;
}

.checkout-loader-wrap {
  display: grid;
  place-items: center;
  min-height: 40vh;
}

.checkout-loader {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255,255,255,.15);
  border-top-color: #18c269;
  border-radius: 999px;
  animation: spin .8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (min-width: 981px) and (max-width: 1440px) and (max-height: 980px) {
  .checkout-title-card {
    font-size: 22px;
    line-height: 1.08;
    letter-spacing: -0.02em;
    white-space: nowrap;
  }
}

@media (min-width: 981px) {
  .checkout-stage {
    transform: scale(0.9);
    transform-origin: center center;
  }

  .checkout-footer {
    position: sticky;
    bottom: 0;
    width: 100%;
    z-index: 10;
  }
}

@media (max-width: 980px) {
  .checkout-shell {
    height: auto;
    min-height: 100dvh;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .checkout-layout {
    grid-template-columns: 1fr;
    height: auto;
    min-height: 100dvh;
  }

  .checkout-banner-desktop {
    display: none;
  }

  .checkout-main {
    display: grid;
    grid-template-rows: auto 1fr auto;
    min-height: 100dvh;
    height: auto;
  }

  .checkout-mobile-banner {
    display: flex;
    align-items: center;
    height: 89px;
    margin: 14px 14px 0;
    padding: 0 20px;
    border-radius: 14px;
    background-position: center;
    background-size: cover;
    background-repeat: no-repeat;
    flex-shrink: 0;
  }

  .checkout-stage {
    max-width: none;
    width: 100%;
    padding: 22px 16px 28px;
    display: block;
    align-self: stretch;
  }

  .checkout-copy,
  .checkout-form,
  .checkout-methods,
  .checkout-card-preview,
  .checkout-pix-card,
  .checkout-note-box,
  .checkout-summary-card,
  .checkout-success,
  .checkout-secondary.mt-8 {
    width: 100%;
  }

  .checkout-protected-footer {
    width: 100%;
    padding: 0 16px;
    margin-bottom: 8px;
  }

  .checkout-title {
    font-size: 22px;
    line-height: 1.12;
  }

  .checkout-subtitle {
    font-size: 15px;
  }

  .checkout-field input,
  .checkout-field select,
  .checkout-password-wrap input {
    font-size: 16px;
  }

  .checkout-method-card {
    height: 116px;
    gap: 18px;
    padding: 0 22px;
  }

  .checkout-card-preview-inner {
    min-height: 176px;
  }

  .checkout-card-number {
    font-size: 22px;
  }

  .checkout-card-preview {
    width: 100%;
    max-width: 100%;
  }

  .checkout-card-meta,
  .checkout-card-meta-left {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .checkout-card-brand-badge {
    justify-self: start;
  }

  .checkout-card-grid {
    grid-template-columns: 1fr;
  }

  .checkout-pix-card {
    grid-template-columns: 1fr;
  }

  .checkout-pix-qr {
    width: 100%;
    height: auto;
    aspect-ratio: 1;
  }

  .checkout-footer {
    position: static;
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
    padding: 14px 16px;
  }

  .checkout-footer-left {
    font-size: 16px;
    line-height: 1.2;
  }

  .checkout-footer-right,
  .checkout-footer-total-only {
    text-align: left;
    align-items: stretch;
  }

  .checkout-footer-price-row {
    justify-content: flex-start;
  }

  .checkout-footer-main-row {
    flex-direction: column;
    align-items: stretch;
  }

  .checkout-footer-discount-line {
    padding: 10px 12px;
  }

  .checkout-footer-discount-main {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    grid-template-areas:
      "icon top x"
      "icon discount economy";
    align-items: center;
    gap: 6px 8px;
  }

  .checkout-footer-discount-text {
    display: contents;
    font-size: 11px;
    line-height: 1.25;
  }

  .checkout-footer-discount-text-top {
    display: contents;
  }

  .checkout-footer-discount-text-bottom {
    display: contents;
  }

  .checkout-footer-discount-text-bottom span {
    min-width: 0;
  }

  .checkout-footer-discount-text-top span {
    white-space: nowrap;
    min-width: 0;
  }

  .checkout-footer-discount-text-top span:first-child {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .checkout-footer-discount-icon {
    grid-area: icon;
  }

  .checkout-footer-discount-text-top span:first-child {
    grid-area: top;
  }

  .checkout-footer-coupon-remove {
    grid-area: x;
    justify-self: end;
    align-self: center;
  }

  .checkout-footer-discount-text-bottom span:first-child {
    grid-area: discount;
    justify-self: start;
    white-space: nowrap;
  }

  .checkout-footer-discount-text-bottom span:last-child {
    grid-area: economy;
    justify-self: end;
    white-space: nowrap;
  }

  .checkout-footer-right strong {
    font-size: 24px;
  }
}
</style>











