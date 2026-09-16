import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    ALIEXPRESS_APP_KEY: str = ""
    ALIEXPRESS_APP_SECRET: str = ""
    DEFAULT_USD_BRL: float = 5.50
    DEFAULT_ICMS_RATE: float = 0.17
    DEFAULT_MARKETPLACE_FEE: float = 0.16
    DEFAULT_TARGET_MARGIN: float = 0.40
    MIN_STORE_RATING: float = 4.5
    MIN_SALES_COUNT: int = 10
    MERCADO_LIVRE_ACCESS_TOKEN: str = ""
    MERCADO_LIVRE_CLIENT_ID: str = ""
    MERCADO_LIVRE_CLIENT_SECRET: str = ""
    MERCADO_LIVRE_REFRESH_TOKEN: str = ""
    MERCADO_LIVRE_TOKEN_FILE: str = "data/mercado_livre_token.json"
    MERCADO_LIVRE_SITE_ID: str = "MLB"
    MERCADO_LIVRE_DB_PATH: str = "data/mercado_livre_radar.db"
    MERCADO_LIVRE_REPORT_DIR: str = "reports"
    MERCADO_LIVRE_CATEGORY_IDS: str = ""

def load_config() -> Config:
    return Config(
        ALIEXPRESS_APP_KEY=os.getenv("ALIEXPRESS_APP_KEY") or "",
        ALIEXPRESS_APP_SECRET=os.getenv("ALIEXPRESS_APP_SECRET") or "",
        DEFAULT_USD_BRL=float(os.getenv("DEFAULT_USD_BRL") or "5.50"),
        DEFAULT_ICMS_RATE=float(os.getenv("DEFAULT_ICMS_RATE") or "0.17"),
        DEFAULT_MARKETPLACE_FEE=float(os.getenv("DEFAULT_MARKETPLACE_FEE") or "0.16"),
        DEFAULT_TARGET_MARGIN=float(os.getenv("DEFAULT_TARGET_MARGIN") or "0.40"),
        MIN_STORE_RATING=float(os.getenv("MIN_STORE_RATING") or "4.5"),
        MIN_SALES_COUNT=int(os.getenv("MIN_SALES_COUNT") or "10"),
        MERCADO_LIVRE_ACCESS_TOKEN=os.getenv("MERCADO_LIVRE_ACCESS_TOKEN") or "",
        MERCADO_LIVRE_CLIENT_ID=os.getenv("MERCADO_LIVRE_CLIENT_ID") or "",
        MERCADO_LIVRE_CLIENT_SECRET=os.getenv("MERCADO_LIVRE_CLIENT_SECRET") or "",
        MERCADO_LIVRE_REFRESH_TOKEN=os.getenv("MERCADO_LIVRE_REFRESH_TOKEN") or "",
        MERCADO_LIVRE_TOKEN_FILE=os.getenv("MERCADO_LIVRE_TOKEN_FILE") or "data/mercado_livre_token.json",
        MERCADO_LIVRE_SITE_ID=os.getenv("MERCADO_LIVRE_SITE_ID") or "MLB",
        MERCADO_LIVRE_DB_PATH=os.getenv("MERCADO_LIVRE_DB_PATH") or "data/mercado_livre_radar.db",
        MERCADO_LIVRE_REPORT_DIR=os.getenv("MERCADO_LIVRE_REPORT_DIR") or "reports",
        MERCADO_LIVRE_CATEGORY_IDS=os.getenv("MERCADO_LIVRE_CATEGORY_IDS") or "",
    )
