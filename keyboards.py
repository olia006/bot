from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import CAR_CATEGORIES, PAYMENT_METHODS, LANGUAGES, MENU_ITEMS

MENU_TRANSLATIONS = {
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
        'es': '💳 Métodos de Pago',
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
    'change_language': {
        'en': '🌐 Change Language',
        'es': '🌐 Cambiar Idioma',
        'ru': '🌐 Изменить язык'
    },
    'back_to_menu': {
        'en': '🔙 Back to Menu',
        'es': '🔙 Volver al Menú',
        'ru': '🔙 Вернуться в меню'
    },
    'about_us': {
        'en': '🏢 About Us',
        'es': '🏢 Sobre Nosotros',
        'ru': '🏢 О нас'
    }
}

def get_language_keyboard():
    """Language selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")],
        [InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es")],
        [InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard(lang='en'):
    """Main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton(MENU_TRANSLATIONS['make_reservation'][lang], callback_data="make_reservation")],
        [InlineKeyboardButton(MENU_TRANSLATIONS['car_fleet'][lang], callback_data="car_fleet")],
        [InlineKeyboardButton(MENU_TRANSLATIONS['conditions'][lang], callback_data="conditions")],
        [InlineKeyboardButton(MENU_TRANSLATIONS['payment_methods'][lang], callback_data="payment_methods")],
        [InlineKeyboardButton(MENU_TRANSLATIONS['contact_us'][lang], callback_data="contact_us")],
        [InlineKeyboardButton(MENU_TRANSLATIONS['leave_review'][lang], callback_data="leave_review")],
        [InlineKeyboardButton(MENU_TRANSLATIONS['about_us'][lang], callback_data="about_us")],
        [InlineKeyboardButton(MENU_TRANSLATIONS['change_language'][lang], callback_data="change_language")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_menu_keyboard(lang='en'):
    """Back to menu keyboard"""
    keyboard = [[InlineKeyboardButton(MENU_TRANSLATIONS['back_to_menu'][lang], callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

def get_car_categories_keyboard(lang='en'):
    """Car categories keyboard"""
    keyboard = []
    for category_id, category_info in CAR_CATEGORIES.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{category_info['name'][lang]} - ${category_info['price_per_day']}/day",
                callback_data=f"category_{category_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_car_list_keyboard(cars, category=None, lang='en'):
    """Car list keyboard"""
    keyboard = []
    for car in cars:
        car_id, model, brand, year, cat, price, available, image_url, description = car
        keyboard.append([
            InlineKeyboardButton(
                f"{brand} {model} ({year}) - ${price}/day",
                callback_data=f"car_{car_id}"
            )
        ])
    
    # Add navigation buttons
    nav_buttons = []
    if category:
        nav_buttons.append(InlineKeyboardButton("🔙 Back", callback_data="browse_cars"))
    nav_buttons.append(InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
    keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(keyboard)

def get_car_detail_keyboard(car_id, lang='en'):
    """Car detail keyboard"""
    keyboard = [
        [InlineKeyboardButton("📅 Book This Car", callback_data=f"book_car_{car_id}")],
        [InlineKeyboardButton("⭐ View Reviews", callback_data=f"car_reviews_{car_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="browse_cars")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_methods_keyboard(lang='en'):
    """Payment methods keyboard"""
    keyboard = []
    for method in PAYMENT_METHODS:
        keyboard.append([InlineKeyboardButton(method[lang], callback_data=f"payment_{method['en']}")])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_booking_confirmation_keyboard(booking_id, lang='en'):
    """Booking confirmation keyboard"""
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_booking_{booking_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_booking_{booking_id}")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_booking_actions_keyboard(booking_id, lang='en'):
    """Booking actions keyboard"""
    keyboard = [
        [InlineKeyboardButton("❌ Cancel Booking", callback_data=f"cancel_booking_{booking_id}")],
        [InlineKeyboardButton("⭐ Leave Review", callback_data=f"leave_review_{booking_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="my_bookings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_rating_keyboard(lang='en'):
    """Get rating keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("⭐", callback_data="rating_1"),
            InlineKeyboardButton("⭐⭐", callback_data="rating_2"),
            InlineKeyboardButton("⭐⭐⭐", callback_data="rating_3"),
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rating_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rating_5")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contact_keyboard(lang='en'):
    """Contact information keyboard"""
    keyboard = [
        [InlineKeyboardButton("📧 Email", callback_data="email_support")],
        [InlineKeyboardButton("📱 Phone", callback_data="phone_support")],
        [InlineKeyboardButton("🌐 Website", callback_data="website")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_conditions_keyboard(lang='en'):
    """Conditions keyboard"""
    keyboard = [
        [InlineKeyboardButton("📖 Rental Terms", callback_data="rental_terms")],
        [InlineKeyboardButton("💰 Pricing", callback_data="pricing_info")],
        [InlineKeyboardButton("📋 Requirements", callback_data="requirements")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_date_keyboard(lang='en'):
    """Date selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("📅 Select Start Date", callback_data="select_start_date")],
        [InlineKeyboardButton("📅 Select End Date", callback_data="select_end_date")],
        [InlineKeyboardButton("🔙 Back", callback_data="browse_cars")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_share_contact_keyboard(lang='en'):
    """Share contact information keyboard"""
    keyboard = [[KeyboardButton("📱 Share Contact", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_remove_keyboard():
    """Remove keyboard"""
    return ReplyKeyboardMarkup([], resize_keyboard=True) 