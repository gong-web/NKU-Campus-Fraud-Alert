import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import zhCn from "element-plus/es/locale/lang/zh-cn";
import "element-plus/dist/index.css";
import App from "./App.vue";
import router from "./router";
import "./styles/global.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- element-plus 类型偶尔与 locale 不一致
app.use(ElementPlus as any, { locale: zhCn });
app.mount("#app");
