<template>
  <teleport to="body">
    <transition name="checkout-fade">
        <div v-if="visible" class="checkout-overlay" @click.self="handleClose">
          <div class="checkout-modal">
          <button type="button" class="checkout-close" @click="handleClose" aria-label="Fechar checkout">
            <span aria-hidden="true">+</span>
          </button>
          <transition name="pix-toast-fade">
            <div v-if="copyToastVisible" class="pix-toast">{{ copyToastMessage }}</div>
          </transition>

          <div v-if="!hasCart" class="checkout-empty">
            <p class="checkout-empty__eyebrow">Checkout</p>
            <h2 class="checkout-empty__title">Selecione um produto para continuar</h2>
            <p class="checkout-empty__text">
              O resumo da compra aparece aqui assim que o cliente escolher os itens na secao de produtos.
            </p>
          </div>

          <div v-else class="checkout-layout">
            <header class="checkout-topbar">
              <div class="checkout-topbar__side">
                <div>
                  <p class="checkout-topbar__title">Checkout seguro</p>
                  <p class="checkout-topbar__text">Seus dados estao protegidos</p>
                </div>
              </div>
              <div class="checkout-topbar__side checkout-topbar__side--end">
                <p class="checkout-topbar__text">Ambiente 100% seguro</p>
              </div>
            </header>

            <section class="checkout-main">
              <div class="checkout-section">
                <div class="checkout-section__head">
                  <div class="checkout-section__title-wrap">
                    <span class="checkout-step">1</span>
                    <div>
                      <h3 class="checkout-section__title">Dados do comprador</h3>
                      <p class="checkout-section__hint">Preencha seus dados para continuar</p>
                    </div>
                  </div>
                </div>

                <div class="checkout-form-grid">
                  <label class="field field--full">
                    <span class="field__label">Nome completo</span>
                    <input
                      v-model="customer.name"
                      type="text"
                      autocomplete="name"
                      class="field__control"
                      placeholder="Digite seu nome completo"
                    />
                  </label>

                  <label class="field">
                    <span class="field__label">E-mail</span>
                    <input
                      v-model="customer.email"
                      type="email"
                      autocomplete="email"
                      class="field__control"
                      placeholder="seu@email.com"
                    />
                  </label>

                  <label class="field">
                    <span class="field__label">Telefone / WhatsApp</span>
                    <input
                      :value="customer.phone_number"
                      type="tel"
                      autocomplete="tel"
                      class="field__control"
                      placeholder="(11) 99999-0000"
                      @input="onPhoneInput"
                    />
                  </label>

                  <label class="field">
                    <span class="field__label">Nacionalidade</span>
                    <select v-model="customer.nationality" class="field__control field__control--select">
                      <option v-for="option in nationalityOptions" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                  </label>

                  <label class="field">
                    <span class="field__label">CPF</span>
                    <input
                      :value="customer.passport"
                      type="text"
                      inputmode="numeric"
                      class="field__control"
                      placeholder="000.000.000-00"
                      @input="onPassportInput"
                    />
                  </label>
                </div>
              </div>

              <div class="checkout-section">
                <template v-if="pixActiveMode">
                  <div class="pix-active">
                    <div class="pix-active__timer-row">
                      <div class="pix-active__timer-copy">
                        <p class="pix-active__timer-label">PEDIDO RESERVADO</p>
                        <p class="pix-active__timer-note">Conclua o pagamento antes do tempo acabar.</p>
                      </div>
                      <span class="pix-active__timer-pill" :class="pixTimerToneClass">{{ pixReservationTime }}</span>
                    </div>

                    <div class="pix-active__hero">
                      <h3 class="pix-active__title">Finalize seu pagamento via PIX</h3>
                      <p class="pix-active__subtitle">Apos o pagamento, a confirmacao sera automatica.</p>
                    </div>

                    <div class="pix-active__qr-wrap" ref="pixQrContainerRef">
                      <img v-if="pixQrImageUrl" :src="pixQrImageUrl" alt="QR Code Pix" class="pix-active__qr" />
                      <p class="pix-active__qr-note">Escaneie com o aplicativo do seu banco</p>
                    </div>

                    <div class="pix-active__copy-row">
                      <div class="pix-active__copy-field">
                        <span class="pix-active__copy-icon">PIX</span>
                        <input class="pix-active__copy-input" readonly :value="pixCopyPasteCode || 'Gerando codigo PIX...'" />
                      </div>
                      <button
                        type="button"
                        class="pix-active__copy-btn"
                        :disabled="!pixCopyPasteCode"
                        @click="copyPixCode"
                      >
                        {{ pixCopyButtonLabel }}
                      </button>
                    </div>

                    <div class="pix-active__status" :class="pixStatusToneClass">
                      <p class="pix-active__status-title">{{ pixStatusTitle }}</p>
                      <p class="pix-active__status-text">{{ pixStatusDescription }}</p>
                    </div>

                    <div class="pix-active__summary">
                      <p class="pix-active__summary-title">RESUMO DO PEDIDO</p>
                      <p class="pix-active__summary-product">{{ groupedSummaryTitle }}</p>
                      <p class="pix-active__summary-meta">{{ totalPassengerCount }} {{ totalPassengerCount === 1 ? "passageiro" : "passageiros" }}</p>
                      <p class="pix-active__summary-total-label">Total a pagar</p>
                      <p class="pix-active__summary-total">{{ formatCurrency(displayTotalAmount, currencyCode) }}</p>
                    </div>

                    <p class="pix-active__security-note">
                      <svg viewBox="0 0 24 24" fill="none" class="pix-active__security-icon" aria-hidden="true">
                        <path d="M8 10V7a4 4 0 1 1 8 0v3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                        <rect x="5" y="10" width="14" height="10" rx="2.6" stroke="currentColor" stroke-width="1.8" />
                      </svg>
                      Pagamento processado em ambiente seguro
                    </p>
                  </div>
                </template>
                <template v-else-if="boletoActiveMode">
                  <div class="boleto-active" ref="boletoContainerRef">
                    <div class="boleto-active__header">
                      <div class="boleto-active__header-copy">
                        <h3 class="boleto-active__title">Boleto gerado com sucesso</h3>
                        <p class="boleto-active__subtitle">Pague ate a data de vencimento para confirmar sua compra.</p>
                      </div>
                      <span v-if="boletoDueBadgeText" class="boleto-active__due-badge">{{ boletoDueBadgeText }}</span>
                    </div>

                    <div class="boleto-active__hero">
                      <div class="boleto-active__icon-wrap" aria-hidden="true">
                        <svg viewBox="0 0 64 64" fill="none" class="boleto-active__icon">
                          <rect x="12" y="8" width="40" height="48" rx="8" stroke="currentColor" stroke-width="2.5" />
                          <rect x="18" y="18" width="28" height="6" rx="3" fill="currentColor" />
                          <rect x="18" y="30" width="5" height="18" rx="1.5" fill="currentColor" />
                          <rect x="26" y="30" width="5" height="18" rx="1.5" fill="currentColor" />
                          <rect x="34" y="30" width="5" height="18" rx="1.5" fill="currentColor" />
                          <rect x="42" y="30" width="3" height="18" rx="1.5" fill="currentColor" />
                        </svg>
                      </div>
                      <p class="boleto-active__amount">Valor total: {{ formatCurrency(displayTotalAmount, currencyCode) }}</p>
                      <p class="boleto-active__due">Vencimento: {{ boletoDueDateText }}</p>
                    </div>

                    <div class="boleto-active__line-wrap">
                      <p class="boleto-active__line-label">Linha digitavel</p>
                      <div class="boleto-active__line-row">
                        <div class="boleto-active__line-field">
                          <span class="boleto-active__line-badge">BOLETO</span>
                          <input class="boleto-active__line-input" readonly :value="boletoLineCode || 'Linha digitavel indisponivel no momento'" />
                        </div>
                        <button
                          type="button"
                          class="boleto-active__copy-btn"
                          :disabled="!boletoLineCode"
                          @click="copyBoletoCode"
                        >
                          {{ boletoCopyButtonLabel }}
                        </button>
                      </div>
                    </div>

                    <a
                      v-if="boletoPaymentUrl"
                      :href="boletoPaymentUrl"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="boleto-active__download-btn"
                      @click="onBoletoDownload"
                    >
                      {{ boletoDownloadButtonLabel }}
                    </a>

                    <div class="boleto-active__status" :class="boletoStatusToneClass">
                      <p class="boleto-active__status-title">{{ boletoStatusTitle }}</p>
                      <p class="boleto-active__status-text">{{ boletoStatusDescription }}</p>
                    </div>
                  </div>
                </template>

                <template v-else>
                <div class="checkout-section__head">
                  <div class="checkout-section__title-wrap">
                    <span class="checkout-step">2</span>
                    <div>
                      <h3 class="checkout-section__title">Forma de pagamento</h3>
                      <p class="checkout-section__hint">Escolha como deseja pagar</p>
                    </div>
                  </div>
                </div>

                <div class="payment-tabs" role="tablist" aria-label="Formas de pagamento">
                  <button
                    v-for="method in allowedMethods"
                    :key="method"
                    type="button"
                    class="payment-tab"
                    :class="{ 'payment-tab--active': selectedMethod === method }"
                    @click="selectedMethod = method"
                  >
                    <span class="payment-tab__icon">
                      <img
                        v-if="method === 'pix'"
                        src="../../assets/simbolopix.png"
                        alt="Pix"
                        class="payment-tab__icon-image"
                      />
                      <img
                        v-else-if="method === 'credit_card'"
                        src="../../assets/cartao.png"
                        alt="Cartao"
                        class="payment-tab__icon-image"
                      />
                      <img
                        v-else-if="method === 'boleto'"
                        src="../../assets/boleto.png"
                        alt="Boleto"
                        class="payment-tab__icon-image payment-tab__icon-image--boleto"
                      />
                      <template v-else>{{ paymentMeta[method].icon }}</template>
                    </span>
                    <span class="payment-tab__copy">
                      <span class="payment-tab__title">{{ paymentMeta[method].label }}</span>
                      <span class="payment-tab__text">{{ paymentMeta[method].summary }}</span>
                    </span>
                  </button>
                </div>

                <div v-if="selectedMethod === 'credit_card'" class="payment-card-shell">
                  <div class="payment-card-previews">
                    <div class="payment-card-preview payment-card-preview--front">
                      <div class="payment-card-preview__top">
                        <span class="payment-card-preview__chip"></span>
                        <span class="payment-card-preview__brand">VISA</span>
                      </div>
                      <p class="payment-card-preview__number">{{ maskedPreviewNumber }}</p>
                      <div class="payment-card-preview__bottom">
                        <div>
                          <span class="payment-card-preview__label">Nome do titular</span>
                          <p>{{ card.holder_name || "Como esta impresso no cartao" }}</p>
                        </div>
                        <div>
                          <span class="payment-card-preview__label">Validade</span>
                          <p>{{ cardExpiryPreview }}</p>
                        </div>
                      </div>
                    </div>

                    <div class="payment-card-preview payment-card-preview--back">
                      <div class="payment-card-preview__magstripe"></div>
                      <div class="payment-card-preview__signature-line">
                        <span class="payment-card-preview__cvv-label">CVV</span>
                        <span class="payment-card-preview__cvv-value">{{ cardCvvPreview }}</span>
                      </div>
                      <div class="payment-card-preview__back-note">
                        Codigo de seguranca
                      </div>
                    </div>
                  </div>

                  <div class="checkout-form-grid checkout-form-grid--card">
                    <label class="field field--full">
                      <span class="field__label">Nome no cartao</span>
                      <input
                        v-model="card.holder_name"
                        type="text"
                        autocomplete="cc-name"
                        class="field__control"
                        placeholder="Como esta impresso no cartao"
                      />
                    </label>

                    <label class="field field--full">
                      <span class="field__label">Numero do cartao</span>
                      <input
                        :value="card.number"
                        type="text"
                        inputmode="numeric"
                        autocomplete="cc-number"
                        class="field__control field__control--mono"
                        placeholder="0000 0000 0000 0000"
                        @input="onCardNumberInput"
                      />
                    </label>

                    <label class="field">
                      <span class="field__label">Mes</span>
                      <select v-model="card.exp_month" class="field__control field__control--select">
                        <option value="">MM</option>
                        <option v-for="month in monthOptions" :key="month" :value="month">{{ month }}</option>
                      </select>
                    </label>

                    <label class="field">
                      <span class="field__label">Ano</span>
                      <select v-model="card.exp_year" class="field__control field__control--select">
                        <option value="">AAAA</option>
                        <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
                      </select>
                    </label>

                    <label class="field">
                      <span class="field__label">CVV</span>
                      <input
                        :value="card.cvv"
                        type="text"
                        inputmode="numeric"
                        autocomplete="cc-csc"
                        class="field__control field__control--mono"
                        placeholder="123"
                        @input="onCvvInput"
                      />
                    </label>

                    <label class="field">
                      <span class="field__label">Parcelas</span>
                      <select
                        v-model.number="card.installments"
                        class="field__control field__control--select"
                        :disabled="installmentSelectDisabled"
                      >
                        <option v-for="option in installmentOptions" :key="option.value" :value="option.value">
                          {{ option.label }}
                        </option>
                      </select>
                      <span v-if="pricingLoading" class="field__hint">Consultando parcelas da Blimboo...</span>
                      <span v-else-if="pricingError" class="field__hint field__hint--error">{{ pricingError }}</span>
                    </label>
                  </div>
                </div>

                <div v-else-if="selectedMethod === 'pix'" class="payment-info payment-info--pix">
                  <div class="payment-info__body">
                    <div class="payment-info__art payment-info__art--pix">
                      <img src="../../assets/pix.png" alt="Pix" class="payment-info__art-image" />
                    </div>
                    <div>
                      <p class="payment-info__title">Pague com PIX e confirme na hora</p>
                      <ul class="payment-benefits">
                        <li>Pagamento aprovado em segundos</li>
                        <li>Voce recebe o acesso imediatamente</li>
                        <li>Mais rapido, pratico e seguro</li>
                        <li>A vista com 5% de desconto</li>
                      </ul>
                      <div class="payment-note">
                        Apos finalizar o pedido, voce vera o QR Code ou o codigo PIX para pagamento.
                      </div>
                      <div v-if="pixQrImageUrl || pixCopyPasteCode" class="payment-dynamic">
                        <img v-if="pixQrImageUrl" :src="pixQrImageUrl" alt="QR Code Pix" class="payment-dynamic__qr" />
                        <label v-if="pixCopyPasteCode" class="field field--full">
                          <span class="field__label">Codigo PIX copia e cola</span>
                          <textarea class="field__control field__control--mono payment-dynamic__code" readonly :value="pixCopyPasteCode"></textarea>
                        </label>
                        <button v-if="pixCopyPasteCode" type="button" class="summary-cta payment-dynamic__copy" @click="copyPixCode">
                          Copiar codigo PIX
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-else class="payment-info payment-info--boleto">
                  <div class="payment-info__body">
                    <div class="payment-info__art payment-info__art--boleto"></div>
                    <div>
                      <p class="payment-info__title">Pague com boleto e quite em ate 1 dia util</p>
                      <ul class="payment-benefits">
                        <li>Vencimento em ate 1 dia util apos a emissao</li>
                        <li>Pagamento a vista</li>
                        <li>Aprovacao em ate 1 dia util apos o pagamento</li>
                        <li>Seguro, confiavel e amplamente aceito</li>
                      </ul>
                      <div class="payment-note">
                        Apos finalizar o pedido, voce vera o codigo do boleto para pagamento.
                      </div>
                      <div v-if="boletoLineCode" class="payment-dynamic">
                        <label class="field field--full">
                          <span class="field__label">Linha digitavel</span>
                          <textarea class="field__control field__control--mono payment-dynamic__code" readonly :value="boletoLineCode"></textarea>
                        </label>
                      </div>
                      <div v-if="boletoPaymentUrl" class="payment-dynamic">
                        <a
                          :href="boletoPaymentUrl"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="summary-cta payment-dynamic__copy"
                        >
                          Abrir boleto
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
                </template>
              </div>

              <div v-if="!pixActiveMode" class="checkout-footer-trust">
                <article class="footer-trust-item">
                  <span class="footer-trust-item__icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" class="footer-trust-item__icon-svg">
                      <path d="M12 3 5 6v5c0 5 3.4 8.3 7 10 3.6-1.7 7-5 7-10V6l-7-3Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                      <path d="m9.5 12 1.7 1.7L14.8 10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </span>
                  <div>
                    <p class="footer-trust-item__title">Compra segura</p>
                    <p class="footer-trust-item__text">Seus dados protegidos</p>
                  </div>
                </article>
                <article class="footer-trust-item">
                  <span class="footer-trust-item__icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" class="footer-trust-item__icon-svg">
                      <rect x="3" y="6" width="18" height="12" rx="2.5" stroke="currentColor" stroke-width="1.8" />
                      <path d="M3 10.5h18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                      <path d="M7 15h3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                    </svg>
                  </span>
                  <div>
                    <p class="footer-trust-item__title">Pagamento protegido</p>
                    <p class="footer-trust-item__text">Ambiente 100% seguro</p>
                  </div>
                </article>
                <article class="footer-trust-item">
                  <span class="footer-trust-item__icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" class="footer-trust-item__icon-svg">
                      <path d="M4 12a8 8 0 0 1 16 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                      <rect x="3" y="11" width="4" height="7" rx="2" stroke="currentColor" stroke-width="1.8" />
                      <rect x="17" y="11" width="4" height="7" rx="2" stroke="currentColor" stroke-width="1.8" />
                      <path d="M12 19v2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                    </svg>
                  </span>
                  <div>
                    <p class="footer-trust-item__title">Suporte especializado</p>
                    <p class="footer-trust-item__text">Atendimento humanizado</p>
                  </div>
                </article>
              </div>
            </section>

            <aside v-if="!pixActiveMode" class="checkout-summary">
              <div class="summary-card">
                <div class="summary-card__head">
                  <div>
                    <h3 class="summary-card__title">Resumo do pedido</h3>
                  </div>
                </div>

                <div v-if="showGroupedSummary" class="summary-product-group">
                  <div class="summary-product-group__header">
                    <div class="summary-item__media" :style="summaryThumbStyle(0)">
                      <img
                        v-if="groupedSummaryImageUrl"
                        :src="groupedSummaryImageUrl"
                        :alt="groupedSummaryTitle"
                        class="summary-item__media-image"
                      />
                      <span v-else>{{ groupedSummaryTitle.slice(0, 1) }}</span>
                    </div>
                    <div class="summary-product-group__copy">
                      <p class="summary-product-group__title">{{ groupedSummaryTitle }}</p>
                    </div>
                  </div>

                  <div class="summary-items summary-items--grouped">
                    <article
                      v-for="(item, index) in cartItems"
                      :key="`${item.productId}-${item.variationId}`"
                      class="summary-item summary-item--package"
                    >
                      <div class="summary-item__copy">
                        <p class="summary-item__title">{{ sanitizeText(item.name) }}</p>
                        <p v-if="item.departureLabel || item.dateLabel" class="summary-item__schedule">
                          {{ [item.dateLabel, item.departureLabel].filter(Boolean).join(" • ") }}
                        </p>
                        <p class="summary-item__meta">
                          {{ item.quantity }} {{ item.quantity === 1 ? "unidade" : "unidades" }}
                          <span>|</span>
                          {{ item.peopleCount }} {{ item.peopleCount === 1 ? "passageiro" : "passageiros" }}
                        </p>
                      </div>
                      <p class="summary-item__amount">
                        {{ formatCurrency(item.unitAmount * item.quantity + item.childExtraAmount, item.currency) }}
                      </p>
                    </article>
                  </div>
                </div>

                <div v-else class="summary-items">
                  <article
                    v-for="(item, index) in cartItems"
                    :key="`${item.productId}-${item.variationId}`"
                    class="summary-item"
                  >
                    <div class="summary-item__media" :style="summaryThumbStyle(index)">
                      <img
                        v-if="getSummaryItemImageUrl(item.productImageUrl)"
                        :src="getSummaryItemImageUrl(item.productImageUrl)!"
                        :alt="sanitizeText(item.productName)"
                        class="summary-item__media-image"
                      />
                      <span v-else>{{ item.productName.slice(0, 1) }}</span>
                    </div>
                    <div class="summary-item__copy">
                      <p class="summary-item__title">{{ sanitizeText(item.productName) }}</p>
                      <p class="summary-item__variant">{{ sanitizeText(item.name) }}</p>
                      <p v-if="item.departureLabel || item.dateLabel" class="summary-item__schedule">
                        {{ [item.dateLabel, item.departureLabel].filter(Boolean).join(" • ") }}
                      </p>
                      <p class="summary-item__meta">
                        {{ item.quantity }} {{ item.quantity === 1 ? "unidade" : "unidades" }}
                        <span>|</span>
                        {{ item.peopleCount }} {{ item.peopleCount === 1 ? "passageiro" : "passageiros" }}
                      </p>
                    </div>
                    <p class="summary-item__amount">
                      {{ formatCurrency(item.unitAmount * item.quantity + item.childExtraAmount, item.currency) }}
                    </p>
                  </article>
                </div>

                <div v-if="discountAmount > 0" class="summary-row summary-row--discount">
                  <span>{{ discountLabel }}</span>
                  <strong>- {{ formatCurrency(discountAmount, currencyCode) }}</strong>
                </div>

                <div class="summary-row">
                  <span>Subtotal</span>
                  <strong>{{ formatCurrency(subtotalAmount, currencyCode) }}</strong>
                </div>
                <div class="summary-total">
                  <div>
                    <span class="summary-total__label">Total</span>
                    <p class="summary-total__caption">Valor final</p>
                  </div>
                  <strong class="summary-total__value">{{ formatCurrency(displayTotalAmount, currencyCode) }}</strong>
                </div>

                <div class="trust-banner">
                  <span class="trust-banner__icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" class="trust-banner__icon-svg">
                      <path d="M12 3 5 6v5c0 5 3.4 8.3 7 10 3.6-1.7 7-5 7-10V6l-7-3Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                      <path d="m9.5 12 1.7 1.7L14.8 10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </span>
                  <div>
                    <p class="trust-banner__title">Ambiente 100% seguro</p>
                    <p class="trust-banner__text">Seus dados protegidos com criptografia de ponta.</p>
                  </div>
                </div>

                <button
                  type="button"
                  class="summary-cta"
                  :class="{ 'summary-cta--awaiting': isAwaitingPayment }"
                  :disabled="isSubmitButtonDisabled"
                  @click="handleSubmit"
                >
                  {{ submitButtonLabel }}
                </button>
                <p class="summary-note">
                  Voce podera revisar todos os dados antes de confirmar
                </p>
                <p v-if="validationMessage" class="summary-error">{{ validationMessage }}</p>
                <p v-else-if="successMessage" class="summary-success">{{ successMessage }}</p>
              </div>
            </aside>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onUnmounted, reactive, ref, watch } from "vue";
import type { ProductCheckoutPayload } from "../../utils/checkoutKeys";
import type {
  CheckoutCartItem,
  PaymentInstallmentOption,
  PaymentPricingResponse,
  PublicCheckoutResponse,
  SectionProductsCheckoutRequest,
  SectionProductsPricingRequest,
} from "../../types/finance";
import {
  confirmPublicSale,
  createProductPublicCheckoutIntent,
  createSectionProductsPublicCheckoutIntent,
  getPublicSaleStatus,
  getSectionProductsPublicPricing,
} from "../../services/finance";
import { resolveMediaUrl } from "../../utils/media";

type PaymentMethod = "pix" | "credit_card" | "boleto";

const props = defineProps<{
  modelValue: boolean;
  pageId: number | null;
  pageSlug?: string | null;
  agencySlug?: string | null;
  pageUrl?: string | null;
  checkoutData: ProductCheckoutPayload | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "payment-succeeded", payload: { passengerToken: string | null; saleId: number }): void;
}>();

const visible = computed(() => props.modelValue);
const customer = reactive({
  name: "",
  email: "",
  phone_number: "",
  nationality: "BR",
  passport: "",
});
const card = reactive({
  holder_name: "",
  number: "",
  exp_month: "",
  exp_year: "",
  cvv: "",
  installments: 1,
});
const selectedMethod = ref<PaymentMethod>("pix");
const validationMessage = ref("");
const successMessage = ref("");
const confirming = ref(false);
const pollingStatus = ref(false);
const checkoutResult = ref<PublicCheckoutResponse | null>(null);
const pixGeneratedAtMs = ref<number | null>(null);
const pixQrContainerRef = ref<HTMLElement | null>(null);
const boletoContainerRef = ref<HTMLElement | null>(null);
const copyToastVisible = ref(false);
const copyToastMessage = ref("Codigo copiado com sucesso");
const pixCopyRecentlyCopied = ref(false);
const boletoCopyRecentlyCopied = ref(false);
const boletoDownloadBusy = ref(false);
const nowMs = ref(Date.now());
const pricingLoading = ref(false);
const pricingError = ref<string | null>(null);
const pricingOptions = ref<PaymentInstallmentOption[]>([]);
let statusPollTimer: ReturnType<typeof setTimeout> | null = null;
let pixClockTimer: ReturnType<typeof setInterval> | null = null;
let pixCopyResetTimer: ReturnType<typeof setTimeout> | null = null;
let boletoCopyResetTimer: ReturnType<typeof setTimeout> | null = null;
let copyToastTimer: ReturnType<typeof setTimeout> | null = null;
let paidRedirectTimer: ReturnType<typeof setTimeout> | null = null;
let boletoDownloadResetTimer: ReturnType<typeof setTimeout> | null = null;
let statusPollRun = 0;
const MAX_STATUS_POLL_RUNS = 40;
const PIX_RESERVATION_SECONDS = 15 * 60;

const paymentMeta: Record<PaymentMethod, { label: string; summary: string; icon: string }> = {
  pix: {
    label: "PIX",
    summary: "Pagamento instantaneo",
    icon: "PIX",
  },
  boleto: {
    label: "BOLETO",
    summary: "Vencimento em 1 dia util",
    icon: "BOL",
  },
  credit_card: {
    label: "CARTAO",
    summary: "Parcelamento seguro",
    icon: "",
  },
};
const nationalityOptions = [
  { value: "BR", label: "Brasil" },
  { value: "AR", label: "Argentina" },
  { value: "PY", label: "Paraguai" },
  { value: "UY", label: "Uruguai" },
  { value: "US", label: "Estados Unidos" },
];
const monthOptions = Array.from({ length: 12 }, (_, index) => String(index + 1).padStart(2, "0"));
const yearOptions = Array.from({ length: 12 }, (_, index) => String(new Date().getFullYear() + index));

const cartItems = computed(() => props.checkoutData?.items ?? []);
const hasCart = computed(() => cartItems.value.length > 0);
const currencyCode = computed(() => props.checkoutData?.currency || "BRL");
const subtotalAmount = computed(() => props.checkoutData?.subtotalAmount ?? props.checkoutData?.totalAmount ?? 0);
const totalAmount = computed(() => props.checkoutData?.totalAmount ?? 0);
const discountAmount = computed(() => props.checkoutData?.discountAmount ?? 0);
const discountLabel = computed(() => props.checkoutData?.discountLabel || "Desconto aplicado");
const allowedMethods = computed<PaymentMethod[]>(() => {
  const raw = props.checkoutData?.allowedPaymentMethods || ["pix", "credit_card", "boleto"];
  const filtered = raw.filter((item): item is PaymentMethod => item === "pix" || item === "credit_card" || item === "boleto");
  return filtered.length ? filtered : ["pix", "credit_card", "boleto"];
});
const uniqueProductIds = computed(() => Array.from(new Set(cartItems.value.map(item => item.productId))));
const showGroupedSummary = computed(() => uniqueProductIds.value.length === 1 && cartItems.value.length > 0);
const groupedSummaryTitle = computed(
  () => sanitizeText(props.checkoutData?.productName || cartItems.value[0]?.productName || "Produto"),
);
const groupedSummaryImageUrl = computed(() => getSummaryItemImageUrl(cartItems.value[0]?.productImageUrl));
const totalPassengerCount = computed(() => cartItems.value.reduce((total, item) => total + (item.peopleCount || 0), 0));
const maxInstallments = computed(() => Math.max(1, Math.min(props.checkoutData?.installments || 12, 12)));
const pricingRequestAvailable = computed(() => Boolean(props.pageId && props.checkoutData?.sectionId && cartItems.value.length));
const formatInstallmentLabel = (option: PaymentInstallmentOption) => {
  const suffix = option.has_interest ? " com juros" : " sem juros";
  return `${option.installments}x de ${formatCurrency(option.installment_amount_cents, currencyCode.value)}${suffix}`;
};
const fallbackInstallmentOptions = computed(() =>
  Array.from({ length: maxInstallments.value }, (_, index) => {
    const value = index + 1;
    return {
      value,
      label: `${value}x de ${formatCurrency(Math.round(totalAmount.value / value), currencyCode.value)}`,
    };
  }),
);
const installmentOptions = computed(() => {
  if (selectedMethod.value === "credit_card" && pricingRequestAvailable.value) {
    if (pricingOptions.value.length) {
      return pricingOptions.value.map(option => ({
        value: option.installments,
        label: formatInstallmentLabel(option),
      }));
    }
    if (pricingLoading.value) {
      return [{ value: card.installments || 1, label: "Consultando parcelas..." }];
    }
    if (pricingError.value) {
      return [{ value: card.installments || 1, label: "Parcelas indisponiveis" }];
    }
    return [];
  }

  if (pricingOptions.value.length) {
    return pricingOptions.value.map(option => ({
      value: option.installments,
      label: formatInstallmentLabel(option),
    }));
  }
  return fallbackInstallmentOptions.value;
});
const installmentSelectDisabled = computed(
  () =>
    selectedMethod.value === "credit_card" &&
    pricingRequestAvailable.value &&
    (pricingLoading.value || (!!pricingError.value && !pricingOptions.value.length)),
);
const normalizedProviderStatus = computed(() => {
  const raw = String(checkoutResult.value?.provider_status || "").trim().toLowerCase();
  if (!raw) return "";
  return raw;
});
const isAwaitingPayment = computed(() => {
  const status = normalizedProviderStatus.value;
  if (!status) return false;
  if (status === "paid") return false;
  if (status === "canceled" || status === "cancelled" || status === "expired" || status === "refunded") return false;
  return [
    "pending",
    "processing",
    "awaiting_payment",
    "waiting_payment",
    "pending_payment",
    "unpaid",
    "in_process",
    "0",
    "1",
  ].includes(status);
});
const isPaymentApproved = computed(() => normalizedProviderStatus.value === "paid");
const submitButtonLabel = computed(() => {
  if (confirming.value) return "Processando...";
  if (isPaymentApproved.value) return "Pagamento aprovado";
  if (isAwaitingPayment.value) return "⏳ Aguardando pagamento";
  return "Finalizar pedido";
});
const isSubmitButtonDisabled = computed(() => {
  if (confirming.value) return true;
  if (isPaymentApproved.value) return true;
  if (isAwaitingPayment.value) return true;
  return !isFormValid.value;
});
const selectedPricingOption = computed<PaymentInstallmentOption | null>(() => {
  const match = pricingOptions.value.find(option => option.installments === card.installments);
  return match || pricingOptions.value[0] || null;
});
const displayTotalAmount = computed(() => {
  if (selectedMethod.value === "credit_card" && selectedPricingOption.value) {
    return selectedPricingOption.value.total_amount_cents;
  }
  return totalAmount.value;
});
const maskedPreviewNumber = computed(() => {
  const digits = card.number.replace(/\D/g, "");
  if (!digits) return "0000 0000 0000 0000";
  return digits.padEnd(16, "*").slice(0, 16).replace(/(.{4})/g, "$1 ").trim();
});
const cardExpiryPreview = computed(() => {
  const month = card.exp_month || "MM";
  const year = card.exp_year ? card.exp_year.slice(-2) : "AA";
  return `${month}/${year}`;
});
const cardCvvPreview = computed(() => {
  const digits = card.cvv.replace(/\D/g, "").slice(0, 4);
  if (!digits) return "***";
  return digits.padEnd(3, "*");
});
const isFormValid = computed(() => {
  const buyerValid = Boolean(
    customer.name.trim() &&
      customer.email.trim() &&
      customer.phone_number.trim() &&
      customer.nationality.trim() &&
      customer.passport.trim(),
  );
  if (!buyerValid) return false;
  if (selectedMethod.value !== "credit_card") return true;
  return Boolean(
    card.holder_name.trim() &&
      card.number.trim() &&
      card.exp_month.trim() &&
      card.exp_year.trim() &&
      card.cvv.trim(),
  );
});

const resetState = () => {
  customer.name = "";
  customer.email = "";
  customer.phone_number = "";
  customer.nationality = "BR";
  customer.passport = "";
  card.holder_name = "";
  card.number = "";
  card.exp_month = "";
  card.exp_year = "";
  card.cvv = "";
  card.installments = 1;
  selectedMethod.value = allowedMethods.value.includes("pix") ? "pix" : allowedMethods.value[0] || "credit_card";
  validationMessage.value = "";
  successMessage.value = "";
  checkoutResult.value = null;
  pixGeneratedAtMs.value = null;
  copyToastVisible.value = false;
  pixCopyRecentlyCopied.value = false;
  boletoCopyRecentlyCopied.value = false;
  boletoDownloadBusy.value = false;
  confirming.value = false;
  pollingStatus.value = false;
  if (statusPollTimer) {
    clearTimeout(statusPollTimer);
    statusPollTimer = null;
  }
  if (paidRedirectTimer) {
    clearTimeout(paidRedirectTimer);
    paidRedirectTimer = null;
  }
  if (pixCopyResetTimer) {
    clearTimeout(pixCopyResetTimer);
    pixCopyResetTimer = null;
  }
  if (boletoCopyResetTimer) {
    clearTimeout(boletoCopyResetTimer);
    boletoCopyResetTimer = null;
  }
  if (copyToastTimer) {
    clearTimeout(copyToastTimer);
    copyToastTimer = null;
  }
  if (boletoDownloadResetTimer) {
    clearTimeout(boletoDownloadResetTimer);
    boletoDownloadResetTimer = null;
  }
  statusPollRun = 0;
  pricingLoading.value = false;
  pricingError.value = null;
  pricingOptions.value = [];
};

const handleClose = () => {
  emit("update:modelValue", false);
  resetState();
};

const sanitizeText = (value: string) =>
  String(value || "")
    .replace(/\uFFFD/g, "")
    .replace(/&[a-zA-Z]+;/g, " ")
    .replace(/\s+/g, " ")
    .trim();

const formatCurrency = (amountCents: number, currency = "BRL") => {
  const value = (amountCents || 0) / 100;
  try {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(value);
  } catch {
    return `R$ ${value.toFixed(2)}`;
  }
};

const parsePricingAmountToCents = (value: number | string | null | undefined): number | null => {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number" && Number.isFinite(value)) {
    return Math.round(value * 100);
  }
  const normalized = String(value).trim().replace(/\s+/g, "");
  if (!normalized) return null;
  const dotCount = (normalized.match(/\./g) || []).length;
  const commaCount = (normalized.match(/,/g) || []).length;
  let decimalText = normalized;
  if (commaCount > 0 && dotCount > 0) {
    decimalText = normalized.replace(/\./g, "").replace(",", ".");
  } else if (commaCount > 0) {
    decimalText = normalized.replace(",", ".");
  }
  const numeric = Number(decimalText);
  if (!Number.isFinite(numeric)) return null;
  return Math.round(numeric * 100);
};

const normalizePricingOptions = (
  response: PaymentPricingResponse | null | undefined,
  fallbackBaseAmountCents: number,
): PaymentInstallmentOption[] => {
  if (!response) return [];

  const normalizedFromOptions = (response.options || [])
    .map(option => {
      const installments = Math.max(1, Math.min(Number(option.installments || 0), 12));
      const installmentAmount = Math.max(0, Number(option.installment_amount_cents || 0));
      const totalAmount = Math.max(
        0,
        Number(option.total_amount_cents || installmentAmount * installments || fallbackBaseAmountCents || 0),
      );
      if (!installments || !totalAmount) return null;
      return {
        installments,
        installment_amount_cents: installmentAmount || Math.round(totalAmount / installments),
        total_amount_cents: totalAmount,
        has_interest: Boolean(option.has_interest) || totalAmount > fallbackBaseAmountCents,
      } satisfies PaymentInstallmentOption;
    })
    .filter((option): option is PaymentInstallmentOption => Boolean(option));

  if (normalizedFromOptions.length) {
    return normalizedFromOptions.slice().sort((left, right) => left.installments - right.installments);
  }

  const normalizedFromPrices = (response.prices || [])
    .map((price, index) => {
      const totalAmountCents = parsePricingAmountToCents(price);
      const installments = index + 1;
      if (!totalAmountCents || installments > 12) return null;
      return {
        installments,
        installment_amount_cents: Math.round(totalAmountCents / installments),
        total_amount_cents: totalAmountCents,
        has_interest: totalAmountCents > fallbackBaseAmountCents,
      } satisfies PaymentInstallmentOption;
    })
    .filter((option): option is PaymentInstallmentOption => Boolean(option));

  return normalizedFromPrices.slice().sort((left, right) => left.installments - right.installments);
};

const digitsOnly = (value: string) => value.replace(/\D/g, "");

const onPhoneInput = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const digits = digitsOnly(input.value).slice(0, 11);
  if (digits.length <= 10) {
    customer.phone_number = digits
      .replace(/^(\d{0,2})(\d{0,4})(\d{0,4}).*/, (_, ddd, first, second) =>
        [ddd ? `(${ddd}` : "", ddd.length === 2 ? ") " : "", first, second ? `-${second}` : ""].join(""),
      )
      .trim();
    return;
  }
  customer.phone_number = digits
    .replace(/^(\d{0,2})(\d{0,5})(\d{0,4}).*/, (_, ddd, first, second) =>
      [ddd ? `(${ddd}` : "", ddd.length === 2 ? ") " : "", first, second ? `-${second}` : ""].join(""),
    )
    .trim();
};

const onPassportInput = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const digits = digitsOnly(input.value).slice(0, 11);
  customer.passport = digits.replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d{1,2})$/, "$1-$2");
};

const onCardNumberInput = (event: Event) => {
  const input = event.target as HTMLInputElement;
  card.number = digitsOnly(input.value).slice(0, 16).replace(/(.{4})/g, "$1 ").trim();
};

const onCvvInput = (event: Event) => {
  const input = event.target as HTMLInputElement;
  card.cvv = digitsOnly(input.value).slice(0, 4);
};

const summaryThumbStyle = (index: number) => {
  const palettes = [
    "linear-gradient(135deg, #3b82f6, #22c55e)",
    "linear-gradient(135deg, #8b5cf6, #f97316)",
    "linear-gradient(135deg, #06b6d4, #14b8a6)",
    "linear-gradient(135deg, #f59e0b, #ef4444)",
  ];
  return { background: palettes[index % palettes.length] };
};

const getSummaryItemImageUrl = (value?: string | null) => resolveMediaUrl(value) || null;

const buildPricingRequest = (): SectionProductsPricingRequest | null => {
  if (!props.pageId || !props.checkoutData?.sectionId || !cartItems.value.length) return null;
  const grouped = new Map<string, SectionProductsPricingRequest["products"][number]>();
  for (const item of cartItems.value) {
    const current = grouped.get(item.productId) || { product_id: item.productId, items: [] };
    current.items.push({
      variation_id: item.variationId,
      quantity: item.quantity,
      children: item.children,
      departure_id: item.departureId ?? null,
    });
    grouped.set(item.productId, current);
  }
  return {
    page_id: props.pageId,
    section_id: props.checkoutData.sectionId,
    fee_mode: props.checkoutData.feeMode,
    products: Array.from(grouped.values()),
    base_amount_cents: props.checkoutData.totalAmount || 0,
    currency: props.checkoutData.currency || "BRL",
    page_slug: props.pageSlug || null,
    agency_slug: props.agencySlug || null,
    source_url: props.pageUrl || null,
    channel: "public_page",
  };
};

const buildCheckoutItems = (): CheckoutCartItem[] =>
  cartItems.value.map(item => ({
    variation_id: item.variationId,
    quantity: item.quantity,
    children: item.children,
    departure_id: item.departureId ?? null,
  }));

const buildSectionCheckoutPayload = (): SectionProductsCheckoutRequest | null => {
  if (!props.pageId || !props.checkoutData?.sectionId || !cartItems.value.length) return null;
  const grouped = new Map<string, SectionProductsCheckoutRequest["products"][number]>();
  for (const item of cartItems.value) {
    const current = grouped.get(item.productId) || { product_id: item.productId, items: [] };
    current.items.push({
      variation_id: item.variationId,
      quantity: item.quantity,
      children: item.children,
      departure_id: item.departureId ?? null,
    });
    grouped.set(item.productId, current);
  }
  return {
    page_id: props.pageId,
    section_id: props.checkoutData.sectionId,
    customer: {
      name: customer.name.trim(),
      email: customer.email.trim(),
      phone: customer.phone_number.trim(),
    },
    products: Array.from(grouped.values()),
    page_slug: props.pageSlug || null,
    agency_slug: props.agencySlug || null,
    source_url: props.pageUrl || null,
    channel: "public_page",
  };
};

const resolveNationalityForProvider = () => (customer.nationality === "BR" ? "1" : "2");

const createSaleIntent = async (): Promise<PublicCheckoutResponse> => {
  const sectionPayload = buildSectionCheckoutPayload();
  if (sectionPayload) {
    const { data } = await createSectionProductsPublicCheckoutIntent(sectionPayload);
    return data;
  }
  if (props.checkoutData?.productId) {
    const { data } = await createProductPublicCheckoutIntent({
      product_id: props.checkoutData.productId,
      items: buildCheckoutItems(),
      customer: {
        name: customer.name.trim(),
        email: customer.email.trim(),
        phone: customer.phone_number.trim(),
      },
      page_id: props.pageId,
      page_slug: props.pageSlug || null,
      agency_slug: props.agencySlug || null,
      source_url: props.pageUrl || null,
      channel: "public_page",
    });
    return data;
  }
  throw new Error("Dados do checkout incompletos para iniciar a cobranca.");
};

const syncInstallments = () => {
  if (!installmentOptions.value.length) {
    card.installments = 1;
    return;
  }
  if (!installmentOptions.value.some(option => option.value === card.installments)) {
    card.installments = installmentOptions.value[0].value;
  }
};

const loadCreditCardPricing = async () => {
  const request = buildPricingRequest();
  if (!request || selectedMethod.value !== "credit_card") {
    pricingOptions.value = [];
    pricingError.value = null;
    syncInstallments();
    return;
  }
  pricingLoading.value = true;
  pricingError.value = null;
  try {
    const { data } = await getSectionProductsPublicPricing(request);
    pricingOptions.value = normalizePricingOptions(data, request.base_amount_cents);
    syncInstallments();
  } catch (error: any) {
    pricingOptions.value = [];
    pricingError.value = error?.response?.data?.detail || "Nao foi possivel consultar as parcelas da Blimboo agora.";
    syncInstallments();
  } finally {
    pricingLoading.value = false;
  }
};

const findFirstStringByKeys = (input: unknown, keys: string[]): string | null => {
  const wanted = new Set(keys.map(key => key.toLowerCase()));
  const stack: unknown[] = [input];
  while (stack.length) {
    const current = stack.pop();
    if (!current || typeof current !== "object") continue;
    if (Array.isArray(current)) {
      for (const entry of current) stack.push(entry);
      continue;
    }
    for (const [rawKey, rawValue] of Object.entries(current as Record<string, unknown>)) {
      const key = rawKey.toLowerCase();
      if (wanted.has(key)) {
        if (typeof rawValue === "string" && rawValue.trim()) {
          return rawValue.trim();
        }
        if (typeof rawValue === "number" && Number.isFinite(rawValue)) {
          return String(rawValue);
        }
      }
      if (rawValue && typeof rawValue === "object") {
        stack.push(rawValue);
      }
    }
  }
  return null;
};

const mergeProviderPayload = (previous: unknown, current: unknown): Record<string, unknown> | null => {
  const prev = previous && typeof previous === "object" && !Array.isArray(previous)
    ? (previous as Record<string, unknown>)
    : null;
  const curr = current && typeof current === "object" && !Array.isArray(current)
    ? (current as Record<string, unknown>)
    : null;
  if (!prev && !curr) return null;
  if (!prev && curr) return { ...curr };
  if (prev && !curr) return { ...prev };
  const merged: Record<string, unknown> = { ...(prev as Record<string, unknown>) };
  for (const [key, value] of Object.entries(curr as Record<string, unknown>)) {
    const prevValue = merged[key];
    if (
      value &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      prevValue &&
      typeof prevValue === "object" &&
      !Array.isArray(prevValue)
    ) {
      merged[key] = mergeProviderPayload(prevValue, value) as Record<string, unknown>;
      continue;
    }
    merged[key] = value;
  }
  return merged;
};

const normalizePossibleImage = (value: string | null) => {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://") || trimmed.startsWith("data:image/")) return trimmed;
  if (/^[A-Za-z0-9+/=]+$/.test(trimmed) && trimmed.length > 128) return `data:image/png;base64,${trimmed}`;
  return null;
};

const providerPayload = computed(() => checkoutResult.value?.provider_payload || null);
const pixCopyPasteCode = computed(() =>
  findFirstStringByKeys(providerPayload.value, [
    "pix_copy_paste",
    "copy_paste",
    "pix_code",
    "pix_payload",
    "emv",
    "brcode",
    "payload",
  ]),
);
const pixQrImageUrl = computed(() =>
  normalizePossibleImage(
    findFirstStringByKeys(providerPayload.value, [
      "qrcode_image",
      "qr_code_image",
      "pix_qrcode_image",
      "pix_qr_image",
      "qr_image",
      "qrcode",
      "qr_code",
    ]),
  ),
);
const boletoLineCode = computed(() =>
  findFirstStringByKeys(providerPayload.value, [
    "payable_code",
    "payablecode",
    "slip_code",
    "linha_digitavel",
    "digitable_line",
    "barcode",
    "barcode_number",
    "billet_number",
    "line",
    "line_code",
    "boleto_code",
    "boleto_number",
  ]),
);
const boletoPaymentUrl = computed(() =>
  findFirstStringByKeys(providerPayload.value, [
    "boleto_url",
    "bank_slip_url",
    "bank_slip_link",
    "billet_url",
    "payment_url",
    "pdf",
    "pdf_url",
  ]),
);
const boletoDueDateRaw = computed(() =>
  findFirstStringByKeys(providerPayload.value, [
    "due_date",
    "vencimento",
    "expiration_date",
    "expires_at",
    "expire_at",
  ]),
);
const boletoActiveMode = computed(() => selectedMethod.value === "boleto" && Boolean(boletoLineCode.value || boletoPaymentUrl.value));
const boletoDueDateText = computed(() => {
  const raw = boletoDueDateRaw.value;
  if (!raw) return "Nao informado";
  const normalized = raw.length >= 10 ? raw.slice(0, 10) : raw;
  const asDate = new Date(normalized);
  if (!Number.isNaN(asDate.getTime())) {
    const day = String(asDate.getDate()).padStart(2, "0");
    const month = String(asDate.getMonth() + 1).padStart(2, "0");
    return `${day}/${month}`;
  }
  const match = normalized.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return raw;
  return `${match[3]}/${match[2]}`;
});
const boletoDueBadgeText = computed(() => {
  const raw = boletoDueDateRaw.value;
  if (!raw) return "";
  const normalized = raw.length >= 10 ? raw.slice(0, 10) : raw;
  const due = new Date(`${normalized}T00:00:00`);
  if (Number.isNaN(due.getTime())) return "";
  const now = new Date(nowMs.value);
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diffDays = Math.ceil((due.getTime() - today.getTime()) / 86400000);
  if (diffDays < 0) return "Vencido";
  if (diffDays === 0) return "Vence hoje";
  if (diffDays === 1) return "Vence em 1 dia";
  return `Vence em ${diffDays} dias`;
});
const boletoStatusToneClass = computed(() => {
  const status = checkoutResult.value?.provider_status;
  if (status === "paid") return "boleto-active__status--ok";
  if (status === "canceled") return "boleto-active__status--error";
  return "boleto-active__status--pending";
});
const boletoStatusTitle = computed(() => {
  const status = checkoutResult.value?.provider_status;
  if (status === "paid") return "Pagamento aprovado";
  if (status === "canceled") return "Pagamento recusado";
  return "Aguardando pagamento";
});
const boletoStatusDescription = computed(() => {
  const status = checkoutResult.value?.provider_status;
  if (status === "paid") return "Sua compra foi confirmada com sucesso.";
  if (status === "canceled") return "Tente novamente ou escolha outra forma de pagamento.";
  return "Apos o pagamento, a compensacao bancaria pode levar ate 1 dia util.";
});
const pixActiveMode = computed(() => selectedMethod.value === "pix" && Boolean(pixQrImageUrl.value || pixCopyPasteCode.value));

const pixReservationSecondsLeft = computed(() => {
  if (!pixGeneratedAtMs.value) return PIX_RESERVATION_SECONDS;
  const elapsed = Math.floor((nowMs.value - pixGeneratedAtMs.value) / 1000);
  return Math.max(0, PIX_RESERVATION_SECONDS - elapsed);
});

const pixReservationTime = computed(() => {
  const mins = Math.floor(pixReservationSecondsLeft.value / 60).toString().padStart(2, "0");
  const secs = (pixReservationSecondsLeft.value % 60).toString().padStart(2, "0");
  return `${mins}:${secs}`;
});

const pixTimerToneClass = computed(() => {
  if (pixReservationSecondsLeft.value <= 60) return "pix-active__timer-pill--danger";
  if (pixReservationSecondsLeft.value <= 180) return "pix-active__timer-pill--warning";
  return "pix-active__timer-pill--ok";
});

const pixStatusToneClass = computed(() => {
  const status = checkoutResult.value?.provider_status;
  if (status === "paid") return "pix-active__status--ok";
  if (status === "canceled") return "pix-active__status--error";
  return "pix-active__status--pending";
});

const pixStatusTitle = computed(() => {
  const status = checkoutResult.value?.provider_status;
  if (status === "paid") return "Pagamento aprovado!";
  if (status === "canceled") return "Pagamento recusado";
  return "Aguardando pagamento";
});

const pixStatusDescription = computed(() => {
  const status = checkoutResult.value?.provider_status;
  if (status === "paid") return "Sua compra foi confirmada com sucesso.";
  if (status === "canceled") return "Tente novamente ou escolha outra forma de pagamento.";
  return "Assim que identificarmos o pagamento, a compra sera confirmada automaticamente.";
});

const pixCopyButtonLabel = computed(() => (pixCopyRecentlyCopied.value ? "Copiado ✓" : "Copiar codigo PIX"));
const boletoCopyButtonLabel = computed(() => (boletoCopyRecentlyCopied.value ? "Copiado ✓" : "Copiar"));
const boletoDownloadButtonLabel = computed(() => (boletoDownloadBusy.value ? "Abrindo boleto..." : "Baixar boleto"));

const copyPixCode = async () => {
  if (!pixCopyPasteCode.value) return;
  try {
    await navigator.clipboard.writeText(pixCopyPasteCode.value);
    pixCopyRecentlyCopied.value = true;
    copyToastMessage.value = "Codigo copiado com sucesso";
    copyToastVisible.value = true;
    if (pixCopyResetTimer) clearTimeout(pixCopyResetTimer);
    if (copyToastTimer) clearTimeout(copyToastTimer);
    pixCopyResetTimer = setTimeout(() => {
      pixCopyRecentlyCopied.value = false;
    }, 2000);
    copyToastTimer = setTimeout(() => {
      copyToastVisible.value = false;
    }, 2200);
  } catch {
    validationMessage.value = "Nao foi possivel copiar o codigo PIX.";
  }
};

const copyBoletoCode = async () => {
  if (!boletoLineCode.value) return;
  try {
    await navigator.clipboard.writeText(boletoLineCode.value);
    boletoCopyRecentlyCopied.value = true;
    copyToastMessage.value = "Codigo copiado com sucesso";
    copyToastVisible.value = true;
    if (boletoCopyResetTimer) clearTimeout(boletoCopyResetTimer);
    if (copyToastTimer) clearTimeout(copyToastTimer);
    boletoCopyResetTimer = setTimeout(() => {
      boletoCopyRecentlyCopied.value = false;
    }, 2000);
    copyToastTimer = setTimeout(() => {
      copyToastVisible.value = false;
    }, 2200);
  } catch {
    validationMessage.value = "Nao foi possivel copiar a linha digitavel.";
  }
};

const onBoletoDownload = () => {
  boletoDownloadBusy.value = true;
  if (boletoDownloadResetTimer) clearTimeout(boletoDownloadResetTimer);
  boletoDownloadResetTimer = setTimeout(() => {
    boletoDownloadBusy.value = false;
  }, 1200);
};

const finalizeAsPaid = (payload: PublicCheckoutResponse) => {
  const completeFlow = () => {
    emit("payment-succeeded", { passengerToken: payload.passenger_token || null, saleId: payload.sale_id });
    emit("update:modelValue", false);
    resetState();
  };
  if (selectedMethod.value === "pix") {
    successMessage.value = "Pagamento aprovado! Redirecionando...";
    if (paidRedirectTimer) clearTimeout(paidRedirectTimer);
    paidRedirectTimer = setTimeout(completeFlow, 1200);
    return;
  }
  completeFlow();
};

const scheduleStatusPolling = (saleId: number) => {
  if (statusPollTimer) clearTimeout(statusPollTimer);
  statusPollTimer = setTimeout(async () => {
    if (!visible.value) return;
    if (!pollingStatus.value) return;
    statusPollRun += 1;
    try {
      const { data } = await getPublicSaleStatus(saleId);
      checkoutResult.value = {
        ...data,
        provider_payload: mergeProviderPayload(checkoutResult.value?.provider_payload || null, data.provider_payload || null),
      };
      const message = data.message || (data.provider_status === "canceled" ? "Pagamento recusado." : "Pagamento pendente.");
      successMessage.value = message;
      if (data.provider_status === "paid") {
        pollingStatus.value = false;
        finalizeAsPaid(data);
        return;
      }
      if (data.provider_status === "canceled") {
        pollingStatus.value = false;
        validationMessage.value = "Pagamento recusado. Tente outro cartao ou forma de pagamento.";
        return;
      }
      if (statusPollRun >= MAX_STATUS_POLL_RUNS) {
        pollingStatus.value = false;
        successMessage.value = "Pagamento ainda pendente. Continuaremos exibindo o status na pagina.";
        return;
      }
      scheduleStatusPolling(saleId);
    } catch {
      if (statusPollRun >= MAX_STATUS_POLL_RUNS) {
        pollingStatus.value = false;
        successMessage.value = "Nao foi possivel atualizar o status agora. Tente novamente em instantes.";
        return;
      }
      scheduleStatusPolling(saleId);
    }
  }, 3000);
};

const handleSubmit = async () => {
  checkoutResult.value = null;
  successMessage.value = "";
  if (!customer.name.trim()) {
    validationMessage.value = "Preencha o nome completo para continuar.";
    return;
  }
  if (!customer.email.trim()) {
    validationMessage.value = "Preencha o e-mail do comprador.";
    return;
  }
  if (!customer.phone_number.trim()) {
    validationMessage.value = "Preencha o telefone ou WhatsApp.";
    return;
  }
  if (!customer.nationality.trim()) {
    validationMessage.value = "Informe a nacionalidade.";
    return;
  }
  if (!customer.passport.trim()) {
    validationMessage.value = "Informe o CPF.";
    return;
  }
  if (selectedMethod.value === "credit_card") {
    if (!card.holder_name.trim() || !card.number.trim() || !card.exp_month.trim() || !card.exp_year.trim() || !card.cvv.trim()) {
      validationMessage.value = "Preencha os dados do cartao para continuar.";
      return;
    }
  }

  const cleanedCpf = digitsOnly(customer.passport);
  if (cleanedCpf.length !== 11) {
    validationMessage.value = "Informe um CPF valido para continuar.";
    return;
  }

  validationMessage.value = "";
  confirming.value = true;
  try {
    const intent = await createSaleIntent();
    const installments = selectedMethod.value === "credit_card" ? card.installments : 1;
    const payload: {
      payment_method: PaymentMethod;
      installments: number;
      total_amount_cents: number;
      customer: { name: string; email: string; phone: string };
      payer_document: string;
      payer_passport: string;
      payer_nationality: string;
      card_holder_name?: string;
      card_number?: string;
      card_exp_month?: number;
      card_exp_year?: number;
      card_cvv?: string;
    } = {
      payment_method: selectedMethod.value,
      installments,
      total_amount_cents:
        selectedMethod.value === "credit_card"
          ? Math.max(1, selectedPricingOption.value?.total_amount_cents || totalAmount.value || 0)
          : Math.max(1, totalAmount.value || 0),
      customer: {
        name: customer.name.trim(),
        email: customer.email.trim(),
        phone: customer.phone_number.trim(),
      },
      payer_document: cleanedCpf,
      payer_passport: cleanedCpf,
      payer_nationality: resolveNationalityForProvider(),
    };
    if (selectedMethod.value === "credit_card") {
      payload.card_holder_name = card.holder_name.trim();
      payload.card_number = digitsOnly(card.number);
      payload.card_exp_month = Number(card.exp_month);
      payload.card_exp_year = Number(card.exp_year);
      payload.card_cvv = digitsOnly(card.cvv);
    }

    const { data } = await confirmPublicSale(intent.sale_id, payload);
    checkoutResult.value = {
      ...data,
      provider_payload: mergeProviderPayload(checkoutResult.value?.provider_payload || null, data.provider_payload || null),
    };
    const fallbackMessage = data.provider_status === "paid"
      ? "Pagamento aprovado."
      : data.provider_status === "canceled"
        ? "Pagamento recusado."
        : "Pagamento pendente.";
    successMessage.value = data.message || fallbackMessage;

    if (data.provider_status === "paid") {
      finalizeAsPaid(data);
      return;
    }
    if (data.provider_status === "processing" || data.provider_status === "pending") {
      pollingStatus.value = true;
      statusPollRun = 0;
      successMessage.value = "Pagamento pendente. Atualizando status automaticamente...";
      scheduleStatusPolling(data.sale_id);
    }
  } catch (error: any) {
    validationMessage.value = error?.response?.data?.detail || "Nao foi possivel finalizar o pedido agora.";
  } finally {
    confirming.value = false;
  }
};

watch(
  () => props.modelValue,
  value => {
    if (!value) resetState();
  },
);

watch(
  () => props.checkoutData,
  () => {
    resetState();
  },
  { deep: true },
);

watch(allowedMethods, methods => {
  if (!methods.includes(selectedMethod.value)) {
    selectedMethod.value = methods.includes("pix") ? "pix" : methods[0] || "credit_card";
  }
});

watch(
  () => [selectedMethod.value, props.checkoutData, props.pageId],
  () => {
    void loadCreditCardPricing();
  },
  { deep: true },
);

watch(installmentOptions, () => {
  syncInstallments();
});

watch(
  () => [selectedMethod.value, pixQrImageUrl.value, pixCopyPasteCode.value],
  () => {
    if (selectedMethod.value === "pix" && (pixQrImageUrl.value || pixCopyPasteCode.value) && !pixGeneratedAtMs.value) {
      pixGeneratedAtMs.value = Date.now();
    }
  },
);

watch(pixActiveMode, async isActive => {
  if (!isActive) return;
  await nextTick();
  pixQrContainerRef.value?.scrollIntoView({ behavior: "smooth", block: "center" });
});

watch(boletoActiveMode, async isActive => {
  if (!isActive) return;
  await nextTick();
  boletoContainerRef.value?.scrollIntoView({ behavior: "smooth", block: "center" });
});

pixClockTimer = setInterval(() => {
  nowMs.value = Date.now();
}, 1000);

onUnmounted(() => {
  if (statusPollTimer) {
    clearTimeout(statusPollTimer);
    statusPollTimer = null;
  }
  if (pixClockTimer) {
    clearInterval(pixClockTimer);
    pixClockTimer = null;
  }
  if (paidRedirectTimer) {
    clearTimeout(paidRedirectTimer);
    paidRedirectTimer = null;
  }
  if (pixCopyResetTimer) {
    clearTimeout(pixCopyResetTimer);
    pixCopyResetTimer = null;
  }
  if (boletoCopyResetTimer) {
    clearTimeout(boletoCopyResetTimer);
    boletoCopyResetTimer = null;
  }
  if (boletoDownloadResetTimer) {
    clearTimeout(boletoDownloadResetTimer);
    boletoDownloadResetTimer = null;
  }
  if (copyToastTimer) {
    clearTimeout(copyToastTimer);
    copyToastTimer = null;
  }
});
</script>

<style scoped>
.checkout-fade-enter-active,
.checkout-fade-leave-active {
  transition: opacity 0.24s ease;
}

.checkout-fade-enter-from,
.checkout-fade-leave-to {
  opacity: 0;
}

.checkout-overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  overflow-y: auto;
  background: #f8fafc;
}

.checkout-modal {
  position: relative;
  width: min(1240px, 100%);
  min-height: 100vh;
  margin: 0 auto;
  padding: 18px 22px 24px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.checkout-close {
  position: absolute;
  top: 18px;
  right: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  border-radius: 999px;
  background: #ffffff;
  color: #475569;
  font-size: 1.35rem;
  line-height: 1;
  transition: transform 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.checkout-close span {
  display: inline-block;
  transform: rotate(45deg);
}

.checkout-close:hover {
  transform: translateY(-1px);
  border-color: rgba(5, 150, 105, 0.35);
  color: #047857;
}

.checkout-empty {
  padding: 72px 24px;
  text-align: center;
}

.checkout-empty__eyebrow {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #059669;
}

.checkout-empty__title,
.checkout-section__title,
.summary-card__title {
  margin: 0;
  color: #0f172a;
  letter-spacing: -0.03em;
}

.checkout-empty__title {
  margin-top: 8px;
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 700;
}

.checkout-empty__text,
.checkout-section__hint,
.payment-tab__text,
.payment-note,
.payment-benefits,
.summary-note,
.summary-item__meta,
.summary-total__caption,
.trust-banner__text,
.footer-trust-item__text,
.checkout-topbar__text {
  color: #64748b;
  line-height: 1.55;
}

.checkout-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(320px, 0.88fr);
  gap: 16px;
  align-items: start;
  padding-top: 18px;
}

.checkout-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.checkout-topbar {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px 18px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
}

.checkout-topbar__side {
  display: flex;
  align-items: center;
  gap: 12px;
}

.checkout-topbar__side--end {
  margin-left: auto;
}

.checkout-topbar__title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
}

.checkout-topbar__text {
  margin: 2px 0 0;
  font-size: 0.82rem;
}

.checkout-section,
.summary-card,
.checkout-footer-trust {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
}

.checkout-section {
  padding: 18px;
}

.checkout-section__head,
.summary-card__head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
}

.checkout-section__title-wrap {
  display: flex;
  align-items: start;
  gap: 12px;
}

.checkout-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background: #059669;
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 800;
  flex-shrink: 0;
}

.checkout-section__title {
  font-size: 1.1rem;
  font-weight: 700;
}

.checkout-section__hint {
  margin: 2px 0 0;
  font-size: 0.86rem;
}

.checkout-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 16px;
  margin-top: 18px;
}

.checkout-form-grid--card {
  margin-top: 0;
  align-content: start;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field--full {
  grid-column: 1 / -1;
}

.field__label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
}

.field__control {
  width: 100%;
  min-height: 42px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  border-radius: 8px;
  background: #ffffff;
  padding: 0 14px;
  color: #0f172a;
  font-size: 0.95rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.field__control:focus {
  outline: none;
  border-color: rgba(5, 150, 105, 0.55);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.12);
}

.field__control::placeholder {
  color: #94a3b8;
}

.field__control--mono {
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.08em;
}

.field__control--select {
  appearance: none;
  background-image:
    linear-gradient(45deg, transparent 50%, #64748b 50%),
    linear-gradient(135deg, #64748b 50%, transparent 50%);
  background-position:
    calc(100% - 18px) calc(50% - 3px),
    calc(100% - 12px) calc(50% - 3px);
  background-size: 6px 6px, 6px 6px;
  background-repeat: no-repeat;
  padding-right: 34px;
}

.field__hint {
  font-size: 0.8rem;
  color: #64748b;
}

.field__hint--error {
  color: #be123c;
}

.payment-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 18px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 12px 12px 0 0;
  overflow: hidden;
}

.payment-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 76px;
  padding: 12px;
  border: 0;
  border-right: 1px solid rgba(226, 232, 240, 0.92);
  background: #ffffff;
  text-align: center;
  transition: background 0.2s ease, box-shadow 0.2s ease;
}

.payment-tab:last-child {
  border-right: 0;
}

.payment-tab--active {
  box-shadow: inset 0 0 0 2px #34d399;
}

.payment-tab__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  color: #0f172a;
  font-size: 0.72rem;
  font-weight: 800;
}

.payment-tab__icon-image {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.payment-tab__icon-image--boleto {
  width: 48px;
  height: 48px;
}

.payment-tab__copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.payment-tab__title,
.payment-info__title,
.summary-item__title,
.trust-banner__title,
.footer-trust-item__title {
  color: #0f172a;
  font-weight: 700;
}

.payment-tab__title {
  font-size: 0.88rem;
}

.payment-tab__text {
  font-size: 0.8rem;
}

.payment-card-shell {
  display: grid;
  grid-template-columns: minmax(240px, 0.92fr) minmax(0, 1.15fr);
  align-items: center;
  gap: 18px;
  margin-top: 0;
  padding: 18px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-top: 0;
  border-radius: 0 0 12px 12px;
}

.payment-card-previews {
  display: grid;
  gap: 12px;
}

.payment-card-preview {
  width: 100%;
  max-width: 340px;
  margin: 0 auto;
  min-height: 162px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-radius: 16px;
  padding: 14px 16px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.16), transparent 28%),
    linear-gradient(135deg, #064e3b 0%, #065f46 55%, #0f766e 100%);
  color: #f8fafc;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.payment-card-preview__top,
.payment-card-preview__bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.payment-card-preview__number {
  margin: 14px 0 12px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
  font-size: 0.92rem;
  line-height: 1.2;
  letter-spacing: 0.08em;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.payment-card-preview__label {
  display: block;
  margin-bottom: 2px;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.65);
}

.payment-card-preview__bottom p {
  margin: 0;
  font-weight: 600;
  line-height: 1.15;
}

.payment-card-preview__chip {
  width: 42px;
  height: 28px;
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(255, 214, 102, 0.95), rgba(255, 239, 181, 0.9)),
    #fcd34d;
}

.payment-card-preview__brand {
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.payment-card-preview--back {
  position: relative;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.16), transparent 28%),
    linear-gradient(135deg, #064e3b 0%, #065f46 55%, #0f766e 100%);
  justify-content: flex-start;
}

.payment-card-preview__magstripe {
  height: 30px;
  margin: 6px -16px 16px;
  background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
}

.payment-card-preview__signature-line {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  height: 34px;
  border-radius: 6px;
  padding: 0 10px;
  background: #e2e8f0;
}

.payment-card-preview__cvv-label {
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #334155;
}

.payment-card-preview__cvv-value {
  min-width: 42px;
  text-align: right;
  font-size: 0.9rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.payment-card-preview__back-note {
  margin-top: 16px;
  font-size: 0.72rem;
  letter-spacing: 0.03em;
  color: rgba(241, 245, 249, 0.72);
}

.payment-info {
  padding: 18px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-top: 0;
  border-radius: 0 0 12px 12px;
  background: #ffffff;
}

.payment-info__body {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: 18px;
  align-items: center;
}

.payment-info__art {
  position: relative;
  width: 150px;
  height: 150px;
  margin: 0 auto;
  border-radius: 24px;
  background: radial-gradient(circle at center, #ecfeff 0%, #d1fae5 55%, transparent 56%);
}

.payment-info__art-image {
  position: absolute;
  inset: 24px;
  width: calc(100% - 48px);
  height: calc(100% - 48px);
  object-fit: contain;
  z-index: 1;
}

.payment-info__art::before,
.payment-info__art::after {
  content: "";
  position: absolute;
  border-radius: 18px;
}

.payment-info__art--pix::after {
  top: 16px;
  right: 14px;
  width: 26px;
  height: 26px;
  background: rgba(16, 185, 129, 0.1);
}

.payment-info__art--boleto::before {
  inset: 28px 36px 30px 30px;
  border: 8px solid #ffffff;
  border-radius: 12px;
  background:
    linear-gradient(180deg, #bbf7d0 0 22%, transparent 22% 32%, #cbd5e1 32% 38%, transparent 38% 46%, #cbd5e1 46% 52%, transparent 52% 60%, #111827 60% 76%, #ffffff 76%);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}

.payment-info__art--boleto::after {
  right: 18px;
  bottom: 26px;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #22c55e 0%, #86efac 100%);
  box-shadow: 0 10px 24px rgba(34, 197, 94, 0.18);
}

.payment-info__title {
  margin: 0;
  font-size: 1.05rem;
}

.payment-benefits {
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.payment-benefits li {
  position: relative;
  margin-top: 7px;
  padding-left: 24px;
}

.payment-benefits li::before {
  content: "";
  position: absolute;
  top: 0.55rem;
  left: 0;
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #34d399;
}

.payment-note {
  margin-top: 16px;
  padding: 10px 14px;
  border: 1px solid rgba(16, 185, 129, 0.16);
  border-radius: 8px;
  background: #f0fdf4;
  font-size: 0.88rem;
}

.payment-dynamic {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.payment-dynamic__qr {
  width: min(220px, 100%);
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #ffffff;
  padding: 6px;
}

.payment-dynamic__code {
  min-height: 78px;
  resize: vertical;
  white-space: pre-wrap;
  word-break: break-all;
}

.payment-dynamic__copy {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: auto;
  min-width: 180px;
  text-decoration: none;
}

.pix-toast {
  position: fixed;
  top: 18px;
  right: 20px;
  z-index: 80;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid rgba(5, 150, 105, 0.3);
  background: #ecfdf5;
  color: #065f46;
  font-size: 0.88rem;
  font-weight: 700;
  box-shadow: 0 12px 22px rgba(15, 23, 42, 0.12);
}

.pix-toast-fade-enter-active,
.pix-toast-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.pix-toast-fade-enter-from,
.pix-toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.pix-active {
  margin: 0 auto;
  width: 100%;
  max-width: 760px;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  padding: 32px;
  background: #ffffff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
  animation: pixActiveFadeIn 0.25s ease;
}

@keyframes pixActiveFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.pix-active__timer-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 22px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
}

.pix-active__timer-copy {
  min-width: 0;
}

.pix-active__timer-label {
  margin: 0;
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: #334155;
  font-weight: 700;
}

.pix-active__timer-note {
  margin: 6px 0 0;
  font-size: 0.8rem;
  line-height: 1.42;
  color: #64748b;
}

.pix-active__timer-pill {
  min-width: 122px;
  text-align: center;
  padding: 10px 18px;
  border-radius: 999px;
  font-size: 1.36rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.08);
  transition: background-color 0.28s ease, color 0.28s ease, box-shadow 0.28s ease, transform 0.28s ease;
}

.pix-active__timer-pill--ok { background: #dcfce7; color: #065f46; }
.pix-active__timer-pill--warning { background: #ffedd5; color: #c2410c; }
.pix-active__timer-pill--danger {
  background: #fee2e2;
  color: #b91c1c;
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.08);
  animation: pixPulse 1.15s ease-in-out infinite;
}

@keyframes pixPulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.04); }
  100% { transform: scale(1); }
}

.pix-active__hero {
  margin-top: 26px;
  text-align: center;
}

.pix-active__title {
  margin: 0;
  font-size: clamp(1.9rem, 4.2vw, 2.625rem);
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: #111827;
  font-weight: 800;
}

.pix-active__subtitle {
  margin: 12px 0 0;
  font-size: 1rem;
  line-height: 1.5;
  color: #6b7280;
  max-width: 540px;
  margin-left: auto;
  margin-right: auto;
}

.pix-active__qr-wrap {
  margin: 26px auto 0;
  display: grid;
  justify-items: center;
  gap: 16px;
  padding: 28px;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.05);
  transition: transform 0.24s ease, box-shadow 0.24s ease;
}

.pix-active__qr-wrap:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.08), 0 0 0 1px rgba(5, 150, 105, 0.08);
}

.pix-active__qr {
  width: min(340px, 100%);
  max-width: 340px;
  min-width: 280px;
  border-radius: 16px;
  border: 1px solid rgba(203, 213, 225, 0.75);
  padding: 12px;
  background: #ffffff;
}

.pix-active__qr-note {
  margin: 0;
  font-size: 0.95rem;
  color: #334155;
  font-weight: 500;
  line-height: 1.4;
}

.pix-active__copy-row {
  margin-top: 26px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.pix-active__copy-field {
  min-height: 58px;
  border-radius: 18px;
  border: 1px solid #e5e7eb;
  background: #f8fafc;
  padding: 0 18px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.pix-active__copy-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  height: 30px;
  border-radius: 999px;
  background: #dcfce7;
  color: #065f46;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.pix-active__copy-input {
  width: 100%;
  min-height: 58px;
  border: 0;
  padding: 0;
  font-size: 0.95rem;
  line-height: 1;
  font-weight: 500;
  color: #0f172a;
  background: #f8fafc;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.pix-active__copy-input:focus {
  outline: none;
}

.pix-active__copy-btn {
  min-height: 58px;
  border: 0;
  border-radius: 18px;
  padding: 0 24px;
  font-size: 0.95rem;
  font-weight: 700;
  color: #ffffff;
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  box-shadow: 0 10px 22px rgba(5, 150, 105, 0.2);
  transition: transform 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
}

.pix-active__copy-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #047857 0%, #065f46 100%);
  box-shadow: 0 14px 24px rgba(5, 150, 105, 0.24);
}

.pix-active__copy-btn:active:not(:disabled) {
  transform: scale(0.985);
}

.pix-active__copy-btn:disabled {
  opacity: 0.5;
  box-shadow: none;
}

.pix-active__status {
  margin-top: 26px;
  border-radius: 18px;
  padding: 18px 20px;
  border: 1px solid #e5e7eb;
  transition: border-color 0.26s ease, background-color 0.26s ease, box-shadow 0.26s ease, color 0.26s ease, opacity 0.26s ease;
}

.pix-active__status--pending {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9);
  color: #1f2937;
  border-color: #dbe3ef;
}
.pix-active__status--ok {
  background: #ecfdf5;
  color: #065f46;
  border-color: rgba(5, 150, 105, 0.35);
  box-shadow: 0 10px 20px rgba(5, 150, 105, 0.12);
}
.pix-active__status--error { background: #fff1f2; color: #9f1239; border-color: rgba(190, 24, 93, 0.35); }

.pix-active__status-title {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 10px;
}

.pix-active__status-title::before {
  content: "";
  width: 18px;
  height: 18px;
  border-radius: 999px;
  flex-shrink: 0;
}

.pix-active__status--pending .pix-active__status-title::before {
  border: 2px solid #b6c3d3;
  border-top-color: #1f2937;
  animation: pixSpinner 1.05s linear infinite;
}

.pix-active__status--ok .pix-active__status-title::before {
  background: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2);
  animation: pixApprovedPop 0.35s ease-out;
}

.pix-active__status--error .pix-active__status-title::before {
  background: #e11d48;
}

@keyframes pixSpinner {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pixApprovedPop {
  0% { transform: scale(0.6); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}

.pix-active__status-text {
  margin: 10px 0 0;
  font-size: 0.9rem;
  line-height: 1.5;
  max-width: 620px;
}

.pix-active__summary {
  margin-top: 26px;
  border: 1px solid #e7edf3;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff, #fbfdff);
  padding: 18px;
}

.pix-active__summary-title {
  margin: 0;
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: #64748b;
  font-weight: 700;
}

.pix-active__summary-product {
  margin: 10px 0 0;
  font-size: 1.08rem;
  color: #111827;
  font-weight: 700;
}

.pix-active__summary-meta {
  margin: 8px 0 0;
  font-size: 0.9rem;
  color: #475569;
}

.pix-active__summary-total-label {
  margin: 14px 0 0;
  padding-top: 12px;
  border-top: 1px solid rgba(226, 232, 240, 0.9);
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
  font-weight: 700;
}

.pix-active__summary-total {
  margin: 6px 0 0;
  font-size: 2.25rem;
  color: #059669;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.pix-active__security-note {
  margin: 24px 0 0;
  padding-top: 16px;
  border-top: 1px solid rgba(226, 232, 240, 0.85);
  color: #64748b;
  font-size: 0.78rem;
  line-height: 1.3;
  text-align: center;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.pix-active__security-icon {
  width: 14px;
  height: 14px;
  color: #059669;
  flex-shrink: 0;
}

.boleto-active {
  margin: 0 auto;
  width: 100%;
  max-width: 760px;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  padding: 30px 32px;
  background: #ffffff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
  animation: pixActiveFadeIn 0.25s ease;
}

.boleto-active__header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 14px;
}

.boleto-active__header-copy {
  min-width: 0;
}

.boleto-active__title {
  margin: 0;
  font-size: clamp(1.6rem, 3.1vw, 2.2rem);
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: #111827;
  font-weight: 800;
}

.boleto-active__subtitle {
  margin: 10px 0 0;
  color: #64748b;
  font-size: 0.95rem;
  line-height: 1.45;
  max-width: 520px;
}

.boleto-active__due-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(245, 158, 11, 0.3);
  background: #fffbeb;
  color: #b45309;
  font-size: 0.84rem;
  font-weight: 700;
  white-space: nowrap;
}

.boleto-active__hero {
  margin-top: 24px;
  display: grid;
  justify-items: center;
  gap: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 22px;
  padding: 24px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
}

.boleto-active__icon-wrap {
  width: 84px;
  height: 84px;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #eef2ff;
  color: #334155;
  border: 1px solid #dbe4ef;
}

.boleto-active__icon {
  width: 44px;
  height: 44px;
}

.boleto-active__amount {
  margin: 8px 0 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
}

.boleto-active__due {
  margin: 0;
  font-size: 0.92rem;
  color: #475569;
  font-weight: 600;
}

.boleto-active__line-wrap {
  margin-top: 24px;
}

.boleto-active__line-label {
  margin: 0 0 10px;
  font-size: 0.86rem;
  color: #475569;
  font-weight: 700;
}

.boleto-active__line-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
}

.boleto-active__line-field {
  min-height: 58px;
  border-radius: 18px;
  border: 1px solid #e5e7eb;
  background: #f8fafc;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.boleto-active__line-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 58px;
  height: 30px;
  border-radius: 999px;
  background: #dcfce7;
  color: #065f46;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.boleto-active__line-input {
  width: 100%;
  min-height: 58px;
  border: 0;
  padding: 0;
  background: #f8fafc;
  color: #0f172a;
  font-size: 0.95rem;
  font-weight: 500;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.boleto-active__line-input:focus {
  outline: none;
}

.boleto-active__copy-btn {
  min-height: 58px;
  border: 0;
  border-radius: 18px;
  padding: 0 24px;
  color: #ffffff;
  font-size: 0.94rem;
  font-weight: 700;
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  box-shadow: 0 10px 20px rgba(5, 150, 105, 0.18);
  transition: transform 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
}

.boleto-active__copy-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #047857 0%, #065f46 100%);
  box-shadow: 0 14px 22px rgba(5, 150, 105, 0.22);
}

.boleto-active__copy-btn:active:not(:disabled) {
  transform: scale(0.985);
}

.boleto-active__copy-btn:disabled {
  opacity: 0.5;
  box-shadow: none;
}

.boleto-active__download-btn {
  margin-top: 18px;
  min-height: 52px;
  border-radius: 14px;
  border: 1px solid rgba(5, 150, 105, 0.35);
  color: #065f46;
  background: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 22px;
  font-size: 0.92rem;
  font-weight: 700;
  text-decoration: none;
  transition: transform 0.16s ease, box-shadow 0.16s ease, background-color 0.16s ease;
}

.boleto-active__download-btn:hover {
  transform: translateY(-1px);
  background: #f0fdf4;
  box-shadow: 0 10px 20px rgba(5, 150, 105, 0.12);
}

.boleto-active__status {
  margin-top: 20px;
  border-radius: 18px;
  padding: 16px 18px;
  border: 1px solid #e5e7eb;
}

.boleto-active__status--pending {
  background: #fffbeb;
  border-color: #f9e6b0;
  color: #92400e;
}

.boleto-active__status--ok {
  background: #ecfdf5;
  border-color: rgba(5, 150, 105, 0.35);
  color: #065f46;
}

.boleto-active__status--error {
  background: #fff1f2;
  border-color: rgba(190, 24, 93, 0.35);
  color: #9f1239;
}

.boleto-active__status-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
}

.boleto-active__status-text {
  margin: 8px 0 0;
  font-size: 0.9rem;
  line-height: 1.5;
}

.checkout-summary {
  position: sticky;
  top: 18px;
}

.summary-card {
  padding: 18px;
}

.summary-card__title {
  font-size: 1.1rem;
  font-weight: 700;
}

.summary-items {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin: 18px 0 10px;
}

.summary-items--grouped {
  margin: 0;
}

.summary-product-group {
  margin: 18px 0 10px;
}

.summary-product-group__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.summary-product-group__copy {
  min-width: 0;
}

.summary-product-group__title {
  margin: 0;
  color: #0f172a;
  font-size: 1rem;
  font-weight: 700;
}

.summary-item {
  display: flex;
  align-items: start;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.summary-item__media {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  border-radius: 14px;
  color: #ffffff;
  font-size: 1.2rem;
  font-weight: 800;
  flex-shrink: 0;
  overflow: hidden;
}

.summary-item__media-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.summary-item__copy {
  min-width: 0;
  flex: 1;
}

.summary-item__title,
.summary-item__variant,
.summary-item__meta,
.summary-item__amount,
.summary-row strong,
.summary-total__value {
  margin: 0;
}

.summary-item__variant {
  margin-top: 4px;
  color: #059669;
  font-weight: 700;
}

.summary-item__schedule {
  margin: 4px 0 0;
  color: #475569;
  font-size: 0.84rem;
  font-weight: 600;
}

.summary-item__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 0.85rem;
}

.summary-item__amount {
  margin-left: auto;
  color: #0f172a;
  font-weight: 700;
  white-space: nowrap;
}

.summary-item--package {
  align-items: center;
}

.summary-item--package .summary-item__title {
  font-size: 0.95rem;
}

.summary-row,
.summary-total {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
}

.summary-row {
  padding: 12px 0;
  border-top: 1px solid rgba(226, 232, 240, 0.8);
  color: #475569;
  font-size: 0.95rem;
}

.summary-row--discount {
  color: #059669;
}

.summary-total {
  padding: 18px 0 0;
  border-top: 1px solid rgba(203, 213, 225, 0.9);
}

.summary-total__label {
  display: block;
  color: #0f172a;
  font-size: 1rem;
  font-weight: 700;
}

.summary-total__caption {
  margin: 2px 0 0;
  font-size: 0.88rem;
}

.summary-total__value {
  color: #059669;
  font-size: 2.1rem;
  font-weight: 700;
  letter-spacing: -0.04em;
}

.trust-banner {
  display: flex;
  align-items: start;
  gap: 12px;
  margin-top: 22px;
  padding: 14px;
  border: 1px solid rgba(16, 185, 129, 0.12);
  border-radius: 14px;
  background: #f6fffb;
}

.trust-banner__icon,
.footer-trust-item__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #059669;
  font-size: 0.78rem;
  font-weight: 800;
  flex-shrink: 0;
}

.footer-trust-item__icon-svg {
  width: 20px;
  height: 20px;
}

.trust-banner__icon-svg {
  width: 18px;
  height: 18px;
}

.summary-cta {
  width: 100%;
  min-height: 52px;
  margin-top: 22px;
  border: 0;
  border-radius: 10px;
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: #ffffff;
  font-size: 1rem;
  font-weight: 700;
  box-shadow: 0 12px 26px rgba(5, 150, 105, 0.2);
  transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}

.summary-cta:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 16px 30px rgba(5, 150, 105, 0.24);
}

.summary-cta:disabled {
  opacity: 0.72;
  box-shadow: none;
  cursor: not-allowed;
}

.summary-cta--awaiting {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  color: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.5);
  box-shadow: 0 8px 16px rgba(100, 116, 139, 0.22);
}

.summary-cta--awaiting:disabled {
  opacity: 0.88;
}

.summary-note,
.summary-error,
.summary-success {
  margin: 12px 0 0;
  font-size: 0.86rem;
  text-align: center;
}

.summary-error {
  color: #be123c;
}

.summary-success {
  color: #0f766e;
}

.checkout-footer-trust {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  padding: 16px 18px;
}

.footer-trust-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.footer-trust-item__title {
  margin: 0;
  font-size: 0.9rem;
}

.footer-trust-item__text {
  margin: 2px 0 0;
  font-size: 0.8rem;
}

@media (max-width: 1140px) {
  .checkout-layout,
  .payment-card-shell,
  .payment-info__body,
  .checkout-footer-trust {
    grid-template-columns: 1fr;
  }

  .checkout-summary {
    position: static;
  }

  .payment-info__art {
    width: 124px;
    height: 124px;
  }
}

@media (max-width: 720px) {
  .checkout-modal {
    padding: 14px 12px 20px;
  }

  .checkout-topbar,
  .checkout-section__head,
  .summary-card__head {
    flex-direction: column;
    align-items: start;
  }

  .checkout-topbar__side--end {
    margin-left: 0;
  }

  .checkout-form-grid,
  .payment-tabs {
    grid-template-columns: 1fr;
  }

  .pix-active {
    padding: 18px;
    border-radius: 16px;
  }

  .pix-active__timer-row {
    position: sticky;
    top: 8px;
    z-index: 2;
    background: #ffffff;
    border-radius: 12px;
    padding: 12px;
    text-align: center;
    justify-content: center;
    flex-direction: column;
    gap: 10px;
  }

  .pix-active__timer-note {
    max-width: 270px;
    margin-left: auto;
    margin-right: auto;
  }

  .pix-active__hero {
    margin-top: 20px;
  }

  .pix-active__title {
    font-size: 1.875rem;
  }

  .pix-active__copy-row {
    grid-template-columns: 1fr;
  }

  .pix-active__copy-field {
    width: 100%;
  }

  .pix-active__copy-btn {
    width: 100%;
  }

  .pix-active__qr {
    min-width: 0;
    width: 100%;
    max-width: 360px;
  }

  .boleto-active {
    padding: 18px;
    border-radius: 16px;
  }

  .boleto-active__header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 10px;
  }

  .boleto-active__subtitle {
    margin-left: auto;
    margin-right: auto;
  }

  .boleto-active__line-row {
    grid-template-columns: 1fr;
  }

  .boleto-active__copy-btn,
  .boleto-active__download-btn {
    width: 100%;
  }

  .payment-tabs {
    border-radius: 12px;
  }

  .payment-tab {
    border-right: 0;
    border-bottom: 1px solid rgba(226, 232, 240, 0.92);
  }

  .payment-tab:last-child {
    border-bottom: 0;
  }

  .payment-card-shell,
  .payment-info {
    margin-top: 12px;
    border-top: 1px solid rgba(226, 232, 240, 0.92);
    border-radius: 12px;
  }

  .summary-item,
  .summary-row,
  .summary-total {
    flex-direction: column;
  }

  .summary-item__amount {
    margin-left: 0;
  }
}
</style>

