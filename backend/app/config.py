from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/cultour.db"

    # Tavily
    tavily_api_key: str = ""
    tavily_max_results: int = 15
    tavily_search_depth: str = "advanced"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    analysis_max_tokens: int = 8192

    # Scraping
    scrape_timeout_seconds: int = 30
    scrape_max_retries: int = 2
    rate_limit_xiaohongshu: int = 2
    rate_limit_douyin: int = 2
    rate_limit_weixin: int = 5

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"

    # CORS
    frontend_url: str = "http://localhost:3000"

    # Data
    data_dir: str = "./data"
    export_dir: str = "./data/exports"

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8"}


settings = Settings()
