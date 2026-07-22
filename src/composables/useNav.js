import { ref } from 'vue'

const PAGES = ['home', 'document', 'changelog']

function readPage() {
  try {
    const p = new URLSearchParams(window.location.search).get('page')
    return PAGES.includes(p) ? p : 'home'
  } catch (e) {
    return 'home'
  }
}

const currentPage = ref(readPage())

export function useNav() {
  function syncUrl() {
    const params = new URLSearchParams(window.location.search)
    if (currentPage.value === 'home') {
      params.delete('page')
    } else {
      params.set('page', currentPage.value)
    }
    const q = params.toString()
    window.history.replaceState({}, '', q ? `?${q}` : '?')
    window.scrollTo(0, 0)
  }

  function navigate(page) {
    currentPage.value = PAGES.includes(page) ? page : 'home'
    syncUrl()
  }

  function back() {
    currentPage.value = 'home'
    syncUrl()
  }

  return { currentPage, navigate, back }
}
