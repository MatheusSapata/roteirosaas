import { reactive } from "vue";
import { uploadStockPhoto, type StockPhotoCredits } from "./imageApiKeys";

/**
 * Envio de várias fotos para o banco próprio, em segundo plano: a fila fica fora da tela, então
 * dá para fechar a gaveta ou ir para outra página do admin que o envio continua (só fechar a aba
 * interrompe, e o navegador avisa antes). Vão 3 fotos de cada vez; falha de rede tenta de novo.
 */
export interface UploadItem {
  file: File;
  path: string;
}

export const uploadState = reactive({
  running: false,
  total: 0,
  done: 0,
  added: 0,
  duplicates: 0,
  skipped: [] as string[],
  finishedAt: null as number | null
});

const CONCURRENCY = 3;
let finishedListeners: Array<() => void> = [];

export const onUploadsFinished = (listener: () => void) => {
  finishedListeners.push(listener);
  return () => {
    finishedListeners = finishedListeners.filter(item => item !== listener);
  };
};

const warnBeforeLeaving = (event: BeforeUnloadEvent) => {
  event.preventDefault();
  event.returnValue = "";
};

const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const sendOne = async ({ file, path }: UploadItem, fields: StockPhotoCredits) => {
  for (let attempt = 1; attempt <= 2; attempt += 1) {
    try {
      await uploadStockPhoto(file, path, fields);
      uploadState.added += 1;
      return;
    } catch (error: any) {
      const status = error?.response?.status as number | undefined;
      if (status === 409) {
        uploadState.duplicates += 1;
        return;
      }
      // Erro da foto (formato, tamanho...): não adianta tentar de novo.
      if ((status && status < 500 && status !== 429) || attempt === 2) {
        uploadState.skipped.push(`${file.name}: ${error?.response?.data?.detail || "falhou"}`);
        return;
      }
      await wait(2000);
    }
  }
};

export const startUploads = async (items: UploadItem[], fields: StockPhotoCredits) => {
  if (uploadState.running) throw new Error("Já existe um envio em andamento. Espere terminar.");
  Object.assign(uploadState, { running: true, total: items.length, done: 0, added: 0, duplicates: 0, skipped: [], finishedAt: null });
  window.addEventListener("beforeunload", warnBeforeLeaving);
  const queue = [...items];
  const worker = async () => {
    while (queue.length) {
      const item = queue.shift()!;
      await sendOne(item, { ...fields });
      uploadState.done += 1;
    }
  };
  try {
    await Promise.all(Array.from({ length: Math.min(CONCURRENCY, items.length) }, worker));
  } finally {
    uploadState.running = false;
    uploadState.finishedAt = Date.now();
    window.removeEventListener("beforeunload", warnBeforeLeaving);
    finishedListeners.forEach(listener => listener());
  }
};
