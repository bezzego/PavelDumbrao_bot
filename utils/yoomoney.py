import aiohttp
import config
import uuid
from urllib.parse import urlencode


def generate_payment_label(user_id: int) -> str:
    """Generate a unique payment label incorporating user_id."""
    # Use UUID4 for uniqueness and embed user id for traceability
    unique_code = uuid.uuid4().hex[:8]  # 8 hex digits
    label = f"{user_id}_{unique_code}"
    return label


async def create_payment_url(amount: int, label: str) -> str:
    """
    Create a YooMoney quickpay payment URL for a given amount and label.
    """
    params = {
        "receiver": config.YOOMONEY_WALLET,
        "quickpay-form": "shop",
        "targets": "Premium Access",  # will be URL-encoded
        "paymentType": "AC",
        "sum": str(amount),
        "label": label,
    }
    base_url = "https://yoomoney.ru/quickpay/confirm.xml"
    query_str = urlencode(params)
    return f"{base_url}?{query_str}"


async def check_payment(label: str) -> bool:
    """
    Check if a payment with the given label has been completed.
    Returns True if payment is found (completed), False if not yet.
    """
    url = "https://yoomoney.ru/api/operation-history"
    headers = {"Authorization": f"Bearer {config.YOOMONEY_TOKEN}"}
    data = {"label": label, "records": 1}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, data=data) as resp:
                if resp.status != 200:
                    return False
                result = await resp.json()
        except Exception:
            return False
    # The API returns an "operations" list if successful
    operations = result.get("operations")
    if not operations:
        return False
    # If at least one operation with this label exists, consider it paid
    # Optionally, check amount and status if needed.
    return True


async def generate_tariff_payment_message(user_id: int, amount: int) -> tuple[str, str]:
    """
    Generate a payment label and a tuple containing:
     - the payment label (string),
     - a plain URL string for the user to click.

    Handlers should create their own inline button using this URL.
    """
    label = generate_payment_label(user_id)
    url = await create_payment_url(amount, label)
    # Return label and the URL (no Markdown formatting)
    return label, url
