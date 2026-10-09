<template>
  <div v-if="article" class="ha">
    <nav class="ha-crumbs" aria-label="Você está em">
      <RouterLink to="/admin/ajuda">Central de Ajuda</RouterLink>
      <ChevronRightIcon aria-hidden="true" />
      <RouterLink :to="`/admin/ajuda#modulo-${article.modulo}`">{{ modulo.titulo }}</RouterLink>
    </nav>

    <div class="ha-grid">
      <article class="ha-main">
        <header class="ha-head">
          <h1>{{ article.titulo }}</h1>
          <p class="ha-lead">{{ article.resumo }}</p>
          <div class="ha-meta">
            <span>Atualizado em {{ formatDate(article.atualizado) }}</span>
            <RouterLink v-if="article.rota" :to="article.rota" class="ha-go">
              {{ article.rotaRotulo || "Abrir esta tela" }}
              <ArrowUpRightIcon aria-hidden="true" />
            </RouterLink>
          </div>
        </header>

        <HelpDemo v-if="tour" :tour-id="tour.id" :inicio="inicioDemo" />

        <section v-if="article.passos?.length" class="ha-card">
          <h2>Passo a passo</h2>
          <ol class="ha-steps">
            <li v-for="(passo, i) in article.passos" :key="i">
              <span class="ha-num">{{ i + 1 }}</span>
              <div class="ha-step-body">
                <b>{{ passo.titulo }}</b>
                <p v-if="passo.texto" v-html="rich(passo.texto)"></p>
                <button v-if="tour && passo.tela" type="button" class="ha-see" @click="verNaDemo(passo.tela)">
                  <MousePointerClickIcon aria-hidden="true" />
                  Ver na demonstração
                </button>
              </div>
            </li>
          </ol>
        </section>

        <template v-for="(bloco, i) in article.blocos || []" :key="`b${i}`">
          <p v-if="bloco.tipo === 'texto'" class="ha-text" v-html="rich(bloco.texto)"></p>
          <div v-else-if="bloco.tipo === 'dica'" class="ha-note is-tip">
            <LightbulbIcon aria-hidden="true" />
            <p v-html="rich(bloco.texto)"></p>
          </div>
          <div v-else-if="bloco.tipo === 'atencao'" class="ha-note is-warn">
            <TriangleAlertIcon aria-hidden="true" />
            <p v-html="rich(bloco.texto)"></p>
          </div>
          <section v-else-if="bloco.tipo === 'lista'" class="ha-card">
            <h2 v-if="bloco.titulo">{{ bloco.titulo }}</h2>
            <ul class="ha-list">
              <li v-for="(item, j) in bloco.itens" :key="j" v-html="rich(item)"></li>
            </ul>
          </section>
          <section v-else-if="bloco.tipo === 'tabela'" class="ha-card">
            <h2 v-if="bloco.titulo">{{ bloco.titulo }}</h2>
            <div class="ha-table-wrap">
              <table class="ha-table">
                <thead>
                  <tr><th v-for="coluna in bloco.colunas" :key="coluna">{{ coluna }}</th></tr>
                </thead>
                <tbody>
                  <tr v-for="(linha, j) in bloco.linhas" :key="j">
                    <td v-for="(celula, k) in linha" :key="k" v-html="rich(celula)"></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </template>

        <section v-if="article.duvidas?.length" class="ha-card">
          <h2>Dúvidas comuns</h2>
          <div class="ha-faq">
            <details v-for="([pergunta, resposta], i) in article.duvidas" :key="i">
              <summary>{{ pergunta }}<ChevronDownIcon aria-hidden="true" /></summary>
              <p v-html="rich(resposta)"></p>
            </details>
          </div>
        </section>

        <div v-if="primeiroPasso" class="ha-done">
          <button type="button" :class="feito ? 'is-on' : ''" @click="alternarFeito">
            <CheckIcon aria-hidden="true" />
            {{ feito ? "Feito" : "Marcar como feito" }}
          </button>
          <RouterLink v-if="proximoPasso" :to="`/admin/ajuda/${proximoPasso.id}`" class="ha-next">
            Próximo: {{ proximoPasso.titulo }}
            <ArrowRightIcon aria-hidden="true" />
          </RouterLink>
        </div>

        <section v-if="relacionados.length" class="ha-related">
          <h2>Veja também</h2>
          <div class="ha-related-list">
            <HelpArticleCard v-for="item in relacionados" :key="item.id" :article="item" />
          </div>
        </section>
      </article>

      <aside class="ha-side">
        <div class="ha-card ha-side-card">
          <p class="ha-side-title">{{ modulo.titulo }}</p>
          <RouterLink
            v-for="item in articlesOf(article.modulo)"
            :key="item.id"
            :to="`/admin/ajuda/${item.id}`"
            class="ha-side-link"
            :class="{ on: item.id === article.id }"
          >
            {{ item.titulo }}
          </RouterLink>
        </div>
      </aside>
    </div>
  </div>
  <div v-else class="ha-missing">
    <p>Não encontramos este artigo.</p>
    <RouterLink to="/admin/ajuda">Voltar para a Central de Ajuda</RouterLink>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  ArrowRightIcon,
  ArrowUpRightIcon,
  CheckIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  LightbulbIcon,
  MousePointerClickIcon,
  TriangleAlertIcon
} from "lucide-vue-next";
import HelpDemo from "../../components/help/HelpDemo.vue";
import HelpArticleCard from "../../components/help/HelpArticleCard.vue";
import { FIRST_STEPS, articlesOf, formatDate, getArticle, getModule } from "../../help";
import { getTour } from "../../help/media";
import { readHelpProgress, setHelpProgress } from "../../help/progress";

const props = defineProps<{ id: string }>();

const article = computed(() => getArticle(props.id));
const modulo = computed(() => getModule(article.value!.modulo));
const tour = computed(() => getTour(article.value?.demo || article.value?.id));
const relacionados = computed(() => (article.value?.relacionados || []).map(id => getArticle(id)).filter(Boolean) as NonNullable<ReturnType<typeof getArticle>>[]);
const inicioDemo = ref(0);
const verNaDemo = (tela: number) => {
  inicioDemo.value = -1;
  requestAnimationFrame(() => (inicioDemo.value = tela - 1));
};

const primeiroPasso = computed(() => FIRST_STEPS.includes(props.id));
const proximoPasso = computed(() => {
  const i = FIRST_STEPS.indexOf(props.id);
  return i >= 0 && i < FIRST_STEPS.length - 1 ? getArticle(FIRST_STEPS[i + 1]) : null;
});
const feito = ref(false);
const alternarFeito = () => {
  feito.value = setHelpProgress(props.id, !feito.value).includes(props.id);
};

watch(
  () => props.id,
  () => {
    inicioDemo.value = 0;
    feito.value = readHelpProgress().includes(props.id);
    if (typeof window !== "undefined") window.scrollTo({ top: 0 });
  },
  { immediate: true }
);

/** Texto do artigo com **negrito** (o conteúdo é nosso, mas escapamos o HTML mesmo assim). */
const rich = (texto: string) =>
  texto
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
</script>

<style scoped>
.ha { display: flex; flex-direction: column; gap: 16px; padding-bottom: 40px; color: var(--foreground); }
.ha-crumbs { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: 13px; color: var(--muted-foreground); }
.ha-crumbs a { color: inherit; text-decoration: none; }
.ha-crumbs a:hover { color: var(--foreground); text-decoration: underline; }
.ha-crumbs svg { width: 14px; height: 14px; }
.ha-grid { display: grid; grid-template-columns: minmax(0, 1fr) 280px; align-items: start; gap: 20px; }
.ha-main { display: flex; min-width: 0; flex-direction: column; gap: 16px; }
.ha-head h1 { font-family: var(--font-display); font-size: 30px; line-height: 1.2; font-weight: 600; }
.ha-lead { margin-top: 8px; max-width: 760px; font-size: 16px; line-height: 1.55; color: var(--muted-foreground); }
.ha-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-top: 12px; font-size: 13px; color: var(--muted-foreground); }
.ha-go { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border-radius: 999px; background: var(--primary); color: var(--primary-foreground); font-weight: 700; text-decoration: none; }
.ha-go svg { width: 15px; height: 15px; }

.ha-card { padding: 20px; border-radius: 20px; background: var(--card); box-shadow: var(--shadow-card); }
.ha-card h2, .ha-related h2 { margin-bottom: 12px; font-family: var(--font-display); font-size: 18px; font-weight: 600; }
.ha-steps { display: flex; flex-direction: column; gap: 14px; margin: 0; padding: 0; list-style: none; }
.ha-steps li { display: flex; gap: 12px; }
.ha-num { display: grid; flex: none; place-items: center; width: 28px; height: 28px; border-radius: 999px; background: color-mix(in srgb, var(--primary) 12%, var(--card)); font-size: 13px; font-weight: 700; color: var(--primary); }
.ha-step-body { display: flex; min-width: 0; flex-direction: column; gap: 3px; padding-top: 3px; }
.ha-step-body b { font-size: 15px; }
.ha-step-body p, .ha-text, .ha-list li, .ha-faq p { font-size: 14.5px; line-height: 1.6; color: var(--muted-foreground); }
.ha-step-body :deep(b), .ha-text :deep(b), .ha-list :deep(b), .ha-faq :deep(b), .ha-note :deep(b), .ha-table :deep(b) { color: var(--foreground); }
.ha-see { display: inline-flex; align-self: flex-start; align-items: center; gap: 6px; margin-top: 4px; font-size: 13px; font-weight: 700; color: var(--primary); }
.ha-see svg { width: 14px; height: 14px; }
.ha-text { max-width: 820px; }

.ha-note { display: flex; gap: 12px; padding: 14px 16px; border-radius: 16px; font-size: 14.5px; line-height: 1.55; }
.ha-note svg { width: 18px; height: 18px; flex: none; margin-top: 2px; }
.ha-note.is-tip { background: color-mix(in srgb, var(--primary) 10%, var(--card)); color: var(--foreground); }
.ha-note.is-tip svg { color: var(--primary); }
.ha-note.is-warn { background: color-mix(in srgb, #f59e0b 14%, var(--card)); color: var(--foreground); }
.ha-note.is-warn svg { color: #b45309; }

.ha-list { display: flex; flex-direction: column; gap: 8px; margin: 0; padding-left: 20px; }
.ha-table-wrap { overflow-x: auto; }
.ha-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.ha-table th { padding: 8px 10px; border-bottom: 1px solid var(--border); text-align: left; font-size: 12px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase; color: var(--muted-foreground); }
.ha-table td { padding: 10px; border-bottom: 1px solid var(--border); vertical-align: top; line-height: 1.5; color: var(--muted-foreground); }
.ha-table td:first-child { font-weight: 700; color: var(--foreground); white-space: nowrap; }
.ha-table tr:last-child td { border-bottom: 0; }

.ha-faq { display: flex; flex-direction: column; gap: 8px; }
.ha-faq details { border-radius: 14px; background: var(--muted); }
.ha-faq summary { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; font-size: 14.5px; font-weight: 700; cursor: pointer; list-style: none; }
.ha-faq summary::-webkit-details-marker { display: none; }
.ha-faq summary svg { width: 16px; height: 16px; flex: none; transition: transform 0.2s ease; }
.ha-faq details[open] summary svg { transform: rotate(180deg); }
.ha-faq p { padding: 0 14px 14px; }

.ha-done { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px; border-radius: 20px; background: var(--card); box-shadow: var(--shadow-card); }
.ha-done button { display: inline-flex; align-items: center; gap: 8px; height: 40px; padding: 0 16px; border-radius: 999px; background: var(--muted); font-size: 14px; font-weight: 700; color: var(--foreground); }
.ha-done button.is-on { background: var(--primary); color: var(--primary-foreground); }
.ha-done button svg { width: 16px; height: 16px; }
.ha-next { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 700; color: var(--primary); text-decoration: none; }
.ha-next svg { width: 16px; height: 16px; }

.ha-related-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr)); gap: 12px; }

.ha-side { position: sticky; top: 16px; }
.ha-side-card { display: flex; flex-direction: column; gap: 2px; padding: 14px; }
.ha-side-title { padding: 4px 10px 8px; font-size: 12px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted-foreground); }
.ha-side-link { padding: 8px 10px; border-radius: 10px; font-size: 13.5px; color: var(--foreground); text-decoration: none; }
.ha-side-link:hover { background: var(--muted); }
.ha-side-link.on { background: color-mix(in srgb, var(--primary) 12%, var(--card)); color: var(--primary); font-weight: 700; }

.ha-missing { display: flex; flex-direction: column; gap: 8px; padding: 40px 0; }
.ha-missing a { font-weight: 700; color: var(--primary); }

@media (max-width: 1100px) {
  .ha-grid { grid-template-columns: minmax(0, 1fr); }
  .ha-side { position: static; }
}
</style>
