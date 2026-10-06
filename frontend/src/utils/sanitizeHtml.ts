import DOMPurify from "dompurify";
import { isAllowedVideoEmbed } from "./video";

/** embeds: aceita vídeos do YouTube e do Vimeo (iframe) dentro do texto, como no Artigo. */
export const sanitizeHtml = (value?: string | null, options: { embeds?: boolean } = {}) => {
  if (!value) return "";
  const sanitized = DOMPurify.sanitize(value, {
    USE_PROFILES: { html: true },
    ADD_ATTR: options.embeds ? ["class", "style", "allowfullscreen", "frameborder", "allow"] : ["class", "style"],
    ADD_TAGS: options.embeds ? ["iframe"] : []
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

  // Qualquer iframe que não seja vídeo do YouTube ou Vimeo sai do texto.
  container.querySelectorAll("iframe").forEach(frame => {
    if (!options.embeds || !isAllowedVideoEmbed(frame.getAttribute("src"))) frame.remove();
  });

  forceTextAlign(".ql-align-left", "left");
  forceTextAlign(".ql-align-center", "center");
  forceTextAlign(".ql-align-right", "right");
  forceTextAlign(".ql-align-justify", "justify");

  return container.innerHTML;
};
