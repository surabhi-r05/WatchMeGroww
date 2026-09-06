from .demo import DemoProvider
from .nse import NSEProvider
from .news import NewsProvider, news_provider

# NSE is the primary market-data source. It automatically falls back to the
# deterministic demo provider if NSE is unavailable, so the hackathon demo
# remains usable without pretending fallback data is live.
provider = NSEProvider()

__all__ = ["DemoProvider", "NSEProvider", "NewsProvider", "news_provider", "provider"]
