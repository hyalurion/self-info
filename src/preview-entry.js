import { createApp } from 'vue'
import PreviewApp from './components/PreviewApp.vue'

// Same global styles as the main app, so the preview is pixel-faithful.
import './assets/styles/style.css'
import './assets/styles/liquid-glass-block.css'
import './assets/styles/splash-screen.css'
import './assets/styles/birthday.css'
import './assets/styles/kana.css'

createApp(PreviewApp).mount('#app')
