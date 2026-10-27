/**
 * "Fast start" de MP4 no navegador, antes do envio: muitos programas gravam o índice do vídeo
 * (a caixa "moov") no fim do arquivo, e aí o navegador precisa baixar o vídeo inteiro antes de
 * tocar. Aqui o índice vai para antes dos dados ("mdat"), como o qt-faststart e o "Otimizar para
 * web" dos editores, sem recodificar: só os endereços dos trechos (stco/co64) andam o tamanho do
 * índice. Arquivo que já está certo, que não é MP4 ou que tem algo inesperado volta como veio.
 */

type Box = { type: string; start: number; size: number };

// Caixas que só agrupam outras, no caminho até a tabela de endereços (moov/trak/mdia/minf/stbl).
const CONTAINERS = new Set(["moov", "trak", "mdia", "minf", "stbl"]);
const MAX_MOOV_BYTES = 64 * 1024 * 1024;

const fourcc = (view: DataView, offset: number) =>
  String.fromCharCode(view.getUint8(offset), view.getUint8(offset + 1), view.getUint8(offset + 2), view.getUint8(offset + 3));

const readTopLevelBoxes = async (file: Blob): Promise<Box[] | null> => {
  const boxes: Box[] = [];
  let offset = 0;
  while (offset < file.size) {
    const view = new DataView(await file.slice(offset, offset + 16).arrayBuffer());
    if (view.byteLength < 8) return null;
    let size = view.getUint32(0);
    let header = 8;
    if (size === 1) {
      if (view.byteLength < 16) return null;
      size = Number(view.getBigUint64(8));
      header = 16;
    } else if (size === 0) {
      size = file.size - offset;
    }
    if (size < header || offset + size > file.size) return null;
    boxes.push({ type: fourcc(view, 4), start: offset, size });
    offset += size;
  }
  return boxes;
};

/** Soma `shift` aos endereços entre [from, to) nas tabelas stco/co64; false se algo não fecha. */
const patchChunkOffsets = (view: DataView, start: number, end: number, from: number, to: number, shift: number): boolean => {
  let pos = start;
  while (pos + 8 <= end) {
    let size = view.getUint32(pos);
    let header = 8;
    if (size === 1) {
      size = Number(view.getBigUint64(pos + 8));
      header = 16;
    } else if (size === 0) {
      size = end - pos;
    }
    if (size < header || pos + size > end) return false;
    const type = fourcc(view, pos + 4);
    if (type === "cmov") return false;
    if (CONTAINERS.has(type)) {
      if (!patchChunkOffsets(view, pos + header, pos + size, from, to, shift)) return false;
    } else if (type === "stco" || type === "co64") {
      const wide = type === "co64";
      const count = view.getUint32(pos + header + 4);
      const first = pos + header + 8;
      if (first + count * (wide ? 8 : 4) > pos + size) return false;
      for (let i = 0; i < count; i += 1) {
        const at = first + i * (wide ? 8 : 4);
        const value = wide ? Number(view.getBigUint64(at)) : view.getUint32(at);
        if (value < from || value >= to) continue;
        if (wide) view.setBigUint64(at, BigInt(value + shift));
        else if (value + shift > 0xffffffff) return false;
        else view.setUint32(at, value + shift);
      }
    }
    pos += size;
  }
  return pos === end;
};

export const mp4Faststart = async (file: Blob): Promise<Blob> => {
  const boxes = await readTopLevelBoxes(file);
  if (!boxes) return file;
  const moovIndex = boxes.findIndex(box => box.type === "moov");
  const mdatIndex = boxes.findIndex(box => box.type === "mdat");
  // Já começa pelo índice, não tem índice/dados ou é MP4 fragmentado (moof): fica como está.
  if (moovIndex < 0 || mdatIndex < 0 || moovIndex < mdatIndex || boxes.some(box => box.type === "moof")) return file;
  const moov = boxes[moovIndex];
  if (moov.size > MAX_MOOV_BYTES) return file;

  const moovBytes = new Uint8Array(await file.slice(moov.start, moov.start + moov.size).arrayBuffer());
  const view = new DataView(moovBytes.buffer);
  const header = view.getUint32(0) === 1 ? 16 : 8;
  // O índice entra onde começavam os dados: o que estava entre esse ponto e o índice anda o
  // tamanho dele; o que vinha depois do índice continua no mesmo lugar.
  const insertAt = boxes[mdatIndex].start;
  if (!patchChunkOffsets(view, header, moov.size, insertAt, moov.start, moov.size)) return file;

  const before = boxes.slice(0, mdatIndex).filter(box => box.type !== "moov");
  const after = boxes.slice(mdatIndex).filter(box => box.type !== "moov");
  const piece = (box: Box) => file.slice(box.start, box.start + box.size);
  return new Blob([...before.map(piece), moovBytes, ...after.map(piece)], { type: file.type || "video/mp4" });
};
