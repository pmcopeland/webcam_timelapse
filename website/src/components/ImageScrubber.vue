<template>
  <div class="image-scrubber">
    <div v-if="images.length">
      <img :src="getImage(currentIndex)" alt="S3 Image" class="responsive-image" />
      <div class="controls">
        <button @click="previousImage">Previous</button>
        <input type="range" min="0" :max="images.length - 1" v-model="currentIndex" />
        <button @click="nextImage">Next</button>
      </div>
      <div class="debug">
        <p>Current index: {{ currentIndex }}</p>
        <p>Current file: {{ currentFile }}</p>
      </div>
    </div>
    <div v-else>
      Loading images...
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      images: [],
      currentIndex: 0,
      currentFile: ''
    };
  },
  methods: {
    previousImage() {
      if (this.currentIndex > 0) {
        this.currentIndex--;
      }
    },
    nextImage() {
      if (this.currentIndex < this.images.length - 1) {
        this.currentIndex++;
      }
    },
    getImage(index) {
      let file_name = this.images[index];
      return `http://192.168.1.157:5000/get-file?file_key=${file_name}`;
    }
  },
  mounted() {
    axios.get('http://192.168.1.157:5000/list-files', { timeout: 10000 }) // Set timeout to 10 seconds
      .then(response => {
        console.log(response);
        this.images = response.data;
        if (this.images.length > 0) {
          this.currentIndex = this.images.length - 1; // Set to the latest image
          this.currentFile = this.images[this.currentIndex]; // Initialize currentFile
        }
      })
      .catch(error => {
        console.error('Error fetching images:', error);
      });
  },
  watch: {
    currentIndex(newIndex) {
      console.log(newIndex);
      console.log(this.images[newIndex]);
      if (this.images.length > 0) {
        this.currentFile = this.images[newIndex];
      }
    }
  }
};
</script>

<style scoped>
.image-scrubber {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
}

.responsive-image {
  max-width: 100%;
  height: auto;
}

.controls {
  display: flex;
  justify-content: space-between;
  width: 100%;
  max-width: 300px;
  margin-top: 10px;
}

button {
  padding: 10px;
  font-size: 16px;
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

input[type="range"] {
  flex-grow: 1;
  margin: 0 10px;
}

@media (max-width: 600px) {
  .controls {
    flex-direction: column;
    align-items: center;
  }

  button {
    width: 100%;
    margin: 5px 0;
  }

  input[type="range"] {
    width: 100%;
    margin: 10px 0;
  }
}
</style>