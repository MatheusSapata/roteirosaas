<template>
  <!-- Dois modelos (Admin Master › Ofertas e checkout › Checkouts): o clássico (imagem na coluna lateral)
       e o "Banner no topo", mobile first, inspirado no checkout do Viaje On. As etapas são as mesmas;
       no modelo com banner os contêineres têm classes próprias (cb-*) para não herdar o layout clássico. -->
  <div :class="[isBannerModel ? 'cb-shell' : 'checkout-shell', themeClass, { 'checkout-pending': !config }]">
    <div :class="isBannerModel ? 'cb-page' : 'checkout-layout'">
      <aside v-if="config && !isBannerModel" class="checkout-banner-desktop" :style="desktopBannerStyle"></aside>

      <main :class="isBannerModel ? 'cb-main' : 'checkout-main'">
        <div v-if="config && !isBannerModel && !isPaymentApproved" class="checkout-mobile-banner" :style="mobileBannerStyle"></div>

        <template v-if="isBannerModel && config">
          <picture v-if="bannerDesktopUrl || bannerMobileUrl" class="cb-banner">
            <source v-if="bannerMobileUrl" media="(max-width: 767px)" :srcset="bannerMobileUrl" />
            <img :src="bannerDesktopUrl || bannerMobileUrl" :alt="config.offer.title" />
          </picture>

          <div class="cb-head">
            <img :src="brandLogoSrc" alt="Roteiro Online" class="cb-head-logo" width="150" height="45" />
            <p class="cb-head-title">{{ config.offer.title }}</p>
            <p v-if="config.offer.subtitle" class="cb-head-sub">{{ config.offer.subtitle }}</p>
            <div class="cb-head-chips">
              <span class="is-ok"><ShieldCheckIcon aria-hidden="true" />Compra segura</span>
              <span><LockIcon aria-hidden="true" />Dados protegidos</span>
              <span><BadgeCheckIcon aria-hidden="true" />7 dias de garantia</span>
            </div>
          </div>

          <ol v-if="!loading && !errorMessage" class="cb-steps" :aria-label="`Etapa ${progressStep} de 3`">
            <li
              v-for="(label, index) in progressLabels"
              :key="label"
              :class="{ 'is-active': index + 1 === progressStep, 'is-done': index + 1 < progressStep }"
              :aria-current="index + 1 === progressStep ? 'step' : undefined"
            >
              <span class="cb-step-pill">
                <span class="cb-step-dot">
                  <CheckIcon v-if="index + 1 < progressStep" aria-hidden="true" />
                  <template v-else>{{ index + 1 }}</template>
                </span>
                <span class="cb-step-label">{{ label }}</span>
              </span>
            </li>
          </ol>
        </template>

        <section :class="isBannerModel ? 'cb-stage' : 'checkout-stage'">
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
              <p class="checkout-eyebrow">{{ isLegacyRenewal ? "Vamos renovar sua assinatura!" : isUpgradeFlow ? "Vamos fazer seu upgrade!" : "Vamos começar!" }}</p>
              <h1 class="checkout-title">Informe seus dados para continuar</h1>
              <p class="checkout-subtitle">Todos os dados são necessários para a emissão da sua compra.</p>
            </div>

            <form id="checkout-details-form" class="checkout-form" @submit.prevent="submitDetails">
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
                    <input
                      v-model="form.customer_zipcode"
                      :disabled="lockedProfileFields.customer_zipcode"
                      placeholder="00000-000"
                      inputmode="numeric"
                      @blur="lookupCep"
                      @input="onCepInput"
                    />
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
              <p v-if="cepStatus" class="checkout-cep-status" :class="{ 'is-error': cepStatusError }" role="status">{{ cepStatus }}</p>
              <div class="checkout-address-grid">
                <label class="checkout-field checkout-address-street">
                  <span>Rua</span>
                  <input v-model="form.address_street" autocomplete="address-line1" placeholder="Rua, avenida..." />
                </label>
                <label class="checkout-field checkout-address-number">
                  <span>Número</span>
                  <input v-model="form.address_number" placeholder="Nº ou S/N" />
                </label>
                <label class="checkout-field checkout-address-complement">
                  <span>Complemento (opcional)</span>
                  <input v-model="form.address_complement" autocomplete="address-line2" placeholder="Sala, apto..." />
                </label>
                <label class="checkout-field checkout-address-neighborhood">
                  <span>Bairro</span>
                  <input v-model="form.address_neighborhood" placeholder="Bairro" />
                </label>
                <label class="checkout-field checkout-address-city">
                  <span>Cidade</span>
                  <input v-model="form.address_city" autocomplete="address-level2" placeholder="Cidade" />
                </label>
                <label class="checkout-field checkout-address-state">
                  <span>UF</span>
                  <input v-model="form.address_state" maxlength="2" autocomplete="address-level1" placeholder="UF" @input="form.address_state = form.address_state.toUpperCase()" />
                </label>
              </div>
              <!-- Renovação do plano antigo (valor que o cliente já pagava) e upgrade do plano antigo (valor cheio): sem cupom. -->
              <label v-if="!isLegacyRenewal && !isLegacyUpgrade" class="checkout-field">
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
                <span>Pagar com PIX Automático</span>
              </button>
              <button class="checkout-method-card" @click="chooseCard">
                <div class="checkout-method-icon">
                  <CreditCardIcon aria-hidden="true" />
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
            <form id="checkout-card-form" class="checkout-form" @submit.prevent="submitCard">
              <div class="checkout-card-info">
                <div class="checkout-card-info-icon">
                  <CreditCardIcon aria-hidden="true" />
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
              <label v-if="installmentOptions.length > 1" class="checkout-field">
                <span>Parcelas</span>
                <select v-model.number="card.installment_count" class="checkout-select">
                  <option v-for="option in installmentOptions" :key="option.count" :value="option.count">
                    {{ installmentOptionLabel(option) }}
                  </option>
                </select>
              </label>
              <button class="checkout-secondary" type="button" @click="goBackToMethod">Pagar com outro método</button>
              <button class="checkout-primary" type="submit" :disabled="submitting || cardAwaitingConfirmation">
                <span v-if="submitting || cardAwaitingConfirmation" class="checkout-inline-spinner" aria-hidden="true"></span>
                {{ submitting ? "Processando..." : (cardAwaitingConfirmation ? "Aguardando confirmação..." : (isBannerModel ? "Pagar agora" : "Prosseguir")) }}
              </button>
            </form>
            </div>
          </template>

          <template v-else-if="step === 'pix'">
            <div class="checkout-copy">
              <p class="checkout-eyebrow">Você está quase lá!</p>
              <h1 class="checkout-title">Boa! Você escolheu pagar no PIX Automático!</h1>
            </div>

            <div class="checkout-pix-card">
              <div class="checkout-pix-qr">
                <img v-if="pixDisplaySrc" :src="pixDisplaySrc" alt="QR Code PIX" />
                <p v-else class="checkout-pix-empty">QR indisponível no momento. Use o código PIX abaixo.</p>
              </div>
              <div class="checkout-pix-copy">
                <p>Escaneie o QR Code para pagar a primeira cobrança e autorizar as próximas cobranças automáticas.</p>
                <button class="checkout-secondary" @click="copyPixCode">Copiar código</button>
              </div>
            </div>

            <div class="checkout-note-box">
              <p>Após o pagamento, você será redirecionado automaticamente.</p>
              <p>Ao confirmar no banco, você autoriza a recorrência mensal ou anual do seu plano.</p>
              <p v-if="promoAmount">Hoje você paga {{ money(promoAmount) }}. As próximas mensalidades são de {{ formattedAmount }}.</p>
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
              <div class="checkout-summary-row"><span>Valor pago</span><strong>{{ paidAmountLabel }}</strong></div>
              <div class="checkout-summary-row"><span>Forma de pagamento</span><strong>{{ paymentMethodLabel }}</strong></div>
              <div class="checkout-summary-row"><span>Data e hora</span><strong>{{ paidAtLabel }}</strong></div>
            </div>

            <div class="checkout-success-action">
              <button class="checkout-primary checkout-success-button" :disabled="true" type="button">
                <span v-if="onboardingRedirecting" class="checkout-inline-spinner" aria-hidden="true"></span>
                <span>{{ isLegacyRenewal ? "Renovando sua assinatura..." : isUpgradeFlow ? "Realizando seu upgrade..." : "Iniciando seu cadastro..." }}</span>
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
                    <EyeOffIcon v-if="showPassword" aria-hidden="true" />
                    <EyeIcon v-else aria-hidden="true" />
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
                    <EyeOffIcon v-if="showConfirmPassword" aria-hidden="true" />
                    <EyeIcon v-else aria-hidden="true" />
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
              {{ isLegacyRenewal ? "Estamos renovando sua assinatura..." : isUpgradeFlow ? "Estamos realizando seu upgrade..." : "Estamos finalizando seu cadastro..." }}
            </p>
            <p class="checkout-access-line checkout-access-line-secondary">
              Sua nova maneira de apresentar viagens começa agora.
            </p>
          </div>

          <p v-if="inlineError" class="checkout-inline-error">{{ inlineError }}</p>
        </section>

        <div v-if="config && step !== 'success' && step !== 'password'" class="checkout-protected checkout-protected-footer">
          <LockIcon aria-hidden="true" />
          <span>Sua compra está protegida. Pagamento processado pelo Asaas</span>
        </div>

        <!-- Modelo com banner: resumo ao lado no computador; no celular, total e botão fixos no rodapé. -->
        <aside v-if="isBannerModel && config && !errorMessage && step !== 'success' && step !== 'password'" class="cb-summary" aria-label="Resumo do pedido">
          <div class="cb-summary-card" :class="{ 'has-cta': Boolean(barAction) }">
            <p class="cb-summary-title">Resumo do pedido</p>
            <div class="cb-summary-item">
              <span>{{ config.offer.footer_product_label || config.offer.title }}</span>
              <span>{{ billingCycle === "annual" ? "Anual" : "Mensal" }}</span>
            </div>
            <div v-if="hasAppliedCoupon" class="cb-summary-coupon">
              <TicketPercentIcon aria-hidden="true" />
              <span>Cupom <b>{{ effectiveAppliedCouponCode }}</b><template v-if="discountPercentLabel"> · {{ discountPercentLabel }}</template></span>
              <button type="button" :disabled="submitting" aria-label="Remover cupom" @click="removeAppliedCoupon">×</button>
            </div>
            <div class="cb-summary-total">
              <small>
                {{ promoAmount ? "Hoje você paga" : "Total a pagar" }}
                <s v-if="promoAmount">{{ formattedAmount }}</s>
                <s v-else-if="hasAppliedCoupon && originalAmountLabel">{{ originalAmountLabel }}</s>
              </small>
              <div class="cb-summary-price">
                <strong>{{ footerPrice }}</strong>
                <span v-if="footerSuffix">{{ footerSuffix }}</span>
              </div>
            </div>
            <p v-if="footerNote" class="cb-summary-note">{{ footerNote }}</p>
            <button
              v-if="barAction"
              class="cb-bar-cta"
              type="submit"
              :form="barAction.form"
              :disabled="submitting || cardAwaitingConfirmation"
            >
              <span v-if="submitting || cardAwaitingConfirmation" class="checkout-inline-spinner" aria-hidden="true"></span>
              {{ barAction.label }}
            </button>
            <p class="cb-summary-guarantee"><ShieldCheckIcon aria-hidden="true" />7 dias de garantia: não gostou, devolvemos 100%.</p>
          </div>
        </aside>

        <footer v-if="config && !isBannerModel && step !== 'success' && step !== 'password'" class="checkout-footer">
          <div v-if="hasAppliedCoupon" class="checkout-footer-discount-line">
            <div class="checkout-footer-discount-main">
              <TicketPercentIcon class="checkout-footer-discount-icon" aria-hidden="true" />
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
                <small>{{ promoAmount ? "Hoje você paga" : "Total a pagar" }}</small>
                <div class="checkout-footer-price-row">
                  <span v-if="promoAmount" class="checkout-footer-original-price">{{ formattedAmount }}</span>
                  <span v-else-if="hasAppliedCoupon && originalAmountLabel" class="checkout-footer-original-price">{{ originalAmountLabel }}</span>
                  <div class="checkout-footer-final-price">
                    <strong>{{ footerPrice }}</strong>
                    <span v-if="footerSuffix" class="checkout-footer-cycle-suffix">{{ footerSuffix }}</span>
                  </div>
                </div>
                <span v-if="footerNote" class="checkout-footer-note">{{ footerNote }}</span>
              </div>
            </div>
          </div>
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  BadgeCheckIcon,
  CheckIcon,
  CreditCardIcon,
  EyeIcon,
  EyeOffIcon,
  LockIcon,
  ShieldCheckIcon,
  TicketPercentIcon
} from "lucide-vue-next";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import { captureAttribution, currentAttribution, currentSellerCode } from "../../utils/attribution";
import { SALES_META_PIXEL_ID, firstMetaSend, metaBrowserContext, metaStandardEventId, startMetaPixels, trackMetaEvent } from "../../utils/metaPixel";
import {
  LEGACY_RENEWAL_OFFER_KEY,
  createCheckoutSession,
  createLegacyRenewalCheckoutSession,
  createLegacyUpgradeCheckoutSession,
  createUpgradeCheckoutSession,
  finishCheckoutPassword,
  getCheckoutConfig,
  getCheckoutSession,
  getLegacyRenewalCheckoutConfig,
  previewCheckoutCoupon,
  trackCheckoutEvent,
  refreshCheckoutSession,
  startCardCheckout,
  startPixCheckout,
  updateUpgradeCheckoutSessionDetails,
  type CheckoutCouponPreview,
  type CheckoutInstallmentOption,
  type CheckoutPublicConfig,
  type CheckoutSession
} from "../../services/checkout";
import { installmentPreview } from "../../utils/cardInstallments";
import { useAuthStore } from "../../store/useAuthStore";
import { resolveMediaUrl } from "../../utils/media";
import ColoredLogo from "../../assets/Logo Cor - Roteiro Online.png";
import WhiteLogo from "../../assets/Logo Branco - Roteiro Online.png";

type Step = "details" | "method" | "card" | "pix" | "success" | "password";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const offerKey = computed(() => String(route.params.offerKey || route.query.offer || "").trim().toLowerCase());
// Renovação do plano antigo (/checkout/renovacao-assinatura): plano, ciclo e valor vêm do servidor.
const isLegacyRenewal = computed(() => offerKey.value === LEGACY_RENEWAL_OFFER_KEY || Boolean(session.value?.is_legacy_renewal));
// Upgrade do plano antigo (Profissional ou Agência) para o plano único: o servidor escolhe a oferta
// do ciclo e cobra o valor cheio, sem cupom e sem promoção.
const isLegacyUpgrade = computed(
  () => String(route.query.legacy_upgrade || "") === "1" || Boolean(session.value?.is_legacy_upgrade)
);
const isUpgradeFlow = computed(
  () =>
    String(route.query.upgrade || "") === "1" ||
    Boolean(session.value?.is_upgrade) ||
    isLegacyRenewal.value ||
    isLegacyUpgrade.value
);
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

// Pixels deste checkout: os da oferta (Admin Master › Ofertas e checkout) e o da página de vendas,
// o mesmo da LP. A renovação do plano antigo não manda eventos ao Meta.
let metaPixelIds: string[] = [];
const checkoutPixelIds = () => {
  if (isLegacyRenewal.value) return [];
  const configured = (config.value?.pixels || []).filter(pixel => pixel.active && pixel.pixel_id.trim()).map(pixel => pixel.pixel_id.trim());
  return [...configured, SALES_META_PIXEL_ID];
};
const initializeMetaPixels = () => {
  if (metaPixelIds.length) return;
  metaPixelIds = startMetaPixels(checkoutPixelIds());
};

// Passo do checkout → evento padrão do Meta, igual ao servidor (META_STANDARD_EVENTS em
// app/services/checkout.py). Só o nome do passo decide: a tela de senha com a compra já paga não é
// outra compra.
const META_STANDARD_EVENTS: Record<string, string> = {
  details_submit_success: "Lead",
  details_completed: "Lead",
  step_method_view: "InitiateCheckout",
  payment_method_click: "AddPaymentInfo",
  pix_started: "AddPaymentInfo",
  card_processing: "AddPaymentInfo",
  payment_success: "Purchase",
};

const sendMetaCheckoutEvent = (
  eventName: string,
  extra: {
    step?: string | null;
    status?: string | null;
    payment_method?: string | null;
  } = {}
) => {
  const token = session.value?.token;
  if (!metaPixelIds.length || !token) return;
  const checkoutStep = extra.step ?? step.value;
  const checkoutStatus = extra.status ?? session.value?.status ?? null;
  const paymentMethod = extra.payment_method ?? session.value?.payment_method ?? null;
  // O que a pessoa paga agora (1ª mensalidade promocional ou o valor com cupom), como o servidor.
  const data = {
    currency: "BRL",
    value: Number(session.value?.first_payment_amount || session.value?.amount || 0),
    content_name: config.value?.offer.title || config.value?.offer.key || "Checkout",
    content_ids: [session.value?.offer_key || config.value?.offer.key].filter(Boolean),
    content_type: "product",
    num_items: 1,
  };
  trackMetaEvent(
    metaPixelIds,
    "CheckoutStatus",
    { ...data, checkout_event_name: eventName, checkout_step: checkoutStep, checkout_status: checkoutStatus, checkout_payment_method: paymentMethod, offer_key: config.value?.offer.key || "" },
    { custom: true, eventId: [token, eventName, checkoutStep, checkoutStatus, paymentMethod].map(value => String(value || "").trim().toLowerCase() || "-").join("|") }
  );
  const standardEvent = META_STANDARD_EVENTS[String(eventName || "").trim().toLowerCase()];
  if (!standardEvent) return;
  const eventId = metaStandardEventId(token, standardEvent);
  if (!firstMetaSend(eventId)) return;
  trackMetaEvent(metaPixelIds, standardEvent, standardEvent === "Purchase" ? { ...data, order_id: token } : data, { eventId });
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
  address_street: "",
  address_number: "",
  address_complement: "",
  address_neighborhood: "",
  address_city: "",
  address_state: "",
  coupon_code: ""
});

// Endereço completo para a nota fiscal: o CEP preenche rua, bairro, cidade e UF (ViaCEP).
const cepStatus = ref("");
const cepStatusError = ref(false);
let lastCepLookup = "";

const addressPayload = () => ({
  street: form.address_street.trim(),
  number: form.address_number.trim(),
  complement: form.address_complement.trim(),
  neighborhood: form.address_neighborhood.trim(),
  city: form.address_city.trim(),
  state: form.address_state.trim().toUpperCase()
});

const lookupCep = async () => {
  const digits = form.customer_zipcode.replace(/\D/g, "");
  if (digits.length !== 8 || digits === lastCepLookup) return;
  lastCepLookup = digits;
  cepStatus.value = "Buscando endereço...";
  cepStatusError.value = false;
  try {
    const response = await fetch(`https://viacep.com.br/ws/${digits}/json/`);
    const data = await response.json();
    if (!response.ok || data?.erro) throw new Error("not_found");
    form.address_street = data.logradouro || form.address_street;
    form.address_neighborhood = data.bairro || form.address_neighborhood;
    form.address_city = data.localidade || form.address_city;
    form.address_state = String(data.uf || form.address_state).toUpperCase().slice(0, 2);
    cepStatus.value = data.logradouro ? "Endereço preenchido pelo CEP. Confira e informe o número." : "CEP geral da cidade: informe rua, número e bairro.";
  } catch {
    cepStatus.value = "Não achamos este CEP. Confira os números ou preencha o endereço.";
    cepStatusError.value = true;
  }
};

const onCepInput = () => {
  if (form.customer_zipcode.replace(/\D/g, "").length === 8) lookupCep();
};

const fillAddressFromSession = (address?: Partial<Record<string, string>> | null) => {
  form.address_street = address?.street || form.address_street;
  form.address_number = address?.number || form.address_number;
  form.address_complement = address?.complement || form.address_complement;
  form.address_neighborhood = address?.neighborhood || form.address_neighborhood;
  form.address_city = address?.city || form.address_city;
  form.address_state = address?.state || form.address_state;
};

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
// Modelo "Banner no topo" (estilo Viaje On): banner, cabeçalho da compra, etapas e resumo/barra fixa.
const isBannerModel = computed(() => config.value?.layout === "banner");
const bannerDesktopUrl = computed(() => resolveMediaUrl(config.value?.desktop_image_url) || "");
const bannerMobileUrl = computed(() => resolveMediaUrl(config.value?.mobile_banner_url) || "");
const brandLogoSrc = computed(() => (config.value?.theme_mode === "light" ? ColoredLogo : WhiteLogo));
const progressStep = computed(() => (step.value === "details" ? 1 : step.value === "success" || step.value === "password" ? 3 : 2));
const progressLabels = computed(() => ["Seus dados", "Pagamento", isUpgradeFlow.value ? "Pronto" : "Acesso"]);
const effectiveAmount = computed(() => Number(session.value?.amount ?? couponPreview.value?.amount ?? config.value?.offer.amount ?? 0));
const effectiveOriginalAmount = computed(() => Number(session.value?.original_amount ?? couponPreview.value?.original_amount ?? config.value?.offer.amount ?? 0));
const effectiveDiscountAmount = computed(() => Number(session.value?.discount_amount ?? couponPreview.value?.discount_amount ?? 0));
const effectiveAppliedCouponCode = computed(() => String(session.value?.applied_coupon_code || couponPreview.value?.applied_coupon_code || "").trim());
const formattedAmount = computed(() => {
  const value = effectiveAmount.value;
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
});
const hasAppliedCoupon = computed(() => Boolean(effectiveAppliedCouponCode.value && effectiveDiscountAmount.value > 0));
const money = (value: number | string) => Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const billingCycle = computed(() => session.value?.billing_cycle || config.value?.offer.billing_cycle || "monthly");
// 1ª mensalidade promocional: depois da compra começar vale o que o servidor travou na sessão;
// antes, a da oferta (só para quem assina pela primeira vez e enquanto a promoção está no prazo).
const promoAmount = computed(() => {
  if (session.value) return Number(session.value.first_payment_amount || 0);
  const offer = config.value?.offer;
  if (!offer || offer.billing_cycle !== "monthly" || isUpgradeFlow.value || !offer.first_payment_amount) return 0;
  if (offer.first_payment_ends_at && new Date(offer.first_payment_ends_at).getTime() <= Date.now()) return 0;
  const value = Number(offer.first_payment_amount);
  return value > 0 && value < effectiveAmount.value ? value : 0;
});
// Parcelas do cartão (anual): as do servidor quando a compra já começou; antes, a prévia da oferta.
const installmentOptions = computed<CheckoutInstallmentOption[]>(() => {
  if (session.value?.installment_options?.length) return session.value.installment_options;
  const offer = config.value?.offer;
  if (!offer || offer.billing_cycle !== "annual" || (offer.max_installments || 1) <= 1 || hasAppliedCoupon.value) return [];
  return installmentPreview(effectiveAmount.value, offer.max_installments || 1, offer.installment_fixed_values || {}).map(row => ({
    count: row.count,
    value: String(row.value),
    total: String(row.total),
    no_interest: row.count === 1
  }));
});
const topInstallment = computed(() => (installmentOptions.value.length > 1 ? installmentOptions.value[installmentOptions.value.length - 1] : null));
const selectedInstallment = computed(() => installmentOptions.value.find(option => option.count === card.installment_count) || null);
const installmentOptionLabel = (option: CheckoutInstallmentOption) =>
  option.count === 1
    ? `À vista: ${money(option.value)}`
    : `${option.count}x de ${money(option.value)} (total ${money(option.total)})`;
const footerPrice = computed(() => {
  if (promoAmount.value) return money(promoAmount.value);
  if (step.value === "card" && selectedInstallment.value && selectedInstallment.value.count > 1) {
    return `${selectedInstallment.value.count}x ${money(selectedInstallment.value.value)}`;
  }
  return formattedAmount.value;
});
const footerSuffix = computed(() => {
  if (promoAmount.value) return "no 1º mês";
  if (step.value === "card" && selectedInstallment.value && selectedInstallment.value.count > 1) return "";
  return billingCycle.value === "annual" ? "/ ano" : "/ mês";
});
const footerNote = computed(() => {
  if (promoAmount.value) return `Depois, ${formattedAmount.value}/mês. Sem fidelidade.`;
  if (step.value === "card" && selectedInstallment.value && selectedInstallment.value.count > 1) {
    return `Total de ${money(selectedInstallment.value.total)} no cartão`;
  }
  if (topInstallment.value) return `ou até ${topInstallment.value.count}x de ${money(topInstallment.value.value)} no cartão`;
  return "";
});
const paidAmountLabel = computed(() => {
  const count = Number(card.installment_count || 1);
  const option = installmentOptions.value.find(item => item.count === count);
  if (session.value?.payment_method === "card" && option && option.count > 1) return `${option.count}x de ${money(option.value)}`;
  if (promoAmount.value) return money(promoAmount.value);
  return formattedAmount.value;
});
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
const paymentMethodLabel = computed(() => (session.value?.payment_method === "card" ? "Cartão de crédito" : "PIX Automático"));
// Modelo com banner: ao trocar de etapa com a etapa acima da tela (ex.: depois do botão da barra fixa),
// a página volta para as etapas.
watch(step, async () => {
  if (!isBannerModel.value || typeof window === "undefined") return;
  await nextTick();
  const steps = document.querySelector(".cb-steps");
  if (steps && steps.getBoundingClientRect().top < 0) steps.scrollIntoView({ block: "start", behavior: "smooth" });
});
// Modelo com banner, no celular: o botão da etapa fica na barra fixa do rodapé (envia o formulário da etapa).
const barAction = computed(() => {
  if (loading.value || errorMessage.value) return null;
  if (step.value === "details") return { form: "checkout-details-form", label: submitting.value ? "Prosseguindo..." : "Prosseguir" };
  if (step.value === "card") {
    const label = submitting.value ? "Processando..." : cardAwaitingConfirmation.value ? "Aguardando confirmação..." : "Pagar agora";
    return { form: "checkout-card-form", label };
  }
  return null;
});
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
    config.value = isLegacyRenewal.value ? await getLegacyRenewalCheckoutConfig() : await getCheckoutConfig(offerKey.value);
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
  // Cliente novo informa o endereço completo (nota fiscal). Quem já é cliente pode seguir sem ele.
  const address = addressPayload();
  if (!isUpgradeFlow.value && (!address.street || !address.number || !address.neighborhood || !address.city || address.state.length !== 2)) {
    inlineError.value = "Informe o endereço completo: precisamos dele para emitir a nota fiscal.";
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
      // Cookies do Meta e a página: o servidor manda os mesmos eventos pela API de Conversões.
      metadata: { ...(extra.metadata || {}), ...metaBrowserContext() },
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
        customer_address: addressPayload(),
      });
    } else {
      session.value = await createCheckoutSession({
        offer_key: config.value.offer.key,
        customer_name: form.customer_name,
        customer_email: normalizedEmail,
        customer_document: form.customer_document,
        customer_phone: form.customer_phone,
        customer_zipcode: form.customer_zipcode,
        customer_address: addressPayload(),
        coupon_code: form.coupon_code,
        // Origem da compra (UTMs do anúncio, guardadas desde a LP): vai para o cadastro da empresa.
        utm: { ...currentAttribution(), seller_code: currentSellerCode() }
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
  if (!config.value || isLegacyRenewal.value || isLegacyUpgrade.value) return;
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
      customer_address: addressPayload(),
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
  fillAddressFromSession(data.customer_address);
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
      customer_address: addressPayload(),
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
      installment_count: installmentOptions.value.some(option => option.count === card.installment_count) ? card.installment_count : 1
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
  if (topInstallment.value && !installmentOptions.value.some(option => option.count === card.installment_count && option.count > 1)) {
    card.installment_count = topInstallment.value.count;
  }
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
  // UTMs do anúncio (vindas no endereço, da LP ou de um link direto para o checkout).
  captureAttribution();
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
      session.value = isLegacyRenewal.value
        ? await createLegacyRenewalCheckoutSession()
        : isLegacyUpgrade.value
          ? await createLegacyUpgradeCheckoutSession(config.value.offer.billing_cycle === "annual" ? "annual" : "monthly")
          : await createUpgradeCheckoutSession(config.value.offer.key, form.coupon_code || null);
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
  background: #07110e;
  color: #fff;
}

.checkout-theme-light {
  background: #f5f7f6;
  color: #0f172a;
}

.checkout-shell :deep(button:focus-visible),
.checkout-shell :deep(input:focus-visible),
.checkout-shell :deep(select:focus-visible) {
  outline: 2px solid #1de9a0;
  outline-offset: 2px;
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

.checkout-address-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.checkout-address-street { grid-column: span 4; }
.checkout-address-number { grid-column: span 2; }
.checkout-address-complement { grid-column: span 3; }
.checkout-address-neighborhood { grid-column: span 3; }
.checkout-address-city { grid-column: span 4; }
.checkout-address-state { grid-column: span 2; }

@media (max-width: 520px) {
  .checkout-address-street,
  .checkout-address-complement,
  .checkout-address-neighborhood,
  .checkout-address-city { grid-column: span 6; }
  .checkout-address-number,
  .checkout-address-state { grid-column: span 3; }
}

.checkout-cep-status {
  margin: -4px 0 0;
  font-size: 12.5px;
  opacity: 0.8;
}

.checkout-cep-status.is-error {
  color: #e05656;
  opacity: 1;
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

.checkout-footer-note {
  margin-top: 2px;
  font-size: 12px;
  font-weight: 600;
  opacity: 0.75;
}

.checkout-select {
  width: 100%;
}

/* A lista aberta do seletor usa o fundo do sistema: texto escuro para não sumir no tema escuro. */
.checkout-select option {
  color: #0f172a;
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

/* Enquanto a configuração carrega (o modelo ainda não é conhecido): só o carregamento, centralizado. */
.checkout-pending.checkout-shell .checkout-layout {
  grid-template-columns: minmax(0, 1fr);
}

/* ===== Modelo "Banner no topo" (mobile first, inspirado no checkout do Viaje On) ===== */
.cb-shell {
  --cb-bg: #edf1ee;
  --cb-card: #ffffff;
  --cb-ink: #111814;
  --cb-muted: #66706b;
  --cb-border: #e4e9e5;
  --cb-field: #ffffff;
  --cb-soft: #f4f7f5;
  --cb-accent: #e3f5ec;
  --cb-accent-ink: #0a7a55;
  --cb-primary: #0b8059;
  --cb-primary-deep: #07684a;
  --cb-on-primary: #ffffff;
  --cb-shadow: 0 1px 2px rgba(17, 24, 20, 0.05), 0 12px 32px -22px rgba(12, 31, 24, 0.35);
  min-height: 100dvh;
  overflow-x: hidden;
  background: var(--cb-bg);
  color: var(--cb-ink);
}
.cb-shell.checkout-theme-dark {
  --cb-bg: #0b100e;
  --cb-card: #141b18;
  --cb-ink: #eef3f0;
  --cb-muted: #9aa6a0;
  --cb-border: #24302b;
  --cb-field: #0f1513;
  --cb-soft: #1a2320;
  --cb-accent: #16302a;
  --cb-accent-ink: #5cf0bb;
  --cb-primary: #1fd497;
  --cb-primary-deep: #13b57f;
  --cb-on-primary: #06140e;
  --cb-shadow: 0 16px 36px -24px rgba(0, 0, 0, 0.7);
}
.cb-shell :deep(button:focus-visible),
.cb-shell :deep(input:focus-visible),
.cb-shell :deep(select:focus-visible),
.cb-shell :deep(a:focus-visible) {
  outline: 2px solid var(--cb-primary);
  outline-offset: 2px;
}
.cb-page {
  width: 100%;
  max-width: 1080px;
  margin: 0 auto;
  padding: 12px 16px calc(132px + env(safe-area-inset-bottom));
}
.cb-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.cb-banner {
  display: block;
}
.cb-banner img {
  display: block;
  width: 100%;
  height: auto;
  aspect-ratio: 9 / 5;
  max-height: 46vh;
  border-radius: 18px;
  object-fit: cover;
  background: var(--cb-soft);
}
.cb-head,
.cb-stage,
.cb-summary-card {
  border-radius: 22px;
  background: var(--cb-card);
  box-shadow: var(--cb-shadow);
}
.cb-head {
  display: grid;
  gap: 8px;
  padding: 18px;
}
/* O arquivo do logo tem margem transparente: o recorte é o mesmo do menu do painel. */
.cb-head-logo {
  width: 124px;
  height: 37px;
  object-fit: cover;
}
.cb-head-title {
  margin: 4px 0 0;
  font-family: var(--font-display, inherit);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.cb-head-sub {
  margin: 0;
  color: var(--cb-muted);
  font-size: 14px;
  line-height: 1.45;
}
.cb-head-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-top: 4px;
}
.cb-head-chips span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: var(--cb-soft);
  color: var(--cb-muted);
  font-size: 11.5px;
  font-weight: 700;
}
.cb-head-chips span.is-ok {
  background: var(--cb-accent);
  color: var(--cb-accent-ink);
}
.cb-head-chips svg {
  width: 13px;
  height: 13px;
}

/* Etapas: número em círculo, a etapa atual em pílula com o nome, traço entre elas. */
.cb-steps {
  scroll-margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 2px 0;
  padding: 0 4px;
  list-style: none;
}
.cb-steps li {
  display: flex;
  flex: 1;
  align-items: center;
  gap: 8px;
}
.cb-steps li:last-child {
  flex: none;
}
.cb-steps li:not(:last-child)::after {
  flex: 1;
  height: 3px;
  border-radius: 999px;
  background: var(--cb-border);
  content: "";
}
.cb-steps li.is-done:not(:last-child)::after {
  background: var(--cb-primary);
}
.cb-step-dot {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--cb-card);
  box-shadow: inset 0 0 0 1.5px var(--cb-border);
  color: var(--cb-muted);
  font-size: 12px;
  font-weight: 700;
}
.cb-step-dot svg {
  width: 14px;
  height: 14px;
}
.cb-steps li.is-active .cb-step-dot,
.cb-steps li.is-done .cb-step-dot {
  background: linear-gradient(135deg, var(--cb-primary), var(--cb-primary-deep));
  box-shadow: none;
  color: var(--cb-on-primary);
}
.cb-step-label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
.cb-step-pill {
  display: inline-flex;
  flex: none;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
}
.cb-steps li.is-active .cb-step-pill {
  padding: 3px 14px 3px 3px;
  background: var(--cb-accent);
}
.cb-steps li.is-active .cb-step-label {
  position: static;
  width: auto;
  height: auto;
  clip: auto;
  color: var(--cb-accent-ink);
  font-size: 13px;
  font-weight: 700;
}

/* A etapa num cartão. */
.cb-stage {
  position: relative;
  padding: 20px 18px 22px;
}
.cb-stage .checkout-copy,
.cb-stage .checkout-form,
.cb-stage .checkout-methods,
.cb-stage .checkout-pix-card,
.cb-stage .checkout-note-box,
.cb-stage .checkout-summary-card,
.cb-stage .checkout-success,
.cb-stage .checkout-secondary.mt-8 {
  width: 100%;
}
.cb-stage .checkout-copy {
  margin-bottom: 18px;
}
.cb-stage .checkout-eyebrow {
  margin-bottom: 6px;
  color: var(--cb-accent-ink);
  font-size: 12.5px;
  font-weight: 700;
  opacity: 1;
}
.cb-stage .checkout-title {
  font-family: var(--font-display, inherit);
  font-size: 21px;
  line-height: 1.2;
  letter-spacing: -0.02em;
  white-space: normal;
}
.cb-stage .checkout-subtitle {
  margin-top: 6px;
  color: var(--cb-muted);
  font-size: 14px;
  opacity: 1;
}
.cb-stage .checkout-form {
  gap: 14px;
}
.cb-stage .checkout-field {
  min-width: 0;
}
.cb-stage .checkout-field input,
.cb-stage .checkout-field select {
  width: 100%;
  min-width: 0;
}
.cb-stage .checkout-field span {
  color: var(--cb-muted);
  font-size: 13px;
  font-weight: 600;
  opacity: 1;
}
.cb-stage .checkout-field input,
.cb-stage .checkout-field select,
.cb-stage .checkout-password-wrap input {
  height: 48px;
  border: 1px solid var(--cb-border);
  border-radius: 14px;
  background: var(--cb-field);
  color: var(--cb-ink);
  font-size: 16px;
}
.cb-stage .checkout-field input:focus,
.cb-stage .checkout-field select:focus {
  border-color: var(--cb-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--cb-primary) 18%, transparent);
  outline: none;
}
.cb-stage .checkout-field-row {
  grid-template-columns: minmax(0, 1fr);
}
.cb-stage .checkout-coupon-apply,
.cb-stage .checkout-link-help {
  color: var(--cb-accent-ink);
  font-size: 13px;
  font-weight: 700;
}
.cb-stage .checkout-primary,
.cb-bar-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 52px;
  border: 0;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--cb-primary), var(--cb-primary-deep));
  color: var(--cb-on-primary);
  font-size: 16px;
  font-weight: 700;
  transition: filter 0.2s ease;
}
.cb-stage .checkout-primary:hover:not(:disabled),
.cb-bar-cta:hover:not(:disabled) {
  filter: brightness(1.08);
}
.cb-stage .checkout-primary:disabled,
.cb-bar-cta:disabled {
  opacity: 0.7;
}
.cb-stage .checkout-secondary {
  height: 48px;
  border: 1px solid var(--cb-border);
  border-radius: 14px;
  background: var(--cb-card);
  color: var(--cb-ink);
  font-size: 15px;
}

/* Formas de pagamento em cartões deitados, como as opções do Viaje On. */
.cb-stage .checkout-methods {
  gap: 10px;
}
.cb-stage .checkout-method-card {
  height: 72px;
  gap: 14px;
  padding: 0 18px;
  border: 0;
  border-radius: 16px;
  background: var(--cb-card);
  box-shadow: inset 0 0 0 1.5px var(--cb-border);
  color: var(--cb-ink);
  font-size: 15px;
  font-weight: 700;
  text-align: left;
}
.cb-stage .checkout-method-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 9px;
  border-radius: 12px;
  background: var(--cb-accent);
  color: var(--cb-accent-ink);
}
@media (hover: hover) and (pointer: fine) {
  .cb-stage .checkout-method-card:hover {
    background: var(--cb-accent);
    box-shadow: inset 0 0 0 2px var(--cb-primary);
    color: var(--cb-ink);
    transform: none;
  }
}
@media (hover: none) {
  .cb-stage .checkout-method-card:active {
    background: var(--cb-accent);
    box-shadow: inset 0 0 0 2px var(--cb-primary);
    color: var(--cb-ink);
  }
}
.cb-stage .checkout-card-info,
.cb-stage .checkout-pix-card,
.cb-stage .checkout-note-box,
.cb-stage .checkout-summary-card {
  border: 0;
  border-radius: 16px;
  background: var(--cb-soft);
}
.cb-stage .checkout-card-info {
  grid-template-columns: 40px minmax(0, 1fr);
  gap: 12px;
  padding: 14px 16px;
}
.cb-stage .checkout-card-info-icon {
  width: 40px;
  height: 40px;
  padding: 9px;
  border-radius: 12px;
  background: var(--cb-accent);
  color: var(--cb-accent-ink);
}
.cb-stage .checkout-card-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: end;
  gap: 12px;
}
.cb-stage .checkout-pix-card {
  grid-template-columns: minmax(0, 1fr);
}
.cb-stage .checkout-pix-qr {
  width: min(100%, 260px);
  height: auto;
  margin: 0 auto;
  aspect-ratio: 1;
}
.cb-stage .checkout-access-transition {
  border-radius: 22px;
}
.cb-main .checkout-protected-footer {
  width: 100%;
  margin: 0;
  padding: 0 8px;
  color: var(--cb-muted);
  opacity: 1;
}

/* Resumo: barra fixa no rodapé do celular (total e botão da etapa). */
.cb-summary {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 30;
  padding: 10px 16px calc(env(safe-area-inset-bottom) + 10px);
  border-top: 1px solid var(--cb-border);
  background: color-mix(in srgb, var(--cb-card) 95%, transparent);
  box-shadow: 0 -8px 24px -16px rgba(12, 31, 24, 0.35);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
}
.cb-summary-card {
  display: grid;
  grid-template-areas:
    "coupon"
    "total"
    "note";
  grid-template-columns: minmax(0, 1fr);
  align-items: center;
  gap: 6px 12px;
  max-width: 640px;
  margin: 0 auto;
  border-radius: 0;
  background: none;
  box-shadow: none;
}
.cb-summary-card.has-cta {
  grid-template-areas:
    "coupon coupon"
    "total cta"
    "note note";
  grid-template-columns: minmax(0, 1fr) auto;
}
.cb-summary-title,
.cb-summary-item,
.cb-summary-guarantee {
  display: none;
}
.cb-summary-coupon {
  display: flex;
  grid-area: coupon;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 6px 10px;
  border-radius: 12px;
  background: var(--cb-accent);
  color: var(--cb-accent-ink);
  font-size: 12.5px;
}
.cb-summary-coupon svg {
  flex: none;
  width: 15px;
  height: 15px;
}
.cb-summary-coupon span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cb-summary-coupon button {
  flex: none;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: 50%;
  background: var(--cb-card);
  color: var(--cb-ink);
  font-size: 15px;
  line-height: 1;
}
.cb-summary-total {
  grid-area: total;
  min-width: 0;
}
.cb-summary-total small {
  display: block;
  color: var(--cb-muted);
  font-size: 11.5px;
  font-weight: 600;
}
.cb-summary-price {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 2px 6px;
}
.cb-summary-total small s {
  margin-left: 4px;
  font-weight: 500;
}
.cb-summary-price strong {
  font-family: var(--font-display, inherit);
  font-size: 20px;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  white-space: nowrap;
}
.cb-summary-price span {
  color: var(--cb-muted);
  font-size: 12.5px;
  font-weight: 600;
}
.cb-summary-note {
  grid-area: note;
  margin: 0;
  color: var(--cb-muted);
  font-size: 12px;
  line-height: 1.35;
}
.cb-bar-cta {
  grid-area: cta;
  min-width: 132px;
  height: 50px;
  padding: 0 18px;
  white-space: nowrap;
}

/* No celular o botão da etapa fica só na barra fixa. */
@media (max-width: 1023px) {
  .cb-shell #checkout-details-form > .checkout-primary,
  .cb-shell #checkout-card-form > .checkout-primary {
    display: none;
  }
}

@media (min-width: 768px) {
  .cb-page {
    padding: 24px 24px calc(132px + env(safe-area-inset-bottom));
  }
  .cb-main {
    gap: 16px;
  }
  .cb-banner img {
    aspect-ratio: 16 / 5;
    border-radius: 22px;
  }
  .cb-head {
    padding: 22px 24px;
  }
  .cb-head-title {
    font-size: 26px;
  }
  .cb-stage {
    padding: 26px 26px 28px;
  }
  .cb-stage .checkout-title {
    font-size: 23px;
  }
}

/* Computador: conteúdo à esquerda e o resumo do pedido fixo à direita. */
@media (min-width: 1024px) {
  .cb-page {
    padding-bottom: 40px;
  }
  .cb-main {
    display: grid;
    grid-template-areas:
      "banner banner"
      "head summary"
      "steps summary"
      "stage summary"
      "protected summary";
    grid-template-columns: minmax(0, 1fr) 340px;
    align-items: start;
    gap: 18px 24px;
  }
  .cb-banner {
    grid-area: banner;
  }
  .cb-head {
    grid-area: head;
  }
  .cb-steps {
    grid-area: steps;
  }
  .cb-stage {
    grid-area: stage;
  }
  .cb-main .checkout-protected-footer {
    grid-area: protected;
    justify-content: flex-start;
  }
  .cb-summary {
    position: sticky;
    top: 24px;
    grid-area: summary;
    grid-row: 2 / span 4;
    align-self: start;
    padding: 0;
    border: 0;
    background: none;
    box-shadow: none;
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
  }
  .cb-summary-card,
  .cb-summary-card.has-cta {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
    max-width: none;
    padding: 22px;
    border-radius: 22px;
    background: var(--cb-card);
    box-shadow: var(--cb-shadow);
  }
  .cb-summary-title {
    display: block;
    margin: 0;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--cb-border);
    font-size: 15px;
    font-weight: 700;
  }
  .cb-summary-item {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    font-size: 14px;
  }
  .cb-summary-item span:last-child {
    color: var(--cb-muted);
  }
  .cb-summary-total {
    padding-top: 12px;
    border-top: 1px solid var(--cb-border);
  }
  .cb-summary-price strong {
    font-size: 26px;
  }
  .cb-summary-note {
    margin-top: -8px;
  }
  .cb-bar-cta {
    display: none;
  }
  .cb-summary-guarantee {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    margin: 0;
    color: var(--cb-muted);
    font-size: 12.5px;
    line-height: 1.4;
  }
  .cb-summary-guarantee svg {
    flex: none;
    width: 15px;
    height: 15px;
    margin-top: 1px;
    color: var(--cb-accent-ink);
  }
}
</style>
