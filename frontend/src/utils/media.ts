import api from "../services/api";
import { API_BASE_URL, API_ROOT_URL } from "./apiBase";

interface MediaAsset {
  id: number;
  url: string;
  original_file_name?: string | null;
}

const buildMediaBase = () => {
  const explicit = import.meta.env.VITE_MEDIA_BASE;
  if (explicit) return explicit.endsWith("/") ? explicit.slice(0, -1) : explicit;

  if (API_BASE_URL.endsWith("/api/v1")) {
    return `${API_ROOT_URL}/uploads`;
  }
  return `${API_BASE_URL.replace(/\/$/, "")}/uploads`;
};

const MEDIA_BASE = buildMediaBase();
const ABSOLUTE_MEDIA_BASE = /^https?:\/\//i.test(MEDIA_BASE);

const ensureLeadingSlash = (value: string) => (value.startsWith("/") ? value : `/${value}`);

export const resolveMediaUrl = (value?: string | null): string | undefined => {
  if (!value) return undefined;
  if (/^(https?:)?\/\//i.test(value) || value.startsWith("data:")) {
    return value;
  }
  if (value.startsWith("/assets/") || value.startsWith("assets/") || value.startsWith("/src/assets/")) {
    return value.startsWith("/") ? value : `/${value}`;
  }
  const normalized = ensureLeadingSlash(value);

  if (ABSOLUTE_MEDIA_BASE) {
    try {
      const url = new URL(MEDIA_BASE.endsWith("/") ? MEDIA_BASE : `${MEDIA_BASE}/`);
      const basePath = url.pathname.replace(/\/$/, "") || "/";
      if (normalized.startsWith(basePath)) {
        return `${url.origin}${normalized}`;
      }
      const composed = `${basePath}${normalized}`.replace(/\/{2,}/g, "/");
      return `${url.origin}${composed.startsWith("/") ? composed : `/${composed}`}`;
    } catch {
      const base = MEDIA_BASE.replace(/\/$/, "");
      return `${base}${normalized}`;
    }
  }

  const basePath = ensureLeadingSlash(MEDIA_BASE);
  if (normalized.startsWith(basePath)) {
    return normalized;
  }
  return `${basePath}${normalized}`.replace(/\/{2,}/g, "/");
};

export const uploadImageFile = async (file: File, agencyId: number): Promise<MediaAsset> => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<MediaAsset>("/media/upload", formData, {
    params: { agency_id: agencyId },
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
};

const blobToDataUrl = (blob: Blob): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("Não foi possível ler a imagem processada."));
    reader.readAsDataURL(blob);
  });

const loadImage = (source: string): Promise<HTMLImageElement> =>
  new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Não foi possível abrir a imagem."));
    image.src = source;
  });

/** Removes a flat logo background connected to the image edges in the browser. */
const removeSolidEdgeBackground = async (source: string): Promise<string | null> => {
  try {
    const image = await loadImage(source);
    const canvas = document.createElement("canvas");
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context || !canvas.width || !canvas.height) return null;
    context.drawImage(image, 0, 0);
    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    const pixels = imageData.data;
    const width = canvas.width;
    const height = canvas.height;
    const cornerIndexes = [0, width - 1, (height - 1) * width, height * width - 1];
    const background = [0, 1, 2].map(channel =>
      Math.round(cornerIndexes.reduce((sum, index) => sum + pixels[index * 4 + channel], 0) / 4)
    );
    const distance = (index: number) =>
      Math.max(
        Math.abs(pixels[index * 4] - background[0]),
        Math.abs(pixels[index * 4 + 1] - background[1]),
        Math.abs(pixels[index * 4 + 2] - background[2])
      );

    let borderCount = 0;
    let matchingBorder = 0;
    const countBorder = (index: number) => {
      borderCount += 1;
      if (distance(index) <= 32) matchingBorder += 1;
    };
    for (let x = 0; x < width; x += 1) {
      countBorder(x);
      countBorder((height - 1) * width + x);
    }
    for (let y = 1; y < height - 1; y += 1) {
      countBorder(y * width);
      countBorder(y * width + width - 1);
    }
    if (!borderCount || matchingBorder / borderCount < 0.6) return null;

    const visited = new Uint8Array(width * height);
    const queue = new Int32Array(width * height);
    let head = 0;
    let tail = 0;
    const enqueue = (index: number) => {
      if (visited[index] || distance(index) > 64) return;
      visited[index] = 1;
      queue[tail++] = index;
    };
    for (let x = 0; x < width; x += 1) {
      enqueue(x);
      enqueue((height - 1) * width + x);
    }
    for (let y = 1; y < height - 1; y += 1) {
      enqueue(y * width);
      enqueue(y * width + width - 1);
    }
    while (head < tail) {
      const index = queue[head++];
      const x = index % width;
      const y = Math.floor(index / width);
      if (x > 0) enqueue(index - 1);
      if (x + 1 < width) enqueue(index + 1);
      if (y > 0) enqueue(index - width);
      if (y + 1 < height) enqueue(index + width);
    }
    if (tail < width + height) return null;

    for (let index = 0; index < visited.length; index += 1) {
      if (!visited[index]) continue;
      const colorDistance = distance(index);
      const alpha = colorDistance <= 24 ? 0 : Math.round(((colorDistance - 24) / 40) * 190);
      pixels[index * 4 + 3] = Math.min(pixels[index * 4 + 3], alpha);
    }
    context.putImageData(imageData, 0, 0);
    return canvas.toDataURL("image/png");
  } catch {
    return null;
  }
};

export const removeImageBackground = async (source: string, agencyId: number): Promise<string> => {
  const locallyProcessed = await removeSolidEdgeBackground(source);
  if (locallyProcessed) return locallyProcessed;

  const sourceResponse = await fetch(source);
  if (!sourceResponse.ok) {
    throw new Error("Não foi possível carregar a imagem selecionada.");
  }
  const sourceBlob = await sourceResponse.blob();
  if (!sourceBlob.type.startsWith("image/")) {
    throw new Error("O arquivo selecionado não é uma imagem válida.");
  }

  const extension = sourceBlob.type.split("/")[1]?.replace("jpeg", "jpg") || "png";
  const formData = new FormData();
  formData.append("file", new File([sourceBlob], `background-source.${extension}`, { type: sourceBlob.type }));
  const response = await api.post<Blob>("/media/remove-background", formData, {
    params: { agency_id: agencyId },
    headers: { "Content-Type": "multipart/form-data" },
    responseType: "blob"
  });
  return blobToDataUrl(response.data);
};
