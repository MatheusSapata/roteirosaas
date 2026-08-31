<template>
  <div class="section-editor">
    <aside class="tabs">
      <button v-for="tab in tabs" :key="tab.id" type="button" class="tab" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id">
        <span class="tab-icon" v-html="tab.icon"></span><span>{{ tab.label }}<small>{{ tab.desc }}</small></span>
      </button>
    </aside>
    <main class="editor">
      <section v-if="activeTab === 'content'" class="card">
        <Header title="Conteúdo e formulário" desc="Defina a chamada e monte os campos exibidos na página." />
        <div class="body">
          <SectionHeadingControls :label="typeof local.headingLabel === 'string' ? local.headingLabel : ''" :style="local.headingLabelStyle" @update:label="local.headingLabel = $event" @update:style="local.headingLabelStyle = $event" />
          <Field label="Título"><input v-model="local.title" placeholder="Fale com um especialista" /></Field>
          <Field label="Subtítulo"><RichTextEditor v-model="subtitleEditor" placeholder="Apresente os benefícios e explique por que o visitante deve entrar em contato." /></Field>
          <Field label="Formulário"><select v-model="local.formId"><option value="">Selecione um formulário</option><option v-for="form in forms" :key="form.id" :value="String(form.id)">{{ form.name || form.title }}</option></select><p class="hint">Os envios criam oportunidades e usam as notificações deste formulário.</p></Field>
          <div class="actions"><button type="button" class="primary" @click="openBuilder(null)">Criar formulário</button><button v-if="selectedForm" type="button" @click="openBuilder(selectedForm)">Editar campos e notificações</button></div>
          <p v-if="loading" class="hint">Carregando formulários...</p><p v-else-if="!forms.length" class="error">Crie um formulário antes de publicar esta seção.</p>
        </div>
      </section>
      <section v-if="activeTab === 'appearance'" class="card">
        <Header title="Aparência" desc="Escolha o fundo, as cores e a posição do formulário." />
        <div class="body">
          <Field label="Tipo de fundo"><div class="options"><button v-for="option in backgroundOptions" :key="option.value" type="button" :class="{ active: local.backgroundType === option.value }" @click="local.backgroundType = option.value">{{ option.label }}<small>{{ option.desc }}</small></button></div></Field>
          <Field v-if="local.backgroundType === 'solid'" label="Cor do fundo"><ColorInput v-model="local.backgroundColor" /></Field>
          <template v-else-if="local.backgroundType === 'gradient'"><div class="columns"><Field label="Cor inicial"><ColorInput v-model="local.gradientStart" /></Field><Field label="Cor final"><ColorInput v-model="local.gradientEnd" /></Field></div><Field label="Direção"><select v-model="local.gradientDirection"><option value="to right">Horizontal</option><option value="to bottom">Vertical</option><option value="to bottom right">Diagonal</option></select></Field></template>
          <template v-else><Field label="Imagem de fundo"><input type="file" accept="image/*" @change="uploadBackground" /><img v-if="imagePreview" :src="imagePreview" class="preview" alt="Prévia do fundo" /><p v-if="uploading" class="hint">Enviando imagem...</p><p v-if="uploadError" class="error">{{ uploadError }}</p></Field><Field :label="`Escurecimento — ${Math.round((local.overlayOpacity || 0) * 100)}%`"><input v-model.number="local.overlayOpacity" type="range" min="0" max="0.8" step="0.05" /></Field></template>
          <div class="columns"><Field label="Alinhamento no computador"><select v-model="local.alignment"><option value="left">Esquerda</option><option value="center">Centro</option><option value="right">Direita</option></select></Field><Field label="Cor do texto"><ColorInput v-model="local.textColor" /></Field></div>
        </div>
      </section>
      <section v-if="activeTab === 'confirmation'" class="card">
        <Header title="Confirmação" desc="Configure o modal mostrado depois do envio." />
        <div class="body"><Field label="Mensagem de confirmação"><textarea v-model="local.successMessage" rows="4" /></Field><Field label="Duração do modal"><div class="duration"><input v-model.number="local.successDurationSeconds" type="number" min="1" max="30" /><span>segundos</span></div><p class="hint">O visitante também pode fechar o modal antes.</p></Field></div>
      </section>
    </main>
    <LeadFormBuilderModal v-model="builderOpen" :form="builderForm" :saving="saving" @save="saveForm" />
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref, watch } from "vue";
import { useLeadCaptureStore } from "../../store/useLeadCaptureStore"; import { useAgencyStore } from "../../store/useAgencyStore";
import type { InternalFormSection } from "../../types/page"; import type { LeadForm, LeadFormPayload } from "../../types/leads";
import { resolveMediaUrl, uploadImageFile } from "../../utils/media"; import { adminTabIcons } from "../../utils/adminTabIcons"; import LeadFormBuilderModal from "./leads/LeadFormBuilderModal.vue"; import SectionHeadingControls from "./inputs/SectionHeadingControls.vue"; import RichTextEditor from "./inputs/RichTextEditor.vue";
type TabId = "content" | "appearance" | "confirmation";
const Header = defineComponent({ props: { title: String, desc: String }, setup: p => () => h("header", [h("h2", p.title), h("p", p.desc)]) });
const Field = defineComponent({ props: { label: String }, setup: (p,{slots}) => () => h("label", { class:"field" }, [h("strong",p.label), slots.default?.()]) });
const ColorInput = defineComponent({ props:{ modelValue:String }, emits:["update:modelValue"], setup:(p,{emit}) => () => h("div",{class:"color"},[h("input",{type:"color",value:p.modelValue,onInput:(e:Event)=>emit("update:modelValue",(e.target as HTMLInputElement).value)}),h("input",{value:p.modelValue,class:"mono",onInput:(e:Event)=>emit("update:modelValue",(e.target as HTMLInputElement).value)})]) });
const props=defineProps<{modelValue:InternalFormSection}>(); const emit=defineEmits<{(e:"update:modelValue",value:InternalFormSection):void}>(); const store=useLeadCaptureStore(); const agencyStore=useAgencyStore();
const activeTab=ref<TabId>("content"); const tabs=[{id:"content" as const,icon:adminTabIcons.text,label:"Conteúdo",desc:"Textos e campos"},{id:"appearance" as const,icon:adminTabIcons.media,label:"Aparência",desc:"Fundo e posição"},{id:"confirmation" as const,icon:adminTabIcons.button,label:"Confirmação",desc:"Modal de sucesso"}];
const backgroundOptions:Array<{value:InternalFormSection["backgroundType"];label:string;desc:string}>=[{value:"solid",label:"Cor sólida",desc:"Uma única cor"},{value:"gradient",label:"Gradiente",desc:"Duas cores"},{value:"image",label:"Imagem",desc:"Foto de fundo"}];
const local=reactive<InternalFormSection>({type:"internal_form",enabled:true,headingLabel:"Fale conosco",headingLabelStyle:"outline",title:"Fale com um especialista",subtitle:"Preencha seus dados e entraremos em contato.",formId:"",backgroundType:"solid",backgroundColor:"#f8fafc",gradientStart:"#0f172a",gradientEnd:"#2563eb",gradientDirection:"to bottom right",overlayOpacity:.35,alignment:"center",textColor:"#0f172a",successMessage:"Obrigado! Recebemos suas informações com sucesso.",successDurationSeconds:5,...props.modelValue});
const forms=computed(()=>store.forms),loading=computed(()=>store.formsLoading),selectedForm=computed(()=>forms.value.find(f=>String(f.id)===String(local.formId))||null),uploading=ref(false),uploadError=ref(""),builderOpen=ref(false),builderForm=ref<LeadForm|null>(null),saving=ref(false),imagePreview=computed(()=>resolveMediaUrl(local.backgroundImage));
const subtitleEditor=computed({get:()=>typeof local.subtitle==="string"?local.subtitle:"",set:value=>{local.subtitle=value}});
const openBuilder=(form:LeadForm|null)=>{builderForm.value=form;builderOpen.value=true}; const saveForm=async({id,form}:{id:string|null;form:LeadFormPayload})=>{saving.value=true;try{const saved=id?await store.updateForm(id,form):await store.createForm(form);local.formId=String(saved.id);builderOpen.value=false}finally{saving.value=false}};
const uploadBackground=async(event:Event)=>{const input=event.target as HTMLInputElement,file=input.files?.[0];if(!file)return;uploading.value=true;uploadError.value="";try{if(!agencyStore.currentAgencyId)await agencyStore.loadAgencies();const id=agencyStore.currentAgencyId||agencyStore.agencies[0]?.id;if(!id)throw new Error();local.backgroundImage=(await uploadImageFile(file,id)).url}catch{uploadError.value="Não foi possível enviar a imagem."}finally{uploading.value=false;input.value=""}};
onMounted(()=>store.fetchForms().catch(()=>undefined));watch(()=>props.modelValue,v=>Object.assign(local,v),{deep:true});watch(local,v=>emit("update:modelValue",{...v}),{deep:true});
</script>

<style scoped>
.section-editor{display:grid;grid-template-columns:220px minmax(0,1fr);min-height:520px;background:#f8fafc;color:#0f172a}.tabs{padding:18px 12px;border-right:1px solid #e2e8f0;background:#fff}.tab{position:relative;display:flex;width:100%;align-items:center;gap:11px;border-radius:12px;padding:11px;text-align:left;color:#64748b}.tab:hover{background:#f1f5f9}.tab.active{background:#ecfdf3;color:#15803d;box-shadow:inset 3px 0 #22c55e}.tab-icon{display:grid;width:23px;place-items:center}.tab-icon :deep(svg){width:20px;height:20px}.tab small,.options small{display:block;margin-top:2px;font-size:10px;color:#94a3b8}.status{position:absolute;right:9px;top:9px;display:grid;width:17px;height:17px;place-items:center;border-radius:50%;background:#dcfce7;color:#16a34a;font-size:10px}.editor{padding:20px}.card{overflow:hidden;border:1px solid #e2e8f0;border-radius:16px;background:#fff}.card header{padding:17px 20px;border-bottom:1px solid #e2e8f0}.card header h2{font-size:17px;font-weight:800}.card header p,.hint{margin-top:3px;font-size:11px;color:#64748b}.body{display:grid;gap:16px;padding:20px}.field{display:grid;gap:7px}.field strong{font-size:12px;text-transform:uppercase;color:#475569}.field input,.field textarea,.field select{width:100%;border:1px solid #cbd5e1;border-radius:10px;background:#fff;padding:10px 12px}.actions{display:flex;gap:8px;flex-wrap:wrap}.actions button{border:1px solid #cbd5e1;border-radius:10px;padding:9px 13px;font-size:12px;font-weight:700}.actions .primary{border-color:#16a34a;background:#16a34a;color:white}.error{font-size:12px;color:#be123c}.options{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.options button{border:1px solid #cbd5e1;border-radius:12px;padding:12px;text-align:left;font-size:13px;font-weight:800}.options button.active{border-color:#22c55e;background:#f0fdf4;color:#15803d}.columns{display:grid;grid-template-columns:1fr 1fr;gap:14px}.color{display:grid;grid-template-columns:48px 1fr;gap:8px}.color input[type=color]{height:42px;padding:4px}.mono{font-family:monospace}.preview{max-height:180px;width:100%;border-radius:12px;object-fit:cover}.duration{display:flex;align-items:center;gap:10px}.duration input{max-width:110px}.duration span{font-size:13px;color:#64748b}@media(max-width:720px){.section-editor{grid-template-columns:1fr}.tabs{display:flex;overflow-x:auto;border-right:0;border-bottom:1px solid #e2e8f0}.tab{min-width:150px}.editor{padding:12px}.columns,.options{grid-template-columns:1fr}}
.section-editor{--tab-icon-size:22px;grid-template-columns:178px minmax(0,1fr);background:#f8faf9}.tabs{padding:16px 12px;border-right:0;background:#fff}.tab{position:static;gap:10px;margin-bottom:6px;border:0;border-radius:14px;background:#eef3ef;padding:7px 9px;color:#172132;font-weight:700}.tab:hover{background:#e5ece7}.tab.active{background:#35d467;color:#073417;box-shadow:none}.tab-icon{display:grid;width:var(--tab-icon-size);height:var(--tab-icon-size);flex:0 0 auto;place-items:center;border-radius:8px;background:rgba(255,255,255,.62);font-size:12px}.tab-icon :deep(svg){width:1em;height:1em}.tab small{margin-top:-1px;color:inherit;opacity:.58;font-size:9px}.status{display:none}
</style>
