export interface AdminMasterNavItem {
  path: string;
  label: string;
  icon: string;
  badge?: "online" | "users" | "whatsapp";
}

export interface AdminMasterNavGroup {
  label: string;
  items: AdminMasterNavItem[];
}

export const adminMasterNav: AdminMasterNavGroup[] = [
  {
    label: "Visão geral",
    items: [
      { path: "/admin/administracao/dashboard", label: "Painel", icon: "dash" },
      { path: "/admin/administracao/monitor", label: "Ao vivo", icon: "pulse", badge: "online" }
    ]
  },
  {
    label: "Clientes",
    items: [
      { path: "/admin/administracao/usuarios", label: "Usuários", icon: "users" },
      { path: "/admin/administracao/admin-global", label: "Admins globais", icon: "shield" }
    ]
  },
  {
    label: "Receita",
    items: [
      { path: "/admin/administracao/receita-previsao", label: "Previsão de receita", icon: "cal" },
      { path: "/admin/administracao/conciliacao", label: "Conciliação", icon: "scale" },
      { path: "/admin/administracao/ltv-clientes", label: "LTV por cliente", icon: "trend" },
      { path: "/admin/administracao/ofertas", label: "Ofertas e checkout", icon: "tag" }
    ]
  },
  {
    label: "Conteúdo",
    items: [
      { path: "/admin/administracao/aulas", label: "Aulas", icon: "video" },
      { path: "/admin/administracao/templates", label: "Modelos de página", icon: "layout" },
      { path: "/admin/administracao/banners", label: "Banners", icon: "flag" },
      { path: "/admin/administracao/prompt-construtor", label: "Prompt do construtor", icon: "spark" }
    ]
  },
  {
    label: "Integrações",
    items: [
      { path: "/admin/administracao/apis-voo", label: "APIs de voo", icon: "plane" },
      { path: "/admin/administracao/whatsapp", label: "WhatsApp", icon: "wa", badge: "whatsapp" },
      { path: "/admin/administracao/webhooks", label: "Webhooks e push", icon: "bell" }
    ]
  }
];

export const adminMasterGroupOf = (path: string) =>
  adminMasterNav.find(group => group.items.some(item => path === item.path || path.startsWith(`${item.path}/`)))?.label ?? "";
