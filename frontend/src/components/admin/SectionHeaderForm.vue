<template>
  <div class="header-editor">
    <aside class="tabs">
      <button v-for="tab in tabs" :key="tab.id" type="button" :class="{ active: panel === tab.id }" @click="panel = tab.id"><span>{{ tab.icon }}</span><b>{{ tab.label }}</b><small>{{ tab.desc }}</small></button>
    </aside>
    <main class="editor">
      <section v-if="panel === 'style'" class="card">
        <header><h2>Estrutura do cabeçalho</h2><p>A logo utilizada será a mesma do banner ou da sua agência.</p></header>
        <div class="body">
          <div class="mode-row"><label>Modo<select v-model="local.mode"><option value="solid">Sólido — antes do banner</option><option value="transparent" :disabled="!hasBanner">Transparente — sobre o banner</option><option value="blurred" :disabled="!hasBanner">Desfoque — sobre o banner</option></select></label><label class="sticky-toggle"><input v-model="local.stickyEnabled" type="checkbox" /><span></span><b>Fixar ao rolar</b></label></div>
          <p v-if="!hasBanner" class="mode-warning">Adicione e ative um banner para usar os modos transparente ou desfoque.</p>
          <div class="columns"><label v-if="local.mode === 'solid'">Cor do fundo<ColorInput v-model="local.backgroundColor" /></label><label>Cor dos links e ícones<ColorInput v-model="local.linkTextColor" /></label></div>
          <template v-if="local.mode === 'blurred'">
            <label>Intensidade do desfoque<div class="range"><input v-model.number="local.blurAmount" type="range" min="0" max="30" step="1" /><span>{{ local.blurAmount ?? 14 }} px</span></div></label>
            <p class="note">O fundo permanece sempre 100% transparente.</p>
          </template>
          <label>Tamanho dos textos<div class="range"><input v-model.number="local.linkFontSize" type="range" min="11" max="20" step="1" /><span>{{ local.linkFontSize || 14 }} px</span></div></label>
          <div class="columns"><label>Cor ao passar o mouse<ColorInput v-model="local.linkHoverColor" /></label><label>Animação do hover<select v-model="local.linkHoverAnimation"><option value="none">Sem animação</option><option value="underline">Linha animada</option><option value="lift">Elevar</option><option value="scale">Ampliar</option></select></label></div>
          <label>Tamanho da logo<div class="range"><input v-model.number="local.logoSize" type="range" min="36" max="96" step="2" /><span>{{ local.logoSize || 56 }} px</span></div></label>
          <label>Ação ao clicar na logo<select v-model="local.logoActionType" @change="local.logoActionTarget = ''"><option value="none">Nenhuma ação</option><option value="top">Voltar ao topo</option><option value="section">Ir para uma seção</option><option value="page">Abrir outra página da conta</option><option value="external">Abrir link externo</option></select></label>
          <label v-if="local.logoActionType === 'section'">Seção de destino<select v-model="local.logoActionTarget"><option value="">Selecione</option><option v-for="option in sectionOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
          <label v-else-if="local.logoActionType === 'page'">Página de destino<select v-model="local.logoActionTarget"><option value="">Selecione</option><option v-for="page in pages" :key="page.id" :value="pageUrl(page)">{{ page.title }}</option></select></label>
          <label v-else-if="local.logoActionType === 'external'">Link da logo<input v-model="local.logoActionTarget" placeholder="https://exemplo.com" /></label>
          <label v-if="local.logoActionType === 'page' || local.logoActionType === 'external'" class="check"><input v-model="local.logoOpenInNewTab" type="checkbox" /> Abrir em nova aba</label>
          <p class="note">Quando este cabeçalho estiver ativo, a logo deixa de aparecer dentro do banner.</p>
        </div>
      </section>

      <section v-else-if="panel === 'links'" class="card">
        <header><h2>Links de navegação</h2><p>Adicione até 7 links para seções, páginas da conta ou endereços externos.</p></header>
        <div class="body">
          <button class="add" type="button" :disabled="local.links.length >= 7" @click="addLink">+ Adicionar link</button>
          <p class="counter">{{ local.links.length }}/7 links</p>
          <article v-for="(item,index) in local.links" :key="item.id" class="link-card" :class="{ expanded: expandedLinkIndex === index }">
            <div class="link-head" role="button" tabindex="0" @click="toggleLink(index)" @keydown.enter.prevent="toggleLink(index)"><span class="link-chevron">›</span><strong>{{ typeof item.label === 'string' && item.label.trim() ? item.label : `Link ${index + 1}` }}</strong><button type="button" @click.stop="removeLink(index)">Remover</button></div>
            <div v-if="expandedLinkIndex === index" class="link-fields">
              <div class="columns"><label>Texto<input v-model="item.label" maxlength="40" placeholder="Ex.: Roteiro" /></label><label>Destino<select v-model="item.targetType" @change="item.target = ''"><option value="section">Seção desta página</option><option value="page">Outra página da conta</option><option value="external">Link externo</option></select></label></div>
              <label v-if="item.targetType === 'section'">Seção<select v-model="item.target"><option value="">Selecione</option><option v-for="option in sectionOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
              <label v-else-if="item.targetType === 'page'">Página<select v-model="item.target"><option value="">Selecione</option><option v-for="page in pages" :key="page.id" :value="pageUrl(page)">{{ page.title }}</option></select></label>
              <label v-else>URL externa<input v-model="item.target" placeholder="https://exemplo.com" /></label>
              <label v-if="item.targetType !== 'section'" class="check"><input v-model="item.openInNewTab" type="checkbox" /> Abrir em nova aba</label>
            </div>
          </article>
        </div>
      </section>

      <section v-else class="card">
        <header><h2>Ações à direita</h2><p>Escolha redes sociais, um botão de contato ou nenhuma ação.</p></header>
        <div class="body">
          <label>Conteúdo da coluna direita<select v-model="local.actionType"><option value="none">Nenhum — usar duas colunas</option><option value="social">Redes sociais</option><option value="contact">Botão de contato</option></select></label>
          <template v-if="local.actionType === 'social'">
            <div class="agency-socials">
              <div class="agency-socials-copy"><strong>Redes sociais da agência</strong>
                <p v-if="agencySocialLinks.length">Serão exibidas automaticamente: {{ agencySocialLinks.map(link => socialName(link.network)).join(', ') }}.</p>
                <p v-else>Nenhuma rede social está cadastrada. Adicione os links nas configurações da agência para que apareçam no cabeçalho.</p>
              </div>
              <a href="/admin/agency" target="_blank" rel="noopener noreferrer">Configurar redes</a>
            </div>
          </template>
          <template v-else-if="local.actionType === 'contact'">
            <div class="columns"><label>Texto do botão<input v-model="local.contactLabel" placeholder="Entrar em contato" /></label><label>Tipo<select v-model="local.contactType"><option value="whatsapp">WhatsApp</option><option value="link">Link</option></select></label></div>
            <label>{{ local.contactType === 'whatsapp' ? 'Número com DDD e país' : 'URL do contato' }}<input v-model="local.contactValue" :placeholder="local.contactType === 'whatsapp' ? '5511999999999' : 'https://exemplo.com/contato'" /></label>
            <label v-if="local.contactType === 'whatsapp'">Mensagem inicial<textarea v-model="local.whatsappMessage" rows="3" placeholder="Olá! Gostaria de mais informações." /></label>
            <label>Cor do botão<ColorInput v-model="local.buttonColor" /></label>
          </template>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import type { HeaderLinkItem, HeaderSection, HeaderSocialLink, PageSection } from "../../types/page";
import { sectionLabels } from "../../utils/sectionLabels";
import { getReadableTextColor } from "../../utils/colorContrast";

interface AgencyPage { id:number; title:string; slug:string; status:string }
const props = defineProps<{ modelValue: HeaderSection; pageSections?: PageSection[] }>();
const emit = defineEmits<{ (e:"update:modelValue", value:HeaderSection):void }>();
const agencyStore = useAgencyStore();
const panel = ref<"style"|"links"|"actions">("style");
const expandedLinkIndex = ref<number|null>(null);
const tabs = [{id:"style" as const,icon:"▧",label:"Visual",desc:"Modo e cores"},{id:"links" as const,icon:"↗",label:"Links",desc:"Até 7 itens"},{id:"actions" as const,icon:"◎",label:"Ações",desc:"Contato e redes"}];
const socialDefaults:HeaderSocialLink[] = ["instagram","facebook","youtube","tiktok","linkedin"].map(platform => ({ platform:platform as HeaderSocialLink["platform"], url:"" }));
const cloneLinks = (items?:HeaderLinkItem[]) => (items || []).slice(0,7).map(item => ({...item}));
const cloneSocials = (items?:HeaderSocialLink[]) => socialDefaults.map(defaultItem => ({ ...defaultItem, ...(items || []).find(item => item.platform === defaultItem.platform) }));
const local = reactive<HeaderSection>({type:"header",enabled:true,mode:"solid",backgroundColor:"#ffffff",blurAmount:14,textColor:"#0f172a",linkTextColor:props.modelValue.textColor || "#0f172a",linkFontSize:14,linkHoverColor:"#22c55e",linkHoverAnimation:"underline",logoSize:56,logoActionType:"top",logoActionTarget:"",logoOpenInNewTab:false,stickyEnabled:true,actionType:"none",contactLabel:"Entrar em contato",contactType:"whatsapp",contactValue:"",whatsappMessage:"Olá! Gostaria de mais informações.",buttonColor:"#22c55e",...props.modelValue,links:cloneLinks(props.modelValue.links),socialLinks:cloneSocials(props.modelValue.socialLinks)});
const pages = ref<AgencyPage[]>([]);
const hasBanner = computed(() => (props.pageSections || []).some(section=>section.type==="hero"&&section.enabled!==false));
const agencySocialLinks = computed(() => (agencyStore.agencies.find(item=>item.id===agencyStore.currentAgencyId)?.social_links || []).filter(link=>link.url?.trim()));
let syncing = false;
const ColorInput = defineComponent({props:{modelValue:String},emits:["update:modelValue"],setup:(p,{emit})=>()=>h("div",{class:"color-input"},[h("input",{type:"color",value:p.modelValue,onInput:(e:Event)=>emit("update:modelValue",(e.target as HTMLInputElement).value)}),h("input",{value:p.modelValue,onInput:(e:Event)=>emit("update:modelValue",(e.target as HTMLInputElement).value)})])});
const sectionOptions = computed(() => (props.pageSections || []).filter(section => section.type !== "header" && section.anchorId).map((section,index) => ({value:section.anchorId!,label:`${sectionLabels[section.type] || "Seção"} ${index + 1}`})));
const makeId = () => `header-link-${Date.now()}-${Math.random().toString(36).slice(2,7)}`;
const addLink = () => { if(local.links.length<7){local.links.push({id:makeId(),label:"Novo link",targetType:"section",target:""});expandedLinkIndex.value=local.links.length-1;} };
const toggleLink = (index:number) => { expandedLinkIndex.value=expandedLinkIndex.value===index?null:index; };
const removeLink = (index:number) => {local.links.splice(index,1);if(expandedLinkIndex.value===index)expandedLinkIndex.value=null;else if(expandedLinkIndex.value!==null&&expandedLinkIndex.value>index)expandedLinkIndex.value-=1;};
const pageUrl = (page:AgencyPage) => { const agency=agencyStore.agencies.find(item=>item.id===agencyStore.currentAgencyId); return `/${agency?.slug || ""}/${page.slug}`; };
const socialName = (platform:string) => ({instagram:"Instagram",facebook:"Facebook",youtube:"YouTube",tiktok:"TikTok",linkedin:"LinkedIn"}[platform] || platform);
const loadPages = async () => { if(!agencyStore.currentAgencyId)await agencyStore.loadAgencies().catch(()=>undefined);if(!agencyStore.currentAgencyId)return;try{pages.value=(await api.get<AgencyPage[]>("/pages",{params:{agency_id:agencyStore.currentAgencyId}})).data.filter(page=>page.status==="published"||page.status==="draft");}catch{pages.value=[];} };
watch(()=>props.modelValue,value=>{syncing=true;Object.assign(local,value);local.links=cloneLinks(value.links);local.socialLinks=cloneSocials(value.socialLinks);queueMicrotask(()=>syncing=false);},{deep:true});
watch(local,value=>{if(!syncing)emit("update:modelValue",{...value,links:cloneLinks(value.links),socialLinks:cloneSocials(value.socialLinks)});},{deep:true});
watch(()=>local.mode,(mode,previous)=>{if((mode==="transparent"||mode==="blurred")&&previous==="solid"&&(local.linkTextColor||"").toLowerCase()==="#0f172a")local.linkTextColor="#ffffff";if(mode==="solid"&&(previous==="transparent"||previous==="blurred")&&(local.linkTextColor||"").toLowerCase()==="#ffffff")local.linkTextColor=getReadableTextColor(local.backgroundColor||"#ffffff");});
watch(hasBanner,available=>{if(!available&&local.mode!=="solid"){local.mode="solid";local.backgroundColor="#ffffff";local.textColor="#0f172a";local.linkTextColor="#0f172a";}},{immediate:true});
onMounted(loadPages);
</script>

<style scoped>
.header-editor{display:grid;grid-template-columns:178px minmax(0,1fr);min-height:520px;background:var(--background);color:var(--foreground)}.tabs{display:flex;flex-direction:column;gap:7px;padding:16px 12px;background:var(--card)}.tabs button{display:grid;grid-template-columns:28px 1fr;align-items:center;border:0;border-radius:13px;padding:9px;background:var(--muted);color:var(--foreground);text-align:left}.tabs button>span{grid-row:1/3;display:grid;width:26px;height:26px;place-items:center;border-radius:8px;background:var(--card)}.tabs b{font-size:13px}.tabs small{font-size:9px;opacity:.6}.tabs button.active{background:var(--primary);color:var(--primary-foreground)}.editor{min-width:0;padding:18px}.card{overflow:hidden;border:1px solid var(--border);border-radius:16px;background:var(--card)}.card>header{padding:17px 20px;border-bottom:1px solid var(--border)}.card h2{font-size:18px;font-weight:800}.card header p,.note,.counter{margin-top:4px;color:var(--muted-foreground);font-size:12px}.body{display:grid;gap:15px;padding:20px}.body label{display:grid;gap:7px;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:var(--muted-foreground)}.body input,.body select,.body textarea{width:100%;border:1px solid var(--input);border-radius:10px;background:var(--background);padding:10px 12px;color:var(--foreground);font-size:14px;text-transform:none;letter-spacing:normal}.columns{display:grid;grid-template-columns:1fr 1fr;gap:14px}.color-input{display:grid;grid-template-columns:48px 1fr;gap:8px}.color-input input[type=color]{height:42px;padding:4px}.range{display:flex;align-items:center;gap:12px}.range span{min-width:52px;font-size:13px}.add{justify-self:start;border-radius:10px;background:var(--primary);padding:10px 15px;color:var(--primary-foreground);font-size:12px;font-weight:800}.add:disabled{opacity:.45}.link-card{display:grid;gap:12px;border:1px solid var(--border);border-radius:14px;padding:14px;background:var(--background)}.link-head{display:flex;justify-content:space-between}.link-head button{border:0;background:none;color:#dc2626;font-size:12px;font-weight:800}.check{display:flex!important;align-items:center;text-transform:none!important;letter-spacing:normal!important}.check input{width:auto}@media(max-width:720px){.header-editor{grid-template-columns:1fr}.tabs{flex-direction:row;overflow:auto}.tabs button{min-width:145px}.editor{padding:12px}.columns{grid-template-columns:1fr}}
.agency-socials{display:flex;align-items:center;justify-content:space-between;gap:16px;border:1px solid var(--border);border-radius:12px;padding:14px;background:var(--background)}.agency-socials-copy{min-width:0}.agency-socials strong{font-size:13px}.agency-socials p{margin-top:5px;color:var(--muted-foreground);font-size:12px;line-height:1.5}.agency-socials>a{flex:0 0 auto;border-radius:999px;background:var(--primary);padding:9px 14px;color:var(--primary-foreground);text-decoration:none;font-size:11px;font-weight:800;white-space:nowrap}.agency-socials>a:hover{filter:brightness(.96)}
.sticky-option{padding:12px;border:1px solid var(--border);border-radius:12px;background:var(--background)}.sticky-option span{display:flex;flex-direction:column;gap:2px}.sticky-option strong{color:var(--foreground);font-size:13px}.sticky-option small{font-weight:500;color:var(--muted-foreground);font-size:11px}
.mode-row{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;gap:14px}.sticky-toggle{display:flex!important;height:42px;align-items:center;gap:8px;padding:0 4px;text-transform:none!important;letter-spacing:normal!important;cursor:pointer}.sticky-toggle input{position:absolute;width:1px!important;height:1px;opacity:0}.sticky-toggle>span{position:relative;width:38px;height:22px;flex:0 0 auto;border-radius:99px;background:#cbd5e1;transition:background .2s}.sticky-toggle>span::after{position:absolute;left:3px;top:3px;width:16px;height:16px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(15,23,42,.25);content:"";transition:transform .2s}.sticky-toggle input:checked+span{background:var(--primary)}.sticky-toggle input:checked+span::after{transform:translateX(16px)}.sticky-toggle b{font-size:12px;color:var(--foreground);white-space:nowrap}.link-card{padding:0;gap:0;overflow:hidden}.link-head{min-height:52px;align-items:center;gap:9px;padding:10px 14px;cursor:pointer}.link-head strong{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.link-chevron{font-size:24px;color:var(--muted-foreground);transition:transform .18s}.link-card.expanded .link-chevron{transform:rotate(90deg);color:var(--primary)}.link-fields{display:grid;gap:12px;padding:14px;border-top:1px solid var(--border)}
.mode-warning{margin:-8px 0 0;border-radius:9px;background:#fff7ed;padding:9px 11px;color:#9a3412;font-size:11px}
@media(max-width:600px){.agency-socials{align-items:flex-start;flex-direction:column}.agency-socials>a{width:100%;text-align:center}.mode-row{grid-template-columns:1fr}.sticky-toggle{height:auto;justify-self:start}}
</style>
