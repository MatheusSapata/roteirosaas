/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_GLOBAL_META_PIXEL_ID?: string;
  readonly VITE_CUSTOM_DOMAIN_CNAME_TARGET?: string;
  readonly VITE_CUSTOM_DOMAIN_APEX_IP?: string;
  readonly VITE_PLATFORM_HOSTS?: string;
  readonly VITE_PLATFORM_ORIGIN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
