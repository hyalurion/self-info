// Browser compatibility detection module.
// Runs before the Vue app mounts. If the browser/OS is too old, redirect to outdate.html.
// A `?force=1` query parameter bypasses the check (used by the "force visit" link).

(function () {
  'use strict';

  // ---------- Utility functions ----------

  function compareVersions(v1, v2) {
    if (!v1 && !v2) return 0;
    if (!v1) return -1;
    if (!v2) return 1;
    var parts1 = String(v1).split(/[._-]/);
    var parts2 = String(v2).split(/[._-]/);
    var len = Math.max(parts1.length, parts2.length);
    for (var i = 0; i < len; i++) {
      var a = i < parts1.length ? (parseInt(parts1[i], 10) || 0) : 0;
      var b = i < parts2.length ? (parseInt(parts2[i], 10) || 0) : 0;
      if (a > b) return 1;
      if (a < b) return -1;
    }
    return 0;
  }

  function isVersionAtLeast(version, target) {
    if (!version) return false;
    return compareVersions(version, target) >= 0;
  }

  // ---------- UA parsing ----------

  function parseUA(ua) {
    var result = {
      os: { name: '不明', version: '' },
      browser: { name: '不明', version: '' }
    };

    if (!ua) ua = navigator.userAgent || '';
    ua = String(ua);

    // ----- OS -----
    var osName = '不明';
    var osVer = '';

    var iosMatch = ua.match(/iPhone OS (\d+)[._](\d+)(?:[._](\d+))?/i);
    var iPadMatch = ua.match(/iPad OS (\d+)[._](\d+)(?:[._](\d+))?/i);
    var iPodMatch = ua.match(/iPod touch; CPU iPhone OS (\d+)[._](\d+)(?:[._](\d+))?/i);

    if (iPadMatch) {
      osName = 'iPadOS';
      osVer = iPadMatch[1] + '.' + iPadMatch[2];
    } else if (iosMatch || iPodMatch) {
      var m = iosMatch || iPodMatch;
      osName = 'iOS';
      osVer = m[1] + '.' + m[2];
    } else if (/iPad|iPhone|iPod/.test(ua) && /Mac OS X/.test(ua)) {
      var plat = navigator.platform || '';
      if (/iPad|iPhone|iPod/.test(plat)) {
        osName = plat.indexOf('iPad') !== -1 ? 'iPadOS' : 'iOS';
        var verMatch = ua.match(/OS (\d+)[._](\d+)(?:[._](\d+))?/i);
        if (verMatch) osVer = verMatch[1] + '.' + verMatch[2];
      }
    }

    if (osName === '不明') {
      var macMatch = ua.match(/Mac OS X (\d+)[._](\d+)(?:[._](\d+))?/i);
      if (macMatch) {
        osName = 'macOS';
        osVer = parseInt(macMatch[1], 10) + '.' + parseInt(macMatch[2], 10);
      }
    }

    if (osName === '不明') {
      var andMatch = ua.match(/Android (\d+)(?:[._](\d+))?(?:[._](\d+))?/i);
      if (andMatch) {
        osName = 'Android';
        osVer = andMatch[1];
        if (andMatch[2]) osVer += '.' + andMatch[2];
      }
    }

    if (osName === '不明') {
      var winMatch = ua.match(/Windows NT (\d+)[._](\d+)/i);
      if (winMatch) {
        osName = 'Windows';
        osVer = winMatch[1] + '.' + winMatch[2];
      }
    }

    result.os.name = osName;
    result.os.version = osVer;

    // ----- Browser -----
    var browserName = '不明';
    var browserVer = '';

    var edgeMatch = ua.match(/Edg(?:iOS)?\/(\d+)(?:[._](\d+))?(?:[._](\d+))?/i);
    if (edgeMatch) {
      browserName = 'Edge';
      browserVer = edgeMatch[1];
    }

    if (browserName === '不明') {
      var chromeMatch = ua.match(/(?:Chrome|CriOS|HeadlessChrome)\/(\d+)/i);
      if (chromeMatch && !/Edg\//.test(ua) && !/OPR\//.test(ua) && !/FxiOS/.test(ua)) {
        browserName = 'Chrome';
        browserVer = chromeMatch[1];
      }
    }

    if (browserName === '不明') {
      var ffMatch = ua.match(/(?:Firefox|FxiOS)\/(\d+)/i);
      if (ffMatch) {
        browserName = 'Firefox';
        browserVer = ffMatch[1];
      }
    }

    if (browserName === '不明') {
      var safMatch = ua.match(/Version\/(\d+)(?:[._](\d+))?.*?Safari\//i);
      if (safMatch && !/Chrome\//.test(ua) && !/Edg\//.test(ua) && !/CriOS/.test(ua) && !/FxiOS/.test(ua)) {
        browserName = 'Safari';
        browserVer = safMatch[1];
      }
    }

    if (browserName === '不明') {
      var oprMatch = ua.match(/OPR\/(\d+)/i);
      if (oprMatch) {
        browserName = 'Opera';
        browserVer = oprMatch[1];
      }
    }

    if (browserName === '不明') {
      var samMatch = ua.match(/SamsungBrowser\/(\d+)/i);
      if (samMatch) {
        browserName = 'Samsung Internet';
        browserVer = samMatch[1];
      }
    }

    result.browser.name = browserName;
    result.browser.version = browserVer;

    return result;
  }

  // ---------- Compatibility check ----------

  // Minimum supported versions
  var MIN_MACOS = '15.4';
  var MIN_IOS = '18.4';
  var MIN_ANDROID = '10';
  var MIN_WINDOWS = '10';
  var MIN_CHROME = '115';
  var MIN_EDGE = '115';
  var MIN_FIREFOX = '128';
  var MIN_SAFARI = '18.4';

  // Returns true if the current environment is supported
  function isSupported(parsed) {
    var os = parsed.os;
    var browser = parsed.browser;
    var osName = os.name || '';
    var osVer = os.version || '';
    var browserName = browser.name || '';
    var browserVer = browser.version || '';

    // iOS / iPadOS: must be >= MIN_IOS (cannot upgrade browser independently)
    if (/iPadOS|iOS/.test(osName)) {
      return isVersionAtLeast(osVer, MIN_IOS);
    }

    // macOS: OS >= MIN_MACOS, and browser must meet its minimum
    if (/macOS/.test(osName)) {
      if (!isVersionAtLeast(osVer, MIN_MACOS)) return false;
      return checkBrowser(browserName, browserVer);
    }

    // Android: OS >= MIN_ANDROID, Chrome must meet minimum
    if (/Android/.test(osName)) {
      if (!isVersionAtLeast(osVer, MIN_ANDROID)) return false;
      return checkBrowser(browserName, browserVer);
    }

    // Windows: OS >= MIN_WINDOWS, browser must meet minimum
    if (/Windows/.test(osName)) {
      if (!isVersionAtLeast(osVer, MIN_WINDOWS)) return false;
      return checkBrowser(browserName, browserVer);
    }

    // ChromeOS: Chrome must meet minimum
    if (/ChromeOS/.test(osName)) {
      return checkBrowser(browserName, browserVer);
    }

    // HarmonyOS / Linux / unknown: treat as unsupported (advice will guide user)
    return false;
  }

  function checkBrowser(browserName, browserVer) {
    if (/Chrome/.test(browserName)) return isVersionAtLeast(browserVer, MIN_CHROME);
    if (/Edge/.test(browserName)) return isVersionAtLeast(browserVer, MIN_EDGE);
    if (/Firefox/.test(browserName)) return isVersionAtLeast(browserVer, MIN_FIREFOX);
    if (/Safari/.test(browserName)) return isVersionAtLeast(browserVer, MIN_SAFARI);
    if (/Opera/.test(browserName)) return isVersionAtLeast(browserVer, MIN_CHROME);
    if (/Samsung Internet/.test(browserName)) return isVersionAtLeast(browserVer, MIN_CHROME);
    return false;
  }

  // ---------- Public API ----------

  // Check compatibility. If unsupported, redirect to outdate.html (unless bypassed).
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

    var parsed = parseUA();
    var supported = isSupported(parsed);

    if (!supported) {
      // Redirect to outdate.html. Preserve the force flag so the "visit anyway" link can set it.
      var redirect = 'outdate.html';
      window.location.replace(redirect);
      return false;
    }
    return true;
  }

  // Expose for main.js
  window.__checkBrowserCompat = checkCompatibility;
})();
