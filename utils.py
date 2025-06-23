import re
from datetime import datetime, date, timedelta
from typing import Tuple, Optional, List
from config import DISCOUNT_TIERS, CURRENCY_SYMBOL, CURRENCY

def validate_date_format(date_str: str) -> bool:
    """Validate date string format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False

def parse_date_range(date_range: str) -> Tuple[date, date]:
    """Parse date range string into start and end dates"""
    start_str, end_str = date_range.split(" - ")
    start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d").date()
    end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d").date()
    return start_date, end_date

def calculate_rental_days(start_date: date, end_date: date) -> int:
    """Calculate number of rental days"""
    return (end_date - start_date).days

def calculate_discount_percentage(days: int) -> float:
    """Calculate discount percentage based on rental duration"""
    discount = 0
    for min_days, percentage in sorted(DISCOUNT_TIERS.items()):
        if days >= min_days:
            discount = percentage
    return discount

def calculate_total_price(price_per_day: float, days: int) -> float:
    """Calculate total rental price including discounts"""
    discount_percentage = calculate_discount_percentage(days)
    base_price = price_per_day * days
    discount_amount = base_price * (discount_percentage / 100)
    return base_price - discount_amount

def format_price(price: int) -> str:
    """Format price with thousand separators"""
    return "{:,.0f}".format(price)

def format_date(date_obj: date) -> str:
    """Format date for display"""
    return date_obj.strftime("%B %d, %Y")

def format_datetime(datetime_obj: datetime) -> str:
    """Format datetime for display"""
    return datetime_obj.strftime("%B %d, %Y at %I:%M %p")

def is_valid_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Basic phone validation - can be customized based on requirements
    phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
    return bool(phone_pattern.match(phone))

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))

def sanitize_text(text: str) -> str:
    """Sanitize text input"""
    # Remove potentially dangerous characters
    return re.sub(r'[<>"\']', '', text.strip())

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_car_info(car_data: tuple) -> str:
    """Format car information for display"""
    car_id, model, brand, year, category, price, available, image_url, description = car_data
    
    status = "✅ Available" if available else "❌ Not Available"
    
    return f"""
🚗 *{brand} {model}* ({year})
💰 Price: ${price}/day
📋 Category: {category}
📝 {description}
📊 Status: {status}
    """.strip()

def format_booking_info(booking_data: tuple) -> str:
    """Format booking information for display"""
    booking_id, user_id, car_id, start_date, end_date, total_price, status, payment_method, payment_status, created_at, model, brand, year = booking_data
    
    days = calculate_rental_days(start_date, end_date)
    
    return f"""
📋 *Booking #{booking_id}*
🚗 {brand} {model} ({year})
📅 {format_date(start_date)} to {format_date(end_date)} ({days} days)
💰 Total: {format_price(total_price)}
💳 Payment: {payment_method} ({payment_status})
📊 Status: {status}
    """.strip()

def format_review_info(review_data: tuple) -> str:
    """Format review information for display"""
    review_id, booking_id, user_id, car_id, rating, comment, created_at, first_name, last_name = review_data
    
    reviewer_name = f"{first_name} {last_name}" if first_name and last_name else "Anonymous"
    stars = "⭐" * rating + "☆" * (5 - rating)
    
    return f"""
⭐ {stars}
👤 {reviewer_name}
💬 {comment if comment else "No comment"}
📅 {format_date(created_at)}
    """.strip()

def get_rating_text(rating: int) -> str:
    """Get text description for rating"""
    rating_descriptions = {
        1: "Poor",
        2: "Fair", 
        3: "Good",
        4: "Very Good",
        5: "Excellent"
    }
    return rating_descriptions.get(rating, "Unknown")

def calculate_average_rating(ratings: List[int]) -> float:
    """Calculate average rating"""
    if not ratings:
        return 0.0
    return sum(ratings) / len(ratings)

def is_business_day(check_date: date) -> bool:
    """Check if date is a business day (Monday-Friday)"""
    return check_date.weekday() < 5

def get_next_business_day(start_date: date) -> date:
    """Get next business day"""
    next_day = start_date + timedelta(days=1)
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    return next_day

def validate_rental_period(start_date: date, end_date: date, min_days: int = 1, max_days: int = 30) -> Tuple[bool, str]:
    """Validate rental period"""
    today = date.today()
    
    if start_date < today:
        return False, "Start date cannot be in the past"
    
    if end_date <= start_date:
        return False, "End date must be after start date"
    
    days = calculate_rental_days(start_date, end_date)
    
    if days < min_days:
        return False, f"Minimum rental period is {min_days} day(s)"
    
    if days > max_days:
        return False, f"Maximum rental period is {max_days} days"
    
    return True, "Valid rental period"

def generate_booking_summary(car_data: tuple, start_date: date, end_date: date, total_price: float) -> str:
    """Generate booking summary text"""
    days = calculate_rental_days(start_date, end_date)
    car_id, model, brand, year, category, price, available, image_url, description = car_data
    discount_percentage = calculate_discount_percentage(days)
    
    summary = f"""
📋 *Resumen de Reserva*

🚗 *Vehículo:* {brand} {model} ({year})
📅 *Período:* {format_date(start_date)} a {format_date(end_date)}
⏱️ *Duración:* {days} día(s)
💰 *Tarifa diaria:* {format_price(price)}"""

    if discount_percentage > 0:
        base_price = price * days
        summary += f"""
💫 *Descuento:* {discount_percentage}% por {days} días
💵 *Precio base:* {format_price(base_price)}
💎 *Precio final:* {format_price(total_price)}"""
    else:
        summary += f"""
💵 *Precio total:* {format_price(total_price)}"""

    summary += """

Por favor confirma los detalles de tu reserva."""
    
    return summary.strip()

def format_error_message(error: str) -> str:
    """Format error message for user display"""
    return f"❌ *Error:* {error}\n\nPlease try again or contact support if the problem persists."

def format_success_message(message: str) -> str:
    """Format success message for user display"""
    return f"✅ *Success:* {message}"

def format_warning_message(message: str) -> str:
    """Format warning message for user display"""
    return f"⚠️ *Warning:* {message}"

def format_info_message(message: str) -> str:
    """Format info message for user display"""
    return f"ℹ️ *Info:* {message}"

def create_pagination_keyboard(current_page: int, total_pages: int, base_callback: str) -> List[List]:
    """Create pagination keyboard"""
    keyboard = []
    
    # Previous page button
    if current_page > 1:
        keyboard.append([f"⬅️ Previous", f"{base_callback}_page_{current_page-1}"])
    
    # Page numbers
    page_buttons = []
    for page in range(max(1, current_page-2), min(total_pages+1, current_page+3)):
        if page == current_page:
            page_buttons.append(f"• {page} •")
        else:
            page_buttons.append(f"{page}")
    
    if page_buttons:
        keyboard.append(page_buttons)
    
    # Next page button
    if current_page < total_pages:
        keyboard.append([f"Next ➡️", f"{base_callback}_page_{current_page+1}"])
    
    return keyboard

def validate_car_data(model: str, brand: str, year: int, price: float) -> Tuple[bool, str]:
    """Validate car data"""
    if not model or not brand:
        return False, "Model and brand are required"
    
    if year < 1900 or year > datetime.now().year + 1:
        return False, "Invalid year"
    
    if price <= 0:
        return False, "Price must be greater than 0"
    
    return True, "Valid car data"

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥"
    }
    
    symbol = currency_symbols.get(currency, "$")
    return f"{symbol}{amount:.2f}"

def calculate_discount(original_price: float, discount_percent: float) -> float:
    """Calculate discounted price"""
    return original_price * (1 - discount_percent / 100)

def apply_weekly_discount(daily_price: float, days: int) -> float:
    """Apply weekly discount (10% off for 7+ days)"""
    if days >= 7:
        return daily_price * 0.9
    return daily_price

def apply_monthly_discount(daily_price: float, days: int) -> float:
    """Apply monthly discount (20% off for 30+ days)"""
    if days >= 30:
        return daily_price * 0.8
    return daily_price

def get_date_range_description(start_date: date, end_date: date) -> str:
    """Get human-readable description of date range"""
    days = (end_date - start_date).days
    if days == 1:
        return "1 día"
    return f"{days} días" 