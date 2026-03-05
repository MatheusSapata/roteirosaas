const VIAJECHAT_API_BASE = "https://painel.viajechat.com.br/api/v1";
const API_KEY = import.meta.env.VITE_VIAJECHAT_API_KEY || "crz_vRCzsXxHBIbJu_pUT5gEiU-RekrbE9NF";

export const viajeChatTagIds = {
  ROTEIRO_ONLINE: "c9b3c9e7-a081-44c1-993c-917dbb4e90bd",
  AGENCIA_CRIADA: "5ca87edb-0259-4941-bc79-98ce0a52fe1e",
  PLANO_AGENCIA: "ae856294-eaab-4e9d-8510-b8e1b2e3871b",
  PLANO_ESCALA: "f407945c-1d85-4459-9229-dd8b954ec3df",
  PLANO_PROFISSIONAL: "dded875c-cb90-4c30-9bce-f665db6234a8",
  PLANO_TESTE: "54612f9c-574a-42b0-94b2-39f1bd7bff64",
  PRIMEIRA_PAGINA: "ed33c49a-cb15-49ce-a44d-e705a6bb4c2c"
} as const;

interface ViajeChatTag {
  id: string;
  name: string;
}

export interface ViajeChatContact {
  id: string;
  email: string;
  name?: string;
  tags?: ViajeChatTag[];
}

const authorizedFetch = async (path: string, options: RequestInit = {}) => {
  if (!API_KEY) return null;
  const url = `${VIAJECHAT_API_BASE}${path}`;
  const headers: HeadersInit = {
    Authorization: `Bearer ${API_KEY}`,
    ...(options.headers || {})
  };
  return fetch(url, { ...options, headers });
};

export const fetchContactByEmail = async (email?: string | null): Promise<ViajeChatContact | null> => {
  if (!email || !API_KEY) return null;
  try {
    const res = await authorizedFetch(`/contacts?search=${encodeURIComponent(email)}&limit=1`);
    if (!res || !res.ok) return null;
    const data = await res.json();
    return data?.data?.[0] ?? null;
  } catch (err) {
    console.error("Erro ao buscar contato no ViajeChat", err);
    return null;
  }
};

export const addTagsToContact = async (contactId: string, tagIds: string[]) => {
  if (!API_KEY || !contactId || !tagIds.length) return;
  try {
    await authorizedFetch("/contacts/tags", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        contact_id: contactId,
        tag_ids: tagIds
      })
    });
  } catch (err) {
    console.error("Erro ao adicionar etiquetas ViajeChat", err);
  }
};

export const addTagsToContactByEmail = async (email: string, tagIds: string[]) => {
  const contact = await fetchContactByEmail(email);
  if (!contact?.id) return;
  await addTagsToContact(contact.id, tagIds);
};

export const removeTagFromContact = async (contactId: string, tagId: string) => {
  if (!API_KEY || !contactId || !tagId) return;
  try {
    await authorizedFetch("/contacts/tags/remove", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        contact_id: contactId,
        tag_id: tagId
      })
    });
  } catch (err) {
    console.error("Erro ao remover etiqueta ViajeChat", err);
  }
};

export const syncPlanTagForEmail = async (
  email: string,
  desiredTagId: string | null,
  planTagIds: string[]
) => {
  if (!email || !API_KEY) return;
  const contact = await fetchContactByEmail(email);
  if (!contact?.id) return;
  const currentPlanTag = contact.tags?.find(tag => planTagIds.includes(tag.id));

  if (currentPlanTag && currentPlanTag.id !== desiredTagId) {
    await removeTagFromContact(contact.id, currentPlanTag.id);
  }

  if (desiredTagId && currentPlanTag?.id !== desiredTagId) {
    await addTagsToContact(contact.id, [desiredTagId]);
  }
};
