import { defineStore } from "pinia";
import { computed, ref } from "vue";
import api from "../services/api";

export type AgencySocialNetwork = "instagram" | "facebook" | "youtube" | "tiktok";

export interface AgencySocialLink {
  id: number;
  network: AgencySocialNetwork;
  url: string;
}

export interface Agency {
  id: number;
  name: string;
  slug: string;
  logo_url?: string | null;
  primary_color?: string | null;
  secondary_color?: string | null;
  contact_email?: string | null;
  default_page_id?: number | null;
  cta_whatsapp?: string | null;
  social_links?: AgencySocialLink[];
}

export const useAgencyStore = defineStore("agency", () => {
  const agencies = ref<Agency[]>([]);
  const currentAgencyId = ref<number | null>(null);
  const primaryDomains = ref<Record<number, string | null>>({});

  const loadAgencies = async () => {
    const res = await api.get<Agency[]>("/agencies/me");
    agencies.value = res.data;
    if (!currentAgencyId.value && agencies.value.length > 0) {
      currentAgencyId.value = agencies.value[0].id;
    }
  };

  interface AgencyDomainSummary {
    id: number;
    host: string;
    is_primary: boolean;
    is_active: boolean;
    is_verified: boolean;
  }

  const selectPrimaryHost = (domains: AgencyDomainSummary[]) => {
    if (!domains.length) return null;
    const activeDomains = domains.filter(domain => domain.is_active);
    const primaryActive = activeDomains.find(domain => domain.is_primary);
    if (primaryActive) return primaryActive.host;
    if (activeDomains.length) return activeDomains[0].host;
    const verified = domains.find(domain => domain.is_verified);
    if (verified) return verified.host;
    return domains[0].host;
  };

  const loadPrimaryDomain = async (agencyId: number | null) => {
    if (!agencyId) return null;
    try {
      const res = await api.get<AgencyDomainSummary[]>("/agencies/me/domains", {
        params: { agency_id: agencyId }
      });
      const host = selectPrimaryHost(res.data) || null;
      primaryDomains.value = { ...primaryDomains.value, [agencyId]: host };
      return host;
    } catch (err) {
      console.error("Erro ao carregar domínios da agência", err);
      primaryDomains.value = { ...primaryDomains.value, [agencyId]: null };
      return null;
    }
  };

  const currentPrimaryDomain = computed(() => {
    if (!currentAgencyId.value) return null;
    return primaryDomains.value[currentAgencyId.value] ?? null;
  });

  return { agencies, currentAgencyId, loadAgencies, loadPrimaryDomain, primaryDomains, currentPrimaryDomain };
});
