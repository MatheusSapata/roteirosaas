<template>
  <div v-if="isBootstrappingAdminManagement" class="am-empty min-h-[60vh]">
    <div class="am-spinner"></div>
  </div>
  <div v-else class="admin-master-view admin-master-surface am-page w-full">
    <div v-if="error" class="am-notice am-tone-danger">
      <AmIcon name="alert" />
      <span>{{ error }}</span>
    </div>

    <!-- PAINEL -->
    <template v-if="activeTab === 'dashboard'">
      <DashboardPanel />
    </template>

    <!-- AO VIVO -->
    <template v-else-if="activeTab === 'monitor'">
      <AdminMasterHeader title="Ao vivo" subtitle="Quem está usando o sistema agora (sessões ativas nos últimos 10 minutos).">
        <span v-if="monitorLastUpdated" class="am-sub !mt-0">Atualizado às {{ monitorLastUpdated }}</span>
        <button type="button" class="am-btn" :disabled="onlineSessionsLoading" @click="loadOnlineSessions(true)">
          <AmIcon name="refresh" :class="onlineSessionsLoading ? 'animate-spin' : ''" />
          {{ onlineSessionsLoading ? "Atualizando..." : "Atualizar" }}
        </button>
      </AdminMasterHeader>

      <section class="am-grid-4">
        <AdminMasterKpi icon="pulse" tone="success" label="Online agora" :value="formatInt(onlineSessionsMeta?.unique_users ?? 0)" :hint="`${formatInt(onlineSessionsMeta?.total_online ?? 0)} sessões abertas`" />
        <AdminMasterKpi icon="monitor" tone="info" label="No computador" :value="formatInt(monitorDeviceSplit.desktop)" :hint="`${formatInt(monitorDeviceSplit.mobile)} no celular`" />
        <AdminMasterKpi icon="pages" tone="violet" label="No editor de página" :value="formatInt(monitorInEditor)" hint="Editando uma página agora" />
        <AdminMasterKpi icon="history" tone="neutral" label="Monitor" :value="monitorStatusLabel" hint="Atualiza sozinho a cada 20 segundos" />
      </section>

      <section class="am-card am-card-flush">
        <div v-if="onlineSessionsLoading && !onlineSessions.length" class="am-empty">
          <div class="am-spinner"></div>
          Carregando sessões ativas...
        </div>
        <div v-else-if="onlineSessionsError" class="am-empty !text-status-danger-foreground">{{ onlineSessionsError }}</div>
        <div v-else-if="!onlineSessions.length" class="am-empty">Ninguém está online neste momento.</div>
        <div v-else class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Pessoa</th>
                <th>Plano</th>
                <th>Onde está</th>
                <th>Dispositivo</th>
                <th>Última ação</th>
                <th>Na sessão</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in onlineSessions" :key="session.session_id">
                <td>
                  <div class="am-who">
                    <span class="am-avatar relative">
                      {{ initials(session.user_name) }}
                      <i class="absolute -bottom-px -right-px h-2.5 w-2.5 rounded-full border-2 border-card bg-status-success-foreground"></i>
                    </span>
                    <div class="min-w-0">
                      <b class="truncate">{{ session.user_name }}</b>
                      <small class="truncate">{{ session.user_email }}</small>
                    </div>
                  </div>
                </td>
                <td><span class="am-badge" :class="planToneClass(session.user_plan)">{{ planLabel(session.user_plan) }}</span></td>
                <td>
                  <b class="font-semibold">{{ pathLabel(session.last_path) }}</b>
                  <div v-if="session.last_path" class="am-mono am-muted max-w-[260px] truncate">{{ session.last_path }}</div>
                </td>
                <td>
                  {{ session.device_label || "Desconhecido" }}<span v-if="session.client_name"> · {{ session.client_name }}</span>
                  <span v-if="session.active_sessions > 1" class="am-badge am-tone-neutral ml-1">{{ session.active_sessions }} sessões</span>
                  <div v-if="session.ip_address" class="am-mono am-muted">{{ session.ip_address }}</div>
                </td>
                <td class="am-num">{{ formatRelativeMoment(session.last_seen_at) }}</td>
                <td class="am-num">{{ formatDurationSince(session.created_at) }}</td>
                <td class="am-right">
                  <button
                    type="button"
                    class="am-btn am-btn-sm"
                    :disabled="revokingUserId === session.user_id"
                    @click="revokeUserSessions(session)"
                  >
                    <AmIcon name="logout" />
                    {{ revokingUserId === session.user_id ? "Deslogando..." : "Deslogar" }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>


    <!-- USUÁRIOS -->
    <template v-else-if="activeTab === 'users'">
      <UsersPanel />
    </template>

    <!-- LESSONS -->
    <template v-else-if="activeTab === 'lessons'">
      <AdminMasterHeader title="Aulas" subtitle="As aulas aparecem para todas as agências em Aprender › Aulas.">
        <button type="button" class="am-btn" :disabled="resettingLessons" @click="handleResetLessons"><AmIcon name="undo" />Restaurar padrão</button>
        <button type="button" class="am-btn am-btn-primary" @click="openNewLesson()"><AmIcon name="plus" />Nova aula</button>
      </AdminMasterHeader>

      <section class="am-grid-3">
        <AdminMasterKpi icon="video" tone="success" label="Aulas publicadas" :value="formatInt(adminLessons.length)" :hint="`em ${formatInt(lessonGroups.length)} ${lessonGroups.length === 1 ? 'módulo' : 'módulos'}`" />
        <AdminMasterKpi icon="layout" tone="info" label="Com capa" :value="formatInt(adminLessons.filter(lesson => lesson.thumbnail).length)" hint="As outras usam a capa do vídeo" />
        <AdminMasterKpi icon="play" tone="violet" label="Vídeos do YouTube" :value="formatInt(adminLessons.filter(lesson => lesson.videoType !== 'file').length)" :hint="`${formatInt(adminLessons.filter(lesson => lesson.videoType === 'file').length)} por arquivo ou link direto`" />
      </section>

      <div v-if="lessonsLoading" class="am-card am-empty"><div class="am-spinner"></div>Carregando aulas...</div>
      <div v-else-if="!adminLessons.length" class="am-card am-empty">
        Nenhuma aula cadastrada ainda.
        <button type="button" class="am-btn am-btn-primary" @click="openNewLesson()"><AmIcon name="plus" />Nova aula</button>
      </div>
      <template v-else>
        <section v-for="group in lessonGroups" :key="group.key" class="am-card am-card-flush">
          <div class="am-toolbar justify-between">
            <div>
              <h2 class="am-card-title">{{ group.label }}</h2>
              <p class="am-card-sub">{{ group.lessons.length }} {{ group.lessons.length === 1 ? "aula" : "aulas" }} · use as setas para ordenar</p>
            </div>
            <button type="button" class="am-btn am-btn-sm" @click="openNewLesson(group.key === '__default__' ? '' : group.label)"><AmIcon name="plus" />Aula neste módulo</button>
          </div>
          <div class="am-list">
            <div v-for="(lesson, index) in group.lessons" :key="lesson.id" class="flex flex-wrap items-center gap-3 px-3.5 py-2.5">
              <div class="flex flex-col">
                <button type="button" class="am-icon-btn !h-6 !w-6" :disabled="index === 0 || lessonSaving" :aria-label="`Subir ${lesson.title}`" @click="moveLessonInGroup(group, index, -1)">
                  <AmIcon name="chevron" class="rotate-180" />
                </button>
                <button type="button" class="am-icon-btn !h-6 !w-6" :disabled="index === group.lessons.length - 1 || lessonSaving" :aria-label="`Descer ${lesson.title}`" @click="moveLessonInGroup(group, index, 1)">
                  <AmIcon name="chevron" />
                </button>
              </div>
              <div class="lesson-thumb">
                <img v-if="lesson.thumbnail" :src="lesson.thumbnail" alt="" class="h-full w-full object-cover" />
                <AmIcon v-else name="play" />
              </div>
              <div class="min-w-[180px] flex-1">
                <b class="block font-semibold">{{ lesson.title }}</b>
                <p class="am-card-sub !mt-0">
                  {{ lesson.videoType === "file" ? "Arquivo ou link direto" : "YouTube" }}<template v-if="lesson.level"> · {{ lesson.level }}</template><template v-if="lesson.duration"> · {{ lesson.duration }}</template>
                </p>
                <p v-if="lessonReplacement(lesson)" class="am-card-sub !mt-0.5">
                  <span class="am-badge am-tone-warning mr-1">Desatualizada</span>
                  As agências veem o artigo “{{ lessonReplacement(lesson)!.titulo }}”, revisado em {{ formatHelpDate(lessonReplacement(lesson)!.atualizado) }}. Grave um vídeo novo para voltar a mostrar a aula.
                </p>
              </div>
              <button type="button" class="am-btn am-btn-sm" @click="openLessonEdit(lesson)"><AmIcon name="edit" />Editar</button>
              <button type="button" class="am-icon-btn" :disabled="deletingLessonId === lesson.id" :aria-label="`Excluir ${lesson.title}`" @click="deleteLesson(lesson.id)">
                <AmIcon name="trash" />
              </button>
            </div>
          </div>
        </section>
      </template>

      <AdminMasterDrawer
        :open="lessonDrawerOpen"
        :title="isEditingLesson ? 'Editar aula' : 'Nova aula'"
        subtitle="Título, descrição e o link ou iframe do vídeo."
        icon="video"
        :width="600"
        @close="closeLessonDrawer"
      >
        <form id="lesson-form" class="space-y-3.5" @submit.prevent="saveLesson">
          <div class="am-field">
            <label for="ls-title">Título</label>
            <input id="ls-title" v-model="lessonForm.title" type="text" class="am-input" placeholder="Ex.: Dominando o editor" required />
          </div>
          <div class="am-field">
            <label for="ls-desc">Descrição</label>
            <textarea id="ls-desc" v-model="lessonForm.description" rows="3" class="am-input" placeholder="O que a pessoa aprende nessa aula"></textarea>
          </div>
          <div class="grid gap-3.5 sm:grid-cols-3">
            <div class="am-field">
              <label for="ls-module">Módulo</label>
              <input id="ls-module" v-model="lessonForm.moduleName" type="text" list="lesson-module-options" class="am-input" placeholder="Ex.: Primeiros passos" />
              <datalist id="lesson-module-options">
                <option v-for="module in lessonModuleOptions" :key="module" :value="module"></option>
              </datalist>
            </div>
            <div class="am-field">
              <label for="ls-duration">Duração</label>
              <input id="ls-duration" v-model="lessonForm.duration" type="text" class="am-input" placeholder="Ex.: 10:45" />
            </div>
            <div class="am-field">
              <label for="ls-level">Nível</label>
              <input id="ls-level" v-model="lessonForm.level" type="text" class="am-input" placeholder="Ex.: Iniciante" />
            </div>
          </div>
          <div class="am-field">
            <label for="ls-help">Artigo da Central de Ajuda <span class="font-normal text-muted-foreground">(opcional)</span></label>
            <select id="ls-help" v-model="lessonForm.helpArticle" class="am-input">
              <option value="">Nenhum</option>
              <optgroup v-for="group in helpArticleOptions" :key="group.label" :label="group.label">
                <option v-for="article in group.articles" :key="article.id" :value="article.id">{{ article.titulo }}</option>
              </optgroup>
            </select>
            <p class="am-card-sub">Quando o artigo for revisado depois do vídeo desta aula, a aula passa a mostrar o artigo atualizado no lugar.</p>
          </div>
          <div class="am-field">
            <label for="ls-video">Link ou iframe do vídeo</label>
            <textarea id="ls-video" v-model="lessonForm.videoInput" rows="2" class="am-input am-mono" placeholder="Cole o link do YouTube ou o iframe completo" required></textarea>
          </div>
          <div class="am-field">
            <label for="ls-thumb">Capa por link <span class="font-normal text-muted-foreground">(opcional)</span></label>
            <input id="ls-thumb" v-model="lessonForm.thumbnailUrl" type="url" :disabled="Boolean(lessonForm.thumbnailData)" class="am-input" placeholder="https://..." />
            <p v-if="lessonForm.thumbnailData" class="am-card-sub">Remova a imagem enviada para usar um link.</p>
          </div>
          <div class="rounded-[14px] border border-dashed border-border p-3.5">
            <p class="am-eyebrow">Ou envie uma imagem de capa</p>
            <div class="mt-2 flex flex-wrap items-center gap-3">
              <input type="file" accept="image/*" aria-label="Enviar capa da aula" @change="handleThumbnailUpload" />
              <button v-if="lessonForm.thumbnailData" type="button" class="am-btn am-btn-sm" @click="clearThumbnailUpload">Remover imagem</button>
            </div>
            <p v-if="lessonForm.thumbnailUploadName" class="am-card-sub">Selecionada: {{ lessonForm.thumbnailUploadName }}</p>
          </div>
          <div v-if="lessonPreview.videoUrl">
            <p class="am-eyebrow mb-2">Prévia</p>
            <div class="overflow-hidden rounded-xl border border-border">
              <iframe v-if="lessonPreview.videoType !== 'file'" :src="lessonPreview.videoUrl" class="aspect-video w-full border-0" allowfullscreen></iframe>
              <video v-else class="aspect-video w-full bg-black object-cover" controls>
                <source :src="lessonPreview.videoUrl" type="video/mp4" />
              </video>
            </div>
          </div>
        </form>
        <template #footer>
          <button type="button" class="am-btn" @click="closeLessonDrawer">Cancelar</button>
          <button type="submit" form="lesson-form" class="am-btn am-btn-primary" :disabled="lessonSaving">
            {{ lessonSaving ? "Salvando..." : isEditingLesson ? "Salvar aula" : "Adicionar aula" }}
          </button>
        </template>
      </AdminMasterDrawer>
    </template>

    <!-- TEMPLATES -->
    <template v-else-if="activeTab === 'templates'">
      <AdminMasterHeader title="Modelos de página" subtitle="Modelos que as agências escolhem ao criar uma página nova.">
        <button type="button" class="am-btn" :disabled="pageTemplatesLoading" @click="loadTemplates"><AmIcon name="refresh" />Atualizar</button>
        <button type="button" class="am-btn am-btn-primary" @click="templatesTab = 'create'"><AmIcon name="plus" />Novo modelo</button>
      </AdminMasterHeader>

      <nav class="am-tabs" aria-label="Seções de modelos">
        <button type="button" class="am-tab" :class="{ on: templatesTab === 'published' }" @click="templatesTab = 'published'">
          Publicados <span class="am-count">{{ pageTemplates.length }}</span>
        </button>
        <button type="button" class="am-tab" :class="{ on: templatesTab === 'create' }" @click="templatesTab = 'create'">Criar a partir de uma página</button>
      </nav>

      <template v-if="templatesTab === 'published'">
        <div v-if="pageTemplatesLoading" class="am-card am-empty"><div class="am-spinner"></div>Carregando modelos...</div>
        <div v-else-if="pageTemplatesError" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ pageTemplatesError }}</span></div>
        <div v-else-if="!pageTemplates.length" class="am-card am-empty">
          Nenhum modelo publicado ainda.
          <button type="button" class="am-btn am-btn-primary" @click="templatesTab = 'create'">Criar a partir de uma página</button>
        </div>
        <div v-else class="am-grid-3">
          <article v-for="template in pageTemplates" :key="template.id" class="tpl-card">
            <div class="tpl-cover" :style="templateCoverStyle(template)">
              <span v-if="template.is_default" class="am-badge am-tone-success absolute left-2.5 top-2.5">Padrão</span>
            </div>
            <div class="p-3.5">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <b class="block truncate font-semibold">{{ template.name }}</b>
                  <small class="am-mono am-muted block truncate">/{{ template.slug }}</small>
                </div>
                <div class="relative" data-template-menu="true">
                  <button type="button" class="am-icon-btn" :aria-label="`Ações de ${template.name}`" @click="templateMenuId = templateMenuId === template.id ? null : template.id">
                    <AmIcon name="dots" />
                  </button>
                  <div v-if="templateMenuId === template.id" class="am-menu right-0 top-full mt-1">
                    <button type="button" @click="runTemplateMenu(() => openTemplatePreview(template))"><AmIcon name="eye" />Pré-visualizar</button>
                    <button type="button" @click="runTemplateMenu(() => openTemplateEditDialog(template))"><AmIcon name="edit" />Editar nome e descrição</button>
                    <button type="button" class="is-danger" :disabled="deletingTemplateId === template.id" @click="runTemplateMenu(() => handleDeleteTemplate(template))">
                      <AmIcon name="trash" />{{ deletingTemplateId === template.id ? "Excluindo..." : "Excluir" }}
                    </button>
                  </div>
                </div>
              </div>
              <p class="am-card-sub line-clamp-2 min-h-[36px]">{{ template.description || "Sem descrição" }}</p>
              <div class="mt-2.5 flex items-center justify-between">
                <span class="am-card-sub !mt-0">{{ templateStats(template).enabledSections }} de {{ templateStats(template).totalSections }} seções ativas</span>
                <button type="button" class="text-xs font-semibold text-primary" @click="openTemplatePreview(template)">Pré-visualizar</button>
              </div>
            </div>
          </article>
        </div>
      </template>

      <section v-else class="am-card am-card-flush">
        <div class="am-toolbar">
          <div class="relative w-full max-w-[320px]" data-template-agency-selector="true">
            <label class="am-search">
              <AmIcon name="search" />
              <input
                ref="templateAgencySearchInput"
                v-model="templateAgencySearch"
                type="search"
                placeholder="Buscar a agência de origem"
                aria-label="Buscar agência de origem"
                @focus="handleTemplateAgencyInputFocus"
              />
              <button type="button" class="am-icon-btn !h-6 !w-6" aria-label="Abrir lista de agências" @click="toggleTemplateAgencyDropdown">
                <AmIcon name="chevron" :class="templateAgencyDropdownOpen ? 'rotate-180' : ''" />
              </button>
            </label>
            <div v-if="templateAgencyDropdownOpen" class="am-menu left-0 right-0 top-full mt-1 max-h-64 overflow-y-auto">
              <p v-if="templateAgencyLoading" class="am-card-sub px-2.5 py-2">Buscando agências...</p>
              <p v-else-if="templateAgencyError" class="px-2.5 py-2 text-sm text-status-danger-foreground">{{ templateAgencyError }}</p>
              <template v-else-if="templateAgencyOptions.length">
                <button v-for="agency in templateAgencyOptions" :key="agency.id" type="button" class="!items-start" @click="selectTemplateAgency(agency)">
                  <span class="min-w-0">
                    <b class="block truncate font-semibold">{{ agency.name }}</b>
                    <small class="am-muted block text-xs">/{{ agency.slug }} · {{ agency.pages_count }} páginas</small>
                  </span>
                </button>
              </template>
              <p v-else class="am-card-sub px-2.5 py-2">Nenhuma agência encontrada.</p>
            </div>
          </div>
          <span v-if="selectedTemplateAgency" class="am-chip on">{{ selectedTemplateAgency.name }}</span>
          <button type="button" class="am-btn am-btn-sm ml-auto" :disabled="templatePagesLoading || !templateAgencyId" @click="loadTemplatePages">
            <AmIcon name="refresh" />Recarregar páginas
          </button>
        </div>

        <div v-if="!templateAgencyId" class="am-empty">Escolha a agência de origem para listar as páginas dela.</div>
        <div v-else-if="templatePagesLoading" class="am-empty"><div class="am-spinner"></div>Carregando páginas...</div>
        <div v-else-if="templatePagesError" class="am-empty !text-status-danger-foreground">{{ templatePagesError }}</div>
        <div v-else-if="!templatePages.length" class="am-empty">Essa agência não tem páginas.</div>
        <div v-else class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Página</th>
                <th>Situação</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="page in templatePages" :key="page.id">
                <td>
                  <b class="font-semibold">{{ page.title }}</b>
                  <small class="am-mono am-muted block">/{{ page.slug }}</small>
                </td>
                <td>
                  <span class="am-badge" :class="page.status === 'published' ? 'am-tone-success' : 'am-tone-warning'">
                    {{ page.status === "published" ? "Publicada" : "Rascunho" }}
                  </span>
                </td>
                <td class="am-right whitespace-nowrap">
                  <a v-if="templatePublicUrl(page)" :href="templatePublicUrl(page)" class="am-btn am-btn-sm" target="_blank" rel="noopener noreferrer">Ver página</a>
                  <button type="button" class="am-btn am-btn-sm am-btn-primary ml-1.5" @click="openTemplateDialog(page)">Usar como modelo</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="am-foot"><span>Prefira páginas publicadas: elas já foram revisadas pela agência.</span></div>
      </section>

      <AdminMasterDrawer
        :open="templateDialog.open"
        :title="templateDialog.mode === 'edit' ? 'Editar modelo' : 'Novo modelo'"
        :subtitle="templateDialog.mode === 'edit' ? 'Nome, identificador e descrição do modelo.' : 'Como o modelo aparece para as agências.'"
        icon="layout"
        tone="info"
        @close="closeTemplateDialog"
      >
        <div class="space-y-3.5">
          <div class="am-field">
            <label for="tp-name">Nome</label>
            <input id="tp-name" v-model="templateDialog.name" type="text" class="am-input" />
          </div>
          <div class="am-field">
            <label for="tp-slug">Identificador</label>
            <input id="tp-slug" v-model="templateDialog.slug" type="text" class="am-input am-mono" @input="handleTemplateSlugInput" />
          </div>
          <div class="am-field">
            <label for="tp-desc">Descrição</label>
            <textarea id="tp-desc" v-model="templateDialog.description" rows="3" class="am-input" placeholder="Resumo do que este modelo entrega"></textarea>
          </div>
          <div v-if="templateDialog.error" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ templateDialog.error }}</span></div>
        </div>
        <template #footer>
          <button type="button" class="am-btn" @click="closeTemplateDialog">Cancelar</button>
          <button type="button" class="am-btn am-btn-primary" :disabled="templateDialog.saving" @click="submitTemplateDialog">
            {{ templateDialog.saving ? "Salvando..." : templateDialog.mode === "edit" ? "Salvar alterações" : "Criar modelo" }}
          </button>
        </template>
      </AdminMasterDrawer>

      <div
        v-if="templatePreviewDialog.open"
        class="app-modal-overlay admin-master-surface fixed inset-0 z-40 flex items-center justify-center px-4 py-8"
        @click.self="closeTemplatePreview"
      >
        <div class="h-[90vh] w-full max-w-4xl overflow-y-auto rounded-[22px] border border-border bg-card p-5 shadow-elegant">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <p class="am-eyebrow">Pré-visualização</p>
              <h3 class="am-card-title">{{ templatePreviewDialog.template?.name }}</h3>
            </div>
            <button type="button" class="am-icon-btn" aria-label="Fechar" @click="closeTemplatePreview"><AmIcon name="x" /></button>
          </div>
          <PageTemplatePreview v-if="templatePreviewConfig" :config="templatePreviewConfig" :branding="templatePreviewBranding" />
          <p v-else class="am-empty">Não foi possível mostrar este modelo.</p>
        </div>
      </div>
    </template>
    <template v-else-if="activeTab === 'flight_apis'">
      <FlightApiKeysPanel />
    </template>
    <template v-else-if="activeTab === 'storage'">
      <StoragePanel />
    </template>
    <template v-else-if="activeTab === 'companies'">
      <CompaniesPanel />
    </template>
    <template v-else-if="activeTab === 'image_apis'">
      <ImageApiKeysPanel />
    </template>
    <template v-else-if="activeTab === 'revenue_forecast'">
      <RevenuePanel />
    </template>
  </div>

  <!-- SNACKBAR -->
  <transition name="fade">
    <div
      v-if="snackbar?.open"
      class="app-snackbar-layer z-50 rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-2xl"
    >
      {{ snackbar.text }}
    </div>
  </transition>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import { useAgencyStore } from "../../store/useAgencyStore";
import { getPlanLabel } from "../../utils/planLabels";
import { normalizeVideoInput, useLessonsStore, type Lesson } from "../../store/useLessonsStore";
import { HELP_MODULES, articleReplacingLesson, articlesOf, formatDate as formatHelpDate } from "../../help";
import { slugify } from "../../utils/slugify";
import PageTemplatePreview from "../../components/admin/PageTemplatePreview.vue";
import FlightApiKeysPanel from "../../components/admin/FlightApiKeysPanel.vue";
import ImageApiKeysPanel from "../../components/admin/ImageApiKeysPanel.vue";
import CompaniesPanel from "../../components/admin/CompaniesPanel.vue";
import DashboardPanel from "../../components/admin/DashboardPanel.vue";
import UsersPanel from "../../components/admin/UsersPanel.vue";
import StoragePanel from "../../components/admin/StoragePanel.vue";
import RevenuePanel from "../../components/admin/RevenuePanel.vue";
import { listPageTemplates, createTemplateFromPage, deleteTemplate, updateTemplate } from "../../services/templates";
import type { PageTemplate } from "../../types/templates";
import { applyTemplateBranding, summarizeTemplate } from "../../utils/pageTemplates";
import { sanitizeDigits, buildWhatsappLink } from "../../utils/whatsapp";
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";
import AdminMasterKpi from "../../components/admin/master/AdminMasterKpi.vue";
import AdminMasterDrawer from "../../components/admin/master/AdminMasterDrawer.vue";

interface AdminAgencySummary {
  id: number;
  name: string;
  slug: string;
  created_at?: string;
  pages_count: number;
  logo_url?: string | null;
  primary_color?: string | null;
  secondary_color?: string | null;
  cta_whatsapp?: string | null;
}

interface AdminPageSummary {
  id: number;
  title: string;
  slug: string;
  status: string;
}

interface AdminOnlineSession {
  session_id: string;
  user_id: number;
  user_name: string;
  user_email: string;
  user_plan: string;
  ip_address?: string | null;
  device_label?: string | null;
  client_name?: string | null;
  created_at: string;
  last_seen_at: string;
  active_sessions: number;
  last_path?: string | null;
}

interface AdminOnlineSessionsResponse {
  sessions: AdminOnlineSession[];
  total_online: number;
  unique_users: number;
  generated_at: string;
}

type AdminTab = "dashboard" | "monitor" | "users" | "lessons" | "templates" | "flight_apis" | "image_apis" | "companies" | "storage" | "revenue_forecast";
type TemplateDialogMode = "create" | "edit";

const onlineSessions = ref<AdminOnlineSession[]>([]);
const onlineSessionsMeta = ref<AdminOnlineSessionsResponse | null>(null);
const onlineSessionsLoading = ref(false);
const onlineSessionsError = ref("");
const revokingUserId = ref<number | null>(null);
let onlineSessionsInterval: number | null = null;

const monitorStatusLabel = computed(() => (onlineSessionsLoading.value ? "Atualizando" : "Operacional"));
const monitorLastUpdated = computed(() => {
  const value = onlineSessionsMeta.value?.generated_at;
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
});

const error = ref("");
const auth = useAuthStore();
const agencyStore = useAgencyStore();
const route = useRoute();
const router = useRouter();
const snackbar = ref<{ open: boolean; text: string } | null>(null);
const isBootstrappingAdminManagement = ref(true);

const templateAgencyId = ref<number | null>(null);
const templateAgencyOptions = ref<AdminAgencySummary[]>([]);
const templateAgencySearch = ref("");
const templateAgencyDropdownOpen = ref(false);
const templateAgencyLoading = ref(false);
const templateAgencyError = ref("");
const templateAgencyFetchedOnce = ref(false);
const templateAgencySearchInput = ref<HTMLInputElement | null>(null);
let templateAgencySearchDebounce: ReturnType<typeof setTimeout> | null = null;
let templateAgencySearchRequestId = 0;
let skipTemplateAgencySearchWatcher = false;
const templatePages = ref<AdminPageSummary[]>([]);
const templatePagesLoading = ref(false);
const templatePagesError = ref("");
const pageTemplates = ref<PageTemplate[]>([]);
const pageTemplatesLoading = ref(false);
const pageTemplatesError = ref("");
const deletingTemplateId = ref<number | null>(null);
const templateDialog = reactive({
  open: false,
  mode: "create" as TemplateDialogMode,
  page: null as AdminPageSummary | null,
  templateId: null as number | null,
  name: "",
  slug: "",
  description: "",
  error: "",
  saving: false
});
const templateSlugAuto = ref("");
const templatePreviewDialog = reactive({
  open: false,
  template: null as PageTemplate | null
});
const updateTemplateAgencySearchLabel = (value: string) => {
  skipTemplateAgencySearchWatcher = true;
  templateAgencySearch.value = value;
};
const fetchTemplateAgencies = async (term?: string) => {
  const requestId = ++templateAgencySearchRequestId;
  templateAgencyLoading.value = true;
  templateAgencyError.value = "";
  const params: Record<string, string | number> = { limit: 40 };
  const query = term?.trim();
  if (query) {
    params.q = query;
  }
  try {
    const { data } = await api.get<AdminAgencySummary[]>("/admin/agencies/search", { params });
    if (requestId === templateAgencySearchRequestId) {
      templateAgencyOptions.value = data || [];
      templateAgencyFetchedOnce.value = true;
    }
  } catch (err: any) {
    console.error(err);
    if (requestId === templateAgencySearchRequestId) {
      templateAgencyError.value = err?.response?.data?.detail || "Não foi possível buscar Agências.";
      templateAgencyOptions.value = [];
    }
  } finally {
    if (requestId === templateAgencySearchRequestId) {
      templateAgencyLoading.value = false;
    }
  }
};
const ensureTemplateAgencyOptions = () => {
  if (!templateAgencyFetchedOnce.value && !templateAgencyLoading.value) {
    void fetchTemplateAgencies(templateAgencySearch.value);
  }
};
const openTemplateAgencyDropdown = () => {
  templateAgencyDropdownOpen.value = true;
  ensureTemplateAgencyOptions();
};
const toggleTemplateAgencyDropdown = () => {
  if (templateAgencyDropdownOpen.value) {
    templateAgencyDropdownOpen.value = false;
    return;
  }
  openTemplateAgencyDropdown();
  templateAgencySearchInput.value?.focus();
};
const handleTemplateAgencyInputFocus = () => {
  openTemplateAgencyDropdown();
};
const selectTemplateAgency = (agency: AdminAgencySummary) => {
  templateAgencyId.value = agency.id;
  updateTemplateAgencySearchLabel(agency.name);
  templateAgencyDropdownOpen.value = false;
};

const activeTab = ref<AdminTab>("dashboard");
const syncActiveTabFromRoute = () => {
  const routeName = typeof route.name === "string" ? route.name : "";
  if (routeName === "admin-management-monitor") {
    activeTab.value = "monitor";
    return;
  }
  if (routeName === "admin-management-users") {
    activeTab.value = "users";
    return;
  }
  if (routeName === "admin-management-lessons") {
    activeTab.value = "lessons";
    return;
  }
  if (routeName === "admin-management-templates") {
    activeTab.value = "templates";
    return;
  }
  if (routeName === "admin-management-flight-apis") {
    activeTab.value = "flight_apis";
    return;
  }
  if (routeName === "admin-management-companies") {
    activeTab.value = "companies";
    return;
  }
  if (routeName === "admin-management-storage") {
    activeTab.value = "storage";
    return;
  }
  if (routeName === "admin-management-image-apis") {
    activeTab.value = "image_apis";
    return;
  }
  if (routeName === "admin-management-revenue-forecast") {
    activeTab.value = "revenue_forecast";
    return;
  }
  activeTab.value = "dashboard";
};
const selectedTemplateAgency = computed(() => {
  return templateAgencyOptions.value.find(agency => agency.id === templateAgencyId.value) || null;
});

const templatePublicUrl = (page: AdminPageSummary) => {
  const agencySlug = selectedTemplateAgency.value?.slug;
  if (!agencySlug) return "";
  return `/${agencySlug}/${page.slug}`;
};
const loadTemplatePages = async () => {
  if (!templateAgencyId.value) {
    templatePages.value = [];
    return;
  }
  try {
    templatePagesLoading.value = true;
    templatePagesError.value = "";
    const { data } = await api.get<AdminPageSummary[]>("/pages", {
      params: { agency_id: templateAgencyId.value }
    });
    templatePages.value = data || [];
  } catch (err: any) {
    console.error(err);
    templatePagesError.value = err?.response?.data?.detail || "Não foi possível carregar as páginas.";
  } finally {
    templatePagesLoading.value = false;
  }
};
const loadTemplates = async () => {
  try {
    pageTemplatesLoading.value = true;
    pageTemplatesError.value = "";
    pageTemplates.value = await listPageTemplates();
  } catch (err: any) {
    console.error(err);
    pageTemplatesError.value = err?.response?.data?.detail || "Não foi possível carregar os modelos.";
  } finally {
    pageTemplatesLoading.value = false;
  }
};
const openTemplateDialog = (page: AdminPageSummary) => {
  templateDialog.mode = "create";
  templateDialog.templateId = null;
  templateDialog.page = page;
  templateDialog.name = page.title;
  templateDialog.slug = slugify(page.title, "modelo");
  templateDialog.description = "";
  templateDialog.error = "";
  templateDialog.saving = false;
  templateSlugAuto.value = templateDialog.slug;
  templateDialog.open = true;
};
const closeTemplateDialog = () => {
  templateDialog.open = false;
  templateDialog.mode = "create";
  templateDialog.page = null;
  templateDialog.templateId = null;
  templateDialog.name = "";
  templateDialog.slug = "";
  templateDialog.description = "";
  templateDialog.error = "";
  templateDialog.saving = false;
  templateSlugAuto.value = "";
};
const handleTemplateSlugInput = () => {
  templateSlugAuto.value = templateDialog.slug;
};
const submitTemplateDialog = async () => {
  const name = templateDialog.name.trim();
  const slug = templateDialog.slug.trim();
  if (!name || !slug) {
    templateDialog.error = "Informe nome e slug do template.";
    return;
  }
  templateDialog.saving = true;
  templateDialog.error = "";
  try {
    if (templateDialog.mode === "edit") {
      if (!templateDialog.templateId) {
        templateDialog.error = "Modelo inválido.";
        templateDialog.saving = false;
        return;
      }
      await updateTemplate(templateDialog.templateId, {
        name,
        slug,
        description: templateDialog.description.trim() || null
      });
      showSnackbar("Modelo atualizado com sucesso.");
    } else {
      if (!templateDialog.page) {
        templateDialog.error = "Selecione uma página para criar o modelo.";
        templateDialog.saving = false;
        return;
      }
      await createTemplateFromPage({
        page_id: templateDialog.page.id,
        name,
        slug,
        description: templateDialog.description.trim() || undefined
      });
      showSnackbar("Modelo criado com sucesso.");
    }
    closeTemplateDialog();
    await loadTemplates();
  } catch (err: any) {
    console.error(err);
    templateDialog.error =
      err?.response?.data?.detail ||
      (templateDialog.mode === "edit" ? "Não foi possível atualizar o modelo." : "Não foi possível criar o modelo.");
    templateDialog.saving = false;
  }
};
const openTemplatePreview = (template: PageTemplate) => {
  templatePreviewDialog.template = template;
  templatePreviewDialog.open = true;
};
const closeTemplatePreview = () => {
  templatePreviewDialog.open = false;
  templatePreviewDialog.template = null;
};
const openTemplateEditDialog = (template: PageTemplate) => {
  templateDialog.mode = "edit";
  templateDialog.page = null;
  templateDialog.templateId = template.id;
  templateDialog.name = template.name;
  templateDialog.slug = template.slug;
  templateDialog.description = template.description || "";
  templateDialog.error = "";
  templateDialog.saving = false;
  templateSlugAuto.value = templateDialog.slug;
  templateDialog.open = true;
};
const handleDeleteTemplate = async (template: PageTemplate) => {
  if (deletingTemplateId.value) return;
  const confirmed = window.confirm(`Deseja realmente excluir o modelo "${template.name}"?`);
  if (!confirmed) return;
  try {
    deletingTemplateId.value = template.id;
    await deleteTemplate(template.id);
    pageTemplates.value = pageTemplates.value.filter(item => item.id !== template.id);
    showSnackbar("Modelo removido com sucesso.");
  } catch (err: any) {
    console.error(err);
    const detail = err?.response?.data?.detail || "Não foi possível remover o modelo.";
    showSnackbar(detail);
  } finally {
    deletingTemplateId.value = null;
  }
};
const previewAgency = computed(() => selectedTemplateAgency.value || agencyStore.agencies[0] || null);
const previewWhatsappDigits = computed(() => {
  const agencyDigits = sanitizeDigits(previewAgency.value?.cta_whatsapp || "");
  if (agencyDigits) return agencyDigits;
  return sanitizeDigits(auth.user?.whatsapp || "");
});
const templatePreviewBranding = computed(() => {
  const agency = previewAgency.value;
  return {
    agency_name: agency?.name || "Sua Agência",
    logo_url: agency?.logo_url || "",
    primary_color: agency?.primary_color || "#0f172a",
    secondary_color: agency?.secondary_color || agency?.primary_color || "#1f2937",
    whatsapp_link: templatePreviewDialog.template
      ? buildWhatsappLink(previewWhatsappDigits.value, templatePreviewDialog.template.name)
      : ""
  };
});
const templatePreviewConfig = computed(() => {
  if (!templatePreviewDialog.template) return null;
  return applyTemplateBranding(templatePreviewDialog.template.config_json, {
    logoUrl: templatePreviewBranding.value.logo_url,
    whatsappLink: templatePreviewBranding.value.whatsapp_link,
    primaryColor: templatePreviewBranding.value.primary_color,
    enforcePrimaryColor: !!templatePreviewBranding.value.primary_color
  });
});
const templateStats = (template: PageTemplate) => summarizeTemplate(template);

const lessonsStore = useLessonsStore();
const adminLessons = computed(() => lessonsStore.sortedLessons);
type LessonGroup = {
  key: string;
  label: string;
  moduleName: string;
  lessons: Lesson[];
};
const lessonGroups = computed<LessonGroup[]>(() => {
  const groups = new Map<string, LessonGroup>();
  for (const lesson of adminLessons.value) {
    const moduleName = (lesson.moduleName || "").trim();
    const key = moduleName || "__default__";
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        label: moduleName || "Sem módulo",
        moduleName,
        lessons: []
      });
    }
    groups.get(key)!.lessons.push(lesson);
  }
  return Array.from(groups.values());
});
const lessonModuleOptions = computed(() =>
  Array.from(new Set(adminLessons.value.map(lesson => lesson.moduleName.trim()).filter(Boolean))).sort((a, b) => a.localeCompare(b))
);
const lessonsLoading = computed(() => lessonsStore.loading);
const lessonSaving = ref(false);
const deletingLessonId = ref<number | null>(null);
const resettingLessons = ref(false);
const lessonForm = reactive({
  moduleName: "",
  title: "",
  description: "",
  duration: "",
  level: "",
  videoInput: "",
  thumbnailUrl: "",
  thumbnailData: "",
  thumbnailUploadName: "",
  helpArticle: ""
});
const lessonReplacement = (lesson: Lesson) =>
  articleReplacingLesson({ titulo: lesson.title, artigo: lesson.helpArticle, atualizadaEm: lesson.videoUpdatedAt });
const helpArticleOptions = HELP_MODULES.map(module => ({ label: module.titulo, articles: articlesOf(module.id) })).filter(group => group.articles.length);
const editingLessonId = ref<number | null>(null);
const isEditingLesson = computed(() => editingLessonId.value !== null);
const lessonPreview = computed(() => normalizeVideoInput(lessonForm.videoInput || ""));
const persistLessonGroupOrder = async (group: LessonGroup, lessonIds: number[]) => {
  const reorderAction = (lessonsStore as any).reorderLessonsInModule;
  if (typeof reorderAction === "function") {
    await reorderAction.call(lessonsStore, group.moduleName, lessonIds);
    return;
  }
  const { data } = await api.post("/lessons/reorder", {
    module_name: group.moduleName.trim() || null,
    lesson_ids: lessonIds
  });
  lessonsStore.lessons = data.map((lesson: any) => ({
    id: lesson.id,
    moduleName: (lesson.module_name || "").trim(),
    sortOrder: lesson.sort_order ?? 0,
    title: lesson.title,
    description: lesson.description || "",
    duration: lesson.duration || "",
    level: lesson.level || "",
    videoType: lesson.video_type,
    videoUrl: lesson.video_url,
    thumbnail: lesson.thumbnail_url || undefined,
    helpArticle: lesson.help_article || undefined,
    videoUpdatedAt: lesson.video_updated_at || lesson.updated_at || lesson.created_at || undefined
  }));
  lessonsStore.loaded = true;
};

const moveLessonInGroup = async (group: LessonGroup, index: number, delta: -1 | 1) => {
  const targetIndex = index + delta;
  if (targetIndex < 0 || targetIndex >= group.lessons.length) return;
  const reordered = [...group.lessons];
  const [moved] = reordered.splice(index, 1);
  if (!moved) return;
  reordered.splice(targetIndex, 0, moved);
  lessonSaving.value = true;
  try {
    await persistLessonGroupOrder(group, reordered.map(lesson => lesson.id));
    showSnackbar("Ordem atualizada.");
  } catch (err) {
    console.error(err);
    showSnackbar("Não foi possível reordenar as aulas.");
  } finally {
    lessonSaving.value = false;
  }
};

const formatRelativeMoment = (val?: string | null) => {
  if (!val) return "--";
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return "--";
  const diff = Date.now() - d.getTime();
  if (diff < 30_000) return "há instantes";
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "há instantes";
  if (minutes < 60) return `há ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `há ${hours} h`;
  const days = Math.floor(hours / 24);
  return `há ${days} d`;
};

const formatDurationSince = (val?: string | null) => {
  if (!val) return "--";
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return "--";
  const diff = Date.now() - d.getTime();
  if (diff < 60_000) return "Ativo há instantes";
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `Ativo há ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Ativo há ${hours} h`;
  const days = Math.floor(hours / 24);
  return `Ativo há ${days} d`;
};

const showSnackbar = (text: string) => {
  snackbar.value = { open: true, text };
  setTimeout(() => {
    snackbar.value = null;
  }, 3000);
};

const loadOnlineSessions = async (notify = false) => {
  try {
    onlineSessionsLoading.value = true;
    onlineSessionsError.value = "";
    const { data } = await api.get<AdminOnlineSessionsResponse>("/admin/online-sessions");
    onlineSessions.value = data.sessions;
    onlineSessionsMeta.value = data;
    if (notify) {
      showSnackbar("Monitor atualizado.");
    }
  } catch (err: any) {
    console.error(err);
    const message = err?.response?.data?.detail || "Não foi possível carregar o monitor agora.";
    onlineSessionsError.value = message;
    if (notify) {
      showSnackbar(message);
    }
  } finally {
    onlineSessionsLoading.value = false;
  }
};

const startOnlineSessionsPolling = () => {
  if (typeof window === "undefined") return;
  if (onlineSessionsInterval) {
    window.clearInterval(onlineSessionsInterval);
  }
  onlineSessionsInterval = window.setInterval(() => {
    if (activeTab.value === "monitor") {
      loadOnlineSessions();
    }
  }, 20000);
};

const stopOnlineSessionsPolling = () => {
  if (typeof window === "undefined") return;
  if (onlineSessionsInterval) {
    window.clearInterval(onlineSessionsInterval);
    onlineSessionsInterval = null;
  }
};

const revokeUserSessions = async (session: AdminOnlineSession) => {
  if (revokingUserId.value) return;
  revokingUserId.value = session.user_id;
  try {
    await api.post(`/admin/online-sessions/user/${session.user_id}/revoke`);
    showSnackbar(`Sessões de ${session.user_name} encerradas.`);
    await loadOnlineSessions();
  } catch (err: any) {
    console.error(err);
    const detail = err?.response?.data?.detail || "Não foi possível deslogar este usuário.";
    showSnackbar(detail);
  } finally {
    revokingUserId.value = null;
  }
};

const handleThumbnailUpload = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    showSnackbar("Envie apenas imagens.");
    input.value = "";
    return;
  }
  const maxSize = 4 * 1024 * 1024;
  if (file.size > maxSize) {
    showSnackbar("Imagem muito grande (máximo 4MB).");
    input.value = "";
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    lessonForm.thumbnailData = reader.result as string;
    lessonForm.thumbnailUploadName = file.name;
    lessonForm.thumbnailUrl = "";
  };
  reader.readAsDataURL(file);
};

const clearThumbnailUpload = () => {
  lessonForm.thumbnailData = "";
  lessonForm.thumbnailUploadName = "";
};

const resetLessonForm = () => {
  editingLessonId.value = null;
  lessonForm.moduleName = "";
  lessonForm.title = "";
  lessonForm.description = "";
  lessonForm.duration = "";
  lessonForm.level = "";
  lessonForm.videoInput = "";
  lessonForm.thumbnailUrl = "";
  lessonForm.thumbnailData = "";
  lessonForm.thumbnailUploadName = "";
  lessonForm.helpArticle = "";
};

const startLessonEdit = (lesson: Lesson) => {
  editingLessonId.value = lesson.id;
  lessonForm.moduleName = lesson.moduleName || "";
  lessonForm.title = lesson.title;
  lessonForm.description = lesson.description;
  lessonForm.duration = lesson.duration;
  lessonForm.level = lesson.level;
  lessonForm.videoInput = lesson.videoUrl;
  const isDataUrl = Boolean(lesson.thumbnail?.startsWith("data:"));
  lessonForm.thumbnailUrl = isDataUrl ? "" : lesson.thumbnail || "";
  lessonForm.thumbnailData = isDataUrl ? lesson.thumbnail || "" : "";
  lessonForm.thumbnailUploadName = isDataUrl ? "Imagem enviada" : "";
  lessonForm.helpArticle = lesson.helpArticle || "";
};

const saveLesson = async () => {
  if (!lessonForm.title.trim() || !lessonForm.videoInput.trim()) {
    showSnackbar("Informe Título e link do vídeo.");
    return;
  }
  const parsed = normalizeVideoInput(lessonForm.videoInput);
  if (!parsed.videoUrl) {
    showSnackbar("Link de vídeo inválido.");
    return;
  }
  const payload = {
    moduleName: lessonForm.moduleName.trim(),
    title: lessonForm.title.trim(),
    description: lessonForm.description.trim(),
    duration: lessonForm.duration.trim(),
    level: lessonForm.level.trim(),
    videoType: parsed.videoType,
    videoUrl: parsed.videoUrl,
    thumbnailUrl: lessonForm.thumbnailUrl || undefined,
    thumbnailBase64: lessonForm.thumbnailData || undefined,
    helpArticle: lessonForm.helpArticle
  };
  lessonSaving.value = true;
  try {
    if (editingLessonId.value) {
      await lessonsStore.updateLesson(editingLessonId.value, payload);
      showSnackbar("Aula atualizada.");
    } else {
      await lessonsStore.addLesson(payload);
      showSnackbar("Aula adicionada.");
    }
    resetLessonForm();
    lessonDrawerOpen.value = false;
  } catch (err) {
    console.error(err);
    showSnackbar("Não foi possível salvar a aula.");
  } finally {
    lessonSaving.value = false;
  }
};

const deleteLesson = async (lessonId: number) => {
  if (!confirm("Deseja remover esta aula?")) return;
  deletingLessonId.value = lessonId;
  try {
    await lessonsStore.deleteLesson(lessonId);
    if (editingLessonId.value === lessonId) {
      resetLessonForm();
    }
    showSnackbar("Aula removida.");
  } catch (err) {
    console.error(err);
    showSnackbar("Não foi possível remover a aula.");
  } finally {
    deletingLessonId.value = null;
  }
};

const handleResetLessons = () => {
  if (!confirm("Restaurar a lista padrão de aulas?")) return;
  lessonsStore.resetLessons();
  resetLessonForm();
  showSnackbar("Aulas restauradas.");
};

// ---------- Visual do admin master ----------
const intFormatter = new Intl.NumberFormat("pt-BR");
const formatInt = (value?: number | null) => intFormatter.format(Number(value || 0));
const initials = (name?: string | null) =>
  String(name || "?")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase() || "")
    .join("") || "?";

const planToneClass = (plan?: string | null) => {
  const label = getPlanLabel(plan);
  if (label === "Escala") return "am-tone-success";
  if (label === "Agência") return "am-tone-info";
  if (label === "Teste" || label === "Trial") return "am-tone-warning";
  return "am-tone-neutral";
};

const isMobileDevice = (label?: string | null) => /android|iphone|ipad|ios|mobile|celular/i.test(String(label || ""));
const monitorDeviceSplit = computed(() => {
  const mobile = onlineSessions.value.filter(session => isMobileDevice(`${session.device_label} ${session.client_name}`)).length;
  return { mobile, desktop: onlineSessions.value.length - mobile };
});
const monitorInEditor = computed(
  () => onlineSessions.value.filter(session => /\/admin\/pages\/[^/]+\/edit/.test(String(session.last_path || ""))).length
);

const pathLabels: Array<[RegExp, string]> = [
  [/^\/admin\/pages\/[^/]+\/edit/, "Editor de página"],
  [/^\/admin\/pages/, "Páginas"],
  [/^\/admin\/dashboard/, "Dashboard"],
  [/^\/admin\/leads\/forms/, "Leads › Formulários"],
  [/^\/admin\/leads\/opportunities/, "Leads › Oportunidades"],
  [/^\/admin\/leads\/clients/, "Leads › Clientes"],
  [/^\/admin\/leads\/settings/, "Leads › Configurações"],
  [/^\/admin\/inbox/, "Caixa de entrada"],
  [/^\/admin\/integracoes/, "Integrações"],
  [/^\/admin\/agency\/team/, "Minha agência › Equipe"],
  [/^\/admin\/agency\/invoices/, "Minha agência › Faturas"],
  [/^\/admin\/agency/, "Minha agência"],
  [/^\/admin\/domains/, "Domínios"],
  [/^\/admin\/aulas/, "Aulas"],
  [/^\/admin\/perfil/, "Perfil"],
  [/^\/admin\/planos/, "Planos"],
  [/^\/admin\/administracao/, "Admin master"]
];
const pathLabel = (path?: string | null) => {
  if (!path) return "Não identificado";
  const clean = path.split("?")[0];
  return pathLabels.find(([pattern]) => pattern.test(clean))?.[1] || "Outra tela";
};

const lessonDrawerOpen = ref(false);
const openNewLesson = (moduleName = "") => {
  resetLessonForm();
  lessonForm.moduleName = moduleName;
  lessonDrawerOpen.value = true;
};
const openLessonEdit = (lesson: Lesson) => {
  startLessonEdit(lesson);
  lessonDrawerOpen.value = true;
};
const closeLessonDrawer = () => {
  lessonDrawerOpen.value = false;
  resetLessonForm();
};

const templatesTab = ref<"published" | "create">("published");
const templateMenuId = ref<number | null>(null);
const runTemplateMenu = (action: () => unknown) => {
  templateMenuId.value = null;
  void action();
};
const coverGradients = [
  "linear-gradient(135deg, #1e3a5f, #3b6e8f 55%, #d9a066)",
  "linear-gradient(135deg, #0e4d64, #1fa2b8 60%, #f3d28b)",
  "linear-gradient(135deg, #4a1d6b, #a23d8f 55%, #f6b73c)",
  "linear-gradient(135deg, #1a1a2e, #3e2a5e 60%, #e94560)",
  "linear-gradient(135deg, #3b2f1e, #8a6a3a 55%, #e8d5a8)",
  "linear-gradient(135deg, #0b3d2e, #1a7f5a 55%, #b6e3c9)"
];
const templateCoverStyle = (template: PageTemplate) => {
  const match = JSON.stringify(template.config_json || {}).match(/https?:[^"\s]+?\.(?:jpe?g|png|webp|avif)(?:\?[^"\s]*)?/i);
  const gradient = coverGradients[template.id % coverGradients.length];
  return match
    ? { backgroundImage: `linear-gradient(180deg, transparent 40%, rgba(0,0,0,.35)), url("${match[0].replace(/\\\//g, "/")}")`, backgroundSize: "cover", backgroundPosition: "center" }
    : { backgroundImage: gradient };
};

const planLabel = (plan: string) => {
  if (!plan) return "Indefinido";
  const lower = plan.toLowerCase();
  if (lower.includes("trial")) return plan;
  return getPlanLabel(plan);
};

const handleOutsideClick = (event: MouseEvent) => {
  const path = event.composedPath();
  if (templateAgencyDropdownOpen.value) {
    const insideAgencySelector = path.some(el => (el as HTMLElement)?.dataset?.templateAgencySelector === "true");
    if (!insideAgencySelector) templateAgencyDropdownOpen.value = false;
  }
  if (templateMenuId.value !== null) {
    const insideTemplateMenu = path.some(el => (el as HTMLElement)?.dataset?.templateMenu === "true");
    if (!insideTemplateMenu) templateMenuId.value = null;
  }
};

watch(
  () => templateDialog.name,
  value => {
    if (!templateDialog.open || templateDialog.mode !== "create") return;
    if (!templateDialog.slug || templateDialog.slug === templateSlugAuto.value) {
      const next = slugify(value, "modelo");
      templateDialog.slug = next;
      templateSlugAuto.value = next;
    }
  }
);

watch(
  templateAgencySearch,
  value => {
    if (skipTemplateAgencySearchWatcher) {
      skipTemplateAgencySearchWatcher = false;
      return;
    }
    if (templateAgencySearchDebounce) {
      clearTimeout(templateAgencySearchDebounce);
    }
    templateAgencyDropdownOpen.value = true;
    templateAgencySearchDebounce = setTimeout(() => {
      void fetchTemplateAgencies(value);
    }, 250);
  }
);

watch(
  templateAgencyOptions,
  options => {
    if (!options?.length) {
      if (!templateAgencySearch.value.trim()) {
        templateAgencyId.value = null;
        updateTemplateAgencySearchLabel("");
      }
      return;
    }
    const exists = options.some(option => option.id === templateAgencyId.value);
    if (!templateAgencyId.value && options[0] && !templateAgencySearch.value.trim()) {
      templateAgencyId.value = options[0].id;
      updateTemplateAgencySearchLabel(options[0].name);
      return;
    }
    if (!exists && options[0] && !templateAgencySearch.value.trim()) {
      templateAgencyId.value = options[0].id;
      updateTemplateAgencySearchLabel(options[0].name);
    }
  },
  { immediate: true }
);

watch(
  templateAgencyId,
  async value => {
    if (activeTab.value === "templates" && value) {
      await loadTemplatePages();
    }
    if (!value) {
      templatePages.value = [];
    }
  }
);

onMounted(async () => {
  if (typeof window !== "undefined") {
    window.addEventListener("click", handleOutsideClick);
  }
  try {
    if (!auth.user && auth.token) {
      await auth.fetchProfile();
    }
    if (!agencyStore.agencies.length) {
      try {
        await agencyStore.loadAgencies();
      } catch (err) {
        console.error(err);
      }
    }
    await lessonsStore.ensureLessons();
    if (activeTab.value === "monitor") await loadOnlineSessions();
    startOnlineSessionsPolling();
  } finally {
    isBootstrappingAdminManagement.value = false;
  }
});

watch(
  () => route.name,
  () => {
    syncActiveTabFromRoute();
  },
  { immediate: true }
);

watch(activeTab, (tab) => {
  if (tab === "monitor") {
    loadOnlineSessions();
  }
  if (tab === "templates") {
    ensureTemplateAgencyOptions();
    if (!pageTemplates.value.length) {
      loadTemplates();
    }
    if (templateAgencyId.value) {
      loadTemplatePages();
    }
  }

});

onUnmounted(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("click", handleOutsideClick);
  }
  if (templateAgencySearchDebounce) {
    clearTimeout(templateAgencySearchDebounce);
    templateAgencySearchDebounce = null;
  }
  stopOnlineSessionsPolling();

});
</script>

<style scoped>
.admin-master-view {
  --card-border: var(--border);
  --ink-900: var(--foreground);
  --ink-500: var(--muted-foreground);
  --surface: var(--card);
  --shadow: var(--shadow-soft);
}

.topbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (min-width: 768px) {
  .topbar {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.page-kicker {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.24em;
  color: var(--ink-500);
  font-weight: 700;
}

.page-title {
  margin-top: 4px;
  font-size: 22px;
  line-height: 1.1;
  font-weight: 800;
  color: var(--ink-900);
}

.page-sub {
  margin-top: 4px;
  color: var(--ink-500);
  font-size: 14px;
}

.metrics-grid {
  display: grid;
  gap: 16px;
}

.metrics-grid-4 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.metrics-grid-3 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

@media (min-width: 768px) {
  .metrics-grid-4 {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .metrics-grid-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.metric-card {
  border-radius: 18px;
  border: 1px solid var(--card-border);
  background: var(--surface);
  box-shadow: var(--shadow);
  padding: 16px 18px;
}

.metric-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.34em;
  color: #5f7990;
  font-weight: 700;
}

.metric-value {
  margin-top: 8px;
  font-size: 30px;
  line-height: 1;
  font-weight: 800;
  color: var(--ink-900);
}

.metric-footer-text {
  margin-top: 6px;
  color: var(--ink-500);
  font-size: 13px;
}

.chart-card,
.list-card {
  border-radius: 18px;
  border: 1px solid var(--card-border);
  background: var(--surface);
  box-shadow: var(--shadow);
  padding: 18px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

@media (min-width: 1024px) {
  .bottom-grid {
    grid-template-columns: 2fr 1fr;
  }
}

.chart-tooltip {
  position: absolute;
  transform: translate(-50%, -100%);
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.4;
  box-shadow: var(--shadow-elegant);
  pointer-events: none;
  z-index: 20;
}

.chart-tooltip-date {
  font-weight: 700;
  margin-bottom: 4px;
}

.am-cal-day {
  display: flex;
  min-height: 62px;
  flex-direction: column;
  justify-content: space-between;
  border-radius: 12px;
  background: var(--muted);
  padding: 7px 8px;
  text-align: left;
  color: var(--muted-foreground);
  transition: box-shadow 0.15s ease;
}
.am-cal-day b {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--foreground);
}
.am-cal-day:not(:disabled):hover {
  box-shadow: inset 0 0 0 1px var(--border);
}
.am-cal-day.is-off {
  border: 1px dashed var(--border);
  background: transparent;
}
.am-cal-day.heat-1 {
  background: color-mix(in srgb, var(--primary) 10%, var(--muted));
}
.am-cal-day.heat-2 {
  background: color-mix(in srgb, var(--primary) 22%, var(--muted));
}
.am-cal-day.heat-3 {
  background: color-mix(in srgb, var(--primary) 36%, var(--muted));
}
.am-cal-day.is-selected {
  box-shadow: inset 0 0 0 2px var(--primary);
  color: var(--foreground);
}
@media (max-width: 640px) {
  .am-cal-day {
    min-height: 48px;
    padding: 5px;
  }
  .am-cal-day b {
    font-size: 10px;
  }
}

.tpl-card {
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--card);
  box-shadow: var(--shadow-card);
}
.tpl-cover {
  position: relative;
  height: 128px;
  background-color: var(--muted);
}

.lesson-thumb {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 72px;
  height: 42px;
  overflow: hidden;
  border-radius: 8px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--chart-3) 55%, var(--muted)), color-mix(in srgb, var(--chart-1) 45%, var(--muted)));
  color: #fff;
}
.lesson-thumb svg {
  width: 16px;
  height: 16px;
}

.am-user-detail {
  border: 1px solid var(--border);
  border-radius: 16px;
  background: color-mix(in srgb, var(--muted) 55%, var(--card));
  padding: 16px;
}
.am-detail-row:hover td {
  background: transparent !important;
}

.legend-toggle-sub {
  transition: opacity 0.15s ease;
}

.legend-toggle-sub.off {
  opacity: 0.35;
}

.premium-panel {
  background: radial-gradient(circle at top, #101828 0%, #05060f 60%);
  min-height: 100vh;
  color: #f8fafc;
  border-radius: 0;
  margin: 0;
  padding: 0;
}

.premium-panel .premium-card {
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.03);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(14px);
}

.interactive-table,
.interactive-table * {
  user-select: auto;
  caret-color: inherit;
}

.copyable {
  user-select: text !important;
  caret-color: auto !important;
}

</style>
