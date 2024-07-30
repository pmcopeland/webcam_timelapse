// This file is the entry point of the Vue application.
// It initializes the Vue instance and mounts the root component (App.vue) to the DOM.

import Vue from 'vue';
import App from './App.vue';

Vue.config.productionTip = false;

new Vue({
  render: (h) => h(App),
}).$mount('#app');