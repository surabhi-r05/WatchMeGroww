from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -----------------------------
    # Existing application settings
    # -----------------------------
    database_url: str = "sqlite:///./watchmegroww.db"

    demo_mode: bool = True
    demo_disable_auth: bool = False

    redis_url: str | None = None

    cors_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    # -----------------------------
    # GNews
    # -----------------------------
    gnews_api_key: str | None = None

    # Cache news responses for this many minutes.
    # This prevents repeatedly hitting GNews for the same query.
    news_cache_minutes: int = 20

    # Safety limit for our application.
    # GNews free tier is limited, so we deliberately stay below it.
    gnews_daily_limit: int = 70

    # HTTP behaviour
    gnews_timeout_seconds: float = 8.0
    gnews_max_retries: int = 2

    # -----------------------------
    # NSE market-data provider
    # -----------------------------
    nse_timeout_seconds: float = 8.0
    nse_quote_cache_seconds: int = 20
    nse_index_cache_seconds: int = 30
    nse_history_cache_seconds: int = 900
    nse_options_cache_seconds: int = 30
    nse_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )

    # -----------------------------
    # Alerts / background jobs
    # -----------------------------
    alert_interval_seconds: int = 60

    # -----------------------------
    # Helpers
    # -----------------------------
    @property
    def cors_origin_list(self) -> list[str]:
        return [
            x.strip()
            for x in self.cors_origins.split(",")
            if x.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()