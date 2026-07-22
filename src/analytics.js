// Google Analytics 4
const GA_MEASUREMENT_ID = 'G-9K2N1RVSTR'

function loadGAScript() {
  console.log('[GA] Loading script...')
  const script = document.createElement('script')
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`
  script.async = true
  script.onload = () => console.log('[GA] Script loaded successfully')
  document.head.appendChild(script)

  window.dataLayer = window.dataLayer || []
  function gtag() { window.dataLayer.push(arguments) }
  window.gtag = gtag
  gtag('js', new Date())
  gtag('config', GA_MEASUREMENT_ID)
}

function recordPageView() {
  if (window.gtag) {
    window.gtag('event', 'page_view', {
      page_title: document.title,
      page_location: window.location.href,
      page_path: window.location.pathname,
    })
    console.log('[GA] Page view recorded')
  }
}

async function fetchVisitorInfo() {
  try {
    const res = await fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout(5000) })
    if (!res.ok) return null
    const data = await res.json()
    if (window.gtag) {
      window.gtag('event', 'visitor_info', {
        ip_address: data.ip,
        country: data.country_name,
        city: data.city,
        region: data.region,
        timezone: data.timezone,
      })
      console.log('[GA] Visitor info sent:', data.country_name, data.city)
    }
    return data
  } catch {
    return null
  }
}

export async function initAnalytics() {
  loadGAScript()
  for (let i = 0; i < 50; i++) {
    if (window.gtag) break
    await new Promise(r => setTimeout(r, 100))
  }
  if (window.gtag) {
    console.log('[GA] Initialized successfully')
    recordPageView()
    await fetchVisitorInfo()
  } else {
    console.warn('[GA] Failed to initialize after 5s')
  }
}