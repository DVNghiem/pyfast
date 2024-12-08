# Caching Strategies

## Overview

Caching is a technique used to store and retrieve data quickly by keeping a copy of frequently accessed data in a temporary storage location. This helps to reduce the time and resources required to fetch data from the original source. In this document, we will discuss two caching strategies implemented in our project: `StaleWhileRevalidateStrategy` and `CacheAsideStrategy`.

## Caching Strategies

### Stale-While-Revalidate Strategy

The `StaleWhileRevalidateStrategy` allows serving stale content while revalidating it in the background. This strategy is useful when you want to provide a fast response to the user while ensuring that the data is eventually consistent.

#### Key Features:
- Serves stale content if available.
- Revalidates the content in the background if it is stale.
- Updates the cache with fresh data after revalidation.

#### Usage:

```python
from hypern.hypern import BaseBackend
from strategies import StaleWhileRevalidateStrategy

async def revalidate_fn(key: str) -> Any:
    # Implement your revalidation logic here
    pass

backend = BaseBackend()
strategy = StaleWhileRevalidateStrategy(
    backend=backend,
    revalidate_after=60,  # Revalidate after 60 seconds
    ttl=300,  # Time-to-live for cache entries is 300 seconds
    revalidate_fn=revalidate_fn
)
```

### Cache-Aside Strategy

The `CacheAsideStrategy` (also known as lazy loading) loads data into the cache only when it is requested. This strategy is useful when you want to cache data on-demand and avoid unnecessary cache population.

#### Key Features:
- Loads data into the cache only when requested.
- Updates the cache with fresh data on cache miss.
- Optionally supports write-through mode to update the source data.

#### Usage:

```python
from hypern.hypern import BaseBackend
from strategies import CacheAsideStrategy

async def load_fn(key: str) -> Any:
    # Implement your data loading logic here
    pass

backend = BaseBackend()
strategy = CacheAsideStrategy(
    backend=backend,
    load_fn=load_fn,
    ttl=300,  # Time-to-live for cache entries is 300 seconds
    write_through=True  # Enable write-through mode
)
```

## Integrating Cache with API Requests

To integrate caching with your API requests, you can use the `cache_with_strategy` decorator. This decorator allows you to apply a caching strategy to your API endpoints.

### Example:

```python
from hypern import Hypern, Request
from hypern.routing import Route
from hypern.response import PlainTextResponse

from hypern.caching import StaleWhileRevalidateStrategy, cache_with_strategy,RedisBackend


async def revalidate_fn(key: str) -> Any:
    # Implement your revalidation logic here
    pass

backend = RedisBackend(url="redis://localhost:6379")
strategy = StaleWhileRevalidateStrategy(
    backend=backend,
    revalidate_after=60,  # Revalidate after 60 seconds
    ttl=300,  # Time-to-live for cache entries is 300 seconds
    revalidate_fn=revalidate_fn
)

app = Hypern()
route = Route("/my-api")

@cache_with_strategy(strategy, key_prefix="test")
async def get_result():
    return "Hello, World!"

@route.get("/hello")
async def my_api_endpoint(request: Request):
    result = await self.get_result()
    return PlainTextResponse(result)

app.add_route(route)

if __name__ == "__main__":
    app.start()
```

In this example, the `my_api_endpoint` function is decorated with the `cache_with_strategy` decorator, which applies the `StaleWhileRevalidateStrategy` to the endpoint. The cache key is prefixed with `my_api` to ensure uniqueness.

By following these steps, you can effectively integrate caching into your API requests and improve the performance and scalability of your application.