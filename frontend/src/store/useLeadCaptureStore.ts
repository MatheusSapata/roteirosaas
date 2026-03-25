import { defineStore } from "pinia";
import { computed, ref } from "vue";
import api from "../services/api";
import type {
  LeadContact,
  LeadContactGroup,
  LeadForm,
  LeadFormPayload,
  LeadStatus,
  LeadStatusPayload
} from "../types/leads";
import { useAgencyStore } from "./useAgencyStore";

const formatContactsByForm = (contacts: LeadContact[]): LeadContactGroup[] => {
  const map = new Map<string, LeadContactGroup>();
  contacts.forEach(contact => {
    if (!contact.form_id) return;
    const key = String(contact.form_id);
    if (!map.has(key)) {
      map.set(key, {
        formId: key,
        formName: contact.form_name || "Formulário",
        contacts: []
      });
    }
    map.get(key)!.contacts.push(contact);
  });
  return Array.from(map.values()).map(group => ({
    ...group,
    contacts: group.contacts.sort((a, b) => {
      const left = a.created_at ? new Date(a.created_at).getTime() : 0;
      const right = b.created_at ? new Date(b.created_at).getTime() : 0;
      return right - left;
    })
  }));
};

export const useLeadCaptureStore = defineStore("leadCapture", () => {
  const forms = ref<LeadForm[]>([]);
  const formsLoading = ref(false);
  const formsLoadedAtLeastOnce = ref(false);
  const contacts = ref<LeadContact[]>([]);
  const contactsLoading = ref(false);
  const contactsLoadedAtLeastOnce = ref(false);
  const statuses = ref<LeadStatus[]>([]);
  const statusesLoading = ref(false);
  const statusesLoadedAtLeastOnce = ref(false);
  const lastError = ref<string | null>(null);
  const agencyStore = useAgencyStore();

  const resolveAgencyId = async (): Promise<number> => {
    if (!agencyStore.currentAgencyId && !agencyStore.agencies.length) {
      try {
        await agencyStore.loadAgencies();
      } catch {
        /* ignore load errors, handled later */
      }
    }
    const id = agencyStore.currentAgencyId || agencyStore.agencies[0]?.id;
    if (!id) {
      throw new Error("Nenhuma agência disponível para gerenciar leads.");
    }
    return id;
  };

  const fetchForms = async (force = false) => {
    if (formsLoading.value) return;
    if (!force && formsLoadedAtLeastOnce.value) return;
    formsLoading.value = true;
    lastError.value = null;
    try {
      const agencyId = await resolveAgencyId();
      const res = await api.get<LeadForm[]>("/lead-forms", { params: { agencyId } });
      forms.value = res.data;
      formsLoadedAtLeastOnce.value = true;
    } catch (err) {
      console.error("Erro ao carregar formulários", err);
      lastError.value = "Não foi possível carregar formulários.";
      throw err;
    } finally {
      formsLoading.value = false;
    }
  };

  const refreshForms = async () => {
    formsLoadedAtLeastOnce.value = false;
    await fetchForms(true);
  };

  const createForm = async (payload: LeadFormPayload) => {
    lastError.value = null;
    const agencyId = await resolveAgencyId();
    const res = await api.post<LeadForm>("/lead-forms", { ...payload, agencyId });
    forms.value = [res.data, ...forms.value];
    formsLoadedAtLeastOnce.value = true;
    return res.data;
  };

  const updateForm = async (id: string | number, payload: LeadFormPayload) => {
    lastError.value = null;
    const res = await api.put<LeadForm>(`/lead-forms/${id}`, payload);
    forms.value = forms.value.map(form => (form.id === res.data.id ? res.data : form));
    return res.data;
  };

  const deleteForm = async (id: string | number) => {
    const agencyId = await resolveAgencyId();
    await api.delete(`/lead-forms/${id}`, { params: { agencyId } });
    forms.value = forms.value.filter(form => String(form.id) !== String(id));
  };

  const fetchContacts = async (formId?: string, force = false) => {
    if (contactsLoading.value) return;
    if (!force && contactsLoadedAtLeastOnce.value && !formId) return;
    contactsLoading.value = true;
    lastError.value = null;
    try {
      const agencyId = await resolveAgencyId();
      const res = await api.get<LeadContact[]>("/lead-forms/contacts", {
        params: { agencyId, formId }
      });
      if (formId) {
        const sanitized = contacts.value.filter(contact => contact.form_id !== formId);
        contacts.value = sanitized.concat(res.data);
      } else {
        contacts.value = res.data;
        contactsLoadedAtLeastOnce.value = true;
      }
    } catch (err) {
      console.error("Erro ao carregar contatos de leads", err);
      lastError.value = "Não foi possível carregar contatos coletados.";
      throw err;
    } finally {
      contactsLoading.value = false;
    }
  };

  const formsTotal = computed(() => forms.value.length);
  const groupedContacts = computed(() => formatContactsByForm(contacts.value));
  const totalContacts = computed(() => contacts.value.length);

  const normalizeId = (value: string | number | null | undefined) => {
    if (value === null || typeof value === "undefined") return null;
    return String(value);
  };

  const getFormById = (id?: string | null) => {
    const target = normalizeId(id);
    if (!target) return null;
    return forms.value.find(form => normalizeId(form.id) === target) || null;
  };

  const replaceContact = (updated: LeadContact) => {
    const target = normalizeId(updated.id);
    if (!target) return;
    contacts.value = contacts.value.map(contact =>
      normalizeId(contact.id) === target ? updated : contact
    );
  };

  const statusSortValue = (status: LeadStatus) => {
    const created = status.created_at ? Date.parse(status.created_at) : Number.NaN;
    if (!Number.isNaN(created)) return created;
    const idNumber = Number(status.id);
    if (!Number.isNaN(idNumber)) return idNumber;
    return Number.MAX_SAFE_INTEGER;
  };

  const sortStatuses = (list: LeadStatus[]) => {
    return [...list].sort((a, b) => {
      const diff = statusSortValue(a) - statusSortValue(b);
      if (diff !== 0) return diff;
      return String(a.id).localeCompare(String(b.id));
    });
  };

  const fetchStatuses = async (force = false) => {
    if (statusesLoading.value) return;
    if (!force && statusesLoadedAtLeastOnce.value) return;
    statusesLoading.value = true;
    lastError.value = null;
    try {
      const agencyId = await resolveAgencyId();
      const res = await api.get<LeadStatus[]>("/lead-forms/statuses", { params: { agencyId } });
      statuses.value = sortStatuses(res.data);
      statusesLoadedAtLeastOnce.value = true;
    } catch (err) {
      console.error("Erro ao carregar status de leads", err);
      lastError.value = "Não foi possível carregar status de leads.";
      throw err;
    } finally {
      statusesLoading.value = false;
    }
  };

  const createStatus = async (payload: LeadStatusPayload) => {
    const agencyId = await resolveAgencyId();
    const res = await api.post<LeadStatus>("/lead-forms/statuses", { ...payload, agencyId });
    const sanitized = statuses.value.filter(status => status.id !== res.data.id);
    statuses.value = sortStatuses([...sanitized, res.data]);
    statusesLoadedAtLeastOnce.value = true;
    return res.data;
  };

  const updateStatus = async (id: string | number, payload: LeadStatusPayload) => {
    const res = await api.put<LeadStatus>(`/lead-forms/statuses/${id}`, payload);
    const target = normalizeId(id);
    statuses.value = sortStatuses(
      statuses.value.map(status => (normalizeId(status.id) === target ? res.data : status))
    );
    return res.data;
  };

  const deleteStatus = async (id: string | number) => {
    await api.delete(`/lead-forms/statuses/${id}`);
    const target = normalizeId(id);
    statuses.value = statuses.value.filter(status => normalizeId(status.id) !== target);
    if (target) {
      contacts.value = contacts.value.map(contact =>
        normalizeId(contact.status_id) === target
          ? { ...contact, status_id: null, status_name: null, status_color: null }
          : contact
      );
    }
  };

  const setContactStatus = async (contactId: string | number, statusId: string | number | null) => {
    const res = await api.put<LeadContact>(`/lead-forms/contacts/${contactId}/status`, {
      statusId: statusId ?? null
    });
    replaceContact(res.data);
    return res.data;
  };

  const deleteContact = async (contactId: string | number) => {
    await api.delete(`/lead-forms/contacts/${contactId}`);
    const target = normalizeId(contactId);
    contacts.value = contacts.value.filter(contact => normalizeId(contact.id) !== target);
  };

  return {
    forms,
    formsLoading,
    formsTotal,
    formsLoadedAtLeastOnce,
    lastError,
    contacts,
    contactsLoading,
    contactsLoadedAtLeastOnce,
    totalContacts,
    groupedContacts,
    statuses,
    statusesLoading,
    statusesLoadedAtLeastOnce,
    fetchForms,
    refreshForms,
    createForm,
    updateForm,
    deleteForm,
    fetchContacts,
    getFormById,
    fetchStatuses,
    createStatus,
    updateStatus,
    deleteStatus,
    setContactStatus,
    deleteContact
  };
});
