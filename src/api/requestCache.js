// Deduplicate in-flight reads and retain successful responses briefly.
export function createRequestCache(now = Date.now) {
  const entries = new Map()
  return function cached(key, loader, ttl = 60000) {
    const entry = entries.get(key)
    if (entry && (entry.pending || entry.expires > now())) return entry.promise
    const next = { pending: true, expires: 0 }
    next.promise = Promise.resolve().then(loader).then(result => {
      next.pending = false
      next.expires = now() + ttl
      return result
    }, error => { entries.delete(key); throw error })
    entries.set(key, next)
    if (entries.size > 250) {
      for (const [id, value] of entries) if (!value.pending && value.expires <= now()) entries.delete(id)
    }
    return next.promise
  }
}
export const cachedRequest = createRequestCache()
