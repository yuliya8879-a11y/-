import os
import logging
from typing import Optional
import httpx
from .ai_processor import generate_ad_text, get_missing_fields_list

logger = logging.getLogger(__name__)

CHANNEL_LABELS = {
    "telegram": "Telegram",
    "whatsapp": "WhatsApp",
    "max": "MAX",
}


def generate_yulia_notification(lot, contact) -> str:
    culture = lot.culture or "—"
    quality_type = lot.quality_type or ""
    culture_str = f"{culture} {quality_type}".strip()
    volume_str = f"{int(lot.volume)} т" if lot.volume else "—"
    region_str = lot.region or "—"

    indicators = []
    if lot.humidity is not None:
        indicators.append(f"влажность {lot.humidity}%")
    if lot.weed is not None:
        indicators.append(f"сорность {lot.weed}%")
    if lot.grain_impurity is not None:
        indicators.append(f"зерн. примесь {lot.grain_impurity}%")
    if lot.nature is not None:
        indicators.append(f"натура {lot.nature} г/л")
    if lot.protein is not None:
        indicators.append(f"протеин {lot.protein}%")
    if lot.oil_content is not None:
        indicators.append(f"масличность {lot.oil_content}%")
    if lot.acid_value is not None:
        indicators.append(f"кислотное число {lot.acid_value}")
    indicators_str = ", ".join(indicators) if indicators else "не указаны"

    vat_str = lot.vat_type or "—"
    price_str = f"{int(lot.price)} руб/т" if lot.price else "—"

    contact_name = contact.name or "—"
    contact_phone = contact.phone or "—"
    channel = CHANNEL_LABELS.get(contact.last_channel or "", contact.last_channel or "—")

    missing = get_missing_fields_list(lot)
    missing_str = ", ".join(missing) if missing else "все данные есть"

    ad_text = generate_ad_text(lot, contact)

    return (
        f"🌾 Новый лот Agro Hub\n\n"
        f"Культура: {culture_str}\n"
        f"Объём: {volume_str}\n"
        f"Регион: {region_str}\n"
        f"Показатели: {indicators_str}\n"
        f"Цена: {price_str}\n"
        f"НДС: {vat_str}\n"
        f"Контакт: {contact_name}, {contact_phone}\n"
        f"Канал: {channel}\n\n"
        f"❓ Нужно уточнить: {missing_str}\n\n"
        f"📢 Готовый текст объявления:\n{ad_text}"
    )


async def send_telegram_notification(token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
            })
            if resp.status_code == 200:
                return True
            logger.error(f"Telegram API error: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления Юлии: {e}")
        return False


async def notify_yulia(lot, contact) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("YULIA_TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN или YULIA_TELEGRAM_CHAT_ID не заданы")
        return False
    text = generate_yulia_notification(lot, contact)
    return await send_telegram_notification(token, chat_id, text)
