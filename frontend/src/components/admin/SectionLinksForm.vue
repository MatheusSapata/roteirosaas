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
          <div class="item-head" role="button" tabindex="0" :aria-expanded="expandedIndex === index" @click="toggleCard(index)" @keydown.enter.prevent="toggleCard(index)" @keydown.space.prevent="toggleCard(index)"><span class="handle" title="Arraste para reordenar" @click.stop>⋮⋮</span><span class="chevron">›</span><strong>{{ cardName(item, index) }}</strong><button v-if="item.source === 'external'" type="button" class="refresh" :disabled="refreshingIndex === index" @click.stop="refreshMetadata(item, index)">{{ refreshingIndex === index ? 'Atualizando…' : 'Atualizar metadados' }}</button><button type="button" class="remove" @click.stop="remove(index)">Remover</button></div>
          <div v-if="expandedIndex === index" class="fields">
            <label>URL<input v-model="item.url" type="url" /></label>
            <label>Imagem (URL)<input v-model="item.image" type="url" placeholder="https://…/imagem.jpg" /></label>
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

interface AgencyPage { id:number; title:string; slug:string; status:string; cover_image_url?:string; seo_description?:string; }
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
const errorMessage = ref("");
const listRef = ref<HTMLElement|null>(null);
let sortable: Sortable|null = null;
let syncing = false;
const cloneItems = (items?:LinkCardItem[]) => Array.isArray(items) ? items.map(item => ({ ...item })) : [];
const local = reactive<LinksSection>({ type:"links", enabled:true, title:"Links recomendados", items:[], ...props.modelValue, headingLabel:props.modelValue.headingLabel ?? defaults.label, headingLabelStyle:props.modelValue.headingLabelStyle || defaults.style, items:cloneItems(props.modelValue.items) });
const makeId = () => `link-${Date.now()}-${Math.random().toString(36).slice(2,7)}`;

watch(() => props.modelValue, value => { syncing=true; Object.assign(local,value); local.items=cloneItems(value.items); nextTick(() => syncing=false); }, { deep:true });
watch(local, value => { if (!syncing) emit("update:modelValue", { ...value, items:cloneItems(value.items) }); }, { deep:true });
const loadPages = async () => {
  const agencyId = agencyStore.currentAgencyId;
  if (!agencyId) return;
  try { pages.value = (await api.get<AgencyPage[]>("/pages", { params:{ agency_id:agencyId } })).data; } catch { pages.value=[]; }
};
const availablePages = pages;
const addPage = () => {
  const page = pages.value.find(candidate => candidate.id === Number(selectedPageId.value));
  if (!page) return;
  const agency = agencyStore.agencies.find(item => item.id === agencyStore.currentAgencyId);
  const agencySlug = agency?.slug || "";
  local.items.push({ id:makeId(), source:"page", pageId:page.id, url:`/${agencySlug}/${page.slug}`, image:page.cover_image_url || "", title:page.title, description:page.seo_description || "", buttonLabel:"Abrir roteiro", openInNewTab:false });
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
    errorMessage.value=error?.response?.data?.detail || "Não foi possível ler os dados desse link. Confira a URL e tente novamente.";
  } finally { loadingMetadata.value=false; }
};
const toggleCard = (index:number) => { expandedIndex.value=expandedIndex.value === index ? null : index; };
const cardName = (item:LinkCardItem, index:number) => typeof item.title === "string" && item.title.trim() ? item.title : `Card ${index+1}`;
const remove = (index:number) => {
  local.items.splice(index,1);
  if (expandedIndex.value === index) expandedIndex.value=null;
  else if (expandedIndex.value !== null && expandedIndex.value > index) expandedIndex.value-=1;
};
const refreshMetadata = async (item:LinkCardItem, index:number) => {
  if (!item.url || refreshingIndex.value !== null) return;
  refreshingIndex.value=index; errorMessage.value="";
  try {
    const { data } = await api.post<{url:string;title:string;description:string;image:string}>("/pages/link-metadata", { url:item.url });
    item.url=data.url || item.url; item.title=data.title || item.title; item.description=data.description || ""; item.image=data.image || item.image;
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
</style>
