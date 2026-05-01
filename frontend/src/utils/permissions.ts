export const PERMISSION_KEYS = [
  "dashboard",
  "leads",
  "leads_forms",
  "leads_opportunities",
  "leads_clients",
  "leads_settings",
  "leads_manager",
  "leads_full",
  "pages",
  "pages_viewer",
  "pages_editor",
  "settings",
  "integrations",
  "domains",
  "lessons",
  "team_management"
] as const;

export type PermissionKey = (typeof PERMISSION_KEYS)[number];

const PLAN_ALIAS: Record<string, string> = {
  free: "free",
  trial: "professional",
  essencial: "professional",
  professional: "professional",
  profissional: "professional",
  growth: "agency",
  agency: "agency",
  agencia: "agency",
  infinity: "scale",
  scale: "scale",
  escala: "scale",
  teste: "test",
  test: "test"
};

const PLAN_ALLOWED: Record<string, PermissionKey[]> = {
  free: ["dashboard", "pages", "pages_viewer"],
  professional: ["dashboard", "leads", "leads_forms", "leads_opportunities", "leads_clients", "leads_settings", "leads_manager", "leads_full", "pages", "pages_viewer", "pages_editor", "integrations", "domains", "lessons", "team_management"],
  agency: ["dashboard", "leads", "leads_forms", "leads_opportunities", "leads_clients", "leads_settings", "leads_manager", "leads_full", "pages", "pages_viewer", "pages_editor", "integrations", "domains", "lessons", "team_management"],
  scale: ["dashboard", "leads", "leads_forms", "leads_opportunities", "leads_clients", "leads_settings", "leads_manager", "leads_full", "pages", "pages_viewer", "pages_editor", "settings", "integrations", "domains", "lessons", "team_management"],
  test: [...PERMISSION_KEYS]
};

export const normalizePlan = (plan?: string | null) => PLAN_ALIAS[(plan || "free").toLowerCase()] || "free";

export const allowedByPlan = (plan?: string | null): PermissionKey[] => PLAN_ALLOWED[normalizePlan(plan)] || PLAN_ALLOWED.free;

export const canAccessPermission = (
  permission: PermissionKey,
  opts: { isOwner?: boolean | null; selected?: string[] | null; plan?: string | null; effective?: string[] | null }
) => {
  if (opts.effective?.length) return opts.effective.includes(permission);
  const planAllowed = new Set(allowedByPlan(opts.plan));
  if (!planAllowed.has(permission)) return false;
  if (opts.isOwner ?? true) return true;
  const selected = new Set(opts.selected || []);
  return selected.has(permission);
};

export const hasAnyPermission = (
  permissions: string[] | null | undefined,
  keys: string[]
) => {
  const set = new Set(permissions || []);
  return keys.some(key => set.has(key));
};
