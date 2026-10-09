<template>
  <div class="hc">
    <header class="hc-head">
      <p class="hc-eyebrow">Aprender</p>
      <h1 class="hc-title">Central de Ajuda</h1>
      <p class="hc-sub">Guias passo a passo com demonstrações interativas de cada parte do Roteiro Online.</p>
      <label class="hc-search">
        <SearchIcon aria-hidden="true" />
        <input
          ref="searchRef"
          v-model="consulta"
          type="search"
          placeholder="Buscar: publicar página, formulário, pixel, domínio…"
          aria-label="Buscar na Central de Ajuda"
          @keydown.esc="consulta = ''"
        />
        <button v-if="consulta" type="button" aria-label="Limpar busca" @click="consulta = ''"><XIcon aria-hidden="true" /></button>
      </label>
    </header>

    <section v-if="consulta.trim()" class="hc-results" aria-live="polite">
      <p class="hc-results-count">
        {{ resultados.length ? `${resultados.length} ${resultados.length === 1 ? "artigo encontrado" : "artigos encontrados"}` : "Nada encontrado." }}
      </p>
      <p v-if="!resultados.length" class="hc-empty">Tente outras palavras, como “publicar”, “leads” ou “WhatsApp”.</p>
      <div class="hc-list">
        <HelpArticleCard v-for="article in resultados" :key="article.id" :article="article" show-module />
      </div>
    </section>

    <template v-else>
      <section class="hc-card hc-start">
        <div class="hc-start-head">
          <div>
            <p class="hc-eyebrow">Comece por aqui</p>
            <h2>Sua primeira página no ar em {{ FIRST_STEPS.length }} passos</h2>
          </div>
          <span class="hc-progress">{{ feitos.length }} de {{ FIRST_STEPS.length }}</span>
        </div>
        <ol class="hc-steps">
          <li v-for="(id, i) in FIRST_STEPS" :key="id">
            <RouterLink :to="`/admin/ajuda/${id}`" class="hc-step" :class="{ done: feitos.includes(id) }">
              <span class="hc-step-num">
                <CheckIcon v-if="feitos.includes(id)" aria-hidden="true" />
                <template v-else>{{ i + 1 }}</template>
              </span>
              <span class="hc-step-text">
                <b>{{ getArticle(id)?.titulo }}</b>
                <small>{{ getArticle(id)?.resumo }}</small>
              </span>
            </RouterLink>
          </li>
        </ol>
      </section>

      <section v-for="module in modulos" :key="module.id" class="hc-module" :id="`modulo-${module.id}`">
        <header class="hc-module-head">
          <span class="hc-module-icon" aria-hidden="true"><component :is="module.icone" /></span>
          <div>
            <h2>{{ module.titulo }}</h2>
            <p>{{ module.descricao }}</p>
          </div>
        </header>
        <div class="hc-list">
          <HelpArticleCard v-for="article in articlesOf(module.id)" :key="article.id" :article="article" />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { CheckIcon, SearchIcon, XIcon } from "lucide-vue-next";
import HelpArticleCard from "../../components/help/HelpArticleCard.vue";
import { FIRST_STEPS, HELP_MODULES, articlesOf, getArticle, searchArticles } from "../../help";
import { readHelpProgress } from "../../help/progress";

const route = useRoute();
const router = useRouter();
const consulta = ref(typeof route.query.q === "string" ? route.query.q : "");
const searchRef = ref<HTMLInputElement | null>(null);
const resultados = computed(() => searchArticles(consulta.value));
const modulos = computed(() => HELP_MODULES.filter(module => articlesOf(module.id).length));
const feitos = ref<string[]>([]);

watch(consulta, valor => {
  router.replace({ query: valor.trim() ? { q: valor } : {} }).catch(() => undefined);
});

onMounted(() => {
  feitos.value = readHelpProgress().filter(id => FIRST_STEPS.includes(id));
  if (consulta.value) searchRef.value?.focus();
});
</script>

<style scoped>
.hc { display: flex; flex-direction: column; gap: 20px; padding-bottom: 40px; color: var(--foreground); }
.hc-head { display: flex; flex-direction: column; gap: 4px; }
.hc-eyebrow { font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: color-mix(in srgb, var(--muted-foreground) 80%, transparent); }
.hc-title { margin-top: 4px; font-family: var(--font-display); font-size: 30px; line-height: 38px; font-weight: 600; }
.hc-sub { font-size: 14px; color: var(--muted-foreground); }
.hc-search { display: flex; align-items: center; gap: 10px; max-width: 640px; height: 52px; margin-top: 14px; padding: 0 8px 0 18px; border-radius: 999px; background: var(--card); box-shadow: var(--shadow-card); }
.hc-search:focus-within { box-shadow: var(--shadow-card), 0 0 0 2px var(--ring); }
.hc-search > svg { width: 18px; height: 18px; flex: none; color: var(--muted-foreground); }
.hc-search input { flex: 1; min-width: 0; height: 100%; border: 0; background: transparent; font-size: 15px; color: var(--foreground); outline: none; }
.hc-search input::-webkit-search-cancel-button { display: none; }
.hc-search button { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 999px; color: var(--muted-foreground); }
.hc-search button:hover { background: var(--muted); }
.hc-search button svg { width: 16px; height: 16px; }

.hc-results-count { font-size: 13px; font-weight: 600; color: var(--muted-foreground); }
.hc-empty { margin-top: 4px; font-size: 14px; color: var(--muted-foreground); }
.hc-results .hc-list { margin-top: 12px; }

.hc-card { border-radius: 20px; background: var(--card); box-shadow: var(--shadow-card); }
.hc-start { padding: 20px; }
.hc-start-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.hc-start-head h2 { margin-top: 4px; font-family: var(--font-display); font-size: 20px; font-weight: 600; }
.hc-progress { flex: none; padding: 4px 10px; border-radius: 999px; background: var(--muted); font-size: 12.5px; font-weight: 700; color: var(--muted-foreground); }
.hc-steps { display: grid; grid-template-columns: minmax(0, 1fr); gap: 10px; margin: 0; padding: 0; list-style: none; }
@media (min-width: 640px) { .hc-steps { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (min-width: 1100px) { .hc-steps { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
.hc-step { display: flex; height: 100%; gap: 12px; padding: 14px; border-radius: 16px; background: var(--muted); text-decoration: none; color: inherit; transition: background-color 0.2s ease, transform 0.2s ease; }
.hc-step:hover { background: color-mix(in srgb, var(--primary) 8%, var(--muted)); transform: translateY(-1px); }
.hc-step-num { display: grid; flex: none; place-items: center; width: 30px; height: 30px; border-radius: 999px; background: var(--card); font-size: 13px; font-weight: 700; color: var(--primary); }
.hc-step.done .hc-step-num { background: var(--primary); color: var(--primary-foreground); }
.hc-step-num svg { width: 16px; height: 16px; }
.hc-step-text { display: flex; min-width: 0; flex-direction: column; gap: 3px; }
.hc-step-text b { font-size: 14px; font-weight: 700; }
.hc-step-text small { font-size: 12.5px; line-height: 1.45; color: var(--muted-foreground); }

.hc-module { display: flex; flex-direction: column; gap: 12px; scroll-margin-top: 16px; }
.hc-module-head { display: flex; align-items: center; gap: 12px; }
.hc-module-icon { display: grid; flex: none; place-items: center; width: 40px; height: 40px; border-radius: 12px; background: color-mix(in srgb, var(--primary) 12%, var(--card)); color: var(--primary); }
.hc-module-icon svg { width: 19px; height: 19px; }
.hc-module-head h2 { font-family: var(--font-display); font-size: 18px; font-weight: 600; }
.hc-module-head p { font-size: 13.5px; color: var(--muted-foreground); }
.hc-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr)); gap: 12px; }
</style>
