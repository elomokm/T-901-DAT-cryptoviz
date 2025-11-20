from ..models import GlobalStats
from .coins_service import _query_last_snapshot


def get_global_stats() -> GlobalStats:
    coins = _query_last_snapshot()
    total_market_cap = sum(c.market_cap or 0 for c in coins)
    total_volume_24h = sum(c.volume_24h or 0 for c in coins)

    # Weighted average of 24h change by market cap
    num = 0.0
    den = 0.0
    for c in coins:
        if c.market_cap and c.change_24h is not None:
            num += c.market_cap * c.change_24h
            den += c.market_cap
    market_cap_change_24h = num / den if den else None

    return GlobalStats(
        total_market_cap=total_market_cap,
        total_volume_24h=total_volume_24h,
        market_cap_change_24h=market_cap_change_24h,
        count=len(coins),
    )
