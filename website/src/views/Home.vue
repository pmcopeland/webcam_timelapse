<template>
  <div class="home">
    <ImageScrubber :images="images" />
  </div>
</template>

<script>
import ImageScrubber from "@/components/ImageScrubber.vue";

export default {
  name: "Home",
  components: {
    ImageScrubber,
  },
  data() {
    return {
      images: [], // Add your logic to fetch the images from the S3 bucket here
    };
  },
};
</script>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}
</style>