# vue-s3-image-viewer

This project is a Vue website that allows users to scrub through the images in a specified S3 bucket.

## Project Structure

```
vue-s3-image-viewer
├── public
│   └── index.html
├── src
│   ├── assets
│   ├── components
│   │   └── ImageScrubber.vue
│   ├── views
│   │   └── Home.vue
│   ├── App.vue
│   └── main.js
├── package.json
├── README.md
└── vue.config.js
```

## Installation

To set up the project, follow these steps:

1. Make sure you have Node.js and npm installed on your machine.
2. Create a new directory for your project and navigate to it in the terminal.
3. Run `npm init` to initialize a new `package.json` file. Follow the prompts to set up the project details.
4. Install the necessary dependencies by running the following command:
   ```
   npm install vue vue-router axios
   ```
   This will install Vue, Vue Router, and Axios.
5. Create the project file structure as shown in the project tree structure above.
6. Update `public/index.html` to include the necessary Vue script tags and a placeholder element for mounting the Vue app.
7. Update `src/main.js` with the following code:
   ```javascript
   import Vue from 'vue';
   import App from './App.vue';

   new Vue({
     render: h => h(App),
   }).$mount('#app');
   ```
8. Update `src/App.vue` with the following code:
   ```vue
   <template>
     <div id="app">
       <router-view></router-view>
     </div>
   </template>

   <style>
   /* Add your global styles here */
   </style>
   ```
9. Implement the logic and functionality for the `ImageScrubber` component and any other components as needed. You can find the `ImageScrubber` component in `src/components/ImageScrubber.vue`.
10. Update `src/views/Home.vue` to include the `ImageScrubber` component and any other content specific to the home page.
11. Customize the project as needed, including adding styles, configuring routes, and making API requests to the S3 bucket.
12. Run `npm run serve` to start the development server and view the website in your browser.

Remember to configure any necessary settings for accessing the S3 bucket, such as API credentials or CORS configurations.