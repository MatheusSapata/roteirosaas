import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./styles/main.css";
import { reloadForNewBuild } from "./utils/staleBuild";

// O Vite avisa quando um arquivo de uma tela não carrega (deploy novo com a aba aberta).
window.addEventListener("vite:preloadError", event => {
  if (reloadForNewBuild()) event.preventDefault();
});

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
