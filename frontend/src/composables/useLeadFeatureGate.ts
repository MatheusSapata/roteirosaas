import { computed } from "vue";
import { useAuthStore } from "../store/useAuthStore";

const allowedPlans = ["teste", "growth", "infinity"];
const leadPermissionKeys = [
  "leads",
  "leads_forms",
  "leads_opportunities",
  "leads_clients",
  "leads_settings",
  "leads_manager",
  "leads_full"
];

export const useLeadFeatureGate = () => {
  const auth = useAuthStore();
  const effectivePlan = computed(() => (auth.user?.trial_plan || auth.user?.plan || "").toLowerCase());
  const hasPermissionAccess = computed(() => {
    const perms = auth.user?.effective_permissions || [];
    return perms.some(p => leadPermissionKeys.includes(String(p)));
  });
  const hasAccess = computed(() => allowedPlans.includes(effectivePlan.value) || hasPermissionAccess.value);
  return { hasLeadFeatureAccess: hasAccess, effectivePlan };
};
