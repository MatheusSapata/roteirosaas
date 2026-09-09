<template>
  <div class="featured-video-proto-body video-vsl-form">
    <aside class="tabs">
      <button v-for="tab in tabs" :key="tab.id" type="button" class="tab" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id">
        <span class="tab-icon" v-html="tab.icon"></span><span>{{ tab.label }}<small>{{ tab.description }}</small></span>
      </button>
    </aside>
    <section class="editor"><div class="section-card">
      <div class="section-head"><h2 class="section-title">{{ panelTitle }}</h2><p class="section-desc">{{ panelDescription }}</p></div>
      <div class="content-area">
        <template v-if="activeTab === 'text'">
          <div class="field"><label>Etiqueta acima do título <span class="help" data-tip="Texto pequeno exibido no chip acima do título.">?</span></label><input v-model="local.headingLabel" /></div>
          <div class="field"><label>Título principal <span class="help" data-tip="Chamada principal exibida antes do vídeo.">?</span></label><input v-model="local.title" placeholder="Assista ao vídeo antes de continuar" /></div>
          <div class="field"><label>Subtítulo</label><RichTextEditor v-model="local.subtitle" placeholder="Explique o que a pessoa verá no vídeo" /></div>
        </template>
        <template v-else-if="activeTab === 'video'">
          <div class="field"><label>URL do YouTube <span class="help" data-tip="Cole um link público de vídeo do YouTube.">?</span></label><input v-model="local.videoUrl" placeholder="https://www.youtube.com/watch?v=..." /><p class="field-hint">O tempo é contado somente enquanto o vídeo estiver sendo reproduzido.</p></div>
          <div class="grid-2">
            <div class="field"><label>Formato do vídeo</label><select v-model="local.videoAspectRatio"><option value="horizontal">Horizontal — 16:9</option><option value="vertical">Vertical — 9:16</option><option value="square">Quadrado — 1:1</option></select></div>
            <div class="field"><label>Desbloquear após <span class="help" data-tip="Tempo efetivamente assistido antes de liberar a ação.">?</span></label><div class="input-suffix"><input v-model.number="local.unlockAfterSeconds" type="number" min="0" step="1" /><span>segundos</span></div></div>
          </div>
          <div class="note-box">A barra de progresso acompanha somente o tempo realmente reproduzido.</div>
          <label class="inline-check"><input v-model="local.progressBarEnabled" type="checkbox" /> Exibir barra de progresso fictícia</label>
        </template>
        <template v-else>
          <div class="field"><label>O que liberar</label><div class="choice-grid">
            <button v-for="choice in actionChoices" :key="choice.value" type="button" class="choice" :class="{ active: local.unlockAction === choice.value }" @click="local.unlockAction = choice.value"><strong>{{ choice.label }}</strong><small>{{ choice.description }}</small></button>
          </div></div>
          <template v-if="local.unlockAction !== 'reveal_page'">
            <div class="field"><label>Destino do botão</label><div class="pill-row"><button type="button" class="pill" :class="{ active: local.ctaDestinationMode !== 'page' }" @click="setDestinationMode('external')">Link externo</button><button type="button" class="pill" :class="{ active: local.ctaDestinationMode === 'page' }" @click="setDestinationMode('page')">Página da agência</button></div></div>
            <div class="grid-2"><div class="field"><label>Texto do botão</label><input v-model="local.ctaLabel" placeholder="Quero saber mais" /></div><div v-if="local.ctaDestinationMode !== 'page'" class="field"><label>Link externo</label><input v-model="local.ctaLink" placeholder="https://..." /></div><div v-else class="field"><label>Página da agência</label><select v-model.number="local.ctaPageId" @change="applySelectedPage"><option :value="null">Selecione uma página</option><option v-for="page in agencyPages" :key="page.id" :value="page.id">{{ pageTitle(page) }}</option></select><p v-if="pagesLoading" class="field-hint">Carregando páginas...</p></div></div>
            <label class="inline-check"><input v-model="local.ctaOpenInNewTab" type="checkbox" /> Abrir o link em nova aba</label>
            <div class="note-box">A cor segue a configuração global de botões e destaques.</div>
          </template>
        </template>
      </div>
    </div></section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import type { VideoVslSection } from "../../types/page";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { adminTabIcons } from "../../utils/adminTabIcons";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
const props=defineProps<{modelValue:VideoVslSection}>();
const emit=defineEmits<{(event:"update:modelValue",value:VideoVslSection):void}>();
const defaults=getSectionHeadingDefaults("video_vsl");
const activeTab=ref<"text"|"video"|"action">("text");
const tabs=[{id:"text",label:"Textos",description:"Título e descrição",icon:adminTabIcons.text},{id:"video",label:"Vídeo",description:"Player e tempo",icon:adminTabIcons.media},{id:"action",label:"Desbloqueio",description:"Página e botão",icon:adminTabIcons.button}] as const;
const actionChoices=[{value:"reveal_page",label:"Exibir página",description:"Libera as seções abaixo."},{value:"show_button",label:"Exibir botão",description:"Mantém a página oculta."},{value:"both",label:"Exibir ambos",description:"Libera página e botão."}] as const;
interface AgencyPage { id:number; title:any; slug:string; }
const agencyStore=useAgencyStore();const agencyPages=ref<AgencyPage[]>([]);const pagesLoading=ref(false);
const pageTitle=(page:AgencyPage)=>typeof page.title==="string"?page.title:(page.title?.pt||page.title?.es||page.slug);
const applySelectedPage=()=>{const page=agencyPages.value.find(item=>item.id===Number(local.ctaPageId));const agency=agencyStore.agencies.find(item=>item.id===agencyStore.currentAgencyId);if(page&&agency)local.ctaLink=`/${agency.slug}/${page.slug}`};
const setDestinationMode=(mode:"external"|"page")=>{local.ctaDestinationMode=mode;if(mode==="page")applySelectedPage()};
const loadPages=async()=>{if(!agencyStore.currentAgencyId)return;pagesLoading.value=true;try{agencyPages.value=(await api.get<AgencyPage[]>("/pages",{params:{agency_id:agencyStore.currentAgencyId}})).data}catch{agencyPages.value=[]}finally{pagesLoading.value=false}};
onMounted(loadPages);
const panelTitle=computed(()=>activeTab.value==="text"?"Textos da Video VSL":activeTab.value==="video"?"Vídeo e reprodução":"Ação após o tempo");
const panelDescription=computed(()=>activeTab.value==="text"?"Configure o chip, o título e o texto de apoio da seção.":activeTab.value==="video"?"Defina o vídeo, formato e momento do desbloqueio.":"Escolha o que será exibido após o tempo assistido.");
const local=reactive<VideoVslSection>({type:"video_vsl",enabled:true,...props.modelValue});let syncing=false;
const sync=(value:VideoVslSection)=>{syncing=true;Object.assign(local,value,{headingLabel:value.headingLabel??defaults.label,headingLabelStyle:value.headingLabelStyle??defaults.style,videoAspectRatio:value.videoAspectRatio==="vertical"||value.videoAspectRatio==="square"?value.videoAspectRatio:"horizontal",progressBarEnabled:value.progressBarEnabled!==false,unlockAfterSeconds:Math.max(0,Number(value.unlockAfterSeconds)||0),unlockAction:value.unlockAction==="show_button"||value.unlockAction==="both"?value.unlockAction:"reveal_page",ctaDestinationMode:value.ctaDestinationMode==="page"?"page":"external",ctaPageId:value.ctaPageId??null,ctaOpenInNewTab:value.ctaOpenInNewTab!==false});nextTick(()=>{syncing=false})};
watch(()=>props.modelValue,sync,{deep:true,immediate:true});watch(local,value=>{if(!syncing)emit("update:modelValue",{...value})},{deep:true});
</script>

<style scoped>
.featured-video-proto-body{display:grid;grid-template-columns:178px 1fr;height:100%}.tabs{border-right:1px solid #e6eee8;padding:16px 12px;display:flex;flex-direction:column;gap:8px;background:#fff}.tab{display:flex;align-items:center;gap:10px;border:1px solid #d8dfda;border-radius:14px;padding:7px 9px;background:#eef2ef;color:#0f172a;text-align:left}.tab.active{background:var(--primary);border-color:var(--primary);color:var(--primary-foreground)}.tab-icon{width:22px;height:22px;border-radius:8px;background:rgba(255,255,255,.82);display:inline-flex;align-items:center;justify-content:center}.tab>span{display:flex;flex-direction:column;font-size:15px;font-weight:700}.tab small{font-size:12px;font-weight:600;color:rgba(15,23,42,.55)}.editor{background:#edf1ef;min-width:0}.section-head{padding:14px 16px 10px;border-bottom:1px solid #dde5e1}.section-title{margin:0;font-size:18px;font-weight:800}.section-desc{margin:6px 0 0;font-size:13px;color:#6a7e74}.content-area{padding:12px 14px;display:grid;gap:12px}.field{display:grid;gap:6px}.field label{font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:800;color:#6a7e74;display:flex;align-items:center;gap:7px}.field input,.field select{width:100%;border:1px solid #cad7d1;border-radius:12px;background:#fff;padding:9px 12px;font-size:15px;color:#1f2937}.field-hint{margin:0;font-size:11px;color:#7d9087}.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.help{width:16px;height:16px;border:1px solid #cdd8d2;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:10px;position:relative}.help:hover:after{content:attr(data-tip);position:absolute;left:22px;white-space:nowrap;padding:6px 8px;background:#0f172a;color:#fff;border-radius:8px;z-index:20;text-transform:none;letter-spacing:0}.input-suffix{display:flex}.input-suffix input{border-radius:12px 0 0 12px}.input-suffix span{display:flex;align-items:center;padding:0 11px;border:1px solid #cad7d1;border-left:0;border-radius:0 12px 12px 0;background:#f5f7f6;font-size:12px}.choice-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.choice{display:grid;gap:3px;text-align:left;padding:11px;border:1px solid #d8dfda;border-radius:12px;background:#fff;color:#475569}.choice small{font-size:11px;color:#7d9087}.choice.active{border-color:var(--primary);box-shadow:0 0 0 2px color-mix(in srgb,var(--primary) 20%,transparent)}.note-box{padding:10px 12px;border-radius:12px;background:#fff;border:1px solid #dfe8e2;color:#607269;font-size:12px}.inline-check{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:#475569}.inline-check input{width:15px;height:15px}@media(max-width:720px){.featured-video-proto-body{grid-template-columns:1fr}.tabs{flex-direction:row;border-right:0}.tab{flex:1}.tab small{display:none}.grid-2,.choice-grid{grid-template-columns:1fr}}
.pill-row{display:flex;gap:8px;flex-wrap:wrap}.pill{border:1px solid #d8dfda;border-radius:12px;padding:8px 12px;background:#fff;color:#516358;font-size:13px;font-weight:700}.pill.active{border-color:var(--primary);background:var(--primary);color:var(--primary-foreground)}
</style>
