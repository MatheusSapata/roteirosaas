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

    <template v-if="activeTab === 'templates'">
      <section class="space-y-5">
        <div class="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-100">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">{{ copy.templates.eyebrow }}</p>
              <h2 class="text-2xl font-semibold text-slate-900">{{ copy.templates.title }}</h2>
              <p class="text-sm text-slate-500">{{ copy.templates.description }}</p>
            </div>
            <div class="flex flex-wrap gap-3">
              <button type="button" class="btn-secondary" :disabled="savingTemplate" @click="startNewTemplate">
                {{ copy.templates.new }}
              </button>
              <button
                type="button"
                class="btn-primary"
                :disabled="savingTemplate || !canSaveTemplate"
                @click="persistTemplate"
              >
                {{ templateForm.id ? copy.templates.save : copy.templates.create }}
              </button>
            </div>
          </div>

          <div
            v-if="feedbackMessage"
            class="mt-4 rounded-2xl px-4 py-2 text-sm font-semibold"
            :class="feedbackToneClass"
          >
            {{ feedbackMessage }}
          </div>
        </div>

        <div>
          <div v-if="templatesLoading" class="placeholder-card">{{ copy.templates.loading }}</div>

          <transition name="fade">
            <div v-if="!templatesLoading && !templates.length" class="placeholder-card">
              {{ copy.templates.empty }}
            </div>
          </transition>

          <transition name="slide-fade">
            <div v-if="!templatesLoading && templates.length" class="space-y-3">
              <button type="button" class="collapse-toggle" @click="templatesCollapsed = !templatesCollapsed">
                {{ templatesCollapsed ? copy.templates.show : copy.templates.hide }}
              </button>

              <div
                v-show="!templatesCollapsed"
                class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-6"
              >
                <article
                  v-for="template in templates"
                  :key="template.id"
                  class="cursor-pointer rounded-3xl border p-4 transition hover:-translate-y-0.5 hover:shadow-lg"
                  :class="templateForm.id === template.id ? 'border-emerald-300 bg-white shadow-lg shadow-emerald-100' : 'border-slate-100 bg-white/70 shadow-sm'"
                  @click="selectTemplate(template.id)"
                >
                  <header class="flex items-center justify-between gap-3">
                    <div>
                      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">#{{ template.id }}</p>
                      <h3 class="text-lg font-semibold text-slate-900">{{ template.name }}</h3>
                      <p class="text-xs text-slate-500">{{ formatShortDate(template.updated_at || template.created_at) }}</p>
                    </div>

                    <span :class="template.is_active ? 'badge-success' : 'badge-muted'">
                      {{ template.is_active ? copy.templates.active : copy.templates.inactive }}
                    </span>
                  </header>

                  <p class="mt-2 line-clamp-3 text-sm text-slate-600">
                    {{ template.description || copy.templates.noDescription }}
                  </p>

                  <div class="mt-3 flex flex-wrap gap-3">
                    <button type="button" class="pill" @click.stop="selectTemplate(template.id)">
                      {{ copy.templates.edit }}
                    </button>
                    <button type="button" class="pill pill--ghost" @click.stop="duplicateTemplate(template)">
                      {{ copy.templates.duplicate }}
                    </button>
                    <button
                      type="button"
                      class="text-xs font-semibold text-rose-500 hover:text-rose-600"
                      @click.stop="removeTemplate(template)"
                    >
                      {{ copy.templates.delete }}
                    </button>
                  </div>
                </article>
              </div>
            </div>
          </transition>
        </div>

        <div class="grid gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
            <header class="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">{{ copy.editor.eyebrow }}</p>
                <h3 class="text-xl font-semibold text-slate-900">
                  {{ templateForm.id ? copy.editor.editing(templateForm.name || copy.editor.untitled) : copy.editor.new }}
                </h3>
                <p class="text-sm text-slate-500">{{ copy.editor.subtitle }}</p>
              </div>

              <label class="inline-flex cursor-pointer items-center gap-2 text-sm font-semibold text-slate-600">
                <input
                  v-model="templateForm.is_active"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300 text-emerald-500 focus:ring-emerald-500"
                />
                {{ templateForm.is_active ? copy.templates.active : copy.templates.inactive }}
              </label>
            </header>

            <div
              v-if="templateEditorLoading"
              class="mt-6 rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500"
            >
              {{ copy.editor.loading }}
            </div>

            <div v-else class="mt-6 space-y-4">
              <div>
                <label class="input-label">{{ copy.form.name }}</label>
                <input v-model="templateForm.name" type="text" class="input" :placeholder="copy.form.namePlaceholder" />
              </div>

              <div>
                <label class="input-label">{{ copy.form.description }}</label>
                <textarea
                  v-model="templateForm.description"
                  rows="2"
                  class="input"
                  :placeholder="copy.form.descriptionPlaceholder"
                ></textarea>
              </div>

              <div>
                <div class="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p class="input-label mb-1">{{ copy.form.content }}</p>
                    <p class="text-[11px] font-normal text-slate-400">{{ copy.form.contentHint }}</p>
                  </div>

                  <div class="editor-actions">
                    <button type="button" class="editor-action" @click="insertClauseSnippet">
                      {{ copy.quickInsert.clause }}
                    </button>
                    <button type="button" class="editor-action" @click="insertPassengersSnippet">
                      {{ copy.quickInsert.passengers }}
                    </button>
                    <button type="button" class="editor-action" @click="insertSignatureSnippet">
                      {{ copy.quickInsert.signatures }}
                    </button>
                  </div>
                </div>

                <p class="text-xs text-slate-500">{{ copy.quickInsert.helper }}</p>

                <QuillEditor
                  ref="quillRef"
                  v-model:content="templateForm.content"
                  content-type="html"
                  theme="snow"
                  class="rich-editor mt-3"
                  :toolbar="editorToolbar"
                  :placeholder="copy.form.contentPlaceholder"
                />
              </div>
            </div>
          </div>

          <TemplateVariablesPanel
            :categories="templateVariables"
            :loading="variablesLoading"
            @insert="insertVariable"
            @preview="openPreview"
          />
        </div>
      </section>
    </template>

    <template v-else-if="activeTab === 'contracts'">
      <section class="space-y-4">
        <div class="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-100">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">{{ copy.contracts.eyebrow }}</p>
              <h2 class="text-2xl font-semibold text-slate-900">{{ copy.contracts.title }}</h2>
              <p class="text-sm text-slate-500">{{ copy.contracts.description }}</p>
            </div>

            <button type="button" class="btn-secondary" @click="loadContracts" :disabled="contractsLoading">
              {{ copy.contracts.refresh }}
            </button>
          </div>
        </div>

        <div v-if="contractsLoading" class="placeholder-card">{{ copy.contracts.loading }}</div>
        <div v-else-if="!contracts.length" class="placeholder-card">{{ copy.contracts.empty }}</div>

        <div v-else class="overflow-x-auto rounded-3xl border border-slate-100 bg-white shadow-sm">
          <table class="min-w-full divide-y divide-slate-100 text-sm">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
              <tr>
                <th class="px-6 py-3">{{ copy.contracts.buyer }}</th>
                <th class="px-6 py-3">{{ copy.contracts.product }}</th>
                <th class="px-6 py-3">{{ copy.contracts.amount }}</th>
                <th class="px-6 py-3">{{ copy.contracts.date }}</th>
                <th class="px-6 py-3">{{ copy.contracts.status }}</th>
                <th class="px-6 py-3">{{ copy.contracts.signature.column }}</th>
                <th class="px-6 py-3">{{ copy.contracts.verification.column }}</th>
                <th class="px-6 py-3 text-right">{{ copy.contracts.actions }}</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-slate-100 text-slate-700">
              <tr v-for="contract in contracts" :key="contract.id">
                <td class="px-6 py-4">
                  <p class="font-semibold text-slate-900">{{ contract.buyer_name || copy.contracts.noName }}</p>
                  <p class="text-xs text-slate-500">ID {{ contract.sale_id }}</p>
                </td>

                <td class="px-6 py-4">
                  <p class="font-semibold text-slate-900">{{ contract.product_name }}</p>
                  <p v-if="contract.template_id" class="text-xs text-slate-500">Template #{{ contract.template_id }}</p>
                </td>

                <td class="px-6 py-4 font-semibold">{{ formatCurrency(contract.total_amount, contract.currency) }}</td>
                <td class="px-6 py-4 text-sm text-slate-500">{{ formatShortDate(contract.created_at) }}</td>

                <td class="px-6 py-4">
                  <span :class="statusBadgeClass(contract.status)">
                    {{ contractStatusLabel(contract.status) }}
                  </span>
                  <p v-if="contract.status === 'failed' && contract.last_error" class="mt-1 text-xs text-rose-500">
                    {{ contract.last_error }}
                  </p>
                </td>

                <td class="px-6 py-4">
                  <div class="space-y-2">
                    <div class="flex flex-wrap items-center gap-2">
                      <span :class="signatureBadgeClass(contract.signature_status)">
                        {{ signatureStatusLabel(contract.signature_status) }}
                      </span>
                      <span v-if="contract.signature_signed_at" class="text-xs font-semibold text-slate-500">
                        {{ copy.contracts.signature.signedAt }} {{ formatShortDateTime(contract.signature_signed_at) }}
                      </span>
                    </div>

                    <p v-if="contract.signature_status === 'pending' && !contract.signature_link" class="text-xs text-slate-500">
                      {{ copy.contracts.signature.unavailable }}
                    </p>

                    <p v-else-if="contract.signature_status === 'signed'" class="text-xs text-slate-500">
                      {{ copy.contracts.signature.signedBy }}
                      {{ contract.signature_name || contract.buyer_name }}
                    </p>

                    <div v-if="contract.signature_status === 'pending'" class="flex flex-wrap gap-2">
                      <button
                        type="button"
                        class="pill"
                        :disabled="!contract.signature_link"
                        @click="copySignatureLink(contract)"
                      >
                        {{ copy.contracts.signature.copy }}
                      </button>

                      <button
                        type="button"
                        class="pill"
                        :disabled="!contract.signature_link"
                        @click="openSignatureLink(contract)"
                      >
                        {{ copy.contracts.signature.open }}
                      </button>
                    </div>

                    <p v-else class="text-xs text-slate-500">
                      {{ copy.contracts.signature.completed }}
                    </p>
                  </div>
                </td>

                <td class="px-6 py-4">
                  <div class="space-y-2">
                    <div class="flex flex-wrap items-center gap-2">
                      <span :class="verificationBadgeClass(contractVerificationStatus(contract))">
                        {{ verificationStatusLabel(contractVerificationStatus(contract)) }}
                      </span>
                      <button
                        type="button"
                        class="text-xs font-semibold text-emerald-600 underline-offset-4 hover:underline"
                        @click="openVerificationModal(contract)"
                      >
                        {{ copy.contracts.verification.view }}
                      </button>
                    </div>
                    <div v-if="contract.verification_url" class="flex flex-wrap gap-2">
                      <button type="button" class="pill pill--ghost" @click="copyVerificationLink(contract)">
                        {{ copy.contracts.verification.copy }}
                      </button>
                      <button type="button" class="pill" @click="openVerificationLink(contract)">
                        {{ copy.contracts.verification.open }}
                      </button>
                    </div>
                    <p v-else class="text-xs text-slate-500">
                      {{ copy.contracts.verification.unavailable }}
                    </p>
                  </div>
                </td>

                <td class="px-6 py-4">
                  <div class="flex justify-end gap-2">
                    <template v-if="contract.signed_pdf_url">
                      <button type="button" class="pill" @click="viewContractPdf(contract.signed_pdf_url)">
                        {{ copy.contracts.signedView }}
                      </button>
                      <button type="button" class="pill" @click="downloadContractPdf(contract.signed_pdf_url)">
                        {{ copy.contracts.signedDownload }}
                      </button>
                      <button
                        v-if="contract.pdf_url"
                        type="button"
                        class="pill pill--ghost"
                        @click="viewContractPdf(contract.pdf_url)"
                      >
                        {{ copy.contracts.originalView }}
                      </button>
                    </template>

                    <template v-else>
                      <button type="button" class="pill" :disabled="!contract.pdf_url" @click="viewContractPdf(contract.pdf_url)">
                        {{ copy.contracts.view }}
                      </button>
                      <button
                        type="button"
                        class="pill"
                        :disabled="!contract.pdf_url"
                        @click="downloadContractPdf(contract.pdf_url)"
                      >
                        {{ copy.contracts.download }}
                      </button>
                    </template>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <template v-else-if="activeTab === 'signature'">
      <section class="space-y-5">
        <div class="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-100">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">{{ copy.signature.eyebrow }}</p>
          <h2 class="text-2xl font-semibold text-slate-900">{{ copy.signature.title }}</h2>
          <p class="text-sm text-slate-500">{{ copy.signature.description }}</p>
        </div>

        <div v-if="signatureLoading" class="placeholder-card">Carregando assinatura...</div>

        <div v-else class="grid gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <div class="space-y-5">
            <div>
              <p class="input-label">{{ copy.signature.typeLabel }}</p>
              <div class="flex flex-wrap gap-2">
                <button
                  type="button"
                  class="pill"
                  :class="signatureForm.signature_type === 'drawn' ? 'pill--active' : ''"
                  @click="signatureForm.signature_type = 'drawn'"
                >
                  {{ copy.signature.drawn }}
                </button>
                <button
                  type="button"
                  class="pill"
                  :class="signatureForm.signature_type === 'typed' ? 'pill--active' : ''"
                  @click="signatureForm.signature_type = 'typed'"
                >
                  {{ copy.signature.typed }}
                </button>
              </div>
            </div>

            <div class="grid gap-4 md:grid-cols-2">
              <div>
                <label class="input-label">{{ copy.signature.displayName }}</label>
                <input v-model="signatureForm.signature_display_name" type="text" class="input" />
              </div>
              <div>
                <label class="input-label">{{ copy.signature.role }}</label>
                <input v-model="signatureForm.signature_role" type="text" class="input" />
              </div>
              <div>
                <label class="input-label">{{ copy.signature.company }}</label>
                <input v-model="signatureForm.signature_company_name" type="text" class="input" />
              </div>
              <div>
                <label class="input-label">{{ copy.signature.city }}</label>
                <input v-model="signatureForm.signature_city" type="text" class="input" />
              </div>
            </div>

            <div v-if="signatureForm.signature_type === 'drawn'" class="space-y-2">
              <LegalSignatureDrawPad
                v-model="signatureForm.signature_drawn_image"
                :disabled="signatureSaving"
              />
              <p class="text-xs text-slate-500">{{ copy.signature.drawnHelper }}</p>
            </div>

            <div v-else class="space-y-3">
              <div>
                <label class="input-label">{{ copy.signature.typedValue }}</label>
                <input
                  v-model="signatureForm.signature_typed_value"
                  type="text"
                  class="input"
                  placeholder="Ex.: Matheus Sapata"
                />
              </div>

              <div>
                <label class="input-label">{{ copy.signature.fontStyle }}</label>
                <select v-model="signatureForm.signature_font_style" class="input">
                  <option value="classic">{{ copy.signature.styles.classic }}</option>
                  <option value="cursive">{{ copy.signature.styles.cursive }}</option>
                  <option value="elegant">{{ copy.signature.styles.elegant }}</option>
                </select>
              </div>

              <p class="text-xs text-slate-500">{{ copy.signature.typedHelper }}</p>
            </div>
          </div>

          <div class="signature-preview-card">
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">{{ copy.signature.eyebrow }}</p>

            <div class="signature-preview-visual">
              <img
                v-if="signatureForm.signature_type === 'drawn' && signatureForm.signature_drawn_image"
                :src="signatureForm.signature_drawn_image"
                alt="Assinatura desenhada"
                class="signature-preview-image"
              />
              <p v-else :class="signatureTypedClass">
                {{
                  signatureForm.signature_type === "typed" && signatureForm.signature_typed_value
                    ? signatureForm.signature_typed_value
                    : signaturePreviewName
                }}
              </p>
            </div>

            <p class="signature-preview-name">{{ signaturePreviewName }}</p>
            <p class="signature-preview-role">{{ signaturePreviewRole }}</p>
            <p v-if="signaturePreviewCompany" class="signature-preview-company">{{ signaturePreviewCompany }}</p>
            <p v-if="signaturePreviewCity" class="signature-preview-city">{{ signaturePreviewCity }}</p>
            <p class="signature-preview-badge">Assinatura institucional da contratada</p>
          </div>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-4">
          <p class="text-xs text-slate-500">{{ copy.signature.info }}</p>

          <div class="flex flex-wrap gap-3">
            <button
              type="button"
              class="btn-secondary"
              :disabled="signatureRemoving || signatureSaving || !signatureProfileLoaded"
              @click="removeSignatureProfile"
            >
              {{ copy.signature.remove }}
            </button>

            <button
              type="button"
              class="btn-primary"
              :disabled="signatureSaving || !canSaveSignatureProfile"
              @click="persistSignatureProfile"
            >
              {{ copy.signature.save }}
            </button>
          </div>
        </div>
      </section>
    </template>

    <div v-if="previewVisible" class="modal-overlay" @click.self="closePreview">
      <div class="modal-card modal-card--preview">
        <header class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">{{ copy.preview.eyebrow }}</p>
            <h3 class="text-lg font-semibold text-slate-900">{{ templateForm.name || copy.preview.title }}</h3>
          </div>
          <button type="button" class="text-sm font-semibold text-slate-500 hover:text-slate-900" @click="closePreview">
            {{ copy.preview.close }}
          </button>
        </header>

        <div class="preview-content custom-scroll" v-html="previewHtml"></div>
      </div>
    </div>

    <div v-if="verificationModalVisible" class="modal-overlay" @click.self="closeVerificationModal">
      <div class="modal-card max-w-2xl">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              {{ copy.contracts.verification.modalEyebrow }}
            </p>
            <h3 class="mt-1 text-xl font-semibold text-slate-900">{{ copy.contracts.verification.modalTitle }}</h3>
            <p class="text-sm text-slate-500">{{ copy.contracts.verification.modalHelper }}</p>
          </div>
          <button type="button" class="btn-secondary" @click="closeVerificationModal">{{ copy.preview.close }}</button>
        </div>

        <div class="mt-4" v-if="verificationLoading">
          <p class="text-sm text-slate-500">{{ copy.contracts.verification.loading }}</p>
        </div>
        <div v-else-if="verificationError" class="rounded-2xl bg-rose-50 p-4 text-sm text-rose-600">
          {{ verificationError }}
        </div>
        <div v-else-if="verificationDetail" class="mt-4 space-y-5">
          <div class="flex flex-wrap items-center gap-2">
            <span :class="verificationBadgeClass(verificationDetail.status)">
              {{ verificationStatusLabel(verificationDetail.status) }}
            </span>
            <span class="text-sm font-semibold text-slate-500">ID #{{ verificationDetail.contract_id }}</span>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <p class="input-label">{{ copy.contracts.buyer }}</p>
              <p class="value">{{ verificationDetail.buyer_name || copy.contracts.noName }}</p>
            </div>
            <div>
              <p class="input-label">{{ copy.contracts.product }}</p>
              <p class="value">{{ verificationDetail.product_name || "-" }}</p>
            </div>
            <div>
              <p class="input-label">{{ copy.contracts.date }}</p>
              <p class="value">
                {{ formatShortDate(verificationDetail.generated_at || verificationDetail.created_at) }}
              </p>
            </div>
            <div>
              <p class="input-label">{{ copy.contracts.signature.column }}</p>
              <p class="value">
                {{ signatureStatusLabel(verificationDetail.signature_status || "pending") }}
              </p>
            </div>
          </div>

          <div>
            <p class="input-label">
              Hash ({{ (verificationDetail.document_hash_algorithm || "SHA-256").toUpperCase() }})
            </p>
            <p class="hash-box">{{ verificationDetail.document_hash || "Em processamento" }}</p>
          </div>

          <div class="flex flex-wrap gap-3">
            <button type="button" class="pill" :disabled="verificationLoading" @click="regenerateVerification">
              {{ copy.contracts.verification.regenerate }}
            </button>
            <button
              type="button"
              class="pill pill--ghost"
              :disabled="!verificationDetail.verification_url"
              @click="copyVerificationDetailLink"
            >
              {{ copy.contracts.verification.copy }}
            </button>
            <button
              type="button"
              class="pill"
              :disabled="!verificationDetail.verification_url"
              @click="openVerificationDetailLink"
            >
              {{ copy.contracts.verification.open }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import DOMPurify from "dompurify";
import { QuillEditor } from "@vueup/vue-quill";
import "@vueup/vue-quill/dist/vue-quill.snow.css";

import TemplateVariablesPanel from "../../components/legal/TemplateVariablesPanel.vue";
import LegalSignatureDrawPad from "../../components/legal/LegalSignatureDrawPad.vue";
import {
  createLegalTemplate,
  deleteLegalSignatureProfile,
  deleteLegalTemplate,
  getLegalTemplateDetail,
  getLegalContractVerification,
  getLegalSignatureProfile,
  getLegalVariables,
  listLegalContracts,
  listLegalTemplates,
  regenerateLegalContractVerification,
  saveLegalSignatureProfile,
  updateLegalTemplate,
} from "../../services/legal";
import type {
  LegalContract,
  LegalContractVerificationDetail,
  LegalContractVerificationStatus,
  LegalSignatureProfile,
  LegalSignatureProfilePayload,
  SignatureFontStyle,
  LegalTemplateDetail,
  LegalTemplatePayload,
  LegalTemplateSummary,
  LegalVariableCategory,
} from "../../types/legal";
import { createAdminLocalizer } from "../../utils/adminI18n";

const t = createAdminLocalizer();
const tabs = [
  { label: t({ pt: "Templates", es: "Plantillas" }), value: "templates" },
  { label: t({ pt: "Contratos gerados", es: "Contratos generados" }), value: "contracts" },
  { label: t({ pt: "Assinatura", es: "Firma" }), value: "signature" },
] as const;
type TabValue = (typeof tabs)[number]["value"];

const activeTab = ref<TabValue>("templates");
const templates = ref<LegalTemplateSummary[]>([]);
const templateVariables = ref<LegalVariableCategory[]>([]);
const templateForm = reactive({
  id: null as number | null,
  name: "",
  description: "",
  content: "",
  is_active: true,
});
const templatesLoading = ref(true);
const variablesLoading = ref(true);
const templateEditorLoading = ref(false);
const savingTemplate = ref(false);
const previewVisible = ref(false);
const contractsLoading = ref(true);
const contracts = ref<LegalContract[]>([]);
const verificationModalVisible = ref(false);
const verificationLoading = ref(false);
const verificationError = ref("");
const verificationDetail = ref<LegalContractVerificationDetail | null>(null);
const quillRef = ref<InstanceType<typeof QuillEditor> | null>(null);
const templatesCollapsed = ref(false);
const feedbackMessage = ref("");
const feedbackTone = ref<"success" | "error">("success");
let feedbackTimeout: number | null = null;
const signatureProfileLoaded = ref(false);
const signatureLoading = ref(false);
const signatureSaving = ref(false);
const signatureRemoving = ref(false);
const signatureForm = reactive({
  signature_type: "drawn" as "drawn" | "typed",
  signature_drawn_image: null as string | null,
  signature_typed_value: "",
  signature_font_style: "classic" as SignatureFontStyle,
  signature_display_name: "",
  signature_role: "",
  signature_company_name: "",
  signature_city: "",
});
const editorToolbar = [
  ["bold", "italic", "underline"],
  [{ list: "ordered" }, { list: "bullet" }],
  [{ align: [] }],
  ["link"],
  ["clean"],
];

const getQuillInstance = () => {
  const instance = quillRef.value;
  if (!instance || typeof instance.getQuill !== "function") {
    return null;
  }
  try {
    return instance.getQuill();
  } catch {
    return null;
  }
};

const insertSnippet = (snippet: string) => {
  const editor = getQuillInstance();
  if (!editor) {
    templateForm.content = `${templateForm.content || ""}${snippet}`;
    return;
  }
  const selection = editor.getSelection();
  const index = selection ? selection.index : editor.getLength();
  editor.insertText(index, snippet, "user");
  editor.setSelection(index + snippet.length, 0, "user");
  editor.focus();
};

const insertClauseSnippet = () => {
  insertSnippet("\nDO OBJETO\n\nDigite o conteúdo desta cláusula.\n\n");
};

const insertPassengersSnippet = () => {
  insertSnippet("\nDOS PASSAGEIROS\n\nParticiparão da viagem os seguintes passageiros:\n[[PASSAGEIROS]]\n\n");
};

const insertSignatureSnippet = () => {
  insertSnippet("\n[[ASSINATURAS]]\n");
};

const copy = {
  templates: {
    eyebrow: t({ pt: "Contratos", es: "Contratos" }),
    title: t({ pt: "Templates jurídicos", es: "Plantillas legales" }),
    description: t({
      pt: "Centralize seus contratos, personalize variáveis e publique com um clique.",
      es: "Centraliza tus contratos, personaliza variables y publícalos con un clic.",
    }),
    new: t({ pt: "Novo template", es: "Nueva plantilla" }),
    save: t({ pt: "Salvar alterações", es: "Guardar cambios" }),
    create: t({ pt: "Criar template", es: "Crear plantilla" }),
    loading: t({ pt: "Carregando templates...", es: "Cargando plantillas..." }),
    empty: t({
      pt: "Nenhum template cadastrado. Crie um template para automatizar seus contratos.",
      es: "No hay plantillas. Crea una para automatizar tus contratos.",
    }),
    hide: t({ pt: "Ocultar templates", es: "Ocultar plantillas" }),
    show: t({ pt: "Exibir templates", es: "Mostrar plantillas" }),
    active: t({ pt: "Ativo", es: "Activo" }),
    inactive: t({ pt: "Inativo", es: "Inactivo" }),
    edit: t({ pt: "Editar", es: "Editar" }),
    duplicate: t({ pt: "Duplicar", es: "Duplicar" }),
    delete: t({ pt: "Excluir", es: "Eliminar" }),
    noDescription: t({ pt: "Sem descrição", es: "Sin descripción" }),
  },
  editor: {
    eyebrow: t({ pt: "Editor", es: "Editor" }),
    new: t({ pt: "Novo template", es: "Nueva plantilla" }),
    editing: (name: string) =>
      t({ pt: "Editando {{name}}", es: "Editando {{name}}" }).replace("{{name}}", name),
    subtitle: t({ pt: "Edite o conteúdo e use as variáveis dinâmicas ao lado.", es: "Edita el contenido y usa las variables dinámicas al lado." }),
    loading: t({ pt: "Carregando template selecionado...", es: "Cargando plantilla seleccionada..." }),
    untitled: t({ pt: "Sem título", es: "Sin título" }),
  },
  quickInsert: {
    clause: t({ pt: "Inserir cláusula", es: "Insertar cláusula" }),
    passengers: t({ pt: "Inserir passageiros", es: "Insertar pasajeros" }),
    signatures: t({ pt: "Inserir assinaturas", es: "Insertar firmas" }),
    helper: t({
      pt: "Use os atalhos para adicionar seções rápidas. As cláusulas serão numeradas automaticamente no PDF.",
      es: "Usa los atajos para añadir secciones rápidas. Las cláusulas se numerarán automáticamente en el PDF.",
    }),
  },
  form: {
    name: t({ pt: "Nome do template", es: "Nombre de la plantilla" }),
    namePlaceholder: t({ pt: "Contrato padrão de viagens", es: "Contrato estándar de viajes" }),
    description: t({ pt: "Descrição", es: "Descripción" }),
    descriptionPlaceholder: t({ pt: "Resumo interno para identificar o template.", es: "Resumen interno para identificar la plantilla." }),
    content: t({ pt: "Conteúdo do contrato", es: "Contenido del contrato" }),
    contentHint: t({ pt: "Use {{variavel}} para inserir dados", es: "Usa {{variable}} para insertar datos" }),
    contentPlaceholder: t({
      pt: "Prezados {{nome_comprador}},\nSegue o contrato referente à venda #{{id_venda}}...",
      es: "Apreciado {{nome_comprador}},\nAdjunto contrato referente a la venta #{{id_venda}}...",
    }),
  },
  preview: {
    eyebrow: t({ pt: "Preview em tempo real", es: "Vista previa en tiempo real" }),
    title: t({ pt: "Contrato sem título", es: "Contrato sin título" }),
    close: t({ pt: "Fechar", es: "Cerrar" }),
  },
  contracts: {
    eyebrow: t({ pt: "Histórico", es: "Historial" }),
    title: t({ pt: "Contratos gerados", es: "Contratos generados" }),
    description: t({
      pt: "Todos os contratos emitidos automaticamente após a aprovação da venda.",
      es: "Todos los contratos emitidos automáticamente tras la aprobación de la venta.",
    }),
    refresh: t({ pt: "Atualizar lista", es: "Actualizar lista" }),
    loading: t({ pt: "Carregando contratos...", es: "Cargando contratos..." }),
    empty: t({
      pt: "Ainda não há contratos gerados. Assim que uma venda for concluída com template vinculado, você verá o PDF aqui.",
      es: "Aún no hay contratos generados. En cuanto se cierre una venta con plantilla vinculada, verás el PDF aquí.",
    }),
    buyer: t({ pt: "Comprador", es: "Comprador" }),
    product: t({ pt: "Produto", es: "Producto" }),
    amount: t({ pt: "Valor", es: "Valor" }),
    date: t({ pt: "Data", es: "Fecha" }),
    status: t({ pt: "Status", es: "Estado" }),
    signature: {
      column: t({ pt: "Assinatura", es: "Firma" }),
      pending: t({ pt: "Pendente", es: "Pendiente" }),
      signed: t({ pt: "Assinado", es: "Firmado" }),
      unavailable: t({
        pt: "Link será exibido assim que o contrato for gerado.",
        es: "El enlace aparecerá cuando el contrato se genere.",
      }),
      copy: t({ pt: "Copiar link", es: "Copiar enlace" }),
      open: t({ pt: "Abrir link", es: "Abrir enlace" }),
      copied: t({ pt: "Link copiado para a área de transferência.", es: "Enlace copiado al portapapeles." }),
      copyError: t({ pt: "Não foi possível copiar o link.", es: "No se pudo copiar el enlace." }),
      signedBy: t({ pt: "Assinado por", es: "Firmado por" }),
      signedAt: t({ pt: "Assinado em", es: "Firmado el" }),
      completed: t({
        pt: "Assinatura eletrônica registrada. Use o PDF assinado para consultas.",
        es: "Firma electrónica registrada. Use el PDF firmado para consultas.",
      }),
    },
    verification: {
      column: t({ pt: "Verificação", es: "Verificación" }),
      view: t({ pt: "Ver detalhes", es: "Ver detalles" }),
      open: t({ pt: "Abrir página pública", es: "Abrir página pública" }),
      copy: t({ pt: "Copiar link", es: "Copiar enlace" }),
      copied: t({ pt: "Link de verificação copiado.", es: "Enlace de verificación copiado." }),
      copyError: t({ pt: "Não foi possível copiar o link de verificação.", es: "No se pudo copiar el enlace de verificación." }),
      regenerate: t({ pt: "Reprocessar verificação", es: "Reprocesar verificación" }),
      loading: t({ pt: "Carregando verificação...", es: "Cargando verificación..." }),
      unavailable: t({
        pt: "Disponível após a assinatura eletrônica.",
        es: "Disponible tras la firma electrónica.",
      }),
      refreshed: t({ pt: "Verificação atualizada com sucesso.", es: "Verificación actualizada con éxito." }),
      error: t({ pt: "Não foi possível carregar os detalhes.", es: "No se pudieron cargar los detalles." }),
      status: {
        valid: t({ pt: "Verificado", es: "Verificado" }),
        pending: t({ pt: "Aguardando assinatura", es: "Esperando firma" }),
        incomplete: t({ pt: "Processando", es: "Procesando" }),
        invalid: t({ pt: "Indisponível", es: "No disponible" }),
      },
      modalEyebrow: t({ pt: "Prova de integridade", es: "Prueba de integridad" }),
      modalTitle: t({ pt: "Verificação do contrato", es: "Verificación del contrato" }),
      modalHelper: t({
        pt: "Compartilhe o QR code ou link para que qualquer pessoa valide o documento.",
        es: "Comparte el QR o el enlace para que cualquiera valide el documento.",
      }),
    },
    actions: t({ pt: "Ações", es: "Acciones" }),
    view: t({ pt: "Visualizar", es: "Ver" }),
    download: t({ pt: "Baixar", es: "Descargar" }),
    signedView: t({ pt: "Ver assinado", es: "Ver firmado" }),
    signedDownload: t({ pt: "Baixar assinado", es: "Descargar firmado" }),
    originalView: t({ pt: "Ver original", es: "Ver original" }),
    noName: t({ pt: "Sem nome", es: "Sin nombre" }),
  },
  signature: {
    eyebrow: t({ pt: "Assinatura institucional", es: "Firma institucional" }),
    title: t({ pt: "Configure a assinatura da sua agência", es: "Configura la firma de tu agencia" }),
    description: t({
      pt: "Esta assinatura será aplicada automaticamente aos contratos emitidos. O cliente final assina apenas a parte dele.",
      es: "Esta firma se aplicará automáticamente a los contratos emitidos. El cliente firma solo su parte.",
    }),
    typeLabel: t({ pt: "Tipo de assinatura", es: "Tipo de firma" }),
    drawn: t({ pt: "Desenhada", es: "Dibujada" }),
    typed: t({ pt: "Escrita", es: "Escrita" }),
    displayName: t({ pt: "Nome do responsável", es: "Nombre del responsable" }),
    role: t({ pt: "Cargo/Função", es: "Cargo/Función" }),
    company: t({ pt: "Nome da agência", es: "Nombre de la agencia" }),
    city: t({ pt: "Cidade padrão (opcional)", es: "Ciudad (opcional)" }),
    typedValue: t({ pt: "Texto da assinatura", es: "Texto de la firma" }),
    fontStyle: t({ pt: "Estilo visual", es: "Estilo visual" }),
    helper: t({
      pt: "Atualize a assinatura quando necessário. Ela representará a contratada em todos os contratos.",
      es: "Actualiza la firma cuando sea necesario. Representará a la contratada en todos los contratos.",
    }),
    save: t({ pt: "Salvar assinatura", es: "Guardar firma" }),
    remove: t({ pt: "Remover assinatura", es: "Eliminar firma" }),
    previewName: t({ pt: "Nome da contratada", es: "Nombre de la contratada" }),
    previewRole: t({ pt: "Cargo/função", es: "Cargo/función" }),
    previewCompany: t({ pt: "Sua agência", es: "Tu agencia" }),
    info: t({
      pt: "Esta assinatura será aplicada automaticamente aos contratos gerados.",
      es: "Esta firma se aplicará automáticamente a los contratos generados.",
    }),
    styles: {
      classic: t({ pt: "Clássico", es: "Clásico" }),
      cursive: t({ pt: "Cursivo leve", es: "Cursivo suave" }),
      elegant: t({ pt: "Elegante", es: "Elegante" }),
    },
    drawnHelper: t({
      pt: "Use mouse ou toque para desenhar. Clique em “Atualizar preview” para visualizar.",
      es: "Usa el mouse o el tacto para dibujar. Haz clic en “Actualizar vista previa” para visualizar.",
    }),
    typedHelper: t({
      pt: "O texto digitado será renderizado com estilo profissional direto no PDF.",
      es: "El texto digitado se mostrará con estilo profesional directamente en el PDF.",
    }),
    removeConfirm: t({
      pt: "Remover a assinatura institucional? Os próximos contratos voltarão a exigir a assinatura manual da agência.",
      es: "¿Eliminar la firma institucional? Los próximos contratos volverán a requerir la firma manual de la agencia.",
    }),
  },
};

const statusLabels: Record<string, string> = {
  pending: t({ pt: "Em processamento", es: "En proceso" }),
  generated: t({ pt: "Disponível", es: "Disponible" }),
  failed: t({ pt: "Falhou", es: "Falló" }),
};

const signatureStatusLabels: Record<string, string> = {
  pending: copy.contracts.signature.pending,
  signed: copy.contracts.signature.signed,
};

const verificationStatusLabels: Record<LegalContractVerificationStatus, string> = {
  valid: copy.contracts.verification.status.valid,
  pending: copy.contracts.verification.status.pending,
  incomplete: copy.contracts.verification.status.incomplete,
  invalid: copy.contracts.verification.status.invalid,
  not_found: copy.contracts.verification.status.invalid,
};

const contractVerificationStatus = (contract: LegalContract): LegalContractVerificationStatus => {
  if (contract.signature_status !== "signed") {
    return "pending";
  }
  if (!contract.signed_pdf_url || !contract.document_hash) {
    return "incomplete";
  }
  return "valid";
};

const verificationStatusLabel = (status: LegalContractVerificationStatus) => verificationStatusLabels[status];

const variableRegex = /\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g;

const canSaveTemplate = computed(() => templateForm.name.trim().length > 0 && templateForm.content.trim().length > 0);
const feedbackToneClass = computed(() =>
  feedbackTone.value === "success"
    ? "bg-emerald-50 text-emerald-700"
    : "bg-rose-50 text-rose-600"
);

const sampleValues = computed<Record<string, string>>(() => {
  const values: Record<string, string> = {};
  templateVariables.value.forEach(category => {
    category.variables.forEach(variable => {
      values[variable.key] = variable.sample_value;
    });
  });
  return values;
});

const previewHtml = computed(() => {
  const raw = replaceVariables(templateForm.content || "<p></p>", sampleValues.value);
  return DOMPurify.sanitize(`<div class="leading-7 text-slate-800">${raw}</div>`);
});
const signaturePreviewName = computed(() => signatureForm.signature_display_name.trim() || copy.signature.previewName);
const signaturePreviewRole = computed(() => signatureForm.signature_role?.trim() || copy.signature.previewRole);
const signaturePreviewCompany = computed(() => signatureForm.signature_company_name?.trim() || copy.signature.previewCompany);
const signaturePreviewCity = computed(() => signatureForm.signature_city?.trim() || "");
const signatureTypedClass = computed(() => {
  const style = signatureForm.signature_font_style || "classic";
  return `signature-preview__typed signature-preview__typed--${style}`;
});
const canSaveSignatureProfile = computed(() => {
  if (!signatureForm.signature_display_name.trim()) return false;
  if (signatureForm.signature_type === "drawn") {
    return !!signatureForm.signature_drawn_image;
  }
  return (signatureForm.signature_typed_value || "").trim().length >= 2;
});

const setFeedback = (message: string, tone: "success" | "error" = "success") => {
  feedbackMessage.value = message;
  feedbackTone.value = tone;
  if (feedbackTimeout) {
    window.clearTimeout(feedbackTimeout);
  }
  feedbackTimeout = window.setTimeout(() => {
    feedbackMessage.value = "";
  }, 3500);
};

const resetSignatureForm = () => {
  signatureForm.signature_type = "drawn";
  signatureForm.signature_drawn_image = null;
  signatureForm.signature_typed_value = "";
  signatureForm.signature_font_style = "classic";
  signatureForm.signature_display_name = "";
  signatureForm.signature_role = "";
  signatureForm.signature_company_name = "";
  signatureForm.signature_city = "";
};

const applySignatureProfile = (profile: LegalSignatureProfile) => {
  signatureForm.signature_type = profile.signature_type as "drawn" | "typed";
  signatureForm.signature_display_name = profile.signature_display_name || "";
  signatureForm.signature_role = profile.signature_role || "";
  signatureForm.signature_company_name = profile.signature_company_name || "";
  signatureForm.signature_city = profile.signature_city || "";
  if (profile.signature_type === "drawn") {
    signatureForm.signature_drawn_image = profile.signature_drawn_image_data || profile.signature_drawn_image_url || null;
    signatureForm.signature_typed_value = "";
  } else {
    signatureForm.signature_typed_value = profile.signature_typed_value || "";
    signatureForm.signature_drawn_image = null;
    signatureForm.signature_font_style = (profile.signature_font_style as SignatureFontStyle) || "classic";
  }
};

const loadSignatureProfile = async () => {
  signatureLoading.value = true;
  try {
    const { data } = await getLegalSignatureProfile();
    if (data) {
      applySignatureProfile(data);
    } else {
      resetSignatureForm();
    }
    signatureProfileLoaded.value = !!data;
  } catch (error) {
    console.error("Erro ao carregar assinatura institucional", error);
    setFeedback("Não foi possível carregar a assinatura.", "error");
  } finally {
    signatureLoading.value = false;
  }
};

const buildSignaturePayload = () => {
  const payload: LegalSignatureProfilePayload = {
    signature_type: signatureForm.signature_type,
    signature_display_name: signatureForm.signature_display_name.trim(),
    signature_role: signatureForm.signature_role?.trim() || null,
    signature_company_name: signatureForm.signature_company_name?.trim() || null,
    signature_city: signatureForm.signature_city?.trim() || null,
    signature_drawn_image: null,
    signature_typed_value: null,
    signature_font_style: null,
  };
  if (signatureForm.signature_type === "drawn") {
    payload.signature_drawn_image = signatureForm.signature_drawn_image;
  } else {
    payload.signature_typed_value = signatureForm.signature_typed_value?.trim() || "";
    payload.signature_font_style = signatureForm.signature_font_style;
  }
  return payload;
};

const persistSignatureProfile = async () => {
  if (signatureSaving.value) return;
  signatureSaving.value = true;
  try {
    const payload = buildSignaturePayload();
    const { data } = await saveLegalSignatureProfile(payload);
    applySignatureProfile(data);
    signatureProfileLoaded.value = true;
    setFeedback("Assinatura salva com sucesso.");
  } catch (error) {
    console.error("Erro ao salvar assinatura institucional", error);
    setFeedback("Não foi possível salvar a assinatura.", "error");
  } finally {
    signatureSaving.value = false;
  }
};

const removeSignatureProfile = async () => {
  if (signatureRemoving.value) return;
  if (!signatureProfileLoaded.value) {
    resetSignatureForm();
    return;
  }
  if (typeof window !== "undefined" && !window.confirm(copy.signature.removeConfirm)) {
    return;
  }
  signatureRemoving.value = true;
  try {
    await deleteLegalSignatureProfile();
    resetSignatureForm();
    signatureProfileLoaded.value = false;
    setFeedback("Assinatura removida.");
  } catch (error) {
    console.error("Erro ao remover assinatura institucional", error);
    setFeedback("Não foi possível remover a assinatura.", "error");
  } finally {
    signatureRemoving.value = false;
  }
};

const loadTemplates = async () => {
  templatesLoading.value = true;
  try {
    const { data } = await listLegalTemplates();
    templates.value = data.items;
    if (templates.value.length && !templateForm.id) {
      await selectTemplate(templates.value[0].id);
    }
    if (templateForm.id && !templates.value.find(item => item.id === templateForm.id)) {
      startNewTemplate();
    }
  } catch (error) {
    console.error("Erro ao carregar templates", error);
    setFeedback(t({ pt: "Não foi possível carregar os templates.", es: "No se pudo cargar las plantillas." }), "error");
  } finally {
    templatesLoading.value = false;
  }
};

const selectTemplate = async (templateId: number) => {
  templateEditorLoading.value = true;
  try {
    const { data } = await getLegalTemplateDetail(templateId);
    fillTemplateForm(data);
  } catch (error) {
    console.error("Erro ao buscar template", error);
    setFeedback(t({ pt: "Não foi possível abrir o template.", es: "No se pudo abrir la plantilla." }), "error");
  } finally {
    templateEditorLoading.value = false;
  }
};

const fillTemplateForm = (template: LegalTemplateDetail) => {
  templateForm.id = template.id;
  templateForm.name = template.name;
  templateForm.description = template.description || "";
  templateForm.is_active = template.is_active;
  templateForm.content = template.content || "";
};

const startNewTemplate = () => {
  templateForm.id = null;
  templateForm.name = "";
  templateForm.description = "";
  templateForm.content = "";
  templateForm.is_active = true;
};

const persistTemplate = async () => {
  if (!canSaveTemplate.value) {
    setFeedback(
      t({ pt: "Informe um nome e adicione o conteúdo do contrato.", es: "Indique un nombre y añade el contenido del contrato." }),
      "error"
    );
    return;
  }
  savingTemplate.value = true;
  const payload: LegalTemplatePayload = {
    name: templateForm.name.trim(),
    description: templateForm.description?.trim() || null,
    content: templateForm.content,
    is_active: templateForm.is_active,
  };
  try {
    let response;
    if (templateForm.id) {
      response = await updateLegalTemplate(templateForm.id, payload);
      setFeedback(t({ pt: "Template atualizado com sucesso.", es: "Plantilla actualizada con éxito." }));
    } else {
      response = await createLegalTemplate(payload);
      setFeedback(t({ pt: "Template criado com sucesso.", es: "Plantilla creada con éxito." }));
    }
    fillTemplateForm(response.data);
    await loadTemplates();
  } catch (error) {
    console.error("Erro ao salvar template", error);
    setFeedback(t({ pt: "Falha ao salvar o template.", es: "Error al guardar la plantilla." }), "error");
  } finally {
    savingTemplate.value = false;
  }
};

const removeTemplate = async (template: LegalTemplateSummary) => {
  const confirmed = window.confirm(
    t({ pt: `Deseja excluir "${template.name}"?`, es: `¿Desea eliminar "${template.name}"?` })
  );
  if (!confirmed) return;
  try {
    await deleteLegalTemplate(template.id);
    setFeedback(t({ pt: "Template excluído.", es: "Plantilla eliminada." }));
    if (templateForm.id === template.id) {
      startNewTemplate();
    }
    await loadTemplates();
  } catch (error) {
    console.error("Erro ao excluir template", error);
    setFeedback(t({ pt: "Não foi possível excluir o template.", es: "No se pudo eliminar la plantilla." }), "error");
  }
};

const duplicateTemplate = async (template: LegalTemplateSummary) => {
  try {
    const { data } = await getLegalTemplateDetail(template.id);
    const payload: LegalTemplatePayload = {
      name: `${data.name} (cópia)`,
      description: data.description || null,
      content: data.content,
      is_active: data.is_active,
    };
    const response = await createLegalTemplate(payload);
    setFeedback(t({ pt: "Template duplicado com sucesso.", es: "Plantilla duplicada con éxito." }));
    await loadTemplates();
    fillTemplateForm(response.data);
  } catch (error) {
    console.error("Erro ao duplicar template", error);
    setFeedback(t({ pt: "Não foi possível duplicar o template.", es: "No se pudo duplicar la plantilla." }), "error");
  }
};

const loadVariables = async () => {
  variablesLoading.value = true;
  try {
    const { data } = await getLegalVariables();
    templateVariables.value = data.categories;
  } catch (error) {
    console.error("Erro ao carregar variáveis", error);
    templateVariables.value = [];
  } finally {
    variablesLoading.value = false;
  }
};

const loadContracts = async () => {
  contractsLoading.value = true;
  try {
    const { data } = await listLegalContracts();
    contracts.value = data.items;
  } catch (error) {
    console.error("Erro ao carregar contratos", error);
    contracts.value = [];
  } finally {
    contractsLoading.value = false;
  }
};

const insertVariable = (placeholder: string) => {
  const editor = getQuillInstance();
  if (!editor) {
    templateForm.content = `${templateForm.content || ""}${placeholder} `;
    return;
  }
  const selection = editor.getSelection();
  const index = selection ? selection.index : editor.getLength();
  editor.insertText(index, placeholder, "user");
  editor.setSelection(index + placeholder.length, 0, "user");
  editor.focus();
};

const openPreview = () => {
  previewVisible.value = true;
};

const closePreview = () => {
  previewVisible.value = false;
};

const replaceVariables = (content: string, values: Record<string, string>) =>
  content.replace(variableRegex, (_, key: string) => values[key.trim()] ?? `{{${key.trim()}}}`);

const contractStatusLabel = (status: string) => statusLabels[status] || status;

const signatureStatusLabel = (status: string) => signatureStatusLabels[status] || status;

const statusBadgeClass = (status: string) => {
  if (status === "generated") return "badge-success";
  if (status === "failed") return "badge-danger";
  return "badge-muted";
};

const signatureBadgeClass = (status: string) => {
  if (status === "signed") return "badge-success";
  return "badge-muted";
};

const verificationBadgeClass = (status: LegalContractVerificationStatus) => {
  if (status === "valid") return "badge-success";
  if (status === "invalid") return "badge-danger";
  return "badge-muted";
};

const viewContractPdf = (url?: string | null) => {
  if (!url) return;
  window.open(url, "_blank");
};

const downloadContractPdf = (url?: string | null) => {
  if (!url) return;
  const link = document.createElement("a");
  link.href = url;
  link.download = url.split("/").pop() || "contrato.pdf";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const copySignatureLink = async (contract: LegalContract) => {
  if (!contract.signature_link) {
    setFeedback(copy.contracts.signature.unavailable, "error");
    return;
  }
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(contract.signature_link);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = contract.signature_link;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    setFeedback(copy.contracts.signature.copied, "success");
  } catch (error) {
    console.error("Erro ao copiar link de assinatura", error);
    setFeedback(copy.contracts.signature.copyError, "error");
  }
};

const copyVerificationLink = async (contract: LegalContract) => {
  if (!contract.verification_url) {
    setFeedback(copy.contracts.verification.unavailable, "error");
    return;
  }
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(contract.verification_url);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = contract.verification_url;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    setFeedback(copy.contracts.verification.copied, "success");
  } catch (error) {
    console.error("Erro ao copiar link de verificação", error);
    setFeedback(copy.contracts.verification.copyError, "error");
  }
};

const openVerificationLink = (contract: LegalContract) => {
  if (!contract.verification_url) {
    setFeedback(copy.contracts.verification.unavailable, "error");
    return;
  }
  window.open(contract.verification_url, "_blank");
};

const syncContractVerificationSnapshot = (payload: LegalContractVerificationDetail) => {
  if (!payload.contract_id) return;
  const target = contracts.value.find(contract => contract.id === payload.contract_id);
  if (!target) return;
  target.document_hash = payload.document_hash ?? null;
  target.document_hash_algorithm = payload.document_hash_algorithm ?? target.document_hash_algorithm;
  target.verification_url = payload.verification_url ?? target.verification_url;
  target.verification_qr_image_data = payload.verification_qr_image_data ?? target.verification_qr_image_data;
  target.verification_generated_at = payload.verification_generated_at ?? target.verification_generated_at;
  target.signed_pdf_url = payload.signed_pdf_url ?? target.signed_pdf_url;
  target.signed_pdf_generated_at = payload.signed_pdf_generated_at ?? target.signed_pdf_generated_at;
  target.signed_pdf_size_bytes = payload.signed_pdf_size_bytes ?? target.signed_pdf_size_bytes;
};

const openVerificationModal = async (contract: LegalContract) => {
  verificationModalVisible.value = true;
  verificationLoading.value = true;
  verificationError.value = "";
  verificationDetail.value = null;
  try {
    const { data } = await getLegalContractVerification(contract.id);
    verificationDetail.value = data;
    syncContractVerificationSnapshot(data);
  } catch (error) {
    console.error("Erro ao carregar verificação do contrato", error);
    verificationError.value = copy.contracts.verification.error;
  } finally {
    verificationLoading.value = false;
  }
};

const closeVerificationModal = () => {
  verificationModalVisible.value = false;
  verificationDetail.value = null;
  verificationError.value = "";
};

const regenerateVerification = async () => {
  if (!verificationDetail.value?.contract_id) return;
  verificationLoading.value = true;
  verificationError.value = "";
  try {
    const { data } = await regenerateLegalContractVerification(verificationDetail.value.contract_id);
    verificationDetail.value = data;
    syncContractVerificationSnapshot(data);
    setFeedback(copy.contracts.verification.refreshed);
  } catch (error) {
    console.error("Erro ao regenerar verificação", error);
    verificationError.value = copy.contracts.verification.error;
    setFeedback(copy.contracts.verification.error, "error");
  } finally {
    verificationLoading.value = false;
  }
};

const copyVerificationDetailLink = async () => {
  if (!verificationDetail.value?.verification_url) {
    setFeedback(copy.contracts.verification.unavailable, "error");
    return;
  }
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(verificationDetail.value.verification_url);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = verificationDetail.value.verification_url;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    setFeedback(copy.contracts.verification.copied, "success");
  } catch (error) {
    console.error("Erro ao copiar link de verificação", error);
    setFeedback(copy.contracts.verification.copyError, "error");
  }
};

const openVerificationDetailLink = () => {
  if (!verificationDetail.value?.verification_url) {
    setFeedback(copy.contracts.verification.unavailable, "error");
    return;
  }
  window.open(verificationDetail.value.verification_url, "_blank");
};

const openSignatureLink = (contract: LegalContract) => {
  if (!contract.signature_link) return;
  window.open(contract.signature_link, "_blank");
};

const formatCurrency = (amountCents: number, currency: string) => {
  const amount = amountCents / 100;
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: currency || "BRL",
    minimumFractionDigits: 2,
  }).format(amount);
};

const formatShortDate = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-BR");
};

const formatShortDateTime = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const day = date.toLocaleDateString("pt-BR");
  const time = date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${day} ${time}`;
};

watch(
  () => activeTab.value,
  value => {
    if (value === "contracts" && !contracts.value.length) {
      loadContracts();
    }
    if (value === "signature" && !signatureProfileLoaded.value) {
      loadSignatureProfile();
    }
  }
);

onMounted(async () => {
  await Promise.all([loadTemplates(), loadVariables()]);
});
</script>

<style scoped>
.btn-primary {
  @apply rounded-full bg-emerald-500 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:-translate-y-0.5 disabled:bg-emerald-300;
}
.btn-secondary {
  @apply rounded-full border border-slate-200 bg-white px-5 py-2 text-sm font-semibold text-slate-600 shadow-sm transition hover:border-emerald-400 hover:text-emerald-600 disabled:bg-slate-100 disabled:text-slate-400;
}
.pill {
  @apply rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-emerald-400 hover:text-emerald-600 disabled:border-slate-100 disabled:text-slate-400;
}
.pill--ghost {
  @apply bg-white text-emerald-600;
}
.input {
  @apply w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none;
}
.input-label {
  @apply mb-1 block text-xs font-semibold uppercase tracking-[0.3em] text-slate-400;
}

:deep(.rich-editor) {
  display: flex;
  flex-direction: column;
  height: 280px; /* altura fixa */
}

:deep(.rich-editor .ql-toolbar.ql-snow) {
  @apply rounded-t-2xl border border-slate-200;
}

:deep(.rich-editor .ql-container.ql-snow) {
  @apply border border-slate-200 bg-white rounded-b-2xl;
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.rich-editor .ql-editor) {
  flex: 1;
  overflow-y: auto;
  font-size: 0.95rem;
}
.badge-success {
  @apply rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700;
}
.badge-muted {
  @apply rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500;
}
.badge-danger {
  @apply rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700;
}
.placeholder-card {
  @apply rounded-3xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500;
}
.modal-overlay {
  @apply fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4;
}
.modal-card {
  @apply w-full rounded-3xl bg-white p-6 shadow-2xl;
}
.modal-card--preview {
  width: min(900px, 95vw);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
.preview-content {
  @apply mt-4 flex-1 overflow-y-auto rounded-2xl border border-slate-100 bg-slate-50 p-4;
}
.custom-scroll {
  scrollbar-width: thin;
  scrollbar-color: #94a3b8 transparent;
}
.custom-scroll::-webkit-scrollbar {
  width: 6px;
}
.custom-scroll::-webkit-scrollbar-thumb {
  background-color: #94a3b8;
  border-radius: 9999px;
}
.editor-actions {
  @apply flex flex-wrap justify-end gap-2;
}
.editor-action {
  @apply rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 transition hover:-translate-y-0.5 hover:border-emerald-300 hover:bg-white;
}
.collapse-toggle {
  @apply text-xs font-semibold text-slate-500 underline-offset-4 hover:text-slate-900;
}
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
.pill--active {
  @apply border border-emerald-400 bg-emerald-50 text-emerald-700;
}
.signature-preview-card {
  @apply rounded-3xl border border-slate-100 bg-white p-5 shadow-sm;
}
.signature-preview-visual {
  @apply mt-2 flex items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4;
  min-height: 160px;
}
.signature-preview-image {
  max-width: 240px;
  max-height: 70px;
}
.signature-preview__typed {
  font-size: 22px;
  margin: 0;
}
.signature-preview__typed--classic {
  font-family: "Times New Roman", serif;
  font-style: italic;
}
.signature-preview__typed--cursive {
  font-family: "Georgia", serif;
  font-style: italic;
}
.signature-preview__typed--elegant {
  font-family: "Arial", sans-serif;
  font-weight: 600;
  letter-spacing: 0.2em;
}
.signature-preview-name {
  @apply mt-4 text-lg font-semibold text-slate-900 text-center;
}
.signature-preview-role {
  @apply text-xs font-semibold uppercase tracking-[0.3em] text-slate-400 text-center;
}
.hash-box {
  @apply mt-1 rounded-2xl bg-slate-900/80 p-3 font-mono text-xs text-emerald-100;
  word-break: break-all;
}
.value {
  @apply mt-1 text-base font-semibold text-slate-900;
}
.signature-preview-company,
.signature-preview-city {
  @apply text-xs text-slate-500 text-center;
}
.signature-preview-badge {
  @apply mt-3 text-[10px] uppercase tracking-[0.3em] text-emerald-600 text-center;
}
</style>
