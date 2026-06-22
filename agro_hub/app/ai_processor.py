import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

CULTURE_QUALITY_MAP = {
    "ячмень": ["фуражный", "пивоваренный"],
    "пшеница": ["продовольственная", "фуражная"],
    "подсолнечник": ["стандартный"],
    "кукуруза": ["фуражная", "продовольственная"],
    "соя": ["стандартная"],
    "рапс": ["стандартный"],
    "горох": ["продовольственный", "фуражный"],
}

EXTRACTION_SYSTEM_PROMPT = """Ты — система извлечения данных о сельскохозяйственных лотах.
Из сообщения пользователя извлеки следующие поля (все необязательные):
- culture: название культуры на русском (ячмень, пшеница, подсолнечник, кукуруза, соя, рапс, горох и т.д.)
- volume: объём в тоннах (только число)
- region: регион России (например: Орловская область, Краснодарский край)
- district: район внутри региона
- quality_type: тип качества (фуражный/фуражная, продовольственный/продовольственная, пивоваренный и т.д.)
- humidity: влажность в процентах (только число)
- weed: сорность в процентах (только число)
- grain_impurity: зерновая примесь в процентах (только число)
- nature: натура в г/л (только число)
- oil_content: масличность в процентах (только число)
- protein: протеин в процентах (только число)
- acid_value: кислотное число (только число)
- vat_type: НДС — "с НДС" или "без НДС"
- price: цена в руб/тонна (только число)

Верни ТОЛЬКО валидный JSON без пояснений. Для отсутствующих полей используй null.
Пример: {"culture":"ячмень","volume":500,"region":"Орловская область","district":null,"quality_type":null,"humidity":null,"weed":null,"grain_impurity":null,"nature":null,"oil_content":null,"protein":null,"acid_value":null,"vat_type":null,"price":null}"""


async def extract_lot_data(text: str) -> Dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY не задан — используем простой парсер")
        return _simple_extract(text)

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}]
        )
        raw = message.content[0].text.strip()
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Ошибка AI извлечения: {e}")
        return _simple_extract(text)


def _simple_extract(text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "culture": None, "volume": None, "region": None, "district": None,
        "quality_type": None, "humidity": None, "weed": None, "grain_impurity": None,
        "nature": None, "oil_content": None, "protein": None, "acid_value": None,
        "vat_type": None, "price": None
    }
    text_lower = text.lower()

    cultures = ["ячмень", "пшеница", "подсолнечник", "кукуруза", "соя", "рапс",
                "горох", "гречиха", "просо", "овёс", "овес", "тритикале", "лён", "лен"]
    for c in cultures:
        if c in text_lower:
            result["culture"] = c
            break

    import re
    volume_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:тонн|т\.?|тн\.?)', text_lower)
    if volume_match:
        result["volume"] = float(volume_match.group(1).replace(",", "."))

    region_map = {
        "орловская": "Орловская область",
        "краснодарский": "Краснодарский край",
        "ставропольский": "Ставропольский край",
        "ростовская": "Ростовская область",
        "воронежская": "Воронежская область",
        "белгородская": "Белгородская область",
        "курская": "Курская область",
        "тамбовская": "Тамбовская область",
        "липецкая": "Липецкая область",
        "пензенская": "Пензенская область",
        "саратовская": "Саратовская область",
        "самарская": "Самарская область",
        "волгоградская": "Волгоградская область",
        "астраханская": "Астраханская область",
        "нижегородская": "Нижегородская область",
        "ульяновская": "Ульяновская область",
        "оренбургская": "Оренбургская область",
        "тюменская": "Тюменская область",
        "алтайский": "Алтайский край",
        "новосибирская": "Новосибирская область",
        "омская": "Омская область",
        "челябинская": "Челябинская область",
        "свердловская": "Свердловская область",
        "башкортостан": "Республика Башкортостан",
        "татарстан": "Республика Татарстан",
    }
    for key, full_name in region_map.items():
        if key in text_lower:
            result["region"] = full_name
            break

    if not result["region"]:
        region_match = re.search(
            r'([А-ЯЁ][а-яё]+(ская|ской|ский|ского)\s+(?:область|край|республика))', text
        )
        if region_match:
            result["region"] = region_match.group(1)

    if "без ндс" in text_lower:
        result["vat_type"] = "без НДС"
    elif "с ндс" in text_lower or "с ндс" in text_lower:
        result["vat_type"] = "с НДС"

    humidity_match = re.search(r'влажность[:\s]+(\d+(?:[.,]\d+)?)', text_lower)
    if humidity_match:
        result["humidity"] = float(humidity_match.group(1).replace(",", "."))

    weed_match = re.search(r'сорность[:\s]+(\d+(?:[.,]\d+)?)', text_lower)
    if weed_match:
        result["weed"] = float(weed_match.group(1).replace(",", "."))

    protein_match = re.search(r'протеин[:\s]+(\d+(?:[.,]\d+)?)', text_lower)
    if protein_match:
        result["protein"] = float(protein_match.group(1).replace(",", "."))

    price_match = re.search(r'цена[:\s]+(\d+(?:[.,]\d+)?)', text_lower)
    if price_match:
        result["price"] = float(price_match.group(1).replace(",", "."))

    return result


def determine_next_question(lot) -> Optional[str]:
    culture = lot.culture if hasattr(lot, 'culture') else lot.get('culture')
    volume = lot.volume if hasattr(lot, 'volume') else lot.get('volume')
    region = lot.region if hasattr(lot, 'region') else lot.get('region')
    quality_type = lot.quality_type if hasattr(lot, 'quality_type') else lot.get('quality_type')
    humidity = lot.humidity if hasattr(lot, 'humidity') else lot.get('humidity')
    weed = lot.weed if hasattr(lot, 'weed') else lot.get('weed')
    grain_impurity = lot.grain_impurity if hasattr(lot, 'grain_impurity') else lot.get('grain_impurity')
    vat_type = lot.vat_type if hasattr(lot, 'vat_type') else lot.get('vat_type')
    price = lot.price if hasattr(lot, 'price') else lot.get('price')

    if not culture:
        return "Какую культуру продаёте? (пшеница, ячмень, подсолнечник и т.д.)"
    if not volume:
        return "Какой объём (тонн)?"
    if not region:
        return "Из какого региона?"

    quality_question = _quality_question(culture, quality_type)
    if quality_question:
        return quality_question

    if humidity is None:
        return "Какая влажность (%)?"
    if weed is None:
        return "Какая сорность (%)?"
    if grain_impurity is None:
        return "Зерновая примесь (%)?"
    if vat_type is None:
        return "С НДС или без НДС?"
    if price is None:
        return "Какая цена (руб/тонна)?"
    return None


def _quality_question(culture: str, quality_type: Optional[str]) -> Optional[str]:
    if quality_type:
        return None
    culture_lower = culture.lower()
    if "ячмень" in culture_lower:
        return "Ячмень фуражный или пивоваренный?"
    if "пшеница" in culture_lower:
        return "Пшеница продовольственная (3, 4 класс) или фуражная (5 класс)?"
    if "горох" in culture_lower:
        return "Горох продовольственный или фуражный?"
    return None


def generate_ad_text(lot, contact) -> str:
    culture = lot.culture if hasattr(lot, 'culture') else lot.get('culture', '—')
    volume = lot.volume if hasattr(lot, 'volume') else lot.get('volume')
    region = lot.region if hasattr(lot, 'region') else lot.get('region', '—')
    quality_type = lot.quality_type if hasattr(lot, 'quality_type') else lot.get('quality_type')
    humidity = lot.humidity if hasattr(lot, 'humidity') else lot.get('humidity')
    weed = lot.weed if hasattr(lot, 'weed') else lot.get('weed')
    grain_impurity = lot.grain_impurity if hasattr(lot, 'grain_impurity') else lot.get('grain_impurity')
    nature = lot.nature if hasattr(lot, 'nature') else lot.get('nature')
    protein = lot.protein if hasattr(lot, 'protein') else lot.get('protein')
    oil_content = lot.oil_content if hasattr(lot, 'oil_content') else lot.get('oil_content')
    vat_type = lot.vat_type if hasattr(lot, 'vat_type') else lot.get('vat_type', '')
    price = lot.price if hasattr(lot, 'price') else lot.get('price')

    culture_str = culture or '—'
    if quality_type:
        culture_str = f"{culture_str} {quality_type}"

    volume_str = f"{int(volume)} т" if volume else "объём уточняется"

    indicators = []
    if humidity is not None:
        indicators.append(f"влажность {humidity}%")
    if weed is not None:
        indicators.append(f"сорность {weed}%")
    if grain_impurity is not None:
        indicators.append(f"зерн. примесь {grain_impurity}%")
    if nature is not None:
        indicators.append(f"натура {nature} г/л")
    if protein is not None:
        indicators.append(f"протеин {protein}%")
    if oil_content is not None:
        indicators.append(f"масличность {oil_content}%")

    indicators_str = ", ".join(indicators) if indicators else "показатели уточняются"
    vat_str = f" ({vat_type})" if vat_type else ""
    price_str = f"\n💰 Цена: {int(price)} руб/т{vat_str}" if price else ""

    return (
        f"🌾 ПРОДАМ {culture_str.upper()}\n"
        f"📦 Объём: {volume_str}\n"
        f"📍 Регион: {region}\n"
        f"📊 Показатели: {indicators_str}{price_str}\n\n"
        f"📞 Agro Hub — пишите в личные сообщения"
    )


def get_missing_fields_list(lot) -> list:
    missing = []
    fields_map = {
        "quality_type": "тип качества",
        "humidity": "влажность",
        "weed": "сорность",
        "grain_impurity": "зерновая примесь",
        "nature": "натура",
        "protein": "протеин",
        "oil_content": "масличность",
        "vat_type": "НДС",
        "price": "цена",
    }
    for field, label in fields_map.items():
        val = getattr(lot, field) if hasattr(lot, field) else lot.get(field)
        if val is None:
            missing.append(label)
    return missing
