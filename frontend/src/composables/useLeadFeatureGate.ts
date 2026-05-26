import { computed } from "vue";
import { useAuthStore } from "../store/useAuthStore";

const allowedPlans = ["teste", "growth", "infinity"];

export const useLeadFeatureGate = () => {
  const auth = useAuthStore();
  const effectivePlan = computed(() => (auth.user?.plan || "").toLowerCase());
  const isTrialUser = computed(() => Boolean(auth.user?.trial_plan));
  const hasAccess = computed(() => !isTrialUser.value && allowedPlans.includes(effectivePlan.value));
  return { hasLeadFeatureAccess: hasAccess, effectivePlan };
};
