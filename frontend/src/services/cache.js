/**
 * Simple cache utility for frontend data persistence
 * Uses localStorage with timestamps for validity checking
 */

const CACHE_PREFIX = 'stock_discipline_';
const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes default cache TTL

/**
 * Get cached data if valid, otherwise return null
 * @param {string} key - Cache key
 * @param {number} maxAge - Maximum age in milliseconds (default 5 minutes)
 * @returns {object|null} - Cached data or null if expired/missing
 */
export function getCache(key, maxAge = DEFAULT_TTL) {
  try {
    const cacheKey = CACHE_PREFIX + key;
    const cached = localStorage.getItem(cacheKey);
    if (!cached) return null;

    const { data, timestamp } = JSON.parse(cached);
    const now = Date.now();

    // Check if cache is still valid
    if (now - timestamp < maxAge) {
      return data;
    }

    // Cache expired, remove it
    localStorage.removeItem(cacheKey);
    return null;
  } catch {
    return null;
  }
}

/**
 * Set data to cache with current timestamp
 * @param {string} key - Cache key
 * @param {object} data - Data to cache
 */
export function setCache(key, data) {
  try {
    const cacheKey = CACHE_PREFIX + key;
    const cached = {
      data,
      timestamp: Date.now()
    };
    localStorage.setItem(cacheKey, JSON.stringify(cached));
  } catch {
    // localStorage might be full or disabled
  }
}

/**
 * Clear specific cache key
 * @param {string} key - Cache key to clear
 */
export function clearCache(key) {
  try {
    localStorage.removeItem(CACHE_PREFIX + key);
  } catch {
  }
}

/**
 * Clear all app caches
 */
export function clearAllCaches() {
  try {
    Object.keys(localStorage)
      .filter(key => key.startsWith(CACHE_PREFIX))
      .forEach(key => localStorage.removeItem(key));
  } catch {
  }
}

/**
 * Create a cached API getter function
 * Returns cached data immediately if valid, then fetches fresh data in background
 * @param {Function} apiGetFn - The apiGet function from api.js
 * @returns {Function} - Cached getter function
 */
export function createCachedGetter(apiGetFn) {
  return async function cachedApiGet(path, cacheKey = path, maxAge = DEFAULT_TTL) {
    // Return cached data immediately if available
    const cached = getCache(cacheKey, maxAge);

    // Fetch fresh data in background
    const freshPromise = apiGetFn(path).then(data => {
      setCache(cacheKey, data);
      return data;
    }).catch(err => {
      // If fetch fails and we have cache, keep using cache
      if (cached) {
        console.warn(`API fetch failed, using cached data: ${err.message}`);
        return cached;
      }
      throw err;
    });

    // If we have valid cache, return it immediately
    if (cached) {
      // Still fetch fresh data in background for next time
      freshPromise.catch(() => {}); // Silently fail background refresh
      return cached;
    }

    // No cache, wait for fresh data
    return freshPromise;
  };
}