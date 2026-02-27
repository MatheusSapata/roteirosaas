import DOMPurify from "dompurify";

export const sanitizeHtml = (value?: string | null) => {
  if (!value) return "";
  return DOMPurify.sanitize(value, { USE_PROFILES: { html: true } });
};
