use dashmap::DashMap;
use std::time::{Duration, Instant};

use super::route::Route;

#[derive(Clone)]
pub struct CachedRoute {
    pub route: Route,
    pub last_accessed: Instant,
    pub hit_count: u64,
}

pub struct RouteCache {
    cache: DashMap<String, CachedRoute>,
    max_size: usize,
    ttl: Duration,
}

impl RouteCache {
    pub fn new(max_size: usize, ttl_seconds: u64) -> Self {
        Self {
            cache: DashMap::new(),
            max_size,
            ttl: Duration::from_secs(ttl_seconds),
        }
    }

    pub fn get(&self, key: &str) -> Option<Route> {
        if let Some(mut entry) = self.cache.get_mut(key) {
            let now = Instant::now();
            if now.duration_since(entry.last_accessed) > self.ttl {
                self.cache.remove(key);
                return None;
            }
            entry.last_accessed = now;
            entry.hit_count += 1;
            return Some(entry.route.clone());
        }
        None
    }

    pub fn insert(&self, key: String, route: Route) {
        if self.cache.len() >= self.max_size {
            // Evict least recently used entry
            let to_evict = self.cache
                .iter()
                .min_by_key(|entry| (entry.last_accessed, entry.hit_count))
                .map(|entry| entry.key().clone());
            
            if let Some(key) = to_evict {
                self.cache.remove(&key);
            }
        }

        self.cache.insert(key, CachedRoute {
            route,
            last_accessed: Instant::now(),
            hit_count: 1,
        });
    }

    pub fn clear(&self) {
        self.cache.clear();
    }
}