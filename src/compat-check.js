// Browser compatibility detection module.
// Runs before the Vue app mounts. Instead of guessing from the UA string,
// it probes the browser for the advanced features this project actually uses.
// If any required feature is missing, it redirects to outdate.html.
// A `?force=1` query parameter (or sessionStorage flag) bypasses the check
// (used by the "force visit" link on outdate.html).

(function () {
  'use strict';

  // ---------- Feature probes ----------
  // Each probe returns true when the feature is available. Add new probes
  // here as the project adopts more advanced features.

  // --- JavaScript APIs ---

  // Browsers that understand the `nomodule` attribute support ES modules.
  // (index.html loads the app via <script type="module">)
  function hasESModules() {
    var s = document.createElement('script');
    return 'noModule' in s;
  }

  // fetch + AbortSignal.timeout are used for the analytics request.
  function hasFetch() {
    return typeof window.fetch === 'function';
  }
  function hasAbortSignalTimeout() {
    return typeof window.AbortSignal === 'function' &&
      typeof window.AbortSignal.timeout === 'function';
  }

  // async/await (analytics.js) lowers to Promises.
  function hasPromise() {
    return typeof window.Promise === 'function';
  }

  // useI18n.js persists the selected language in localStorage; sessionStorage
  // carries the "force visit" bypass flag.
  function hasLocalStorage() {
    try {
      return typeof window.localStorage !== 'undefined' && window.localStorage !== null;
    } catch (e) {
      return false;
    }
  }
  function hasSessionStorage() {
    try {
      return typeof window.sessionStorage !== 'undefined' && window.sessionStorage !== null;
    } catch (e) {
      return false;
    }
  }

  // UIElements.vue / sakura.js drive animations with requestAnimationFrame.
  function hasRequestAnimationFrame() {
    return typeof window.requestAnimationFrame === 'function';
  }

  // URLSearchParams is used to read the ?force=1 bypass below.
  function hasURLSearchParams() {
    return typeof window.URLSearchParams === 'function';
  }

  // --- CSS features ---
  // CSS.supports is the detection mechanism itself; if it is missing the
  // browser is far too old, so every probe below returns false in that case.
  function cssSupports(prop, value) {
    var css = window.CSS;
    if (!css || typeof css.supports !== 'function') return false;
    try {
      return value !== undefined ? css.supports(prop, value) : css.supports(prop);
    } catch (e) {
      return false;
    }
  }

  // style.css / liquid-glass-block.css rely on var(--…) everywhere.
  function hasCSSCustomProperties() {
    return cssSupports('(--compat-check: 0)') ||
      cssSupports('--compat-check', '0') ||
      cssSupports('color', 'var(--compat-check)');
  }

  // Liquid glass effect (style.css, splash-screen.css, liquid-glass-block.css).
  // Safari only exposes it under the -webkit- prefix.
  function hasBackdropFilter() {
    return cssSupports('backdrop-filter', 'blur(2px)') ||
      cssSupports('-webkit-backdrop-filter', 'blur(2px)');
  }

  // liquid-glass-block.css animates --sheen-x / --sheen-y via @property.
  // The @property at-rule ships alongside CSS.registerProperty in practice.
  function hasPropertyRule() {
    return !!window.CSS && typeof window.CSS.registerProperty === 'function';
  }

  // liquid-glass-block.css ::after rim uses a conic-gradient.
  function hasConicGradient() {
    return cssSupports('background', 'conic-gradient(from 0deg, white, black)');
  }

  // style.css body::before uses the `inset` shorthand.
  function hasInset() {
    return cssSupports('inset', '0');
  }

  // liquid-glass-block.css rim compositing (unprefixed in Chrome/Firefox,
  // -webkit- with the Porter-Duff `xor` keyword in Safari).
  function hasMaskComposite() {
    return cssSupports('mask-composite', 'exclude') ||
      cssSupports('-webkit-mask-composite', 'xor');
  }

  // style.css and DocumentPage.vue request smooth scrolling.
  function hasScrollBehaviorSmooth() {
    return cssSupports('scroll-behavior', 'smooth');
  }

  // ---------- Required feature list ----------
  // Ordered for readability; each entry notes where the feature is used.
  var REQUIRED_FEATURES = [
    { name: 'ES Modules',              check: hasESModules },            // index.html <script type=module>
    { name: 'fetch',                   check: hasFetch },                 // analytics.js
    { name: 'AbortSignal.timeout',     check: hasAbortSignalTimeout },   // analytics.js
    { name: 'Promise',                check: hasPromise },               // async/await
    { name: 'localStorage',           check: hasLocalStorage },          // useI18n.js
    { name: 'sessionStorage',         check: hasSessionStorage },         // bypass flag
    { name: 'requestAnimationFrame',  check: hasRequestAnimationFrame },  // UIElements.vue, sakura.js
    { name: 'URLSearchParams',         check: hasURLSearchParams },       // ?force=1 bypass
    { name: 'CSS Custom Properties',  check: hasCSSCustomProperties },    // style.css var()
    { name: 'backdrop-filter',        check: hasBackdropFilter },         // liquid glass
    { name: 'CSS @property',          check: hasPropertyRule },           // liquid-glass-block.css
    { name: 'conic-gradient',         check: hasConicGradient },          // liquid-glass-block.css rim
    { name: 'inset',                  check: hasInset },                  // style.css body::before
    { name: 'mask-composite',         check: hasMaskComposite },          // liquid-glass-block.css rim
    { name: 'scroll-behavior: smooth', check: hasScrollBehaviorSmooth }   // style.css, DocumentPage.vue
  ];

  // Returns an array of missing feature names (empty when everything is OK).
  function getMissingFeatures() {
    var missing = [];
    for (var i = 0; i < REQUIRED_FEATURES.length; i++) {
      var feature = REQUIRED_FEATURES[i];
      try {
        if (!feature.check()) missing.push(feature.name);
      } catch (e) {
        missing.push(feature.name);
      }
    }
    return missing;
  }

  // ---------- Public API ----------

  // Check compatibility. If any required feature is missing, redirect to
  // outdate.html (unless bypassed via ?force=1 or sessionStorage).
  function checkCompatibility() {
    // Allow bypass via ?force=1 (used by the "force visit" link on outdate.html)
    try {
      var params = new URLSearchParams(window.location.search);
      if (params.get('force') === '1') return true;
    } catch (e) { /* ignore */ }

    // Also allow bypass via sessionStorage (so subsequent navigations don't re-trigger)
    try {
      if (sessionStorage.getItem('forceVisit') === '1') return true;
    } catch (e) { /* ignore */ }

    var missing = getMissingFeatures();
    if (missing.length > 0) {
      // Redirect to outdate.html. The force flag is preserved by the link on
      // that page so the "visit anyway" path can set it.
      window.location.replace('outdate.html');
      return false;
    }
    return true;
  }

  // Expose for main.js
  window.__checkBrowserCompat = checkCompatibility;
})();
