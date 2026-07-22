// Browser compatibility check — must run before the Vue app mounts.
// If the browser/OS is too old, redirects to outdate.html and stops here.
import './compat-check.js'

if (!window.__checkBrowserCompat()) {
  // Redirecting to outdate.html — do not mount the app.
} else {
  // Dynamically import the app so that static imports don't run before the check.
  import('./app-bootstrap.js')
}
