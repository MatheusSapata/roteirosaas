import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import LoginView from "../views/admin/LoginView.vue";
import RegisterView from "../views/admin/RegisterView.vue";
import ForgotPasswordView from "../views/admin/ForgotPasswordView.vue";
import ResetPasswordView from "../views/admin/ResetPasswordView.vue";
import CreatePasswordView from "../views/admin/CreatePasswordView.vue";
import CheckoutProcessingView from "../views/public/CheckoutProcessingView.vue";
import DashboardView from "../views/admin/DashboardView.vue";
import PagesListView from "../views/admin/PagesListView.vue";
import PageEditorView from "../views/admin/PageEditorView.vue";
import AgencySettingsView from "../views/admin/AgencySettingsView.vue";
import LeadsView from "../views/admin/LeadsView.vue";
import PublicPageView from "../views/public/PublicPageView.vue";
import PlansView from "../views/public/PlansView.vue";
import AdminLayout from "../layouts/AdminLayout.vue";
import { useAuthStore } from "../store/useAuthStore";
import { resolveCurrentLanguage, setCurrentLanguage } from "../utils/i18n";

const RedirectPlaceholder = {
  template: "<div>Redirecionando...</div>"
};

const defaultPlatformHosts = ["roteiroonline.com", "www.roteiroonline.com", "localhost", "127.0.0.1"];
const envPlatformHosts = (import.meta.env.VITE_PLATFORM_HOSTS || "")
  .split(",")
  .map(host => host.trim().toLowerCase())
  .filter(Boolean);

const platformHostSet = new Set([...defaultPlatformHosts, ...envPlatformHosts]);
const currentHostname = typeof window !== "undefined" ? window.location.hostname.toLowerCase() : "";
const resolvedLanguage = resolveCurrentLanguage(currentHostname);
setCurrentLanguage(resolvedLanguage);
const isCustomDomainHost = !!currentHostname && !platformHostSet.has(currentHostname);

const redirectRoutes: RouteRecordRaw[] = [
  {
    path: "/profissionalmensal",
    component: RedirectPlaceholder,
    beforeEnter() {
      window.location.href = "https://pay.cakto.com.br/7o7zrup_800651";
    }
  },
  {
    path: "/profissionalanual",
    component: RedirectPlaceholder,
    beforeEnter() {
      window.location.href = "https://pay.cakto.com.br/nxc42uz";
    }
  },
  {
    path: "/agenciamensal",
    component: RedirectPlaceholder,
    beforeEnter() {
      window.location.href = "https://pay.cakto.com.br/n7vnc73_800688";
    }
  },
  {
    path: "/agenciaanual",
    component: RedirectPlaceholder,
    beforeEnter() {
      window.location.href = "https://pay.cakto.com.br/32uvp8b";
    }
  },
  {
    path: "/escalamensal",
    component: RedirectPlaceholder,
    beforeEnter() {
      window.location.href = "https://pay.cakto.com.br/iexkakw_800692";
    }
  },
  {
    path: "/escalaanual",
    component: RedirectPlaceholder,
    beforeEnter() {
      window.location.href = "https://pay.cakto.com.br/pxzgp5s";
    }
  },
  {
    path: "/profissional",
    component: RedirectPlaceholder,
    beforeEnter() {
      window.location.href = "https://pay.cakto.com.br/7o7zrup_818166";
    }
  },
  {
    path: "/agencia",
    component: RedirectPlaceholder,
    beforeEnter() {
      window.location.href = "https://pay.cakto.com.br/n7vnc73_818167";
    }
  },
  {
    path: "/escala",
    component: RedirectPlaceholder,
    beforeEnter() {
      window.location.href = "https://pay.cakto.com.br/iexkakw_818426";
    }
  }
];

const platformRoutes: RouteRecordRaw[] = [
  ...redirectRoutes,
  { path: "/", name: "marketing", component: LoginView, meta: { guestOnly: true } },
  { path: "/login", name: "login", component: LoginView, meta: { guestOnly: true } },
  { path: "/register", name: "register", component: RegisterView, meta: { guestOnly: true } },
  { path: "/forgot-password", name: "forgot-password", component: ForgotPasswordView, meta: { guestOnly: true } },
  { path: "/reset-password", name: "reset-password", component: ResetPasswordView, meta: { guestOnly: true } },
  { path: "/create-password", name: "create-password", component: CreatePasswordView, meta: { guestOnly: true } },
  { path: "/pedido", name: "checkout-processing", component: CheckoutProcessingView, meta: { guestOnly: true } },
  { path: "/planos", redirect: "/admin/planos" },
  {
    path: "/admin",
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      { path: "dashboard", name: "dashboard", component: DashboardView },
      { path: "pages", name: "pages", component: PagesListView },
      { path: "pages/:id/edit", name: "page-edit", component: PageEditorView, props: true },
      { path: "aulas", name: "lessons", component: () => import("../views/admin/AulasView.vue") },
      { path: "leads", name: "leads", component: LeadsView },
      { path: "agency", name: "agency-settings", component: AgencySettingsView },
      {
        path: "domains",
        name: "agency-domains",
        component: () => import("../views/admin/AgencyDomainsView.vue")
      },
      { path: "planos", name: "plans", component: PlansView },
      { path: "integracoes", name: "integrations", component: () => import("../views/admin/IntegrationsView.vue") },
      { path: "perfil", name: "profile", component: () => import("../views/admin/ProfileView.vue") },
      {
        path: "administracao",
        name: "admin-management",
        component: () => import("../views/admin/AdminManagementView.vue"),
        meta: { requiresSuperuser: true }
      }
    ]
  },
  {
    path: "/:agencySlug/:pageSlug?",
    alias: ["/p/:agencySlug/:pageSlug?"],
    name: "public-page",
    component: PublicPageView,
    props: true
  }
];

const customDomainRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "custom-domain-default",
    component: PublicPageView
  },
  {
    path: "/:pageSlug",
    name: "custom-domain-page",
    component: PublicPageView
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/"
  }
];

const routes: RouteRecordRaw[] = isCustomDomainHost ? customDomainRoutes : platformRoutes;

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore();
  const requiresAuth = to.matched.some(record => record.meta?.requiresAuth);
  const guestOnly = to.matched.some(record => record.meta?.guestOnly);
  const requiresSuperuser = to.matched.some(record => record.meta?.requiresSuperuser);
  const targetIsPlans = to.name === "plans";
  const targetIsDashboard = to.name === "dashboard";

  if (requiresAuth) {
    if (!auth.token) {
      next({ name: "login", query: { redirect: to.fullPath } });
      return;
    }

    if (!auth.user) {
      try {
        await auth.fetchProfile();
      } catch {
        auth.logout();
        next({ name: "login", query: { redirect: to.fullPath } });
        return;
      }
    }

    if (auth.user?.trial_blocked && !targetIsPlans && !targetIsDashboard) {
      next({ name: "plans" });
      return;
    }

  }

  if (requiresSuperuser) {
    if (!auth.user?.is_superuser) {
      next({ name: "dashboard" });
      return;
    }
  }

  if (guestOnly && auth.token) {
    const fallback = auth.user?.trial_blocked ? "plans" : "dashboard";
    next({ name: fallback });
    return;
  }

  next();
});

export default router;
