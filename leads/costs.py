"""Turn token counts into dollars, using the prices in config.py."""

from . import config


def prices_set() -> bool:
    return None not in (config.PRICE_INPUT_PER_M, config.PRICE_CACHED_INPUT_PER_M, config.PRICE_OUTPUT_PER_M)


def cost_usd(input_tokens: int, cached_input_tokens: int, output_tokens: int, cache_write_tokens: int = 0) -> float | None:
    """Cached input is billed at the cheap cached rate, newly cached input at the cache-write rate,
    and the rest of the input at the normal rate."""
    if not prices_set():
        return None
    normal = input_tokens - cached_input_tokens - cache_write_tokens
    write_price = getattr(config, "PRICE_CACHE_WRITE_PER_M", config.PRICE_INPUT_PER_M)
    return (normal * config.PRICE_INPUT_PER_M + cached_input_tokens * config.PRICE_CACHED_INPUT_PER_M
            + cache_write_tokens * write_price + output_tokens * config.PRICE_OUTPUT_PER_M) / 1_000_000
