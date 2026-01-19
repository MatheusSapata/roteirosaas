import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../services/api";

export interface Agency {
  id: number;
  name: string;
  slug: string;
  logo_url?: string | null;
  primary_color?: string | null;
  secondary_color?: string | null;
  default_page_id?: number | null;
}

export const useAgencyStore = defineStore("agency", () => {
  const agencies = ref<Agency[]>([]);
  const currentAgencyId = ref<number | null>(null);

  const loadAgencies = async () => {
    const res = await api.get<Agency[]>("/agencies/me");
    agencies.value = res.data;
    if (!currentAgencyId.value && agencies.value.length > 0) {
      currentAgencyId.value = agencies.value[0].id;
    }
  };

  return { agencies, currentAgencyId, loadAgencies };
});
