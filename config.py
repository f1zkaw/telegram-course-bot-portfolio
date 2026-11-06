"""Environment-only configuration (never commit .env)."""
import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int | None
    payment_mode: str
    provider_token: str | None
    price_minor: int
    currency: str
    database_path: Path


def load_config() -> Config:
    mode = os.getenv("PAYMENT_MODE", "demo").lower().strip()
    if mode not in {"demo", "telegram"}:
        raise ValueError("PAYMENT_MODE должен быть 'demo' или 'telegram'")

    raw_admin = os.getenv("ADMIN_ID", "").strip()
    admin_id = int(raw_admin) if raw_admin else None
    provider = os.getenv("PROVIDER_TOKEN", "").strip() or None
    token = os.getenv("BOT_TOKEN", "").strip()
    price = int(os.getenv("PRICE_MINOR", "10000"))
    currency = os.getenv("CURRENCY", "RUB").strip().upper()

    if not token:
        raise ValueError("Не задан BOT_TOKEN в переменных окружения")
    if mode == "telegram" and (not provider or price <= 0):
        raise ValueError("Для реальной оплаты нужны PROVIDER_TOKEN и PRICE_MINOR > 0")

    return Config(
        bot_token=token,
        admin_id=admin_id,
        payment_mode=mode,
        provider_token=provider,
        price_minor=price,
        currency=currency,
        database_path=BASE_DIR / "bot_data.db",
    )
