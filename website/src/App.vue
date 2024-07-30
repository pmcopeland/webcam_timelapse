<!-- /vue-s3-image-viewer/src/App.vue -->

<template>
  <div id="app">
    <Home />
  </div>
</template>

<script>
import Home from './views/Home.vue'
export default {
  name: 'App',
  components: {
    Home
  }
}
</script>

<style>
#app {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
}
</style>