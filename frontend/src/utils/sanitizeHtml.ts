import DOMPurify from "dompurify";

export const sanitizeHtml = (value?: string | null) => {
  if (!value) return "";
  const sanitized = DOMPurify.sanitize(value, {
    USE_PROFILES: { html: true },
    ADD_ATTR: ["class", "style"]
  });
  if (typeof window === "undefined") {
    return sanitized;
  }

  const container = window.document.createElement("div");
  container.innerHTML = sanitized;

  const forceTextAlign = (selector: string, align: "left" | "center" | "right" | "justify") => {
    container.querySelectorAll<HTMLElement>(selector).forEach(el => {
      el.style.textAlign = align;
    });
  };

  forceTextAlign(".ql-align-left", "left");
  forceTextAlign(".ql-align-center", "center");
  forceTextAlign(".ql-align-right", "right");
  forceTextAlign(".ql-align-justify", "justify");

  return container.innerHTML;
};
