type CacheEntry<T> = {
  data: T;
  timestamp: number;
};

const store = new Map<string, CacheEntry<unknown>>();
const inFlight = new Map<string, Promise<unknown>>();

export function getCached<T>(key: string, ttlMs: number): T | null {
  const entry = store.get(key);
  if (!entry) return null;
  if (Date.now() - entry.timestamp > ttlMs) {
    store.delete(key);
    return null;
  }
  return entry.data as T;
}

export function setCache<T>(key: string, data: T): void {
  store.set(key, { data, timestamp: Date.now() });
}

export function invalidateCache(prefix: string): void {
  for (const key of store.keys()) {
    if (key.startsWith(prefix)) store.delete(key);
  }
}

/** Deduplicate in-flight requests: concurrent callers for the same key
 *  share a single promise. On success, result is cached; on failure,
 *  the in-flight entry is removed so retries can proceed. */
export async function dedupeFetch<T>(
  key: string,
  ttlMs: number,
  fetcher: () => Promise<T>,
): Promise<T> {
  // 1. TTL cache hit — return immediately
  const cached = getCached<T>(key, ttlMs);
  if (cached !== null) return cached;

  // 2. In-flight dedup — share the existing promise
  const existing = inFlight.get(key);
  if (existing) return existing as Promise<T>;

  // 3. Execute and track
  const promise = fetcher()
    .then((data) => {
      inFlight.delete(key);
      setCache(key, data);
      return data;
    })
    .catch((err) => {
      inFlight.delete(key);
      throw err;
    });

  inFlight.set(key, promise);
  return promise;
}
