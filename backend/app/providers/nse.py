from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
import threading
import time
import httpx

from app.core.config import settings
from app.providers.demo import DemoProvider


class NSEProvider:
    """NSE-backed market provider with conservative caching and demo fallback.

    NSE's public website endpoints are not an official licensed real-time API.
    This provider therefore treats NSE as the freshest available source and
    falls back to DemoProvider whenever NSE is unavailable.
    """

    BASE = "https://www.nseindia.com"
    source = "NSE"

    def __init__(self) -> None:
        self.demo = DemoProvider()
        self.cache: dict[str, tuple[float, Any]] = {}
        self.lock = threading.Lock()
        self.client = httpx.Client(
            timeout=settings.nse_timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": settings.nse_user_agent,
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": self.BASE + "/",
                "Origin": self.BASE,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        self._warm_session()

    def _warm_session(self) -> None:
        try:
            self.client.get(self.BASE + "/", timeout=settings.nse_timeout_seconds)
        except Exception:
            pass

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat()

    def _cached(self, key: str, max_age: int) -> Any | None:
        item = self.cache.get(key)
        if not item:
            return None
        ts, value = item
        if time.time() - ts <= max_age:
            return value
        return None

    def _put(self, key: str, value: Any) -> Any:
        with self.lock:
            self.cache[key] = (time.time(), value)
        return value

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.client.get(self.BASE + path, params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected NSE response")
        return payload

    def _quote_live(self, symbol: str) -> dict[str, Any]:
        payload = self._get("/api/quote-equity", {"symbol": symbol.upper()})
        price_info = payload.get("priceInfo") or {}
        trade_info = ((payload.get("marketDeptOrderBook") or {}).get("tradeInfo") or {})
        week = price_info.get("weekHighLow") or {}
        last = float(price_info.get("lastPrice"))
        change = float(price_info.get("pChange", 0.0))
        volume = int(float(trade_info.get("totalTradedVolume") or 0))
        if volume <= 0:
            volume = int(float((payload.get("securityInfo") or {}).get("tradedVolume") or 0))
        result = {
            "price": round(last, 2),
            "change_pct": round(change, 2),
            "volume": volume,
            "relative_volume": None,
            "sector_change_pct": None,
            "trend": "Bullish" if change > 1 else "Bearish" if change < -1 else "Sideways",
            "attention": "High" if abs(change) >= 3 else "Medium" if abs(change) >= 1.5 else "Low",
            "reasons": [f"NSE reports a {change:+.2f}% move today."],
            "source": "NSE",
            "freshness": "live",
            "fetched_at": self._now(),
            "open": price_info.get("open"),
            "previous_close": price_info.get("previousClose"),
            "day_high": (price_info.get("intraDayHighLow") or {}).get("max"),
            "day_low": (price_info.get("intraDayHighLow") or {}).get("min"),
            "week_high": week.get("max"),
            "week_low": week.get("min"),
            "isin": (payload.get("info") or {}).get("isin"),
        }
        return result

    def quote(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.upper().strip()
        key = f"quote:{symbol}"
        cached = self._cached(key, settings.nse_quote_cache_seconds)
        if cached:
            result = dict(cached)
            result["freshness"] = "cached"
            result["cache_age_seconds"] = int(time.time() - self.cache[key][0])
            return result
        try:
            result = self._quote_live(symbol)
            return self._put(key, result)
        except Exception as exc:
            demo = dict(self.demo.quote(symbol))
            demo["source"] = "Demo fallback"
            demo["freshness"] = "demo"
            demo["provider_error"] = str(exc)[:160]
            return demo

    def history(self, symbol: str, days: int = 365) -> list[dict[str, Any]]:
        symbol = symbol.upper().strip()
        days = min(max(days, 30), 3650)
        key = f"history:{symbol}:{days}"
        cached = self._cached(key, settings.nse_history_cache_seconds)
        if cached:
            return cached
        try:
            to_date = datetime.utcnow().date()
            from_date = to_date - timedelta(days=days + 10)
            payload = self._get(
                "/api/historical/cm/equity",
                {
                    "symbol": symbol,
                    "series": '["EQ"]',
                    "from": from_date.strftime("%d-%m-%Y"),
                    "to": to_date.strftime("%d-%m-%Y"),
                },
            )
            rows = payload.get("data") or []
            out: list[dict[str, Any]] = []
            for row in rows:
                date = row.get("CH_TIMESTAMP") or row.get("mTIMESTAMP") or row.get("TIMESTAMP")
                close = row.get("CH_CLOSING_PRICE") or row.get("CLOSE")
                volume = row.get("CH_TOT_TRADED_QTY") or row.get("TOTTRDQTY") or 0
                if date is None or close is None:
                    continue
                out.append({
                    "date": str(date),
                    "price": round(float(close), 2),
                    "close": round(float(close), 2),
                    "volume": int(float(volume or 0)),
                    "open": row.get("CH_OPENING_PRICE"),
                    "high": row.get("CH_TRADE_HIGH_PRICE"),
                    "low": row.get("CH_TRADE_LOW_PRICE"),
                })
            out.sort(key=lambda x: x["date"])
            if len(out) >= 20:
                return self._put(key, out[-days:])
        except Exception:
            pass
        return self.demo.history(symbol, min(days, 365))

    def market(self) -> dict[str, Any]:
        key = "indices"
        cached = self._cached(key, settings.nse_index_cache_seconds)
        if cached:
            result = {k: dict(v) for k, v in cached.items()}
            for v in result.values():
                v["freshness"] = "cached"
            return result
        try:
            payload = self._get("/api/allIndices")
            rows = payload.get("data") or []
            wanted = {
                "NIFTY 50": "NIFTY 50",
                "NIFTY BANK": "BANK NIFTY",
                "NIFTY FINANCIAL SERVICES": "NIFTY FINANCIAL SERVICES",
                "NIFTY IT": "NIFTY IT",
                "NIFTY METAL": "NIFTY METAL",
                "NIFTY PHARMA": "NIFTY PHARMA",
                "NIFTY AUTO": "NIFTY AUTO",
                "NIFTY FMCG": "NIFTY FMCG",
            }
            result: dict[str, Any] = {}
            for row in rows:
                name = str(row.get("index", "")).upper()
                if name in wanted:
                    label = wanted[name]
                    result[label] = {
                        "value": float(row.get("last", 0) or 0),
                        "change_pct": round(float(row.get("percentChange", 0) or 0), 2),
                        "source": "NSE",
                        "freshness": "live",
                        "fetched_at": self._now(),
                    }
            if "NIFTY 50" in result:
                return self._put(key, result)
        except Exception:
            pass
        return self.demo.market()

    def sector_quote(self, index_name: str) -> dict[str, Any] | None:
        if not index_name:
            return None
        key = f"sector:{index_name.upper()}"
        cached = self._cached(key, settings.nse_index_cache_seconds)
        if cached:
            result = dict(cached)
            result["freshness"] = "cached"
            return result
        try:
            payload = self._get("/api/equity-stockIndices", {"index": index_name})
            data = payload.get("data") or []
            if not data:
                return None
            index_row = data[0]
            if str(index_row.get("index", "")).upper() == index_name.upper():
                result = {
                    "name": index_row.get("index"),
                    "value": float(index_row.get("last", 0) or 0),
                    "change_pct": round(float(index_row.get("percentChange", 0) or 0), 2),
                    "source": "NSE",
                    "freshness": "live",
                    "fetched_at": self._now(),
                }
                return self._put(key, result)
        except Exception:
            return None
        return None

    def option_chain(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.upper().strip()
        key = f"options:{symbol}"
        cached = self._cached(key, settings.nse_options_cache_seconds)
        if cached:
            result = dict(cached)
            result["freshness"] = "cached"
            return result
        try:
            payload = self._get("/api/option-chain-equities", {"symbol": symbol})
            records = payload.get("records") or {}
            rows = records.get("data") or []
            expiry = (records.get("expiryDates") or [None])[0]
            underlying = records.get("underlyingValue")
            chain = []
            for row in rows:
                strike = row.get("strikePrice")
                if strike is None:
                    continue
                ce = row.get("CE") or {}
                pe = row.get("PE") or {}
                chain.append({
                    "strike": strike,
                    "expiry": row.get("expiryDate") or expiry,
                    "call": {"oi": ce.get("openInterest", 0), "change_oi": ce.get("changeinOpenInterest", 0), "volume": ce.get("totalTradedVolume", 0), "iv": ce.get("impliedVolatility", 0), "ltp": ce.get("lastPrice", 0)},
                    "put": {"oi": pe.get("openInterest", 0), "change_oi": pe.get("changeinOpenInterest", 0), "volume": pe.get("totalTradedVolume", 0), "iv": pe.get("impliedVolatility", 0), "ltp": pe.get("lastPrice", 0)},
                })
            if chain:
                total_call_oi = sum(float(x["call"]["oi"] or 0) for x in chain)
                total_put_oi = sum(float(x["put"]["oi"] or 0) for x in chain)
                result = {
                    "symbol": symbol,
                    "underlying": underlying,
                    "expiry": expiry,
                    "pcr": round(total_put_oi / total_call_oi, 2) if total_call_oi else None,
                    "chain": chain,
                    "source": "NSE",
                    "freshness": "live",
                    "fetched_at": self._now(),
                }
                return self._put(key, result)
        except Exception as exc:
            demo = self.demo.option_chain(symbol)
            demo["fallback_reason"] = "NSE option-chain data is currently unavailable."
            demo["provider_error"] = str(exc)[:120]
            return demo
        demo = self.demo.option_chain(symbol)
        demo["fallback_reason"] = "NSE returned no option-chain rows."
        return demo

    def fundamentals(self, symbol: str) -> dict[str, Any]:
        # NSE is the market-data source for this practice build; complete fundamental ratios
        # are not consistently available from the public quote payload, so use deterministic demo fallback.
        data = self.demo.fundamentals(symbol)
        data["fallback_reason"] = "Fundamental ratios are not present in the NSE quote payload used by this build."
        return data

    def status(self) -> dict[str, Any]:
        return {
            "provider": "NSE",
            "configured": True,
            "cached_entries": len(self.cache),
            "fallback": "DemoProvider",
        }
