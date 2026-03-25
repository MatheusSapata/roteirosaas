import { computed } from "vue";
import { useAuthStore } from "../store/useAuthStore";

const allowedPlans = ["teste", "growth", "infinity"];

export const useLeadFeatureGate = () => {
  const auth = useAuthStore();
  const effectivePlan = computed(() => (auth.user?.trial_plan || auth.user?.plan || "").toLowerCase());
  const hasAccess = computed(() => allowedPlans.includes(effectivePlan.value));
  return { hasLeadFeatureAccess: hasAccess, effectivePlan };
};
