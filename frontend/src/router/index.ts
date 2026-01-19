import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import LoginView from "../views/admin/LoginView.vue";
import RegisterView from "../views/admin/RegisterView.vue";
import ForgotPasswordView from "../views/admin/ForgotPasswordView.vue";
import ResetPasswordView from "../views/admin/ResetPasswordView.vue";
import DashboardView from "../views/admin/DashboardView.vue";
import PagesListView from "../views/admin/PagesListView.vue";
import PageEditorView from "../views/admin/PageEditorView.vue";
import AgencySettingsView from "../views/admin/AgencySettingsView.vue";
import PublicPageView from "../views/public/PublicPageView.vue";
import PlansView from "../views/public/PlansView.vue";
import AdminLayout from "../layouts/AdminLayout.vue";
import { useAuthStore } from "../store/useAuthStore";

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/login" },
  { path: "/login", name: "login", component: LoginView, meta: { guestOnly: true } },
  { path: "/register", name: "register", component: RegisterView, meta: { guestOnly: true } },
  { path: "/forgot-password", name: "forgot-password", component: ForgotPasswordView, meta: { guestOnly: true } },
  { path: "/reset-password", name: "reset-password", component: ResetPasswordView, meta: { guestOnly: true } },
  { path: "/planos", redirect: "/admin/planos" },
  {
    path: "/admin",
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      { path: "dashboard", name: "dashboard", component: DashboardView },
      { path: "pages", name: "pages", component: PagesListView },
      { path: "pages/:id/edit", name: "page-edit", component: PageEditorView, props: true },
      { path: "agency", name: "agency-settings", component: AgencySettingsView },
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

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore();
  const requiresAuth = to.matched.some(record => record.meta?.requiresAuth);
  const guestOnly = to.matched.some(record => record.meta?.guestOnly);
  const requiresSuperuser = to.matched.some(record => record.meta?.requiresSuperuser);

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
  }

  if (requiresSuperuser) {
    if (!auth.user?.is_superuser) {
      next({ name: "dashboard" });
      return;
    }
  }

  if (guestOnly && auth.token) {
    next({ name: "dashboard" });
    return;
  }

  next();
});

export default router;
