import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# Admin Configuration
ADMIN_CHAT_ID = "-4938843558"  # Chat ID where booking requests will be sent
REVIEW_CHAT_ID = "-4820958392"  # Chat ID where reviews will be sent

try:
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))
except ValueError:
    raise ValueError("ADMIN_USER_ID must be a valid integer")

# Language Configuration
LANGUAGES = {
    'en': 'English 🇬🇧',
    'es': 'Español 🇪🇸',
    'ru': 'Русский 🇷🇺'
}

# Database Configuration
DATABASE_PATH = 'car_rental.db'

# Car Categories
CAR_CATEGORIES = {
    'economy': {
        'name': {
            'en': 'Economy',
            'es': 'Económico',
            'ru': 'Эконом'
        },
        'price_per_day': 49990,
        'description': {
            'en': 'Efficient and economical vehicles',
            'es': 'Vehículos económicos y eficientes',
            'ru': 'Экономичные автомобили'
        }
    },
    'suv': {
        'name': {
            'en': 'SUV',
            'es': 'SUV',
            'ru': 'Внедорожник'
        },
        'price_per_day': 71990,
        'description': {
            'en': 'Spacious SUVs ideal for family and trips',
            'es': 'SUVs espaciosos ideales para familia y viajes',
            'ru': 'Просторные внедорожники для семьи и путешествий'
        }
    },
    'premium': {
        'name': {
            'en': 'Premium',
            'es': 'Premium',
            'ru': 'Премиум'
        },
        'price_per_day': 149990,
        'description': {
            'en': 'Luxury vehicles with premium features',
            'es': 'Vehículos de lujo con características premium',
            'ru': 'Люксовые автомобили премиум-класса'
        }
    }
}

# Booking Status
BOOKING_STATUS = {
    'pending': {'en': 'Pending', 'es': 'Pendiente', 'ru': 'Ожидание'},
    'confirmed': {'en': 'Confirmed', 'es': 'Confirmado', 'ru': 'Подтверждено'},
    'completed': {'en': 'Completed', 'es': 'Completado', 'ru': 'Завершено'},
    'cancelled': {'en': 'Cancelled', 'es': 'Cancelado', 'ru': 'Отменено'}
}

# Payment Methods
PAYMENT_METHODS = [
    {'en': 'Credit Card', 'es': 'Tarjeta de Crédito', 'ru': 'Кредитная карта'},
    {'en': 'Debit Card', 'es': 'Tarjeta de Débito', 'ru': 'Дебетовая карта'},
    {'en': 'Bank Transfer', 'es': 'Transferencia Bancaria', 'ru': 'Банковский перевод'},
    {'en': 'WebPay', 'es': 'WebPay', 'ru': 'WebPay'}
]

# Menu Items
MENU_ITEMS = {
    'make_reservation': {
        'en': '🚗 Make a Reservation',
        'es': '🚗 Hacer una Reserva',
        'ru': '🚗 Забронировать'
    },
    'car_fleet': {
        'en': '🚙 Car Fleet',
        'es': '🚙 Flota de Autos',
        'ru': '🚙 Автопарк'
    },
    'conditions': {
        'en': '📋 Conditions',
        'es': '📋 Condiciones',
        'ru': '📋 Условия'
    },
    'payment_methods': {
        'en': '💳 Payment Methods',
        'es': '💳 Formas de Pago',
        'ru': '💳 Способы оплаты'
    },
    'contact_us': {
        'en': '📞 Contact Us',
        'es': '📞 Contáctenos',
        'ru': '📞 Связаться с нами'
    },
    'leave_review': {
        'en': '⭐ Leave Review',
        'es': '⭐ Dejar Reseña',
        'ru': '⭐ Оставить Отзыв'
    },
    'about_us': {
        'en': '🏢 About Us',
        'es': '🏢 Sobre Nosotros',
        'ru': '🏢 О нас'
    }
}

# Discount Tiers (days: percentage)
DISCOUNT_TIERS = {
    3: 15,   # 15% off for 3+ days
    30: 25,  # 25% off for 30+ days
    90: 35   # 35% off for 90+ days
}

# Currency Configuration
CURRENCY = 'CLP'
CURRENCY_SYMBOL = '$' 