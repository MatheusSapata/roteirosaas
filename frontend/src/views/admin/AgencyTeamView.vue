<template>
  <div class="agency-team">
    <div class="page-wrap">
      <AgencyHeader>
        <template #actions>
          <button class="at-btn-primary" :disabled="inviteDisabled" @click="showInvite = true">
            <PlusIcon aria-hidden="true" />
            Convidar pessoa
          </button>
        </template>
      </AgencyHeader>

      <div class="at-stats">
        <article class="at-stat">
          <span class="at-stat-icon tone-success" aria-hidden="true">
            <StarIcon aria-hidden="true" />
          </span>
          <div>
            <p class="at-stat-k">Plano atual</p>
            <p class="at-stat-v">{{ planLabel }}</p>
          </div>
        </article>
        <article class="at-stat">
          <span class="at-stat-icon tone-info" aria-hidden="true">
            <UsersIcon aria-hidden="true" />
          </span>
          <div>
            <p class="at-stat-k">Pessoas na equipe</p>
            <p class="at-stat-v">
              {{ members.length }}
              <small v-if="pendingInvites.length">+{{ pendingInvites.length }} {{ pendingInvites.length === 1 ? "convite pendente" : "convites pendentes" }}</small>
            </p>
          </div>
        </article>
        <article class="at-stat">
          <span class="at-stat-icon tone-warning" aria-hidden="true">
            <UserPlusIcon aria-hidden="true" />
          </span>
          <div class="min-w-0 flex-1">
            <p class="at-stat-k">Usuários extras</p>
            <p class="at-stat-v">{{ summary?.extra_users_used || 0 }} de {{ summary?.extra_users_limit ?? "∞" }}</p>
            <div v-if="summary?.extra_users_limit" class="at-meter"><i :style="{ width: `${extraUsage}%` }"></i></div>
          </div>
        </article>
      </div>
      <p v-if="inviteDisabled && summary" class="at-warn">Seu plano atingiu o limite de usuários extras.</p>

      <section class="at-card">
        <h2 class="at-card-title">Equipe</h2>
        <div v-if="!members.length" class="at-empty">Nenhuma pessoa na equipe.</div>
        <table v-else class="at-table">
          <thead>
            <tr>
              <th>Pessoa</th>
              <th>Acesso</th>
              <th>Pode usar</th>
              <th>Situação</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="member in members" :key="member.id">
              <td>
                <div class="at-person">
                  <span class="at-avatar" :class="member.is_owner ? 'tone-success' : avatarTone(member.id)">
                    <img v-if="member.avatar_url" :src="member.avatar_url" :alt="`Avatar de ${member.name}`" />
                    <template v-else>{{ getInitials(member.name || member.email) }}</template>
                  </span>
                  <span class="min-w-0">
                    <b>{{ member.name }}</b>
                    <small>{{ member.email }}</small>
                  </span>
                </div>
              </td>
              <td><span class="at-pill" :class="accessTone(member)">{{ accessLabel(member) }}</span></td>
              <td>
                <div class="at-chips">
                  <span v-for="chip in chipsForMember(member)" :key="chip" class="at-chip">{{ chip }}</span>
                </div>
              </td>
              <td><span class="at-pill" :class="member.status === 'active' ? 'is-success' : 'is-muted'">{{ member.status === "active" ? "Ativo" : "Inativo" }}</span></td>
              <td>
                <div class="at-actions">
                  <button v-if="!member.is_owner" type="button" class="at-btn-ghost" @click="openEdit(member)">
                    <ShieldIcon aria-hidden="true" />
                    Permissões
                  </button>
                  <button
                    :ref="el => setMemberActionAnchor(member.id, el as HTMLElement | null)"
                    type="button"
                    class="at-icon-btn"
                    aria-label="Mais ações"
                    title="Mais ações"
                    @click="toggleMemberActions(member.id)"
                  >
                    <EllipsisVerticalIcon aria-hidden="true" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <template v-if="pendingInvites.length">
          <h2 class="at-card-title at-card-title-sub">Convites pendentes</h2>
          <table class="at-table at-table-invites">
            <tbody>
              <tr v-for="invite in pendingInvites" :key="invite.id">
                <td>
                  <div class="at-person">
                    <span class="at-avatar is-mail" aria-hidden="true">
                      <MailIcon aria-hidden="true" />
                    </span>
                    <span class="min-w-0">
                      <b>{{ invite.email }}</b>
                      <small v-if="invite.created_at">Enviado em {{ formatDate(invite.created_at) }}</small>
                    </span>
                  </div>
                </td>
                <td>
                  <div class="at-chips">
                    <span v-for="chip in chipsForMember(invite)" :key="chip" class="at-chip">{{ chip }}</span>
                  </div>
                </td>
                <td><span class="at-pill is-warning">Aguardando</span></td>
                <td>
                  <div class="at-actions">
                    <button type="button" class="at-btn-ghost" @click="resendInvite(invite.id)">Reenviar</button>
                    <div class="at-menu-wrap">
                      <button type="button" class="at-icon-btn" aria-label="Mais ações" title="Mais ações" @click.stop="openInviteMenuId = openInviteMenuId === invite.id ? null : invite.id">
                        <EllipsisVerticalIcon aria-hidden="true" />
                      </button>
                      <div v-if="openInviteMenuId === invite.id" class="at-menu" @click="openInviteMenuId = null">
                        <button type="button" class="danger" @click="cancelInvite(invite.id)">Cancelar convite</button>
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </template>
      </section>

      <teleport to="body">
        <div
          v-if="openMemberActionsId !== null && openMemberActions"
          class="fixed inset-0 z-[220]"
          @click="openMemberActionsId = null"
        >
          <div
            class="at-menu at-menu-floating"
            :style="{ top: `${memberActionsPosition.top}px`, left: `${memberActionsPosition.left}px` }"
            @click.stop
          >
            <template v-if="!openMemberActions.is_owner">
              <button @click="handleEditFromMenu(openMemberActions)">Editar permissões</button>
              <button @click="handleMakeAdminFromMenu(openMemberActions.id)">Tornar admin</button>
              <button @click="handleResetAccessFromMenu(openMemberActions.id)">Resetar acesso</button>
              <button class="danger" @click="handleDisableFromMenu(openMemberActions.id)">Remover usuário</button>
            </template>
            <span v-else class="at-menu-note">Dono da conta: o acesso não pode ser alterado.</span>
          </div>
        </div>
      </teleport>

      <teleport to="body">
        <div v-if="showInvite || editingMember" class="app-modal-overlay at-overlay" @click.self="closeModal">
          <div class="at-modal" role="dialog" aria-modal="true">
            <header class="at-modal-head">
              <span v-if="editingMember" class="at-avatar" :class="avatarTone(editingMember.id)">{{ getInitials(editingMember.name || editingMember.email) }}</span>
              <span v-else class="at-avatar tone-success" aria-hidden="true">
                <UserPlusIcon aria-hidden="true" />
              </span>
              <div class="min-w-0 flex-1">
                <h3>{{ editingMember ? `Permissões de ${editingMember.name}` : "Convidar para a equipe" }}</h3>
                <p>{{ editingMember ? editingMember.email : "A pessoa recebe um e-mail para criar a senha e entrar." }}</p>
              </div>
              <button type="button" class="at-close" aria-label="Fechar" @click="closeModal">
                <XIcon aria-hidden="true" />
              </button>
            </header>

            <div v-if="!editingMember" class="at-fields">
              <label>
                <span>Nome</span>
                <input v-model="form.name" class="at-input" placeholder="Nome" />
              </label>
              <label>
                <span>E-mail</span>
                <input v-model="form.email" type="email" class="at-input" placeholder="E-mail" />
              </label>
            </div>

            <p class="at-label">Nível de acesso</p>
            <div class="at-levels">
              <button
                v-for="level in accessLevels"
                :key="level.id"
                type="button"
                class="at-level"
                :class="{ on: accessProfile === level.id }"
                @click="applyAccessProfile(level.id)"
              >
                <span class="at-level-icon" :class="level.tone" aria-hidden="true">
                  <component :is="level.icon" />
                </span>
                <span class="min-w-0 flex-1">
                  <b>{{ level.label }}</b>
                  <small>{{ level.description }}</small>
                </span>
                <i class="at-radio" aria-hidden="true"></i>
              </button>
            </div>

            <template v-if="accessProfile === 'custom'">
              <p class="at-label">{{ editingMember ? `O que ${firstName(editingMember.name)} pode usar` : "O que a pessoa pode usar" }}</p>
              <div class="at-areas">
                <label v-for="area in areaOptions" :key="area.key" class="at-area" :class="{ 'is-disabled': !area.allowed }">
                  <span>{{ area.label }}</span>
                  <button
                    type="button"
                    role="switch"
                    class="at-switch"
                    :class="{ on: isAreaOn(area.key, form.permissions) }"
                    :aria-checked="isAreaOn(area.key, form.permissions)"
                    :disabled="!area.allowed"
                    @click="toggleArea(area.key)"
                  ><i></i></button>
                </label>
              </div>
            </template>
            <p v-else class="at-preview">
              <span>Vai poder usar:</span>
              <span v-for="chip in previewChips" :key="chip" class="at-chip">{{ chip }}</span>
            </p>

            <p v-if="error" class="at-error">{{ error }}</p>

            <footer class="at-modal-foot">
              <button type="button" class="at-btn-ghost at-btn-lg" @click="closeModal">Cancelar</button>
              <button type="button" class="at-btn-primary" :disabled="savingPermissions" @click="saveModal">
                {{ savingPermissions ? "Salvando..." : (editingMember ? "Salvar permissões" : "Enviar convite") }}
              </button>
            </footer>
          </div>
        </div>
      </teleport>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  EllipsisVerticalIcon,
  EyeIcon,
  MailIcon,
  PencilIcon,
  PlusIcon,
  ShieldIcon,
  SlidersVerticalIcon,
  StarIcon,
  UserPlusIcon,
  UsersIcon,
  XIcon
} from "lucide-vue-next";
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";
import AgencyHeader from "../../components/admin/agency/AgencyHeader.vue";
import { agencyCounts } from "../../composables/useAgencyCounts";

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
  agencyCounts.team = Array.isArray(data?.members) ? data.members.length : 0;
};

// ===== Visual da proposta: tabela, níveis de acesso e áreas =====
const members = computed<any[]>(() => summary.value?.members || []);
const pendingInvites = computed<any[]>(() => summary.value?.pending_invites || []);
const openInviteMenuId = ref<number | null>(null);
const closeInviteMenu = (event: MouseEvent) => {
  if (!(event.target as HTMLElement | null)?.closest(".at-menu-wrap")) openInviteMenuId.value = null;
};
onMounted(() => document.addEventListener("click", closeInviteMenu));
onBeforeUnmount(() => document.removeEventListener("click", closeInviteMenu));

const planNames: Record<string, string> = {
  free: "Gratuito",
  professional: "Essencial",
  essencial: "Essencial",
  trial: "Teste grátis",
  agency: "Agência",
  agencia: "Agência",
  growth: "Agência",
  scale: "Escala",
  escala: "Escala",
  infinity: "Escala",
  test: "Teste",
  teste: "Teste"
};
const planLabel = computed(() => {
  const key = String(summary.value?.plan_key || "").trim().toLowerCase();
  if (!key) return "-";
  return planNames[key] || key.charAt(0).toUpperCase() + key.slice(1);
});
const extraUsage = computed(() => {
  const limit = Number(summary.value?.extra_users_limit || 0);
  if (!limit) return 0;
  return Math.min(100, Math.round(((summary.value?.extra_users_used || 0) / limit) * 100));
});

const formatDate = (value?: string) => {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString("pt-BR");
};
const firstName = (value?: string) => String(value || "").trim().split(/\s+/)[0] || "a pessoa";
const avatarTones = ["tone-success", "tone-info", "tone-violet", "tone-warning"];
const avatarTone = (id: number) => avatarTones[Math.abs(Number(id) || 0) % avatarTones.length];

const accessLabel = (member: any) => {
  if (member.is_owner) return "Dono";
  if (member.role === "admin") return "Admin";
  if (member.role === "editor") return "Editor";
  if (member.role === "viewer") return "Visualizador";
  return "Personalizado";
};
const accessTone = (member: any) => {
  if (member.is_owner || member.role === "admin") return "is-success";
  if (member.role === "editor" || member.role === "viewer") return "is-muted";
  return "is-info";
};

// Cada área da proposta aponta para as permissões que já existem.
const leadsAreaKeys = ["leads", "leads_forms", "leads_opportunities", "leads_clients", "leads_settings", "leads_manager", "leads_full"];
const areaDefs = [
  { key: "dashboard", label: "Dashboard" },
  { key: "pages", label: "Páginas" },
  { key: "leads", label: "Leads" },
  { key: "integrations", label: "Integrações" },
  { key: "domains", label: "Domínios" },
  { key: "settings", label: "Minha agência e faturas", chip: "Minha agência" },
  { key: "lessons", label: "Aulas" }
];
const isAreaOn = (area: string, permissions: string[]) => {
  if (area === "pages") return permissions.some(p => p === "pages" || p === "pages_viewer" || p === "pages_editor");
  if (area === "leads") return permissions.some(p => leadsAreaKeys.includes(p));
  return permissions.includes(area);
};
const areaOptions = computed(() =>
  areaDefs.map(area => ({
    ...area,
    allowed: area.key === "pages" ? canUsePages.value : area.key === "leads" ? canUseLeads.value : allowedSet.value.has(area.key)
  }))
);
const toggleArea = (area: string) => {
  const on = !isAreaOn(area, form.permissions);
  if (area === "pages") {
    if (on && !form.permissions.includes("pages_viewer")) form.pages_level = "editor";
    togglePagesModule(on);
    return;
  }
  if (area === "leads") {
    toggleLeadsModule(on);
    return;
  }
  togglePerm(area);
};
const chipsFor = (permissions: string[]) => areaDefs.filter(area => isAreaOn(area.key, permissions)).map(area => area.chip || area.label);
const chipsForMember = (member: any) => {
  if (member.is_owner || member.role === "admin") return ["Tudo"];
  const chips = chipsFor(member.permissions || []);
  return chips.length ? chips : ["Nada ainda"];
};
const previewChips = computed(() => (accessProfile.value === "admin" ? ["Tudo"] : chipsFor(buildPayloadPermissions())));

const accessLevels = [
  { id: "admin" as const, label: "Admin", description: "Acesso a tudo, inclusive equipe e faturas", tone: "tone-success", icon: ShieldIcon },
  { id: "editor" as const, label: "Editor", description: "Edita páginas e cuida dos leads", tone: "tone-info", icon: PencilIcon },
  { id: "viewer" as const, label: "Visualizador", description: "Só consulta, sem alterar nada", tone: "tone-muted", icon: EyeIcon },
  { id: "custom" as const, label: "Personalizado", description: "Você escolhe cada área", tone: "tone-violet", icon: SlidersVerticalIcon }
];

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
.agency-team {
  color: var(--foreground);
}

.page-wrap {
  width: 100%;
  padding: 0 0 48px;
}

.page-eyebrow,
.modal-eyebrow,
.summary-label {
  color: var(--muted-foreground);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.page-title {
  color: var(--foreground);
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 650;
  letter-spacing: -0.3px;
  line-height: 1.2;
}

.page-sub {
  margin-top: 5px;
  color: var(--muted-foreground);
  font-size: 13px;
}

.list-card {
  margin-top: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  background: var(--card);
  padding: 18px;
  color: var(--card-foreground);
  box-shadow: var(--shadow-soft);
}

.top-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.team-summary-grid {
  display: grid;
  flex: 1;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.team-summary-item {
  display: flex;
  min-height: 62px;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  padding: 0 20px;
  border-left: 1px solid color-mix(in srgb, var(--border) 36%, transparent);
}

.team-summary-item:first-child {
  padding-left: 0;
  border-left: 0;
}

.team-summary-item strong {
  color: var(--foreground);
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 650;
}

.warn-msg {
  margin-top: 8px;
  color: var(--status-warning-foreground);
  font-size: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  padding: 9px 14px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.3;
  transition: 0.15s;
}

.btn-sm {
  padding: 7px 12px;
  font-size: 12px;
}

.btn-p {
  background: var(--primary);
  color: var(--primary-foreground);
  box-shadow: var(--shadow-soft);
}

.btn-p:hover:not(:disabled) {
  background: var(--brand-dark);
}

.btn-o {
  border-color: var(--border);
  background: var(--background);
  color: var(--foreground);
}

.btn-o:hover:not(:disabled) {
  background: var(--accent);
}

.btn-danger {
  border-color: color-mix(in srgb, var(--destructive) 28%, var(--border));
  background: color-mix(in srgb, var(--destructive) 8%, var(--card));
  color: var(--destructive);
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.card-title {
  color: var(--foreground);
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 650;
}

.empty-state {
  margin-top: 10px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
  background: var(--muted);
  padding: 18px;
  color: var(--muted-foreground);
  font-size: 13px;
}

.member-list,
.invite-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-top: 10px;
}

.member-card {
  border-top: 1px solid color-mix(in srgb, var(--border) 38%, transparent);
  background: transparent;
  padding: 15px 4px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.member-card:first-child {
  border-top: 0;
}

.member-card:hover {
  background: color-mix(in srgb, var(--accent) 55%, transparent);
}

.member-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.member-main {
  display: flex;
  align-items: center;
  gap: 11px;
  min-width: 0;
}

.avatar {
  display: flex;
  width: 42px;
  height: 42px;
  flex: none;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--muted);
  color: var(--foreground);
  font-size: 12px;
  font-weight: 800;
}

.avatar-image {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 999px;
  object-fit: cover;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.member-name {
  color: var(--foreground);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.2;
}

.member-email,
.perm-summary {
  color: var(--muted-foreground);
  font-size: 13px;
}

.member-meta,
.perm-row {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.meta-label {
  color: var(--muted-foreground);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.member-actions,
.invite-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.icon-btn {
  display: flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--background);
  color: var(--muted-foreground);
  font-size: 19px;
  line-height: 1;
}

.icon-btn:hover {
  background: var(--accent);
  color: var(--foreground);
}

.member-actions-menu {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
}

.member-actions-menu .text-slate-400 {
  color: var(--muted-foreground);
}

.menu-item {
  display: flex;
  width: 100%;
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  padding: 8px 10px;
  color: var(--popover-foreground);
  text-align: left;
  font-size: 13px;
}

.menu-item:hover {
  background: var(--accent);
}

.menu-item.danger {
  color: var(--destructive);
}

.menu-item.danger:hover {
  background: color-mix(in srgb, var(--destructive) 8%, var(--popover));
}

.invite-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border-top: 1px solid color-mix(in srgb, var(--border) 38%, transparent);
  padding: 14px 4px;
}

.invite-card:first-child {
  border-top: 0;
}

.invite-email {
  color: var(--foreground);
  font-size: 14px;
  font-weight: 700;
}

.invite-status {
  color: var(--muted-foreground);
  font-size: 12px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.4;
}

.badge-green {
  border: 1px solid color-mix(in srgb, var(--status-success-foreground) 24%, var(--border));
  background: var(--status-success);
  color: var(--status-success-foreground);
}

.badge-info {
  border: 1px solid color-mix(in srgb, var(--status-info-foreground) 22%, var(--border));
  background: var(--status-info);
  color: var(--status-info-foreground);
}

.badge-muted {
  border: 1px solid var(--border);
  background: var(--status-neutral);
  color: var(--status-neutral-foreground);
}

.permission-modal {
  display: flex;
  width: min(860px, 100%);
  max-height: calc(100vh - 48px);
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: var(--radius-2xl);
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-elegant);
}

.modal-header,
.modal-footer {
  flex-shrink: 0;
  background: var(--card);
}

.modal-header {
  border-bottom: 1px solid color-mix(in srgb, var(--border) 40%, transparent);
  padding: 18px 20px 14px;
}

.modal-header h3 {
  margin-top: 4px;
  color: var(--foreground);
  font-family: var(--font-display);
  font-weight: 650;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  border-top: 1px solid color-mix(in srgb, var(--border) 40%, transparent);
  padding: 12px 20px;
}

.access-profile-option {
  border-color: var(--border);
  background: var(--background);
  color: var(--foreground);
  cursor: pointer;
  transition: 0.15s;
}

.access-profile-option:hover,
.access-profile-option.is-selected {
  border-color: color-mix(in srgb, var(--primary) 35%, var(--border));
  background: color-mix(in srgb, var(--primary) 8%, var(--card));
}

.permission-modal :deep(.border-slate-200),
.permission-modal :deep(.border-slate-100) {
  border-color: var(--border) !important;
}

.permission-modal :deep(.bg-slate-50) {
  background-color: var(--muted) !important;
}

.permission-modal :deep(.text-slate-900),
.permission-modal :deep(.text-slate-800),
.permission-modal :deep(.text-slate-700) {
  color: var(--foreground) !important;
}

.permission-modal :deep(.text-slate-500),
.permission-modal :deep(.text-slate-400) {
  color: var(--muted-foreground) !important;
}

.permission-modal :deep(input),
.permission-modal :deep(select) {
  border-color: var(--input) !important;
  background: var(--background);
  color: var(--foreground);
}

.permission-modal :deep(select option) {
  background: var(--popover);
  color: var(--popover-foreground);
}

.permission-modal :deep(.border-emerald-500) {
  border-color: color-mix(in srgb, var(--primary) 45%, var(--border)) !important;
}

.permission-modal :deep(.bg-emerald-50) {
  background-color: color-mix(in srgb, var(--primary) 10%, var(--card)) !important;
}

.permission-modal :deep(.text-emerald-700) {
  color: var(--primary) !important;
}

.modal-footer > button:first-child {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--background);
  color: var(--foreground);
}

.modal-footer > button:last-child {
  border-radius: var(--radius-lg);
  background: var(--primary) !important;
  color: var(--primary-foreground) !important;
}

.acc-enter-active,
.acc-leave-active {
  transition: all 0.15s ease;
}

.acc-enter-from,
.acc-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 900px) {
  .page-wrap {
    padding: 0 0 32px;
  }

  .top-summary,
  .invite-card,
  .member-top {
    align-items: flex-start;
    flex-direction: column;
  }

  .team-summary-grid {
    width: 100%;
    grid-template-columns: 1fr;
  }

  .team-summary-item {
    min-height: auto;
    border-top: 1px solid color-mix(in srgb, var(--border) 36%, transparent);
    border-left: 0;
    padding: 12px 0;
  }

  .team-summary-item:first-child {
    border-top: 0;
  }

  .member-actions {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .permission-modal {
    max-height: calc(100vh - 24px);
  }

  .modal-header {
    padding: 14px 14px 12px;
  }

  .modal-body {
    padding: 12px 14px;
  }

  .modal-footer {
    padding: 10px 14px;
  }
}

/* Redesign: equipe */
.agency-team .page-wrap { display: flex; flex-direction: column; gap: 16px; }
.at-btn-primary, .at-btn-ghost { display: inline-flex; align-items: center; justify-content: center; gap: 8px; border-radius: 999px; font-weight: 600; }
.at-btn-primary { height: 40px; padding: 0 18px; background: var(--primary); font-size: 13.5px; color: var(--primary-foreground); }
.at-btn-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--primary) 88%, black); }
.at-btn-primary:disabled { cursor: not-allowed; opacity: 0.55; }
.at-btn-primary svg { width: 16px; height: 16px; }
.at-btn-ghost { height: 32px; padding: 0 12px; background: var(--muted); font-size: 12.5px; color: var(--foreground); }
.at-btn-ghost:hover { background: var(--accent); color: var(--accent-foreground); }
.at-btn-ghost svg { width: 14px; height: 14px; }
.at-btn-lg { height: 40px; padding: 0 18px; font-size: 13.5px; }
.at-icon-btn { display: grid; place-items: center; width: 32px; height: 32px; border-radius: 999px; background: var(--muted); color: var(--muted-foreground); }
.at-icon-btn svg { width: 16px; height: 16px; }
.tone-success { background: var(--status-success); color: var(--status-success-foreground); }
.tone-info { background: var(--status-info); color: var(--status-info-foreground); }
.tone-warning { background: var(--status-warning); color: var(--status-warning-foreground); }
.tone-violet { background: var(--status-violet); color: var(--status-violet-foreground); }
.tone-muted { background: var(--muted); color: var(--muted-foreground); }
.at-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.at-stat { display: flex; align-items: center; gap: 12px; border-radius: 20px; background: var(--card); padding: 16px; box-shadow: var(--shadow-card); }
.at-stat-icon { display: grid; place-items: center; width: 40px; height: 40px; flex-shrink: 0; border-radius: 999px; }
.at-stat-icon svg { width: 18px; height: 18px; }
.at-stat-k { font-size: 12.5px; color: var(--muted-foreground); }
.at-stat-v { font-family: var(--font-display); font-size: 20px; line-height: 26px; font-weight: 600; color: var(--foreground); }
.at-stat-v small { margin-left: 4px; font-family: var(--font-sans); font-size: 12px; font-weight: 500; color: var(--muted-foreground); }
.at-meter { width: 160px; max-width: 100%; height: 4px; margin-top: 6px; overflow: hidden; border-radius: 999px; background: var(--muted); }
.at-meter i { display: block; height: 100%; border-radius: 999px; background: var(--primary); }
.at-warn { border-radius: 14px; background: var(--status-warning); padding: 10px 14px; font-size: 13px; color: var(--status-warning-foreground); }
.at-card { overflow-x: auto; border-radius: 20px; background: var(--card); padding-bottom: 4px; box-shadow: var(--shadow-card); }
.at-card-title { padding: 16px 18px 8px; font-size: 15px; font-weight: 600; color: var(--foreground); }
.at-card-title-sub { padding-top: 18px; }
.at-empty { padding: 24px 18px; font-size: 13.5px; color: var(--muted-foreground); }
.at-table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
.at-table th { border-bottom: 1px solid var(--border); padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted-foreground); }
.at-table td { border-top: 1px solid var(--border); padding: 10px 16px; vertical-align: middle; color: var(--foreground); }
.at-table tbody tr:first-child td { border-top: 0; }
.at-table-invites tbody tr:first-child td { border-top: 1px solid var(--border); }
.at-person { display: flex; align-items: center; gap: 10px; min-width: 200px; }
.at-person b { display: block; font-size: 14px; font-weight: 600; }
.at-person small { display: block; font-size: 12.5px; color: var(--muted-foreground); }
.at-avatar { display: grid; place-items: center; width: 34px; height: 34px; flex-shrink: 0; overflow: hidden; border-radius: 999px; font-size: 12px; font-weight: 700; }
.at-avatar img { width: 100%; height: 100%; object-fit: cover; }
.at-avatar svg { width: 16px; height: 16px; }
.at-avatar.is-mail { background: var(--muted); color: var(--muted-foreground); }
.at-pill { display: inline-block; border-radius: 999px; padding: 2px 9px; font-size: 11.5px; font-weight: 600; white-space: nowrap; }
.at-pill.is-success { background: var(--status-success); color: var(--status-success-foreground); }
.at-pill.is-info { background: var(--status-info); color: var(--status-info-foreground); }
.at-pill.is-warning { background: var(--status-warning); color: var(--status-warning-foreground); }
.at-pill.is-muted { background: var(--muted); color: var(--muted-foreground); }
.at-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.at-chip { border-radius: 999px; background: var(--muted); padding: 2px 9px; font-size: 12px; color: var(--foreground); white-space: nowrap; }
.at-actions { display: flex; justify-content: flex-end; gap: 6px; }
.at-menu-wrap { position: relative; }
.at-menu { display: flex; min-width: 190px; flex-direction: column; border-radius: 14px; background: var(--popover); padding: 6px; box-shadow: var(--shadow-elegant); }
.at-menu-wrap .at-menu { position: absolute; top: calc(100% + 6px); right: 0; z-index: 30; }
.at-menu-floating { position: absolute; }
.at-menu button { border-radius: 10px; padding: 8px 10px; text-align: left; font-size: 13px; color: var(--popover-foreground); }
.at-menu button:hover { background: var(--muted); }
.at-menu button.danger { color: var(--status-danger-foreground); }
.at-menu-note { padding: 8px 10px; font-size: 12.5px; color: var(--muted-foreground); }
.at-overlay { position: fixed; inset: 0; z-index: 240; display: flex; align-items: center; justify-content: center; padding: 16px; }
.at-modal { display: flex; width: 100%; max-width: 620px; max-height: calc(100vh - 32px); flex-direction: column; gap: 14px; overflow-y: auto; border-radius: 24px; background: var(--card); padding: 22px 24px; color: var(--foreground); box-shadow: var(--shadow-elegant); }
.at-modal-head { display: flex; align-items: flex-start; gap: 12px; }
.at-modal-head .at-avatar { width: 40px; height: 40px; }
.at-modal-head h3 { font-family: var(--font-display); font-size: 21px; font-weight: 600; }
.at-modal-head p { margin-top: 2px; font-size: 13px; color: var(--muted-foreground); }
.at-close { display: grid; place-items: center; width: 34px; height: 34px; flex-shrink: 0; border-radius: 999px; background: var(--muted); color: var(--muted-foreground); }
.at-close svg { width: 16px; height: 16px; }
.at-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.at-fields label span, .at-label { display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: var(--foreground); }
.at-label { margin-bottom: -6px; }
.at-input { width: 100%; height: 40px; border: 0; border-radius: 12px; background: var(--muted); padding: 0 12px; font-size: 13.5px; color: var(--foreground); outline: none; }
.at-input:focus { box-shadow: 0 0 0 2px var(--ring); }
.at-levels { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.at-level { display: flex; align-items: flex-start; gap: 10px; border: 1px solid var(--border); border-radius: 16px; padding: 12px; text-align: left; }
.at-level:hover { background: color-mix(in srgb, var(--muted) 60%, transparent); }
.at-level.on { border: 2px solid var(--primary); background: var(--accent); padding: 11px; }
.at-level b { display: block; font-size: 14px; font-weight: 600; color: var(--foreground); }
.at-level small { display: block; margin-top: 2px; font-size: 12.5px; line-height: 1.35; color: var(--muted-foreground); }
.at-level-icon { display: grid; place-items: center; width: 32px; height: 32px; flex-shrink: 0; border-radius: 999px; }
.at-level-icon svg { width: 15px; height: 15px; }
.at-radio { width: 18px; height: 18px; flex-shrink: 0; border: 2px solid var(--border); border-radius: 999px; }
.at-level.on .at-radio { border: 5px solid var(--primary); background: var(--card); }
.at-areas { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; border-radius: 16px; background: var(--muted); padding: 6px 14px; }
.at-area { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 9px 0; font-size: 13.5px; color: var(--foreground); }
.at-area.is-disabled { opacity: 0.5; }
.at-switch { position: relative; width: 36px; height: 20px; flex-shrink: 0; border-radius: 999px; background: var(--card); box-shadow: inset 0 0 0 1px var(--border); transition: background 0.15s; }
.at-switch i { position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; border-radius: 999px; background: #fff; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25); transition: transform 0.15s; }
.at-switch.on { background: var(--primary); box-shadow: none; }
.at-switch.on i { transform: translateX(16px); }
.at-switch:disabled { cursor: not-allowed; }
.at-preview { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: 12.5px; color: var(--muted-foreground); }
.at-error { border-radius: 12px; background: var(--status-danger); padding: 8px 12px; font-size: 13px; color: var(--status-danger-foreground); }
.at-modal-foot { display: flex; justify-content: flex-end; gap: 8px; padding-top: 4px; }
@media (max-width: 900px) { .at-stats { grid-template-columns: 1fr; } }
@media (max-width: 640px) {
  .at-fields, .at-levels, .at-areas { grid-template-columns: 1fr; }
  /* Celular: cada pessoa vira um cartão (nome em cima, acesso e situação, áreas e ações). */
  .at-table thead { display: none; }
  .at-table, .at-table tbody { display: block; }
  .at-table tr { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--border); }
  .at-table tbody tr:first-child { border-top: 0; }
  .at-table-invites tbody tr:first-child { border-top: 1px solid var(--border); }
  .at-table td { display: block; border: 0 !important; padding: 0; }
  .at-table td:first-child { flex: 1 1 100%; min-width: 0; }
  .at-table td:last-child { margin-left: auto; }
}
</style>
