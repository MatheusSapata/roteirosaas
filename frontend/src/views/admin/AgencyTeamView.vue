<template>
  <div class="agency-team">
    <div class="page-wrap">
      <div class="space-y-1">
        <h1 class="page-title">Minha Agência • Equipe</h1>
        <p class="page-sub">Gerencie usuários, convites e permissões com clareza.</p>
      </div>

      <section class="list-card top-summary">
        <div>
          <p class="summary-main">Plano atual: <strong>{{ summary?.plan_key || "-" }}</strong></p>
          <p class="summary-sub">{{ summary?.extra_users_used || 0 }} de {{ summary?.extra_users_limit ?? "8" }} usuários utilizados</p>
        </div>
        <button class="btn btn-p" :disabled="inviteDisabled" @click="showInvite = true">+ Convidar</button>
      </section>
      <p v-if="inviteDisabled" class="warn-msg">Seu plano atingiu o limite de usuários extras.</p>

      <section class="list-card">
        <h2 class="card-title">Equipe</h2>
        <div v-if="!(summary?.members || []).length" class="empty-state">Nenhum usuário na equipe.</div>
        <div v-else class="member-list">
          <article
            v-for="member in summary?.members || []"
            :key="member.id"
            class="member-card"
            @click="openEdit(member)"
          >
            <div class="member-top">
              <div class="member-main">
              <div class="avatar">
                <img
                  v-if="member.avatar_url"
                  :src="member.avatar_url"
                  :alt="`Avatar de ${member.name}`"
                  class="avatar-image"
                />
                <span v-else>{{ getInitials(member.name || member.email) }}</span>
              </div>
              <div class="member-copy">
                <div class="name-row">
                  <p class="member-name">{{ member.name }}</p>
                  <span v-if="member.is_owner" class="badge badge-green">Admin principal</span>
                </div>
                <p class="member-email">{{ member.email }}</p>
              </div>
            </div>
              <div class="member-actions" @click.stop>
                <button class="btn btn-p btn-sm" @click="openEdit(member)">Editar permissões</button>
                <button
                  :ref="el => setMemberActionAnchor(member.id, el as HTMLElement | null)"
                  class="icon-btn"
                  @click="toggleMemberActions(member.id)"
                >
                  ...
                </button>
              </div>
            </div>

            <div class="member-meta">
              <span class="meta-label">Tipo:</span>
              <span class="badge badge-info">
                {{
                  member.role === "admin"
                    ? "Admin"
                    : member.role === "editor"
                      ? "Editor"
                      : member.role === "viewer"
                        ? "Visualizador"
                        : "Personalizado"
                }}
              </span>
              <span class="meta-label">Status:</span>
              <span :class="member.status === 'active' ? 'badge badge-green' : 'badge badge-muted'">
                {{ member.status === "active" ? "Ativo" : "Inativo" }}
              </span>
            </div>

            <div class="perm-row">
              <span class="meta-label">Permissões:</span>
              <p class="perm-summary">{{ formatPermissionSummary(member.permissions || []) }}</p>
            </div>
          </article>
        </div>
      </section>

      <teleport to="body">
        <div
          v-if="openMemberActionsId !== null && openMemberActions"
          class="fixed inset-0 z-[220]"
          @click="openMemberActionsId = null"
        >
          <div
            class="absolute min-w-[190px] rounded-lg border border-slate-200 bg-white p-1 shadow-xl"
            :style="{ top: `${memberActionsPosition.top}px`, left: `${memberActionsPosition.left}px` }"
            @click.stop
          >
            <template v-if="!openMemberActions.is_owner">
              <button class="menu-item" @click="handleEditFromMenu(openMemberActions)">Editar permissões</button>
              <button class="menu-item" @click="handleMakeAdminFromMenu(openMemberActions.id)">Tornar admin</button>
              <button class="menu-item" @click="handleResetAccessFromMenu(openMemberActions.id)">Resetar acesso</button>
              <button class="menu-item danger" @click="handleDisableFromMenu(openMemberActions.id)">Remover usuário</button>
            </template>
            <span v-else class="block px-3 py-2 text-sm text-slate-400">Admin principal</span>
          </div>
        </div>
      </teleport>

      <section class="list-card" v-if="(summary?.pending_invites || []).length">
        <h2 class="card-title">Convites pendentes</h2>
        <div class="invite-list">
          <article v-for="invite in summary?.pending_invites || []" :key="invite.id" class="invite-card">
            <div>
              <p class="invite-email">{{ invite.email }}</p>
              <p class="invite-status">Aguardando aceitação</p>
            </div>
            <div class="invite-actions">
              <button class="btn btn-o btn-sm" @click="resendInvite(invite.id)">Reenviar</button>
              <button class="btn btn-danger btn-sm" @click="cancelInvite(invite.id)">Cancelar</button>
            </div>
          </article>
        </div>
      </section>

      <div v-if="showInvite || editingMember" class="app-modal-overlay fixed inset-0 z-40 flex items-center justify-center px-4">
        <div class="permission-modal">
          <div class="modal-header">
            <h3 class="text-xl font-bold text-slate-900">{{ editingMember ? `Editar permissões de ${editingMember.name}` : "Convidar membro da equipe" }}</h3>
          </div>

          <div class="modal-body">
          <div v-if="!editingMember" class="mt-1 grid gap-3 md:grid-cols-2">
            <input v-model="form.name" class="rounded-lg border border-slate-200 px-3 py-2" placeholder="Nome" />
            <input v-model="form.email" class="rounded-lg border border-slate-200 px-3 py-2" placeholder="E-mail" />
          </div>

          <div class="mt-4">
            <p class="text-sm font-semibold text-slate-700">Nível de acesso</p>
            <div class="mt-2 space-y-2">
              <label class="flex items-start gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <input type="radio" name="access_profile" :checked="accessProfile==='admin'" @change="applyAccessProfile('admin')" />
                <span><strong>Admin</strong><br /><small class="text-slate-500">Acesso total ao sistema</small></span>
              </label>
              <label class="flex items-start gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <input type="radio" name="access_profile" :checked="accessProfile==='editor'" @change="applyAccessProfile('editor')" />
                <span><strong>Editor</strong><br /><small class="text-slate-500">Pode editar páginas e leads</small></span>
              </label>
              <label class="flex items-start gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <input type="radio" name="access_profile" :checked="accessProfile==='viewer'" @change="applyAccessProfile('viewer')" />
                <span><strong>Visualizador</strong><br /><small class="text-slate-500">Apenas visualização</small></span>
              </label>
              <label class="flex items-start gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <input type="radio" name="access_profile" :checked="accessProfile==='custom'" @change="applyAccessProfile('custom')" />
                <span><strong>Personalizado</strong><br /><small class="text-slate-500">Definir acesso manualmente</small></span>
              </label>
            </div>
          </div>

          <div v-if="accessProfile === 'custom'" class="mt-4">
            <div class="my-4 h-px bg-slate-200"></div>
            <div class="mt-2 flex flex-wrap gap-2">
              <button class="rounded-md border border-slate-200 px-3 py-1.5 text-sm" @click="resetToDefaultAccess">Resetar para padrão</button>
              <select class="rounded-md border border-slate-200 px-3 py-1.5 text-sm" @change="copyPermissionsFromUser(Number(($event.target as HTMLSelectElement).value))">
                <option value="">Copiar permissões de outro usuário</option>
                <option v-for="member in availableMembersForCopy" :key="`copy-${member.id}`" :value="member.id">{{ member.name }}</option>
              </select>
            </div>

            <div class="mt-4 space-y-3">
              <p class="text-sm font-semibold text-slate-700">Permissões detalhadas</p>

              <div class="rounded-lg border border-slate-200">
                <button class="w-full px-3 py-2 text-left text-sm font-semibold text-slate-800" @click="accordionOpen.pages = !accordionOpen.pages">{{ accordionOpen.pages ? "-" : "+" }} Páginas</button>
                <transition name="acc">
                  <div v-show="accordionOpen.pages" class="px-3 pb-2">
                    <div class="mt-1 flex flex-wrap gap-2">
                      <button class="rounded-md border px-3 py-1.5 text-sm" :class="!form.permissions.includes('pages_viewer') && !form.permissions.includes('pages_editor') ? 'border-emerald-500 bg-emerald-50 text-emerald-700':'border-slate-200'" :disabled="!canUsePages" @click="form.permissions = form.permissions.filter(p => p !== 'pages_viewer' && p !== 'pages_editor')">Nenhum</button>
                      <button class="rounded-md border px-3 py-1.5 text-sm" :class="form.pages_level==='viewer' ? 'border-emerald-500 bg-emerald-50 text-emerald-700':'border-slate-200'" :disabled="!canUsePages" @click="setPagesLevel('viewer')">Visualizador</button>
                      <button class="rounded-md border px-3 py-1.5 text-sm" :class="form.pages_level==='editor' ? 'border-emerald-500 bg-emerald-50 text-emerald-700':'border-slate-200'" :disabled="!canUsePages" @click="setPagesLevel('editor')">Editor</button>
                    </div>
                  </div>
                </transition>
              </div>

              <div class="rounded-lg border border-slate-200">
                <button class="w-full px-3 py-2 text-left text-sm font-semibold text-slate-800" @click="accordionOpen.leads = !accordionOpen.leads">{{ accordionOpen.leads ? "-" : "+" }} Captação de leads</button>
                <transition name="acc">
                  <div v-show="accordionOpen.leads" class="px-3 pb-2">
                    <div class="mt-1 grid gap-1.5 md:grid-cols-2">
                      <label v-for="k in leadsSubKeys" :key="k.key" class="flex items-center justify-between gap-2 rounded border px-2 py-1" :class="canUseLeads ? 'border-slate-200':'border-slate-100 bg-slate-50 text-slate-400'">
                        <span class="text-sm">{{ k.label }}</span>
                        <input type="checkbox" :disabled="!canUseLeads" :checked="form.permissions.includes(k.key)" @change="togglePerm(k.key)" />
                      </label>
                    </div>
                    <div class="mt-2 flex flex-wrap gap-2">
                      <button class="rounded-md border px-3 py-1.5 text-sm" :class="form.leads_level==='manager' ? 'border-emerald-500 bg-emerald-50 text-emerald-700':'border-slate-200'" :disabled="!canUseLeads" @click="setLeadsLevel('manager')">Gerencial</button>
                      <button class="rounded-md border px-3 py-1.5 text-sm" :class="form.leads_level==='full' ? 'border-emerald-500 bg-emerald-50 text-emerald-700':'border-slate-200'" :disabled="!canUseLeads" @click="setLeadsLevel('full')">Total</button>
                    </div>
                  </div>
                </transition>
              </div>

              <div class="rounded-lg border border-slate-200">
                <button class="w-full px-3 py-2 text-left text-sm font-semibold text-slate-800" @click="accordionOpen.system = !accordionOpen.system">{{ accordionOpen.system ? "-" : "+" }} Sistema</button>
                <transition name="acc">
                  <div v-show="accordionOpen.system" class="px-3 pb-2">
                    <div class="mt-1 grid gap-1.5 md:grid-cols-2">
                      <label v-for="item in extraPermissionOptions" :key="item.key" class="flex items-center justify-between gap-2 rounded-lg border px-3 py-1.5 text-sm" :class="item.allowed ? 'border-slate-200' : 'border-slate-100 bg-slate-50 text-slate-400'">
                        <span>{{ item.label }}</span>
                        <input type="checkbox" :value="item.key" :disabled="!item.allowed" :checked="form.permissions.includes(item.key)" @change="togglePerm(item.key)" />
                      </label>
                    </div>
                  </div>
                </transition>
              </div>
            </div>
          </div>

          <p v-else class="mt-4 text-sm text-slate-500">As permissões detalhadas ficam ocultas para simplificar a configuração.</p>

          <p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>
          </div>
          <div class="modal-footer">
            <button class="rounded border border-slate-200 px-4 py-2" @click="closeModal">Cancelar</button>
            <button class="rounded bg-[#41ce5f] px-4 py-2 font-semibold text-[#0f1f14] disabled:opacity-60" :disabled="savingPermissions" @click="saveModal">
              {{ savingPermissions ? "Salvando..." : (editingMember ? "Salvar permissões" : "Enviar convite") }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";

const summary = ref<any>(null);
const showInvite = ref(false);
const editingMember = ref<any>(null);
const openMemberActionsId = ref<number | null>(null);
const memberActionAnchors = new Map<number, HTMLElement>();
const memberActionsPosition = ref({ top: 0, left: 0 });
const error = ref("");
const savingPermissions = ref(false);
const accessProfile = ref<"admin" | "editor" | "viewer" | "custom">("editor");
const accordionOpen = reactive({
  pages: true,
  leads: false,
  system: false
});
const form = reactive({
  name: "",
  email: "",
  role: "member",
  permissions: [] as string[],
  pages_level: "viewer" as "viewer" | "editor",
  leads_level: "manager" as "manager" | "full"
});

const labels: Record<string, string> = {
  dashboard: "Dashboard",
  pages_viewer: "Páginas (visualizador)",
  pages_editor: "Páginas (editor)",
  leads_forms: "Leads: Formulários",
  leads_opportunities: "Leads: Oportunidades",
  leads_clients: "Leads: Clientes",
  leads_settings: "Leads: Configurações",
  leads_manager: "Leads (gerencial)",
  leads_full: "Leads (total)",
  integrations: "Integrações",
  domains: "Domínios",
  lessons: "Aulas",
  settings: "Minha Agência"
};

const leadsSubKeys = [
  { key: "leads_forms", label: "Formulários" },
  { key: "leads_opportunities", label: "Oportunidades" },
  { key: "leads_clients", label: "Clientes" },
  { key: "leads_settings", label: "Configurações" }
];

const inviteDisabled = computed(() => {
  if (!summary.value) return true;
  const limit = summary.value.extra_users_limit;
  if (limit == null) return false;
  return summary.value.extra_users_used >= limit;
});

const allowedSet = computed(() => new Set<string>(summary.value?.plan_allowed_permissions || []));
const canUsePages = computed(() => allowedSet.value.has("pages") || allowedSet.value.has("pages_viewer") || allowedSet.value.has("pages_editor"));
const canUseLeads = computed(() => allowedSet.value.has("leads") || allowedSet.value.has("leads_forms") || allowedSet.value.has("leads_full"));
const availableMembersForCopy = computed(() =>
  (summary.value?.members || []).filter((m: any) => !editingMember.value || m.id !== editingMember.value.id)
);

const extraPermissionOptions = computed(() => {
  const keys = ["dashboard", "integrations", "domains", "lessons", "settings"];
  return keys.map(key => ({ key, label: labels[key], allowed: allowedSet.value.has(key) }));
});

const systemPermissionKeys = ["dashboard", "integrations", "domains", "lessons", "settings"] as const;

const load = async () => {
  const { data } = await api.get("/agency/team");
  summary.value = data;
};

const getInitials = (value?: string) => {
  const text = (value || "").trim();
  if (!text) return "?";
  const parts = text.split(/\s+/).filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0] || ""}${parts[1][0] || ""}`.toUpperCase();
};

const formatPermissionSummary = (permissions: string[]) => {
  if (!permissions.length) return "Sem permissões";
  const uniqueLabels = [...new Set(permissions.map(p => labels[p] || p))];
  const visible = uniqueLabels.slice(0, 4);
  const rest = uniqueLabels.length - visible.length;
  return `${visible.join(" • ")}${rest > 0 ? ` +${rest}` : ""}`;
};

const closeModal = () => {
  showInvite.value = false;
  editingMember.value = null;
  error.value = "";
  form.name = "";
  form.email = "";
  form.role = "member";
  form.permissions = [];
  form.pages_level = "viewer";
  form.leads_level = "manager";
};

const getEditorPermissions = () => {
  const perms = new Set<string>();
  if (allowedSet.value.has("dashboard")) perms.add("dashboard");
  if (canUsePages.value) perms.add("pages_editor");
  if (canUseLeads.value) {
    perms.add("leads_forms");
    perms.add("leads_opportunities");
    perms.add("leads_clients");
    perms.add("leads_settings");
    perms.add("leads_full");
  }
  return [...perms];
};

const getViewerPermissions = () => {
  const perms = new Set<string>();
  if (allowedSet.value.has("dashboard")) perms.add("dashboard");
  if (canUsePages.value) perms.add("pages_viewer");
  if (canUseLeads.value) {
    perms.add("leads");
    perms.add("leads_forms");
    perms.add("leads_opportunities");
    perms.add("leads_clients");
    perms.add("leads_settings");
  }
  if (allowedSet.value.has("integrations")) perms.add("integrations");
  if (allowedSet.value.has("domains")) perms.add("domains");
  return [...perms];
};

const setToArray = (value: Set<string>) => [...value];

const getAllAllowedMemberPermissions = () => {
  const all = new Set<string>();
  if (canUsePages.value) all.add("pages_editor");
  if (canUseLeads.value) {
    leadsSubKeys.forEach(k => all.add(k.key));
    all.add("leads_full");
  }
  systemPermissionKeys.forEach(k => {
    if (allowedSet.value.has(k)) all.add(k);
  });
  return setToArray(all);
};

const samePermissionSet = (left: string[], right: string[]) => {
  const a = new Set(left);
  const b = new Set(right);
  if (a.size !== b.size) return false;
  for (const key of a) if (!b.has(key)) return false;
  return true;
};

const deriveAccessProfile = (role: string, permissions: string[]) => {
  if (role === "admin") return "admin";
  if (role === "editor") return "editor";
  if (role === "viewer") return "viewer";
  if (role === "custom") return "custom";
  if (samePermissionSet(permissions, getEditorPermissions())) return "editor";
  if (samePermissionSet(permissions, getViewerPermissions())) return "viewer";
  return "custom";
};

const applyAccessProfile = (profile: "admin" | "editor" | "viewer" | "custom") => {
  accessProfile.value = profile;
  if (profile === "admin") {
    form.role = "admin";
    form.permissions = [];
    return;
  }
  form.role = profile;
  if (profile === "editor") {
    form.permissions = getEditorPermissions();
    hydrateDerived();
    return;
  }
  if (profile === "viewer") {
    form.permissions = getViewerPermissions();
    hydrateDerived();
    return;
  }
  if (profile === "custom") {
    form.permissions = getAllAllowedMemberPermissions();
    hydrateDerived();
    form.permissions = [...form.permissions];
  }
};

const hydrateDerived = () => {
  form.pages_level = form.permissions.includes("pages_editor") ? "editor" : "viewer";
  form.leads_level = form.permissions.includes("leads_full") ? "full" : "manager";
};

const openEdit = (member: any) => {
  editingMember.value = member;
  form.role = (member.role || "custom") as "admin" | "editor" | "viewer" | "custom" | "member";
  form.permissions = [...(member.permissions || [])];
  hydrateDerived();
  accessProfile.value = deriveAccessProfile(form.role, form.permissions);
  showInvite.value = false;
};

const copyPermissionsFromUser = (userId: number) => {
  const source = (summary.value?.members || []).find((m: any) => m.id === userId);
  if (!source) return;
  form.role = (source.role || "member") === "admin" ? "admin" : "member";
  form.permissions = [...(source.permissions || [])];
  hydrateDerived();
  accessProfile.value = deriveAccessProfile(form.role, form.permissions);
};

const resetToDefaultAccess = () => {
  applyAccessProfile("editor");
};

const toggleMemberActions = (memberId: number) => {
  if (openMemberActionsId.value === memberId) {
    openMemberActionsId.value = null;
    return;
  }
  const anchor = memberActionAnchors.get(memberId);
  if (!anchor) return;
  const rect = anchor.getBoundingClientRect();
  const menuWidth = 190;
  const viewportPadding = 8;
  const left = Math.min(
    window.innerWidth - menuWidth - viewportPadding,
    Math.max(viewportPadding, rect.right - menuWidth)
  );
  const top = rect.bottom + 8;
  memberActionsPosition.value = { top, left };
  openMemberActionsId.value = memberId;
};

const setMemberActionAnchor = (memberId: number, el: HTMLElement | null) => {
  if (!el) {
    memberActionAnchors.delete(memberId);
    return;
  }
  memberActionAnchors.set(memberId, el);
};

const openMemberActions = computed(() =>
  (summary.value?.members || []).find((member: any) => member.id === openMemberActionsId.value) || null
);

const handleEditFromMenu = (member: any) => {
  openMemberActionsId.value = null;
  openEdit(member);
};

const handleDisableFromMenu = async (memberId: number) => {
  openMemberActionsId.value = null;
  await disableMember(memberId);
};

const handleMakeAdminFromMenu = async (memberId: number) => {
  openMemberActionsId.value = null;
  await api.patch(`/agency/team/users/${memberId}/permissions`, { role: "admin", permissions: [] });
  await load();
};

const handleResetAccessFromMenu = async (memberId: number) => {
  openMemberActionsId.value = null;
  applyAccessProfile("editor");
  await api.patch(`/agency/team/users/${memberId}/permissions`, {
    role: "member",
    permissions: buildPayloadPermissions()
  });
  await load();
};

const togglePerm = (key: string) => {
  const has = form.permissions.includes(key);
  if (has) form.permissions = form.permissions.filter(p => p !== key);
  else form.permissions = [...form.permissions, key];
};

const setPagesLevel = (level: "viewer" | "editor") => {
  form.pages_level = level;
  form.permissions = form.permissions.filter(p => p !== "pages_viewer" && p !== "pages_editor");
  form.permissions.push(level === "editor" ? "pages_editor" : "pages_viewer");
};

const setLeadsLevel = (level: "manager" | "full") => {
  form.leads_level = level;
  form.permissions = form.permissions.filter(p => p !== "leads_manager" && p !== "leads_full");
  form.permissions.push(level === "full" ? "leads_full" : "leads_manager");
};

const togglePagesModule = (checked: boolean) => {
  form.permissions = form.permissions.filter(p => p !== "pages_viewer" && p !== "pages_editor");
  if (checked && canUsePages.value) {
    form.permissions.push(form.pages_level === "editor" ? "pages_editor" : "pages_viewer");
  }
};

const toggleLeadsModule = (checked: boolean) => {
  form.permissions = form.permissions.filter(
    p => !["leads_forms", "leads_opportunities", "leads_clients", "leads_settings", "leads_manager", "leads_full"].includes(p)
  );
  if (checked && canUseLeads.value) {
    leadsSubKeys.forEach(k => form.permissions.push(k.key));
    form.permissions.push(form.leads_level === "full" ? "leads_full" : "leads_manager");
  }
};

const buildPayloadPermissions = () => {
  if (accessProfile.value === "admin") return [];
  if (accessProfile.value === "editor") return getEditorPermissions();
  if (accessProfile.value === "viewer") return getViewerPermissions();
  if (accessProfile.value !== "custom") return getEditorPermissions();
  let perms = [...form.permissions];
  if (canUsePages.value && !perms.includes("pages_viewer") && !perms.includes("pages_editor")) {
    perms.push(form.pages_level === "editor" ? "pages_editor" : "pages_viewer");
  }
  if (canUseLeads.value && !perms.includes("leads_manager") && !perms.includes("leads_full")) {
    perms.push(form.leads_level === "full" ? "leads_full" : "leads_manager");
  }
  return [...new Set(perms)];
};

const saveModal = async () => {
  error.value = "";
  savingPermissions.value = true;
  try {
    const payload = {
      role: accessProfile.value,
      permissions: buildPayloadPermissions()
    };

    if (editingMember.value) {
      await api.patch(`/agency/team/users/${editingMember.value.id}/permissions`, payload);
    } else {
      await api.post("/agency/team/invites", {
        name: form.name,
        email: form.email,
        ...payload
      });
    }
    closeModal();
    await load();
  } catch (err: any) {
    error.value = err?.response?.data?.detail || "Não foi possível salvar.";
  } finally {
    savingPermissions.value = false;
  }
};

watch(
  () => showInvite.value,
  value => {
    if (value && !editingMember.value) {
      applyAccessProfile("editor");
    }
  }
);

const resendInvite = async (id: number) => {
  await api.post(`/agency/team/invites/${id}/resend`);
  await load();
};
const cancelInvite = async (id: number) => {
  await api.post(`/agency/team/invites/${id}/cancel`);
  await load();
};
const disableMember = async (id: number) => {
  await api.patch(`/agency/team/users/${id}/disable`);
  await load();
};

onMounted(load);

const closeMemberActions = () => {
  openMemberActionsId.value = null;
};

onMounted(() => {
  window.addEventListener("resize", closeMemberActions);
  window.addEventListener("scroll", closeMemberActions, true);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", closeMemberActions);
  window.removeEventListener("scroll", closeMemberActions, true);
});
</script>

<style scoped>
.agency-team{--verde:#3DCC5F;--verde-d:#2EAD4C;--verde-dim:rgba(61,204,95,.10);--verde-border:rgba(61,204,95,.22);--surface:#fff;--surface2:#F5F7F5;--border:#E4E9E4;--text:#111A14;--text-2:#4A5E4A;--text-3:#8A9E8A;--sh-sm:0 1px 3px rgba(0,0,0,.05),0 1px 2px rgba(0,0,0,.03)}
.page-wrap{padding:28px 32px 64px;width:100%;max-width:1200px}
.page-title{font-size:24px;font-weight:800;color:var(--text);letter-spacing:-.3px;line-height:1.2}
.page-sub{font-size:13px;color:var(--text-3)}
.list-card{margin-top:12px;background:var(--surface);border:1.5px solid var(--border);border-radius:12px;padding:16px;box-shadow:var(--sh-sm)}
.top-summary{display:flex;align-items:center;justify-content:space-between;gap:12px}
.summary-main{font-size:14px;color:var(--text-2)}
.summary-sub{font-size:13px;color:var(--text-3)}
.warn-msg{margin-top:8px;font-size:12px;color:#b45309}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:999px;font-size:13px;font-weight:700;cursor:pointer;border:none;transition:.15s;line-height:1.3}
.btn-sm{padding:6px 12px;font-size:12px}
.btn-p{background:var(--verde);color:#0F1F14}.btn-p:hover{background:var(--verde-d)}
.btn-o{background:#fff;border:1px solid var(--border);color:var(--text-2)}.btn-o:hover{border-color:#cbd6cb;color:var(--text)}
.btn-danger{background:#fff6f6;border:1px solid #f3caca;color:#c0392b}.btn-danger:hover{background:#ffeaea}
.card-title{font-size:18px;font-weight:800;color:var(--text)}
.empty-state{margin-top:10px;border:1px dashed var(--border);border-radius:10px;padding:14px;color:var(--text-3);font-size:13px;background:var(--surface2)}
.member-list{margin-top:10px;display:flex;flex-direction:column;gap:10px}
.member-card{border:1px solid var(--border);border-radius:12px;background:#fff;padding:12px 14px;transition:.15s;cursor:pointer}
.member-card:hover{border-color:#d3dbd3;box-shadow:0 3px 10px rgba(17,26,20,.06)}
.member-top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.member-main{display:flex;align-items:center;gap:10px;min-width:0}
.avatar{width:42px;height:42px;border-radius:999px;background:#e7efe7;color:var(--text-2);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px}
.avatar-image{width:100%;height:100%;object-fit:cover;border-radius:999px;display:block}
.name-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.member-name{font-size:16px;font-weight:800;color:var(--text);letter-spacing:-.2px;line-height:1.2}
.member-email{font-size:13px;color:var(--text-2)}
.member-meta{margin-top:8px;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.meta-label{font-size:12px;font-weight:700;color:var(--text-3)}
.perm-row{margin-top:6px;display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap}
.perm-summary{font-size:13px;color:var(--text-2)}
.member-actions{display:flex;gap:8px;align-items:center;flex-shrink:0}
.icon-btn{width:34px;height:34px;border-radius:999px;border:1px solid var(--border);background:#fff;color:var(--text-2);font-size:20px;line-height:1;display:flex;align-items:center;justify-content:center}
.icon-btn:hover{border-color:#cbd6cb;color:var(--text)}
.menu-item{display:flex;width:100%;border:none;background:transparent;border-radius:6px;padding:8px 10px;text-align:left;font-size:13px;color:#334155}
.menu-item:hover{background:#f8fafc}.menu-item.danger{color:#dc2626}.menu-item.danger:hover{background:#fef2f2}
.invite-list{margin-top:10px;display:flex;flex-direction:column;gap:10px}
.invite-card{border:1px solid var(--border);border-radius:10px;padding:12px;display:flex;align-items:center;justify-content:space-between;gap:10px;background:#fff}
.invite-email{font-size:14px;font-weight:700;color:var(--text)}
.invite-status{font-size:12px;color:var(--text-3)}
.invite-actions{display:flex;gap:8px;flex-wrap:wrap}
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:700;line-height:1.4}
.badge-green{background:var(--verde-dim);color:#1A7A35;border:1.5px solid var(--verde-border)}
.badge-info{background:#e8f3ff;color:#1d5d99;border:1px solid #cde4ff}
.badge-muted{background:#e9eeea;color:#5f6f5f;border:1px solid var(--border)}
.permission-modal{width:min(860px,100%);max-height:calc(100vh - 48px);display:flex;flex-direction:column;background:#fff;border-radius:16px;overflow:hidden}
.modal-header{flex-shrink:0;padding:18px 20px 14px;border-bottom:1px solid var(--border);background:#fff}
.modal-body{flex:1;overflow-y:auto;padding:14px 20px}
.modal-footer{flex-shrink:0;display:flex;justify-content:flex-end;gap:8px;padding:12px 20px;border-top:1px solid var(--border);background:var(--surface)}
.acc-enter-active,.acc-leave-active{transition:all .15s ease}
.acc-enter-from,.acc-leave-to{opacity:0;transform:translateY(-4px)}
@media(max-width:900px){.page-wrap{padding:20px 16px 40px}.top-summary{align-items:flex-start;flex-direction:column}.invite-card{flex-direction:column;align-items:flex-start}.member-top{flex-direction:column}.member-actions{width:100%}}
@media(max-width:640px){.permission-modal{max-height:calc(100vh - 24px)}.modal-header{padding:14px 14px 12px}.modal-body{padding:12px 14px}.modal-footer{padding:10px 14px}}
</style>
