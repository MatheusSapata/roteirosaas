import { ref, watch } from "vue";

/**
 * Para gravar vídeos: o superusuário oculta do menu do painel o que só ele vê (Admin master e
 * Aulas), e o painel fica igual ao de um cliente. Vale só neste navegador; o Admin master continua
 * abrindo pelo endereço /admin/administracao, onde o interruptor desfaz.
 */
const KEY = "admin_master_hidden_in_menu";

const read = () => {
  try {
    return localStorage.getItem(KEY) === "1";
  } catch {
    return false;
  }
};

export const adminMasterHiddenInMenu = ref(typeof window !== "undefined" ? read() : false);

watch(adminMasterHiddenInMenu, hidden => {
  try {
    if (hidden) localStorage.setItem(KEY, "1");
    else localStorage.removeItem(KEY);
  } catch {
    // Sem armazenamento (modo privado restrito): vale até recarregar a página.
  }
});
