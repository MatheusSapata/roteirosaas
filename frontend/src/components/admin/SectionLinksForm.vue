<template>
  <div class="links-editor">
    <aside class="tabs">
      <button type="button" class="tab" :class="{ active: panel === 'texts' }" @click="panel = 'texts'"><span class="tab-icon">▣</span><span>Textos<small>Conteúdo principal</small></span></button>
      <button type="button" class="tab" :class="{ active: panel === 'links' }" @click="panel = 'links'"><span class="tab-icon">↗</span><span>Links<small>Cards do carrossel</small></span><b>{{ local.items.length }}</b></button>
    </aside>

    <section class="editor">
      <div v-if="panel === 'texts'" class="editor-card">
        <div class="section-head"><div><h2>Textos da seção</h2><p class="hint">Configure a chamada exibida acima do carrossel.</p></div></div>
        <div class="content-area">
          <label>Heading<input v-model="local.headingLabel" placeholder="Links" /></label>
          <label>Título<input v-model="local.title" placeholder="Explore nossos roteiros" /></label>
          <label>Subtítulo<textarea v-model="local.subtitle" rows="3" placeholder="Escolha uma experiência para conhecer todos os detalhes." /></label>
        </div>
      </div>

      <div v-else class="editor-card">
      <div class="section-head"><div><h2>Cards do carrossel</h2><p class="hint">Adicione quantos links quiser. Os dados encontrados podem ser alterados manualmente.</p></div></div>
      <div class="content-area">
      <div class="add-grid">
        <label>Página existente
          <select v-model="selectedPageId"><option value="">Selecione uma página</option><option v-for="page in availablePages" :key="page.id" :value="page.id">{{ page.title }}</option></select>
        </label>
        <button type="button" class="secondary" :disabled="!selectedPageId" @click="addPage">Adicionar página</button>
        <label class="external">Link externo
          <input v-model="externalUrl" type="url" placeholder="https://exemplo.com/pagina" @keyup.enter="addExternal" />
        </label>
        <button type="button" class="primary" :disabled="loadingMetadata || !externalUrl.trim()" @click="addExternal">{{ loadingMetadata ? 'Buscando dados…' : 'Adicionar link' }}</button>
      </div>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

      <div v-if="local.items.length" ref="listRef" class="cards-list">
        <article v-for="(item, index) in local.items" :key="item.id" class="item-card" :class="{ expanded: expandedIndex === index }" data-link-card>
          <div class="item-head" role="button" tabindex="0" :aria-expanded="expandedIndex === index" @click="toggleCard(index)" @keydown.enter.prevent="toggleCard(index)" @keydown.space.prevent="toggleCard(index)"><span class="handle" title="Arraste para reordenar" @click.stop>⋮⋮</span><span class="chevron">›</span><strong>{{ cardName(item, index) }}</strong><button type="button" class="refresh" :disabled="refreshingIndex === index" @click.stop="refreshMetadata(item, index)">{{ refreshingIndex === index ? 'Atualizando…' : 'Atualizar metadados' }}</button><button type="button" class="remove" @click.stop="remove(index)">Remover</button></div>
          <div v-if="expandedIndex === index" class="fields">
            <div class="image-field">
              <span class="field-label">Imagem do card</span>
              <div class="image-picker">
                <input :id="`link-image-${item.id}`" class="hidden-file" type="file" accept="image/*" @change="onCardImageFileChange(item, $event)" />
                <button class="image-thumb" type="button" @click="openImagePicker(item.id)">
                  <img v-if="previewImage(item.image)" :src="previewImage(item.image)" alt="Prévia da imagem do card" />
                  <span v-else>IMG</span>
                </button>
                <div class="image-copy"><strong>{{ item.image ? 'Imagem selecionada' : 'Sem imagem' }}</strong><small>Imagem obtida do link ou enviada por você.</small></div>
                <div class="image-actions">
                  <button type="button" @click="openImagePicker(item.id)" :disabled="uploadingImageId === item.id">{{ uploadingImageId === item.id ? 'Enviando…' : (item.image ? 'Substituir' : 'Adicionar') }}</button>
                  <button v-if="item.image" type="button" class="danger" @click="item.image = ''">Remover</button>
                </div>
              </div>
              <small v-if="imageUploadErrorId === item.id" class="upload-error">Não foi possível enviar a imagem. Tente novamente.</small>
            </div>
            <label class="url-field">URL do link<input v-model="item.url" type="url" /></label>
            <label>Título<input v-model="item.title" /></label>
            <label>Descrição<textarea v-model="item.description" rows="3" /></label>
            <label>Texto do botão<input v-model="item.buttonLabel" placeholder="Abrir link" /></label>
            <label class="check"><input v-model="item.openInNewTab" type="checkbox" /> Abrir em nova aba</label>
          </div>
        </article>
      </div>
      <div v-else class="empty">Nenhum link adicionado ainda.</div>
      </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import Sortable from "sortablejs";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import type { LinkCardItem, LinksSection } from "../../types/page";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { resolveMediaUrl, uploadImageFile } from "../../utils/media";

interface AgencyPage { id:number; title:string; slug:string; status:string; cover_image_url?:string; seo_title?:string; seo_description?:string; config_json?:Record<string,any>|string|null; }
const props = defineProps<{ modelValue: LinksSection }>();
const emit = defineEmits<{ (e:"update:modelValue", value:LinksSection):void }>();
const agencyStore = useAgencyStore();
const defaults = getSectionHeadingDefaults("links");
const panel = ref<"texts"|"links">("texts");
const pages = ref<AgencyPage[]>([]);
const selectedPageId = ref<number|"">("");
const externalUrl = ref("");
const loadingMetadata = ref(false);
const refreshingIndex = ref<number|null>(null);
const expandedIndex = ref<number|null>(null);
const uploadingImageId = ref<string|null>(null);
const imageUploadErrorId = ref<string|null>(null);
const errorMessage = ref("");
const listRef = ref<HTMLElement|null>(null);
let sortable: Sortable|null = null;
let syncing = false;
const makeId = () => `link-${Date.now()}-${Math.random().toString(36).slice(2,7)}`;
const cloneItems = (items?:LinkCardItem[]) => Array.isArray(items) ? items.map(item => ({ ...item, id:item.id || makeId() })) : [];
const local = reactive<LinksSection>({ type:"links", enabled:true, title:"Links recomendados", items:[], ...props.modelValue, headingLabel:props.modelValue.headingLabel ?? defaults.label, headingLabelStyle:props.modelValue.headingLabelStyle || defaults.style, items:cloneItems(props.modelValue.items) });

watch(() => props.modelValue, value => { syncing=true; Object.assign(local,value); local.items=cloneItems(value.items); nextTick(() => syncing=false); }, { deep:true });
watch(local, value => { if (!syncing) emit("update:modelValue", { ...value, items:cloneItems(value.items) }); }, { deep:true });
const loadPages = async () => {
  const agencyId = agencyStore.currentAgencyId;
  if (!agencyId) return;
  try { pages.value = (await api.get<AgencyPage[]>("/pages", { params:{ agency_id:agencyId } })).data; } catch { pages.value=[]; }
};
const availablePages = pages;
const plainText = (value:any):string => {
  if (typeof value === "string") return value.replace(/<[^>]+>/g, "").trim();
  if (value && typeof value === "object") return plainText(value.pt || value.es || Object.values(value)[0] || "");
  return "";
};
const pageCardMetadata = (page:AgencyPage) => {
  let config:Record<string,any>={};
  try { config=typeof page.config_json === "string" ? JSON.parse(page.config_json) : (page.config_json || {}); } catch { config={}; }
  const hero=Array.isArray(config.sections) ? config.sections.find((section:any) => section?.type === "hero") || {} : {};
  const general=config.general && typeof config.general === "object" ? config.general : {};
  const baseTitle=(page.seo_title || page.title || "").trim();
  return {
    title:/roteiro online/i.test(baseTitle) ? baseTitle : `${baseTitle} | Roteiro Online`,
    description:plainText(hero.subtitle) || plainText(general.shortDescription) || page.seo_description || "",
    image:hero.backgroundImage || page.cover_image_url || ""
  };
};
const addPage = () => {
  const page = pages.value.find(candidate => candidate.id === Number(selectedPageId.value));
  if (!page) return;
  const agency = agencyStore.agencies.find(item => item.id === agencyStore.currentAgencyId);
  const agencySlug = agency?.slug || "";
  const metadata=pageCardMetadata(page);
  local.items.push({ id:makeId(), source:"page", pageId:page.id, url:`/${agencySlug}/${page.slug}`, image:metadata.image, title:metadata.title, description:metadata.description, buttonLabel:"Abrir roteiro", openInNewTab:false });
  expandedIndex.value=local.items.length-1;
  selectedPageId.value="";
};
const normalizeUrl = (value:string) => /^https?:\/\//i.test(value) ? value : `https://${value}`;
const addExternal = async () => {
  if (!externalUrl.value.trim() || loadingMetadata.value) return;
  loadingMetadata.value=true; errorMessage.value="";
  const url=normalizeUrl(externalUrl.value.trim());
  try {
    const { data } = await api.post<{url:string;title:string;description:string;image:string}>("/pages/link-metadata", { url });
    local.items.push({ id:makeId(), source:"external", url:data.url || url, image:data.image || "", title:data.title || "Novo link", description:data.description || "", buttonLabel:"Abrir link", openInNewTab:true });
    expandedIndex.value=local.items.length-1;
    externalUrl.value="";
  } catch (error:any) {
    const detail=error?.response?.data?.detail || "Não foi possível carregar a prévia automaticamente. Você pode preencher os dados manualmente.";
    local.items.push({ id:makeId(), source:"external", url, image:"", title:new URL(url).hostname.replace(/^www\./,""), description:"", buttonLabel:"Abrir link", openInNewTab:true });
    expandedIndex.value=local.items.length-1;
    externalUrl.value="";
    errorMessage.value=detail;
  } finally { loadingMetadata.value=false; }
};
const toggleCard = (index:number) => { expandedIndex.value=expandedIndex.value === index ? null : index; };
const cardName = (item:LinkCardItem, index:number) => typeof item.title === "string" && item.title.trim() ? item.title : `Card ${index+1}`;
const previewImage = (value?:string) => resolveMediaUrl(value) || "";
const openImagePicker = (itemId?:string) => {
  if (!itemId) return;
  document.getElementById(`link-image-${itemId}`)?.click();
};
const onCardImageFileChange = async (item:LinkCardItem, event:Event) => {
  const input=event.target as HTMLInputElement;
  const file=input.files?.[0];
  if(!file)return;
  if(!agencyStore.currentAgencyId) await agencyStore.loadAgencies().catch(() => undefined);
  const agencyId=agencyStore.currentAgencyId;
  if(!agencyId){ imageUploadErrorId.value=item.id || null; input.value=""; return; }
  uploadingImageId.value=item.id || null; imageUploadErrorId.value=null;
  try { item.image=(await uploadImageFile(file,agencyId)).url; }
  catch { imageUploadErrorId.value=item.id || null; }
  finally { uploadingImageId.value=null; input.value=""; }
};
const remove = (index:number) => {
  local.items.splice(index,1);
  if (expandedIndex.value === index) expandedIndex.value=null;
  else if (expandedIndex.value !== null && expandedIndex.value > index) expandedIndex.value-=1;
};
const refreshMetadata = async (item:LinkCardItem, index:number) => {
  if (!item.url || refreshingIndex.value !== null) return;
  refreshingIndex.value=index; errorMessage.value="";
  try {
    const requestUrl=/^https?:\/\//i.test(item.url) ? item.url : new URL(item.url, window.location.origin).toString();
    const { data } = await api.post<{url:string;title:string;description:string;image:string}>("/pages/link-metadata", { url:requestUrl });
    if(item.source === "external") item.url=data.url || item.url; item.title=data.title || item.title; item.description=data.description || ""; item.image=data.image || item.image;
  } catch (error:any) { errorMessage.value=error?.response?.data?.detail || "Não foi possível atualizar os metadados."; }
  finally { refreshingIndex.value=null; }
};
const setupSortable = () => {
  sortable?.destroy(); if (!listRef.value) return;
  sortable=Sortable.create(listRef.value,{ animation:180, handle:".handle", draggable:"[data-link-card]", onEnd:event => { const from=event.oldIndex, to=event.newIndex; if(from===undefined||to===undefined||from===to)return; const [moved]=local.items.splice(from,1); local.items.splice(to,0,moved); if(expandedIndex.value===from)expandedIndex.value=to; else if(expandedIndex.value!==null&&expandedIndex.value>from&&expandedIndex.value<=to)expandedIndex.value-=1; else if(expandedIndex.value!==null&&expandedIndex.value<from&&expandedIndex.value>=to)expandedIndex.value+=1; } });
};
watch([listRef, () => local.items.length], () => nextTick(setupSortable));
onMounted(() => { loadPages(); setupSortable(); });
onBeforeUnmount(() => sortable?.destroy());
</script>

<style scoped>
.links-editor{display:grid;grid-template-columns:178px 1fr;height:100%;min-height:0;align-items:stretch}.tabs{display:flex;flex-direction:column;gap:8px;padding:16px 12px;background:var(--card);border-right:1px solid var(--border)}.tab{display:flex;align-items:center;gap:10px;height:50px;border:1px solid var(--border);border-radius:14px;padding:7px 9px;background:var(--muted);color:var(--foreground);text-align:left}.tab.active{background:var(--primary);border-color:var(--primary);color:var(--primary-foreground)}.tab-icon{flex:0 0 26px;width:26px;height:26px;border-radius:8px;display:grid;place-items:center;background:color-mix(in srgb,var(--card) 82%,transparent);font-size:12px}.tab>span:nth-child(2){display:flex;flex:1;min-width:0;flex-direction:column;font-size:14px;font-weight:800;line-height:1.05}.tab small{margin-top:4px;font-size:9px;font-weight:600;opacity:.7}.tab b{min-width:24px;padding:4px 7px;border-radius:99px;background:color-mix(in srgb,var(--card) 78%,transparent);text-align:center;font-size:12px}.editor{min-width:0;min-height:100%;background:var(--background)}.editor-card{min-height:100%;background:transparent}.section-head{padding:14px 16px 10px;border-bottom:1px solid color-mix(in srgb,var(--border) 62%,transparent)}.editor-card h2{margin:0;font-size:18px;line-height:1.15;font-weight:800;color:var(--foreground)}.hint{margin:6px 0 0;font-size:13px;color:var(--muted-foreground)}.content-area{display:grid;gap:12px;padding:12px 14px;align-content:start}.editor-card label{display:grid;gap:6px;margin:0;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted-foreground)}.editor-card input,.editor-card textarea,.editor-card select{width:100%;border:1px solid var(--input);border-radius:12px;padding:9px 12px;background:var(--card);color:var(--foreground);font:inherit;font-size:14px;text-transform:none;letter-spacing:normal}.editor-card input:focus,.editor-card textarea:focus,.editor-card select:focus{outline:0;border-color:var(--ring);box-shadow:0 0 0 3px color-mix(in srgb,var(--ring) 15%,transparent)}.add-grid{display:grid;grid-template-columns:1fr auto;gap:10px 12px;align-items:end}.add-grid button{height:40px;border:1px solid var(--border);border-radius:10px;padding:0 16px;font-size:12px;font-weight:800}.primary{background:var(--primary);border-color:var(--primary)!important;color:var(--primary-foreground)}.secondary{background:var(--muted);color:var(--foreground)}button:disabled{opacity:.5}.cards-list{display:grid;gap:12px}.item-card{border:1px solid var(--border);border-radius:14px;padding:14px;background:var(--card)}.item-head{display:flex;align-items:center;gap:10px;margin-bottom:13px}.item-head strong{font-size:14px;color:var(--foreground)}.handle{cursor:grab;font-size:18px;color:var(--muted-foreground)}.remove{border:0;background:none;color:#dc2626;font-size:12px;font-weight:800}.refresh{margin-left:auto;border:1px solid color-mix(in srgb,var(--primary) 35%,var(--border));background:color-mix(in srgb,var(--primary) 10%,var(--card));color:var(--primary);border-radius:9px;padding:7px 10px;font-size:11px;font-weight:800}.fields{display:grid;grid-template-columns:1fr 1fr;gap:12px 14px}.fields label:nth-child(4){grid-column:1/-1}.check{display:flex!important;grid-column:1/-1;flex-direction:row;align-items:center}.check input{width:auto}.error{margin:0;color:#b91c1c;background:#fef2f2;padding:10px;border-radius:9px;font-size:12px}.empty{text-align:center;padding:32px;border:1px dashed var(--border);border-radius:12px;color:var(--muted-foreground);font-size:13px}@media(max-width:700px){.links-editor{grid-template-columns:1fr}.tabs{flex-direction:row;border-right:0;border-bottom:1px solid var(--border)}.tab{flex:1}.tab small{display:none}.add-grid,.fields{grid-template-columns:1fr}.fields label:nth-child(4){grid-column:auto}}
.cards-list{gap:10px}.item-card{padding:0;overflow:hidden}.item-card.expanded{border-color:color-mix(in srgb,var(--primary) 35%,var(--border))}.item-head{min-height:52px;margin:0;padding:10px 14px;cursor:pointer;outline:0}.item-head:focus-visible{box-shadow:inset 0 0 0 2px var(--ring)}.item-head strong{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.chevron{font-size:24px;line-height:1;color:var(--muted-foreground);transition:transform .18s ease}.expanded .chevron{transform:rotate(90deg);color:var(--primary)}.fields{padding:14px;border-top:1px solid var(--border);background:color-mix(in srgb,var(--background) 55%,var(--card))}@media(max-width:700px){.refresh{display:none}}
.image-field{display:grid;gap:6px}.field-label{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted-foreground)}.image-picker{display:flex;align-items:center;gap:12px;min-height:78px;padding:9px;border:1px solid var(--input);border-radius:12px;background:var(--card)}.hidden-file{display:none!important}.image-thumb{flex:0 0 92px;width:92px;height:60px;padding:0;border:1px solid var(--border);border-radius:9px;overflow:hidden;background:var(--muted);color:var(--muted-foreground);font-size:11px;font-weight:800}.image-thumb img{display:block;width:100%;height:100%;object-fit:cover;object-position:center}.image-copy{display:flex;min-width:0;flex:1;flex-direction:column;gap:3px}.image-copy strong{font-size:12px;color:var(--foreground)}.image-copy small{font-size:10px;color:var(--muted-foreground)}.image-actions{display:flex;gap:6px}.image-actions button{border:1px solid var(--border);border-radius:8px;padding:7px 9px;background:var(--muted);color:var(--foreground);font-size:10px;font-weight:800}.image-actions .danger{color:#dc2626;background:#fff}.upload-error{color:#dc2626;font-size:11px}@media(max-width:700px){.image-picker{align-items:flex-start;flex-wrap:wrap}.image-copy{min-width:150px}.image-actions{width:100%}}
.image-field,.url-field{grid-column:1/-1}
</style>
