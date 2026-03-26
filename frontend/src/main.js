import {createApp} from 'vue'
import App from './App.vue'
import router from './router/index.ts'
import {createPinia} from 'pinia'
import {client} from './api/client.gen'
import {userManager} from './auth'

// Vuetify
import 'vuetify/styles'
import {createVuetify} from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Font Awesome (Vue plugin)
import {library} from '@fortawesome/fontawesome-svg-core'
import {fas} from '@fortawesome/free-solid-svg-icons'
import {FontAwesomeIcon} from '@fortawesome/vue-fontawesome'

// Register all solid icons
library.add(fas)

// Create Pinia instance
const pinia = createPinia()

client.setConfig({
  auth: async () => {
    const user = await userManager.getUser()
    return user?.access_token
  }
})

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light'
  }
})

// Create and mount the Vue application
const app = createApp(App)
app.component('font-awesome-icon', FontAwesomeIcon)
app
  .use(pinia)
  .use(router)
  .use(vuetify)
  .mount('#app')
