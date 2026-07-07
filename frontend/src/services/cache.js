/**
 * Simple cache utility for frontend data persistence
 * Uses localStorage with timestamps for validity checking
 */

const CACHE_PREFIX = 'stock_discipline_';
const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes default cache TTL

/**
 * 计算当日A股收盘时间对应的缓存过期时间
 * A股收盘时间:工作日15:00
 * 如果当前时间已过收盘,缓存到次日收盘时间
 */
function getMarketCloseCacheExpiry() {
  const now = new Date();
  const todayClose = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 15, 0, 0);
  
  // 如果当前时间已过收盘时间,设置到明天收盘
  if (now > todayClose) {
    const tomorrowClose = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 15, 0, 0);
    return tomorrowClose.getTime();
  }
  
  // 如果当前时间在收盘前,设置到今天收盘
  return todayClose.getTime();
}

/**
 * Get cached data if valid, otherwise return null
 * @param {string} key - Cache key
 * @param {number} maxAge - Maximum age in milliseconds (default 5 minutes)
 * @param {boolean} useMarketCloseExpiry - 是否使用市场收盘时间作为缓存过期标准(用于K线数据)
 * @returns {object|null} - Cached data or null if expired/missing
 */
export function getCache(key, maxAge = DEFAULT_TTL, useMarketCloseExpiry = false) {
  try {
    const cacheKey = CACHE_PREFIX + key;
    const cached = localStorage.getItem(cacheKey);
    if (!cached) return null;

    const { data, timestamp } = JSON.parse(cached);
    const now = Date.now();

    // K线数据特殊处理:缓存到收盘时间
    if (useMarketCloseExpiry) {
      const expiryTime = getMarketCloseCacheExpiry();
      if (now < expiryTime) {
        return data; // 在收盘前缓存有效
      }
      localStorage.removeItem(cacheKey);
      return null;
    }

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
 * @param {boolean} useMarketCloseExpiry - 是否使用市场收盘时间作为缓存标准
 */
export function setCache(key, data, useMarketCloseExpiry = false) {
  try {
    const cacheKey = CACHE_PREFIX + key;
    const cached = {
      data,
      timestamp: Date.now(),
      useMarketCloseExpiry
    };
    localStorage.setItem(cacheKey, JSON.stringify(cached));
    
    // 同时保存到IndexedDB用于长期持久化
    saveToIndexedDB(cacheKey, cached);
  } catch {
    // localStorage might be full or disabled
  }
}

/**
 * IndexedDB持久化存储(用于长期缓存)
 */
let indexedDB = null;

function initIndexedDB() {
  if (indexedDB) return indexedDB;
  
  return new Promise((resolve, reject) => {
    const request = window.indexedDB.open('StockDisciplineCache', 1);
    
    request.onerror = () => reject(request.error);
    
    request.onsuccess = () => {
      indexedDB = request.result;
      resolve(indexedDB);
    };
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('klineCache')) {
        db.createObjectStore('klineCache', { keyPath: 'key' });
      }
    };
  });
}

async function saveToIndexedDB(key, value) {
  try {
    const db = await initIndexedDB();
    const transaction = db.transaction(['klineCache'], 'readwrite');
    const store = transaction.objectStore('klineCache');
    
    store.put({
      key,
      value,
      savedAt: new Date().toISOString()
    });
  } catch (err) {
    console.warn('IndexedDB save failed:', err);
  }
}

async function getFromIndexedDB(key) {
  try {
    const db = await initIndexedDB();
    const transaction = db.transaction(['klineCache'], 'readonly');
    const store = transaction.objectStore('klineCache');
    
    return new Promise((resolve, reject) => {
      const request = store.get(key);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result?.value || null);
    });
  } catch (err) {
    console.warn('IndexedDB get failed:', err);
    return null;
  }
}

/**
 * Clear specific cache key
 * @param {string} key - Cache key to clear
 */
export function clearCache(key) {
  try {
    const cacheKey = CACHE_PREFIX + key;
    localStorage.removeItem(cacheKey);
    
    // 同时从IndexedDB删除
    clearFromIndexedDB(cacheKey);
  } catch {
  }
}

async function clearFromIndexedDB(key) {
  try {
    const db = await initIndexedDB();
    const transaction = db.transaction(['klineCache'], 'readwrite');
    const store = transaction.objectStore('klineCache');
    store.delete(key);
  } catch (err) {
    console.warn('IndexedDB delete failed:', err);
  }
}

/**
 * 获取持久化缓存(优先IndexedDB,其次是localStorage)
 * 用于页面加载时先展示缓存数据
 */
export async function getPersistentCache(key) {
  // 先尝试从IndexedDB获取长期缓存
  const indexedDBData = await getFromIndexedDB(CACHE_PREFIX + key);
  if (indexedDBData && indexedDBData.data) {
    const now = Date.now();
    const expiryTime = getMarketCloseCacheExpiry();
    
    // K线数据在收盘前缓存有效
    if (indexedDBData.useMarketCloseExpiry && now < expiryTime) {
      return indexedDBData.data;
    }
    
    // 普通数据7天内缓存有效
    if (!indexedDBData.useMarketCloseExpiry && 
        now - indexedDBData.timestamp < 7 * 24 * 60 * 60 * 1000) {
      return indexedDBData.data;
    }
  }
  
  // 其次从localStorage获取
  return getCache(key, DEFAULT_TTL, true);
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