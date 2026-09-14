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

def load_config() -> Config:
    return Config(
        ALIEXPRESS_APP_KEY=os.getenv("ALIEXPRESS_APP_KEY", ""),
        ALIEXPRESS_APP_SECRET=os.getenv("ALIEXPRESS_APP_SECRET", ""),
        DEFAULT_USD_BRL=float(os.getenv("DEFAULT_USD_BRL", "5.50")),
        DEFAULT_ICMS_RATE=float(os.getenv("DEFAULT_ICMS_RATE", "0.17")),
        DEFAULT_MARKETPLACE_FEE=float(os.getenv("DEFAULT_MARKETPLACE_FEE", "0.16")),
        DEFAULT_TARGET_MARGIN=float(os.getenv("DEFAULT_TARGET_MARGIN", "0.40")),
        MIN_STORE_RATING=float(os.getenv("MIN_STORE_RATING", "4.5")),
        MIN_SALES_COUNT=int(os.getenv("MIN_SALES_COUNT", "10")),
    )
