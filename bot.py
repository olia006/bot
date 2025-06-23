import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
import os

from config import BOT_TOKEN, CAR_CATEGORIES, BOOKING_STATUS, LANGUAGES, MENU_ITEMS, ADMIN_CHAT_ID, REVIEW_CHAT_ID
from database import Database
from keyboards import *
from utils import format_price, validate_date_format, parse_date_range, calculate_total_price

# Create images directory if it doesn't exist
os.makedirs('public/images', exist_ok=True)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_LANGUAGE, CHOOSING_CATEGORY, CHOOSING_CAR, SELECTING_DATES, VIEWING_PRIVACY, ENTERING_PERSONAL_INFO, CONFIRMING_BOOKING, SELECTING_RATING, ENTERING_REVIEW = range(9)

class CarRentalBot:
    def __init__(self):
        self.db = Database()
        self.user_states = {}  # Store user booking states
        self.user_languages = {}  # Store user language preferences
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        try:
            print(f"🔍 Chat ID from start command: {update.effective_chat.id}")
            logger.info(f"Chat ID from start command: {update.effective_chat.id}")
            
            message = """
🌐 *Welcome to CarRental Bot!*

Please select your preferred language:
Por favor, seleccione su idioma:
Пожалуйста, выберите язык:
"""
            if update.message:
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_language_keyboard()
                )
            elif update.callback_query:
                await update.callback_query.message.edit_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_language_keyboard()
                )
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            raise
    
    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection"""
        try:
            query = update.callback_query
            print(f"🔍 Chat ID from language selection: {update.effective_chat.id}")
            logger.info(f"Chat ID from language selection: {update.effective_chat.id}")
            
            await query.answer()
            
            language = query.data.split('_')[1]
            user = query.from_user
            
            # Store user's language preference
            self.user_languages[user.id] = language
            
            welcome_messages = {
                'en': f"Welcome {user.first_name}! I'm here to help you rent the perfect car.",
                'es': f"¡Bienvenido {user.first_name}! Estoy aquí para ayudarte a alquilar el auto perfecto.",
                'ru': f"Добро пожаловать, {user.first_name}! Я помогу вам арендовать идеальный автомобиль."
            }
            
            await query.message.edit_text(
                welcome_messages[language],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard(language)
            )
        except Exception as e:
            logger.error(f"Error in language selection: {e}")
            raise
    
    async def change_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language change request"""
        query = update.callback_query
        await query.answer()
        
        welcome_message = """
🌐 *Select Your Language*
Seleccione su idioma
Выберите язык
        """
        
        await query.edit_message_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_language_keyboard()
        )
        
        return CHOOSING_LANGUAGE
    
    async def main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle main menu callbacks"""
        try:
            query = update.callback_query
            print(f"🔍 Chat ID from main menu: {update.effective_chat.id}")
            logger.info(f"Chat ID from main menu: {update.effective_chat.id}")
            
            await query.answer()
            
            if query.data == "make_reservation":
                await self.start_booking_process(update, context)
            elif query.data == "car_fleet":
                await self.show_car_fleet(update, context)
            elif query.data == "conditions":
                await self.show_conditions(update, context)
            elif query.data == "payment_methods":
                await self.show_payment_methods(update, context)
            elif query.data == "contact_us":
                await self.show_contact_info(update, context)
            elif query.data == "change_language":
                await self.change_language(update, context)
            elif query.data == "main_menu":
                await self.show_main_menu(update, context)
        except Exception as e:
            logger.error(f"Error in main menu: {e}")
            raise
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu"""
        try:
            query = update.callback_query
            if query:
                try:
                    await query.answer()
                except Exception as e:
                    logger.error(f"Error answering callback query: {e}")
                    # Continue even if answering the query fails
            
            language = self.get_user_language(update.effective_user.id)
            
            messages = {
                'en': "*Main Menu*\n\nWhat would you like to do?",
                'es': "*Menú Principal*\n\n¿Qué te gustaría hacer?",
                'ru': "*Главное меню*\n\nЧто бы вы хотели сделать?"
            }

            if query:
                try:
                    await query.message.edit_text(
                        messages[language],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_main_menu_keyboard(language)
                    )
                except Exception as edit_error:
                    logger.error(f"Error editing message: {edit_error}")
                    # If editing fails, try sending a new message
                    await query.message.reply_text(
                        messages[language],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_main_menu_keyboard(language)
                    )
            else:
                # If no query (e.g., command), send new message
                await update.message.reply_text(
                    messages[language],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_main_menu_keyboard(language)
                )
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            try:
                # Try to send a new message if all else fails
                if update.effective_chat:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Please use /start to show the menu.",
                        reply_markup=get_main_menu_keyboard('en')
                    )
            except Exception as e2:
                logger.error(f"Error sending fallback message: {e2}")
    
    async def show_car_fleet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show car fleet"""
        try:
            query = update.callback_query
            await query.answer()
            
            language = self.get_user_language(query.from_user.id)

            # Price labels in different languages
            price_labels = {
                'en': {
                    'prices': 'Prices',
                    'currency': 'CLP',
                    'per_day': 'per day',
                    'week': '6 days (15% off)',
                    'month': '30 days (25% off)',
                    'threemonth': '3+ months (35% off)'
                },
                'es': {
                    'prices': 'Precios',
                    'currency': 'CLP',
                    'per_day': 'por día',
                    'week': '6 días (15% desc.)',
                    'month': '30 días (25% desc.)',
                    'threemonth': '+3 meses (35% desc.)'
                },
                'ru': {
                    'prices': 'Цены',
                    'currency': 'CLP',
                    'per_day': 'в день',
                    'week': '6 дней (скидка 15%)',
                    'month': '30 дней (скидка 25%)',
                    'threemonth': '3+ месяца (скидка 35%)'
                }
            }

            # Car categories with their images and pricing
            cars = {
                'premium': [
                    {
                        'name': 'GAC All New GS8 (White)',
                        'name_es': 'GAC All New GS8 (Blanco)',
                        'name_ru': 'GAC All New GS8 (Белый)',
                        'price': '149.990',
                        'week_price': '764.946',
                        'month_price': '3.374.775',
                        'threemonth_price': '2.924.805',
                        'description': {
                            'en': 'Large SUV, 7 seats',
                            'es': 'SUV grande, 7 asientos',
                            'ru': 'Большой внедорожник, 7 мест'
                        },
                        'image': 'public/images/gacfull.png'
                    },
                    {
                        'name': 'GAC All New GS8 (Black)',
                        'name_es': 'GAC All New GS8 (Negro)',
                        'name_ru': 'GAC All New GS8 (Черный)',
                        'price': '149.990',
                        'week_price': '764.946',
                        'month_price': '3.374.775',
                        'threemonth_price': '2.924.805',
                        'description': {
                            'en': 'Large SUV, 7 seats',
                            'es': 'SUV grande, 7 asientos',
                            'ru': 'Большой внедорожник, 7 мест'
                        },
                        'image': 'public/images/gaccomfort.PNG'
                    },
                    {
                        'name': 'Lexus RX 450 H',
                        'name_es': 'Lexus RX 450 H',
                        'name_ru': 'Lexus RX 450 H',
                        'price': '135.990',
                        'week_price': '692.343',
                        'month_price': '3.059.775',
                        'threemonth_price': '2.653.335',
                        'description': {
                            'en': 'Premium hybrid SUV',
                            'es': 'SUV premium híbrido',
                            'ru': 'Премиум гибридный внедорожник'
                        },
                        'image': 'public/images/lexusrx.png'
                    }
                ],
                'economy': [
                    {
                        'name': 'Chevrolet Cavalier',
                        'name_es': 'Chevrolet Cavalier',
                        'name_ru': 'Chevrolet Cavalier',
                        'price': '49.990',
                        'week_price': '254.943',
                        'month_price': '1.124.775',
                        'threemonth_price': '974.805',
                        'description': {
                            'en': 'Compact sedan',
                            'es': 'Sedán compacto',
                            'ru': 'Компактный седан'
                        },
                        'image': 'public/images/chevrolett.png'
                    },
                    {
                        'name': 'Cherry Tiggo 2 Pro Max',
                        'name_es': 'Cherry Tiggo 2 Pro Max',
                        'name_ru': 'Cherry Tiggo 2 Pro Max',
                        'price': '49.990',
                        'week_price': '254.943',
                        'month_price': '1.124.775',
                        'threemonth_price': '974.805',
                        'description': {
                            'en': 'Compact SUV',
                            'es': 'SUV compacto',
                            'ru': 'Компактный внедорожник'
                        },
                        'image': 'public/images/cherry.PNG'
                    },
                    {
                        'name': 'Honda Accord',
                        'name_es': 'Honda Accord',
                        'name_ru': 'Honda Accord',
                        'price': '34.990',
                        'week_price': '178.443',
                        'month_price': '787.275',
                        'threemonth_price': '682.635',
                        'description': {
                            'en': 'Mid-size/full-size sedan',
                            'es': 'Sedán mediano/full-size',
                            'ru': 'Средний/полноразмерный седан'
                        },
                        'image': 'public/images/honda.png'
                    },
                    {
                        'name': 'Mazda 6',
                        'name_es': 'Mazda 6',
                        'name_ru': 'Mazda 6',
                        'price': '49.990',
                        'week_price': '254.943',
                        'month_price': '1.124.775',
                        'threemonth_price': '974.805',
                        'description': {
                            'en': 'Mid-size sedan',
                            'es': 'Sedán mediano',
                            'ru': 'Средний седан'
                        },
                        'image': 'public/images/mazda6.png'
                    },
                    {
                        'name': 'Subaru Impreza',
                        'name_es': 'Subaru Impreza',
                        'name_ru': 'Subaru Impreza',
                        'price': '49.990',
                        'week_price': '254.943',
                        'month_price': '1.124.775',
                        'threemonth_price': '974.805',
                        'description': {
                            'en': 'Compact hatchback',
                            'es': 'Hatchback compacto',
                            'ru': 'Компактный хэтчбек'
                        },
                        'image': 'public/images/Impreza.jpeg'
                    },
                    {
                        'name': 'Lexus ES 350',
                        'name_es': 'Lexus ES 350',
                        'name_ru': 'Lexus ES 350',
                        'price': '54.990',
                        'week_price': '280.743',
                        'month_price': '1.237.275',
                        'threemonth_price': '1.073.535',
                        'description': {
                            'en': 'Premium sedan',
                            'es': 'Sedán premium',
                            'ru': 'Премиум седан'
                        },
                        'image': 'public/images/lexuses.png'
                    }
                ],
                'suv': [
                    {
                        'name': 'Mazda CX-9',
                        'name_es': 'Mazda CX-9',
                        'name_ru': 'Mazda CX-9',
                        'price': '119.990',
                        'week_price': '622.743',
                        'month_price': '2.699.775',
                        'threemonth_price': '2.339.805',
                        'description': {
                            'en': 'Large SUV, 7 seats',
                            'es': '7 asientos, SUV grande',
                            'ru': 'Большой внедорожник, 7 мест'
                        },
                        'image': 'public/images/mazda9.png'
                    },
                    {
                        'name': 'Mitsubishi Outlander',
                        'name_es': 'Mitsubishi Outlander',
                        'name_ru': 'Mitsubishi Outlander',
                        'price': '71.990',
                        'week_price': '373.143',
                        'month_price': '1.619.775',
                        'threemonth_price': '1.405.035',
                        'description': {
                            'en': 'Mid-size SUV',
                            'es': 'SUV mediano',
                            'ru': 'Средний внедорожник'
                        },
                        'image': 'public/images/mitsubishi.png'
                    },
                    {
                        'name': 'Subaru Outback',
                        'name_es': 'Subaru Outback',
                        'name_ru': 'Subaru Outback',
                        'price': '64.990',
                        'week_price': '336.543',
                        'month_price': '1.464.775',
                        'threemonth_price': '1.264.305',
                        'description': {
                            'en': 'Wagon/Crossover 4x4',
                            'es': 'Wagon/Crossover 4x4',
                            'ru': 'Универсал/Кроссовер 4x4'
                        },
                        'image': 'public/images/subaruoutback.png'
                    },
                    {
                        'name': 'Toyota RAV4',
                        'name_es': 'Toyota RAV4',
                        'name_ru': 'Toyota RAV4',
                        'price': '71.990',
                        'week_price': '373.143',
                        'month_price': '1.619.775',
                        'threemonth_price': '1.405.035',
                        'description': {
                            'en': 'Compact SUV',
                            'es': 'SUV compacto',
                            'ru': 'Компактный внедорожник'
                        },
                        'image': 'public/images/toyota.png'
                    }
                ]
            }

            # Category titles in different languages
            category_titles = {
                'premium': {
                    'en': '🎯 Premium Category',
                    'es': '🎯 Categoría Premium',
                    'ru': '🎯 Премиум Категория'
                },
                'economy': {
                    'en': '💰 Economy Category',
                    'es': '💰 Categoría Económica',
                    'ru': '💰 Эконом Категория'
                },
                'suv': {
                    'en': '🚙 SUV Category',
                    'es': '🚙 Categoría SUV',
                    'ru': '🚙 Категория Внедорожников'
                }
            }

            # Price period descriptions
            price_periods = {
                'en': {
                    'day': 'per day',
                    'week': '6 days (15% off)',
                    'month': '30 days (25% off)',
                    'threemonth': '3+ months (35% off)'
                },
                'es': {
                    'day': 'por día',
                    'week': '6 días (15% desc.)',
                    'month': '30 días (25% desc.)',
                    'threemonth': '+3 meses (35% desc.)'
                },
                'ru': {
                    'day': 'в день',
                    'week': '6 дней (скидка 15%)',
                    'month': '30 дней (скидка 25%)',
                    'threemonth': '3+ месяца (скидка 35%)'
                }
            }

            # Send a message for each car with its photo
            first_message = True
            for category, category_cars in cars.items():
                # Send category header
                header = f"*{category_titles[category][language]}*"
                if first_message:
                    await query.edit_message_text(header, parse_mode=ParseMode.MARKDOWN)
                    first_message = False
                else:
                    await query.message.reply_text(header, parse_mode=ParseMode.MARKDOWN)

                # Send each car in the category
                for car in category_cars:
                    car_name = car[f'name_{language}'] if language in ['es', 'ru'] else car['name']
                    message = f"""
{car_name}
📝 {car['description'][language]}

💰 {price_labels[language]['prices']}:
• {car['price']} {price_labels[language]['currency']} - {price_labels[language]['per_day']}
• {car['week_price']} {price_labels[language]['currency']} - {price_labels[language]['week']}
• {car['month_price']} {price_labels[language]['currency']} - {price_labels[language]['month']}
• {car['threemonth_price']} {price_labels[language]['currency']} - {price_labels[language]['threemonth']}
"""
                    with open(car['image'], 'rb') as photo:
                        await query.message.reply_photo(
                            photo=photo,
                            caption=message,
                            parse_mode=ParseMode.MARKDOWN
                        )

            # Send final message with back button
            await query.message.reply_text(
                "_Click the button below to return to the main menu_",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_back_to_menu_keyboard(language)
            )

        except Exception as e:
            logger.error(f"Error showing car fleet: {e}")
            raise
    
    async def show_conditions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show rental conditions"""
        try:
            query = update.callback_query
            await query.answer()
            
            language = self.get_user_language(query.from_user.id)
            
            messages = {
                'en': """
*📋 Rental Terms*

*Requirements:*
• 🪪 Valid driver's license
• 🎂 Minimum age: 21 years
• 💳 Credit card required for deposit (for Latin American residents)
  _Alternative documentation may be accepted without a credit card - please check with our manager_
• ✅ No credit cards required for international tourists
• 🛂 Valid passport/ID

*Insurance:*
• ✅ Basic insurance included
• ➕ Additional coverage available

*Fuel Policy:*
• ⛽ Full-to-full: receive with a full tank, return with a full tank

*Mileage:*
• ♾️ Unlimited mileage plan included
• 📏 Limited mileage plans also available

*Deposit:*
• 💳 Security deposit held on credit card (for Latin American residents)
• 💵 Deposit amount: from 550,000 to 1,000,000 CLP (depending on vehicle category)""",

                'es': """
*📋 Términos de Alquiler*

*Requisitos:*
• 🪪 Licencia de conducir válida
• 🎂 Edad mínima: 21 años
• 💳 Tarjeta de crédito requerida para depósito (para residentes de América Latina)
  _Se puede aceptar documentación alternativa sin tarjeta de crédito - consulte con nuestro gerente_
• ✅ No se requieren tarjetas de crédito para turistas internacionales
• 🛂 Pasaporte/DNI válido

*Seguro:*
• ✅ Seguro básico incluido
• ➕ Coberturas adicionales disponibles

*Política de Combustible:*
• ⛽ Tanque lleno a lleno: recibe con tanque lleno, devuelve con tanque lleno

*Kilometraje:*
• ♾️ Plan de kilometraje ilimitado incluido
• 📏 Planes de kilometraje limitado también disponibles

*Depósito:*
• 💳 Depósito de seguridad retenido en tarjeta de crédito (para residentes de América Latina)
• 💵 Monto del depósito: desde 550.000 hasta 1.000.000 CLP (según categoría del vehículo)""",

                'ru': """
*📋 Условия Аренды*

*Требования:*
• 🪪 Действующие водительские права
• 🎂 Минимальный возраст: 21 год
• 💳 Требуется кредитная карта для депозита (для жителей Латинской Америки)
  _Возможно принятие альтернативной документации без кредитной карты - уточняйте у менеджера_
• ✅ Для иностранных туристов кредитные карты не требуются
• 🛂 Действующий паспорт/удостоверение личности

*Страховка:*
• ✅ Базовая страховка включена
• ➕ Доступно дополнительное покрытие

*Топливная Политика:*
• ⛽ Полный бак-полный бак: получаете с полным баком, возвращаете с полным баком

*Пробег:*
• ♾️ Включен план с неограниченным пробегом
• 📏 Также доступны планы с ограниченным пробегом

*Депозит:*
• 💳 Страховой депозит на кредитной карте (для жителей Латинской Америки)
• 💵 Сумма депозита: от 550.000 до 1.000.000 CLP (в зависимости от категории автомобиля)"""
            }
            
            await query.message.edit_text(
                messages[language],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_back_to_menu_keyboard(language)
            )
        except Exception as e:
            logger.error(f"Error showing conditions: {e}")
            raise
    
    async def show_payment_methods(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show payment methods"""
        try:
            query = update.callback_query
            await query.answer()
            
            language = self.get_user_language(query.from_user.id)
            
            messages = {
                'en': """
*💳 Payment Methods*

We accept the following payment methods:

*For Latin American Residents:*
• 💳 Credit Cards
• 💳 Debit Cards
• 🏦 Bank Transfer
• 🌐 WebPay

*For International Tourists:*
• 💵 Cash (USD, EUR, RUB)
• 🏦 International Wire Transfer
• 🌐 PayPal
• 💎 USDT (Tether)
  _Network options: TRC20, ERC20, BEP20_

*Exchange Rates:*
• Daily rates according to the Central Bank
• Cryptocurrency rates according to Binance""",

                'es': """
*💳 Métodos de Pago*

Aceptamos los siguientes métodos de pago:

*Para Residentes de América Latina:*
• 💳 Tarjetas de Crédito
• 💳 Tarjetas de Débito
• 🏦 Transferencia Bancaria
• 🌐 WebPay

*Para Turistas Internacionales:*
• 💵 Efectivo (USD, EUR, RUB)
• 🏦 Transferencia Internacional
• 🌐 PayPal
• 💎 USDT (Tether)
  _Opciones de red: TRC20, ERC20, BEP20_

*Tipos de Cambio:*
• Tasas diarias según el Banco Central
• Tasas de criptomonedas según Binance""",

                'ru': """
*💳 Способы Оплаты*

Мы принимаем следующие способы оплаты:

*Для Жителей Латинской Америки:*
• 💳 Кредитные карты
• 💳 Дебетовые карты
• 🏦 Банковский перевод
• 🌐 WebPay

*Для Иностранных Туристов:*
• 💵 Наличные (USD, EUR, RUB)
• 🏦 Международный банковский перевод
• 🌐 PayPal
• 💎 USDT (Tether)
  _Варианты сети: TRC20, ERC20, BEP20_

*Курсы Обмена:*
• Ежедневные курсы по Центральному Банку
• Курсы криптовалют по Binance"""
            }
            
            await query.message.edit_text(
                messages[language],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_back_to_menu_keyboard(language)
            )
        except Exception as e:
            logger.error(f"Error showing payment methods: {e}")
            raise
    
    async def show_contact_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show contact information"""
        try:
            query = update.callback_query
            await query.answer()
            
            language = self.get_user_language(query.from_user.id)

            # Contact info for each language
            if language == 'ru':
                text = "🚗 RentCar Chile\n\n"
                text += "📍 Адрес: Santiago, Chile\n"
                text += "📱 WhatsApp: +56982567485\n"
                text += "💬 Telegram: @rentcar_chile\n\n"
                text += "💳 Способы оплаты:\n"
                text += "• Наличные (USD, EUR, RUB)\n"
                text += "• USDT (TRC20, ERC20, BEP20)\n"
                text += "• Банковский перевод\n\n"
                text += "✅ Говорим на русском языке\n"
                text += "⏰ Работаем без выходных"

                keyboard = [
                    [InlineKeyboardButton("💬 Telegram", url="https://t.me/rentcar_chile")],
                    [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/56982567485")],
                    [InlineKeyboardButton("🔙 Вернуться в меню", callback_data="main_menu")]
                ]
            elif language == 'es':
                text = "🚗 RentCar Chile\n\n"
                text += "📍 Dirección: Santiago, Chile\n"
                text += "📱 WhatsApp: +56921701913\n\n"
                text += "💳 Métodos de pago:\n"
                text += "• Efectivo\n"
                text += "• Transferencia bancaria\n"
                text += "• Tarjetas de crédito/débito\n"
                text += "• WebPay\n\n"
                text += "✅ Hablamos español e inglés\n"
                text += "⏰ Abierto todos los días"

                keyboard = [
                    [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/56921701913")],
                    [InlineKeyboardButton("🔙 Volver al Menú", callback_data="main_menu")]
                ]
            else:  # English
                text = "🚗 RentCar Chile\n\n"
                text += "📍 Address: Santiago, Chile\n"
                text += "📱 WhatsApp: +56921701913\n\n"
                text += "💳 Payment methods:\n"
                text += "• Cash\n"
                text += "• Bank transfer\n"
                text += "• Credit/Debit cards\n"
                text += "• WebPay\n\n"
                text += "✅ We speak English and Spanish\n"
                text += "⏰ Open every day"

                keyboard = [
                    [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/56921701913")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
                ]

            await query.message.edit_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            logger.error(f"Error in contact info: {e}")
            try:
                # Simplified fallback message
                if language == 'ru':
                    text = "🚗 RentCar Chile\n"
                    text += "📱 WhatsApp: +56982567485\n"
                    text += "💬 Telegram: @rentcar_chile"
                    keyboard = [
                        [InlineKeyboardButton("💬 Telegram", url="https://t.me/rentcar_chile")],
                        [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/56982567485")],
                        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
                    ]
                else:
                    text = "🚗 RentCar Chile\n"
                    text += "📱 WhatsApp: +56921701913"
                    keyboard = [
                        [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/56921701913")],
                        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
                    ]
                
                await query.message.edit_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e2:
                logger.error(f"Error in fallback contact info: {e2}")
                await query.answer("Please try again later.", show_alert=True)
    
    async def show_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show car categories"""
        query = update.callback_query
        await query.answer()
        
        message = "*Choose a car category:*\n\n"
        for category_id, category_info in CAR_CATEGORIES.items():
            message += f"• *{category_info['name']}* - ${category_info['price_per_day']}/day\n"
            message += f"  {category_info['description']}\n\n"
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_car_categories_keyboard()
        )
    
    async def show_cars_in_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show cars in selected category"""
        try:
            query = update.callback_query
            await query.answer()
            
            category = query.data.split('_')[1]
            language = self.get_user_language(query.from_user.id)
            
            messages = {
                'en': f"*Available {CAR_CATEGORIES[category]['name'][language]} Cars*\n\nPlease select a car:",
                'es': f"*Autos {CAR_CATEGORIES[category]['name'][language]} Disponibles*\n\nPor favor seleccione un auto:",
                'ru': f"*Доступные Автомобили {CAR_CATEGORIES[category]['name'][language]}*\n\nПожалуйста, выберите автомобиль:"
            }
            
            # Get cars for this category
            cars = {
                'premium': [
                    {'id': 'gac_white', 'name': 'GAC All New GS8 (White)', 'price': '149.990'},
                    {'id': 'gac_black', 'name': 'GAC All New GS8 (Black)', 'price': '149.990'},
                    {'id': 'lexus_rx', 'name': 'Lexus RX 450 H', 'price': '135.990'}
                ],
                'economy': [
                    {'id': 'chevrolet', 'name': 'Chevrolet Cavalier', 'price': '49.990'},
                    {'id': 'cherry', 'name': 'Cherry Tiggo 2 Pro Max', 'price': '49.990'},
                    {'id': 'honda', 'name': 'Honda Accord', 'price': '34.990'},
                    {'id': 'mazda6', 'name': 'Mazda 6', 'price': '49.990'},
                    {'id': 'subaru', 'name': 'Subaru Impreza', 'price': '49.990'},
                    {'id': 'lexus_es', 'name': 'Lexus ES 350', 'price': '54.990'}
                ],
                'suv': [
                    {'id': 'mazda_cx9', 'name': 'Mazda CX-9', 'price': '119.990'},
                    {'id': 'mitsubishi', 'name': 'Mitsubishi Outlander', 'price': '71.990'},
                    {'id': 'subaru_out', 'name': 'Subaru Outback', 'price': '64.990'},
                    {'id': 'toyota', 'name': 'Toyota RAV4', 'price': '71.990'}
                ]
            }
            
            # Create keyboard with cars
            keyboard = []
            for car in cars[category]:
                keyboard.append([InlineKeyboardButton(
                    f"{car['name']} - {car['price']} CLP/day",
                    callback_data=f"car_{car['id']}"
                )])
            keyboard.append([InlineKeyboardButton(MENU_TRANSLATIONS['back_to_menu'][language], callback_data="main_menu")])
            
            await query.message.edit_text(
                messages[language],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return CHOOSING_CAR
            
        except Exception as e:
            logger.error(f"Error showing cars in category: {e}")
            raise

    async def handle_car_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle car selection and ask for dates"""
        try:
            query = update.callback_query
            await query.answer()
            
            car_id = query.data.split('_')[1]
            context.user_data['selected_car'] = car_id
            
            language = self.get_user_language(query.from_user.id)
            
            messages = {
                'en': """*📅 Select Dates*

Please enter your desired rental dates in the format:
DD.MM.YYYY - DD.MM.YYYY

Example: 25.12.2023 - 30.12.2023""",
                'es': """*📅 Seleccionar Fechas*

Por favor ingrese las fechas deseadas en el formato:
DD.MM.YYYY - DD.MM.YYYY

Ejemplo: 25.12.2023 - 30.12.2023""",
                'ru': """*📅 Выбор Дат*

Пожалуйста, введите желаемые даты аренды в формате:
DD.MM.YYYY - DD.MM.YYYY

Пример: 25.12.2023 - 30.12.2023"""
            }
            
            keyboard = [[InlineKeyboardButton(MENU_TRANSLATIONS['back_to_menu'][language], callback_data="main_menu")]]
            
            await query.message.edit_text(
                messages[language],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return SELECTING_DATES
            
        except Exception as e:
            logger.error(f"Error handling car selection: {e}")
            raise

    async def handle_dates_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle dates input and show privacy policy"""
        try:
            if not update.message:
                return SELECTING_DATES
            
            text = update.message.text
            print(f"🔍 Processing dates: {text}")
            
            try:
                start_date_str, end_date_str = text.split(' - ')
                start_date = datetime.strptime(start_date_str.strip(), '%d.%m.%Y')
                end_date = datetime.strptime(end_date_str.strip(), '%d.%m.%Y')
                
                # Calculate full 24h periods
                duration_timedelta = end_date - start_date
                duration = duration_timedelta.days  # This will give us full 24h periods
                
                if duration < 1:
                    raise ValueError("Invalid duration")
                
                print(f"✅ Valid dates: {start_date} - {end_date}, duration: {duration} days")
                
                # Store dates and duration
                context.user_data['dates'] = text
                context.user_data['duration'] = duration
                context.user_data['start_date'] = start_date.strftime('%d.%m.%Y')
                context.user_data['end_date'] = end_date.strftime('%d.%m.%Y')
                
                # Get car price and calculate total with discounts
                car_id = context.user_data.get('selected_car')
                base_price = 0
                
                # Find car price from our categories
                for category, cars in {
                    'premium': [
                        {'id': 'gac_white', 'price': 149990},
                        {'id': 'gac_black', 'price': 149990},
                        {'id': 'lexus_rx', 'price': 135990}
                    ],
                    'economy': [
                        {'id': 'chevrolet', 'price': 49990},
                        {'id': 'cherry', 'price': 49990},
                        {'id': 'honda', 'price': 34990},
                        {'id': 'mazda6', 'price': 49990},
                        {'id': 'subaru', 'price': 49990},
                        {'id': 'lexus_es', 'price': 54990}
                    ],
                    'suv': [
                        {'id': 'mazda_cx9', 'price': 119990},
                        {'id': 'mitsubishi', 'price': 71990},
                        {'id': 'subaru_out', 'price': 64990},
                        {'id': 'toyota', 'price': 71990}
                    ]
                }.items():
                    for car in cars:
                        if car['id'] == car_id:
                            base_price = car['price']
                            break
                
                # Calculate discount
                discount = 0
                if duration >= 90:  # 3+ months
                    discount = 35
                elif duration >= 30:  # 1 month
                    discount = 25
                elif duration >= 6:  # 6+ days
                    discount = 15
                
                # Calculate total price
                daily_price = base_price
                total_price = daily_price * duration
                if discount > 0:
                    total_price = total_price * (1 - discount/100)
                
                # Store prices in context
                context.user_data['base_price'] = base_price
                context.user_data['total_price'] = total_price
                context.user_data['discount'] = discount
                
                # Show privacy policy and ask for agreement
                language = self.get_user_language(update.effective_user.id)
                print(f"🌐 User language: {language}")
                
                messages = {
                    'en': """*📋 Privacy Agreement Required*

Before proceeding with your booking, we need to collect some personal information.

Please review our privacy policy and confirm your agreement to continue.""",
                    'es': """*📋 Acuerdo de Privacidad Requerido*

Antes de continuar con su reserva, necesitamos recopilar algunos datos personales.

Por favor revise nuestra política de privacidad y confirme su acuerdo para continuar.""",
                    'ru': """*📋 Требуется Согласие с Политикой Конфиденциальности*

Перед продолжением бронирования нам необходимо собрать некоторые личные данные.

Пожалуйста, ознакомьтесь с нашей политикой конфиденциальности и подтвердите свое согласие для продолжения."""
                }

                # Create keyboard with privacy options
                agree_messages = {
                    'en': {'view': '📋 View Privacy Policy', 'agree': '✅ I Agree & Continue', 'cancel': '❌ Cancel'},
                    'es': {'view': '📋 Ver Política de Privacidad', 'agree': '✅ Acepto y Continúo', 'cancel': '❌ Cancelar'},
                    'ru': {'view': '📋 Посмотреть Политику', 'agree': '✅ Согласен и Продолжить', 'cancel': '❌ Отмена'}
                }

                keyboard = [
                    [InlineKeyboardButton(agree_messages[language]['view'], callback_data="view_privacy")],
                    [InlineKeyboardButton(agree_messages[language]['agree'], callback_data="accept_privacy")],
                    [InlineKeyboardButton(agree_messages[language]['cancel'], callback_data="main_menu")]
                ]

                print("📤 Sending privacy agreement message")
                await update.message.reply_text(
                    messages[language],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                print("✅ Privacy agreement message sent")
                
                return VIEWING_PRIVACY

            except Exception as date_error:
                print(f"❌ Date parsing error: {str(date_error)}")
                logger.error(f"Date parsing error: {date_error}")
                language = self.get_user_language(update.effective_user.id)
                error_messages = {
                    'en': "❌ Invalid date format. Please use: DD.MM.YYYY - DD.MM.YYYY\nNote: Duration is calculated in full 24-hour periods.",
                    'es': "❌ Formato de fecha inválido. Use: DD.MM.YYYY - DD.MM.YYYY\nNota: La duración se calcula en períodos completos de 24 horas.",
                    'ru': "❌ Неверный формат даты. Используйте: DD.MM.YYYY - DD.MM.YYYY\nПримечание: Продолжительность рассчитывается полными 24-часовыми периодами."
                }
                await update.message.reply_text(error_messages[language])
                return SELECTING_DATES

        except Exception as e:
            print(f"❌ Error in handle_dates_input: {str(e)}")
            logger.error(f"Error handling dates input: {e}")
            raise

    async def handle_personal_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle personal information and show booking confirmation"""
        try:
            if not update.message:
                return ENTERING_PERSONAL_INFO
            
            text = update.message.text
            context.user_data['personal_info'] = text
            
            # Get all booking information
            car_id = context.user_data.get('selected_car')
            dates = context.user_data.get('dates')
            duration = context.user_data.get('duration')
            base_price = context.user_data.get('base_price')
            total_price = context.user_data.get('total_price')
            discount = context.user_data.get('discount')
            personal_info = context.user_data.get('personal_info')
            
            language = self.get_user_language(update.effective_user.id)
            
            # Format price information
            price_info = f"💰 *Price Details:*\n"
            price_info += f"• Base price: {base_price:,.0f} CLP/day\n"
            price_info += f"• Duration: {duration} days\n"
            if discount > 0:
                price_info += f"• Discount: {discount}%\n"
            price_info += f"• Total price: {total_price:,.0f} CLP"
            
            # Format confirmation message
            messages = {
                'en': f"""*🎉 Booking Request Summary*

*Selected Car:* {car_id}
*Dates:* {dates}
({duration} days)

{price_info}

*Personal Information:*
{personal_info}

Would you like to confirm this booking?""",
                'es': f"""*🎉 Resumen de la Solicitud*

*Auto Seleccionado:* {car_id}
*Fechas:* {dates}
({duration} días)

{price_info}

*Información Personal:*
{personal_info}

¿Desea confirmar esta reserva?""",
                'ru': f"""*🎉 Сводка Бронирования*

*Выбранный Автомобиль:* {car_id}
*Даты:* {dates}
({duration} дней)

{price_info}

*Личная Информация:*
{personal_info}

Хотите подтвердить это бронирование?"""
            }
            
            # Create confirmation keyboard
            confirm_messages = {
                'en': {'confirm': '✅ Confirm Booking', 'cancel': '❌ Cancel'},
                'es': {'confirm': '✅ Confirmar Reserva', 'cancel': '❌ Cancelar'},
                'ru': {'confirm': '✅ Подтвердить', 'cancel': '❌ Отменить'}
            }
            
            keyboard = [
                [InlineKeyboardButton(confirm_messages[language]['confirm'], callback_data="confirm_booking")],
                [InlineKeyboardButton(confirm_messages[language]['cancel'], callback_data="main_menu")]
            ]
            
            await update.message.reply_text(
                messages[language],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return CONFIRMING_BOOKING
            
        except Exception as e:
            logger.error(f"Error handling personal info: {e}")
            raise

    async def confirm_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle booking confirmation and send to admin"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Get all booking information
            car_id = context.user_data.get('selected_car')
            dates = context.user_data.get('dates')
            duration = context.user_data.get('duration')
            base_price = context.user_data.get('base_price')
            total_price = context.user_data.get('total_price')
            discount = context.user_data.get('discount')
            personal_info = context.user_data.get('personal_info')
            
            # Format price information for admin
            price_info = f"💰 *Price Details:*\n"
            price_info += f"• Base price: {base_price:,.0f} CLP/day\n"
            price_info += f"• Duration: {duration} days\n"
            if discount > 0:
                price_info += f"• Discount: {discount}%\n"
            price_info += f"• Total price: {total_price:,.0f} CLP"
            
            # Format admin message
            admin_message = f"""🚨 *New Booking Request*

🚗 *Selected Car:* {car_id}
📅 *Dates:* {dates}
⏳ *Duration:* {duration} days

{price_info}

👤 *Client Information:*
{personal_info}

📱 *Telegram:* @{update.effective_user.username if update.effective_user.username else 'N/A'}
⏰ *Request Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            print(f"📤 Sending booking request to admin chat: {ADMIN_CHAT_ID}")
            print(f"📄 Message content: {admin_message}")

            # Send to admin chat
            try:
                sent_message = await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=admin_message,
                    parse_mode=ParseMode.MARKDOWN
                )
                print(f"✅ Successfully sent message to admin chat. Message ID: {sent_message.message_id}")
            except Exception as e:
                print(f"❌ Error sending to admin chat: {str(e)}")
                logger.error(f"Error sending to admin chat: {e}")
                # Try sending without markdown
                try:
                    sent_message = await context.bot.send_message(
                        chat_id=ADMIN_CHAT_ID,
                        text=f"🚨 New Booking Request\n\n{admin_message}",
                        parse_mode=None
                    )
                    print("✅ Sent plain text message to admin chat")
                except Exception as e2:
                    print(f"❌ Error sending plain text: {str(e2)}")
                    logger.error(f"Error sending plain text message: {e2}")

            # Send confirmation to user
            language = self.get_user_language(query.from_user.id)
            confirmation_messages = {
                'en': "✅ Thank you! Your booking request has been received.\n\nOur team will contact you shortly to confirm the details.",
                'es': "✅ ¡Gracias! Hemos recibido su solicitud de reserva.\n\nNuestro equipo se pondrá en contacto con usted pronto para confirmar los detalles.",
                'ru': "✅ Спасибо! Ваш запрос на бронирование получен.\n\nНаша команда свяжется с вами в ближайшее время для подтверждения деталей."
            }
            
            await query.message.edit_text(
                confirmation_messages[language],
                reply_markup=get_main_menu_keyboard(language)
            )
            
            # Clear user data
            context.user_data.clear()
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error confirming booking: {e}")
            raise

    async def show_user_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's bookings"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        bookings = self.db.get_user_bookings(user_id)
        
        if not bookings:
            await query.edit_message_text(
                "📭 You don't have any bookings yet.\n\nStart by browsing our available cars!",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        message = "*Your Bookings:*\n\n"
        keyboard = []
        
        for booking in bookings:
            booking_id, user_id, car_id, start_date, end_date, total_price, status, payment_method, payment_status, created_at, model, brand, year = booking
            
            message += f"""
📋 *Booking #{booking_id}*
🚗 {brand} {model} ({year})
📅 {start_date} to {end_date}
💰 ${total_price:.2f}
📊 Status: {BOOKING_STATUS.get(status, status)}
💳 Payment: {payment_method}
            """
            
            if status in ['pending', 'confirmed']:
                keyboard.append([InlineKeyboardButton(f"❌ Cancel #{booking_id}", callback_data=f"cancel_booking_{booking_id}")])
            elif status == 'completed':
                keyboard.append([InlineKeyboardButton(f"⭐ Review #{booking_id}", callback_data=f"leave_review_{booking_id}")])
        
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def cancel_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel a booking"""
        query = update.callback_query
        await query.answer()
        
        booking_id = int(query.data.split('_')[2])
        user_id = query.from_user.id
        
        if self.db.cancel_booking(booking_id, user_id):
            await query.edit_message_text(
                "✅ Booking cancelled successfully!",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ Failed to cancel booking. Please try again.",
                reply_markup=get_main_menu_keyboard()
            )
    
    async def show_reviews_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show reviews menu"""
        query = update.callback_query
        await query.answer()
        
        message = """
⭐ *Reviews & Ratings*

Here you can:
• View reviews for specific cars
• Leave reviews for your completed bookings
• See overall customer satisfaction

What would you like to do?
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 View Car Reviews", callback_data="browse_cars")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_car_reviews(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show reviews for a specific car"""
        query = update.callback_query
        await query.answer()
        
        car_id = int(query.data.split('_')[2])
        reviews = self.db.get_car_reviews(car_id)
        car = self.db.get_car(car_id)
        
        if not reviews:
            await query.edit_message_text(
                f"No reviews yet for {car[2]} {car[1]}.\n\nBe the first to leave a review!",
                reply_markup=get_car_detail_keyboard(car_id)
            )
            return
        
        message = f"*Reviews for {car[2]} {car[1]}:*\n\n"
        
        for review in reviews:
            rating = review[4]
            comment = review[5]
            reviewer_name = f"{review[7]} {review[8]}" if review[7] and review[8] else "Anonymous"
            
            message += f"⭐ {'⭐' * rating}{'☆' * (5 - rating)}\n"
            message += f"👤 {reviewer_name}\n"
            if comment:
                message += f"💬 {comment}\n"
            message += "─" * 30 + "\n"
        
        avg_rating = sum(review[4] for review in reviews) / len(reviews)
        message += f"\n*Average Rating: {avg_rating:.1f}/5*"
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_car_detail_keyboard(car_id)
        )
    
    async def show_help_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help menu"""
        try:
            query = update.callback_query
            await query.answer()
            
            message = """
ℹ️ *Help & Support*

Need help? Here's how to reach us:

• 📞 Call: +1 (555) 123-4567
• 📧 Email: support@carrental.com
• 💬 WhatsApp: +1 (555) 123-4567
• 📱 Telegram: @CarRentalSupport

Our support team is available:
Monday - Friday: 9:00 AM - 6:00 PM
"""
            await query.message.edit_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_back_to_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error showing help menu: {e}")
            raise
    
    async def handle_help_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle help topic selection"""
        query = update.callback_query
        await query.answer()
        
        topic = query.data.split('_')[1]
        
        if topic == "booking":
            message = """
📖 *How to Book a Car*

1. **Browse Cars** - Choose from our available vehicles
2. **Select Category** - Pick economy, standard, premium, or SUV
3. **Choose Car** - View details and select your preferred vehicle
4. **Select Dates** - Pick your rental start and end dates
5. **Payment** - Choose your payment method
6. **Confirm** - Review and confirm your booking

*Requirements:*
• Valid driver's license
• Credit card for payment
• Minimum age: 21 years
            """
        elif topic == "pricing":
            message = """
💰 *Pricing Information*

*Daily Rates:*
• Economy: $50/day
• Standard: $75/day  
• Premium: $120/day
• SUV: $100/day

*Additional Fees:*
• Insurance: $15/day (optional)
• Late return: $25/hour
• Fuel: Pay for what you use
• Cleaning: $25 (if needed)

*Discounts:*
• Weekly rental: 10% off
• Monthly rental: 20% off
            """
        elif topic == "terms":
            message = """
📋 *Terms & Conditions*

*Rental Requirements:*
• Valid driver's license
• Minimum age: 21 years
• Credit card required
• Proof of insurance

*Cancellation Policy:*
• Free cancellation up to 24 hours before pickup
• 50% refund for cancellations within 24 hours
• No refund for no-shows

*Damage Policy:*
• Customer responsible for damage during rental
• Insurance available for additional protection
• Pre-rental inspection required
            """
        else:
            message = "❌ Help topic not found."
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Help", callback_data="help")]]
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        try:
            error = context.error
            logger.error(f"Error: {error}")
            
            # Get the error message
            if isinstance(error, Exception):
                error_msg = str(error)
            else:
                error_msg = "An error occurred. Please try again."
            
            # Try to send error message
            if update and update.effective_chat:
                try:
                    if update.callback_query:
                        # For callback queries, try to edit the message first
                        try:
                            await update.callback_query.message.edit_text(
                                "Please use /start to show the menu.",
                                reply_markup=get_main_menu_keyboard('en')
                            )
                        except Exception:
                            # If editing fails, send a new message
                            await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text="Please use /start to show the menu.",
                                reply_markup=get_main_menu_keyboard('en')
                            )
                    else:
                        # For regular messages
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="Please use /start to show the menu.",
                            reply_markup=get_main_menu_keyboard('en')
                        )
                except Exception as send_error:
                    logger.error(f"Error sending error message: {send_error}")
        except Exception as e:
            logger.error(f"Error in error handler: {e}")

    async def start_review_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the review process"""
        try:
            query = update.callback_query
            await query.answer()
            
            language = self.get_user_language(query.from_user.id)
            
            messages = {
                'en': """*⭐ Leave a Review*

Please rate your experience with our service from 1 to 4 stars:

1 ⭐ - Poor
2 ⭐⭐ - Fair
3 ⭐⭐⭐ - Good
4 ⭐⭐⭐⭐ - Excellent""",
                'es': """*⭐ Dejar una Reseña*

Por favor califique su experiencia con nuestro servicio de 1 a 4 estrellas:

1 ⭐ - Malo
2 ⭐⭐ - Regular
3 ⭐⭐⭐ - Bueno
4 ⭐⭐⭐⭐ - Excelente""",
                'ru': """*⭐ Оставить Отзыв*

Пожалуйста, оцените ваш опыт работы с нашим сервисом от 1 до 4 звезд:

1 ⭐ - Плохо
2 ⭐⭐ - Удовлетворительно
3 ⭐⭐⭐ - Хорошо
4 ⭐⭐⭐⭐ - Отлично"""
            }

            keyboard = [
                [InlineKeyboardButton("⭐", callback_data="rate_1"),
                 InlineKeyboardButton("⭐⭐", callback_data="rate_2"),
                 InlineKeyboardButton("⭐⭐⭐", callback_data="rate_3"),
                 InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rate_4")],
                [InlineKeyboardButton(MENU_TRANSLATIONS['back_to_menu'][language], callback_data="main_menu")]
            ]

            await query.message.edit_text(
                messages[language],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return SELECTING_RATING
            
        except Exception as e:
            logger.error(f"Error starting review process: {e}")
            raise

    async def handle_rating_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle rating selection"""
        try:
            query = update.callback_query
            await query.answer()
            
            rating = int(query.data.split('_')[1])
            context.user_data['rating'] = rating
            
            language = self.get_user_language(query.from_user.id)
            
            messages = {
                'en': f"""*💭 Leave a Comment*

You rated us {rating} {'⭐' * rating}

Please write a brief comment about your experience:
• What did you like?
• What could we improve?
• Would you recommend us?""",
                'es': f"""*💭 Dejar un Comentario*

Nos calificó con {rating} {'⭐' * rating}

Por favor escriba un breve comentario sobre su experiencia:
• ¿Qué le gustó?
• ¿Qué podríamos mejorar?
• ¿Nos recomendaría?""",
                'ru': f"""*💭 Оставить Комментарий*

Вы оценили нас на {rating} {'⭐' * rating}

Пожалуйста, напишите краткий комментарий о вашем опыте:
• Что вам понравилось?
• Что мы могли бы улучшить?
• Порекомендовали бы вы нас?"""
            }

            keyboard = [
                [InlineKeyboardButton('🔄 Change Rating', callback_data="change_rating")],
                [InlineKeyboardButton('🔙 Back to Menu', callback_data="main_menu")]
            ]

            await query.message.edit_text(
                messages[language],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return ENTERING_REVIEW
            
        except Exception as e:
            logger.error(f"Error handling rating selection: {e}")
            raise

    async def handle_review_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle review text input"""
        try:
            if not update.message:
                return ENTERING_REVIEW

            rating = context.user_data.get('rating')
            review_text = update.message.text
            user_id = update.effective_user.id
            language = self.get_user_language(user_id)

            # Format review message for admin chat
            admin_review = f"""📝 *New Review Received*

⭐ *Rating:* {'⭐' * rating} ({rating}/4)
👤 *From:* @{update.effective_user.username if update.effective_user.username else 'N/A'}
📱 *User ID:* `{user_id}`
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💭 *Comment:*
{review_text}"""

            try:
                # Send to review chat
                await context.bot.send_message(
                    chat_id=REVIEW_CHAT_ID,
                    text=admin_review,
                    parse_mode=ParseMode.MARKDOWN
                )
                print(f"✅ Review sent to chat {REVIEW_CHAT_ID}")
            except Exception as e:
                logger.error(f"Error sending review to admin chat: {e}")
                print(f"❌ Error sending review: {str(e)}")
                # Try sending without markdown
                try:
                    await context.bot.send_message(
                        chat_id=REVIEW_CHAT_ID,
                        text=f"New Review:\nRating: {rating}/4\nUser: @{update.effective_user.username}\nComment: {review_text}",
                        parse_mode=None
                    )
                    print("✅ Review sent without markdown formatting")
                except Exception as e2:
                    logger.error(f"Error sending plain review: {e2}")
                    print(f"❌ Error sending plain review: {str(e2)}")

            # Send confirmation to user
            messages = {
                'en': f"""✅ Thank you for your review!

Rating: {'⭐' * rating}
Comment: {review_text}

Your feedback helps us improve our service.""",
                'es': f"""✅ ¡Gracias por su reseña!

Calificación: {'⭐' * rating}
Comentario: {review_text}

Sus comentarios nos ayudan a mejorar nuestro servicio.""",
                'ru': f"""✅ Спасибо за ваш отзыв!

Оценка: {'⭐' * rating}
Комментарий: {review_text}

Ваши отзывы помогают нам улучшать наш сервис."""
            }

            await update.message.reply_text(
                messages[language],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard(language)
            )

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error handling review text: {e}")
            print(f"❌ Error in handle_review_text: {str(e)}")
            raise

    async def skip_review_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Skip review text and submit only rating"""
        try:
            query = update.callback_query
            await query.answer()
            
            rating = context.user_data.get('rating')
            user_id = query.from_user.id
            language = self.get_user_language(user_id)

            # Here you would typically save the rating to your database
            # For now, we'll just show a confirmation message

            messages = {
                'en': f"""✅ Thank you for your rating!

Rating: {'⭐' * rating}

Your feedback helps us improve our service.""",
                'es': f"""✅ ¡Gracias por su calificación!

Calificación: {'⭐' * rating}

Sus comentarios nos ayudan a mejorar nuestro servicio.""",
                'ru': f"""✅ Спасибо за вашу оценку!

Оценка: {'⭐' * rating}

Ваши отзывы помогают нам улучшать наш сервис."""
            }

            await query.message.edit_text(
                messages[language],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard(language)
            )

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error skipping review text: {e}")
            raise

    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        return self.user_languages.get(user_id, 'en')

    async def show_about_us(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show about us information"""
        try:
            query = update.callback_query
            if not query:
                return
            
            try:
                await query.answer()
            except Exception as e:
                logger.error(f"Error answering callback query: {e}")
            
            language = self.get_user_language(query.from_user.id)
            
            if language == 'ru':
                text = "О нас\n\n"
                text += "Rent Car Chile\n"
                text += "🚗 Ваше путешествие, ваш темп. Наше обещание - ваше спокойствие.\n\n"
                text += "Более 3 лет опыта обслуживания путешественников и местных жителей по всему Чили. Мы предлагаем больше, чем просто автомобили - мы дарим свободу, гибкость и по-настоящему персональный сервис на каждом километре пути.\n\n"
                text += "Почему выбирают нас?\n\n"
                text += "🕐 Поддержка 24/7 для долгосрочных клиентов\n"
                text += "✈️ Доставка и возврат где удобно: Аэропорт, Винья-дель-Мар, Конкон, Реньяка и другие места\n"
                text += "🔄 Гибкие условия: Получение и возврат автомобиля по вашему графику\n"
                text += "💵 Различные способы оплаты: CLP, USD, RUB, USDT, PayPal, Western Union и другие\n"
                text += "🤝 Премиум-сервис: Консьерж, перевод и услуги гида\n"
                text += "🌎 Говорим на вашем языке - английский, испанский и русский. Сопровождаем на каждом этапе\n"
                text += "🏆 Местная экспертиза: 3 года репутации и сотни довольных клиентов\n\n"
                text += "Путешествуйте безопасно, путешествуйте по-своему.\n"
                text += "Откройте Чили без границ с Rent Car Chile!\n\n"
                text += "📱 WhatsApp: +56982567485\n"
                text += "🌐 www.rentcarchile.com\n"
                text += "📸 Instagram: rent.carchile\n"
                text += "💬 Telegram: @rentcar_chile"

                keyboard = [
                    [InlineKeyboardButton("🌐 Веб-сайт", url="http://www.rentcarchile.com")],
                    [InlineKeyboardButton("📸 Instagram", url="https://instagram.com/rent.carchile")],
                    [InlineKeyboardButton("💬 Telegram", url="https://t.me/rentcar_chile")],
                    [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/56982567485")],
                    [InlineKeyboardButton("🔙 Вернуться в меню", callback_data="main_menu")]
                ]

            elif language == 'es':
                text = "Sobre Nosotros\n\n"
                text += "Rent Car Chile\n"
                text += "🚗 Tu viaje, tu ritmo. Nuestra promesa, tu tranquilidad.\n\n"
                text += "Con más de 3 años de experiencia sirviendo a viajeros y locales en todo Chile, ofrecemos más que solo autos: entregamos libertad, flexibilidad y un servicio verdaderamente personal en cada kilómetro del camino.\n\n"
                text += "¿Por qué elegirnos?\n\n"
                text += "🕐 Soporte 24/7 para clientes de largo plazo\n"
                text += "✈️ Recogida y entrega donde lo necesites: Aeropuerto, Viña del Mar, Concón, Reñaca y más\n"
                text += "🔄 Términos flexibles: Recoge y devuelve tu auto según tu horario\n"
                text += "💵 Múltiples opciones de pago: CLP, USD, RUB, USDT, PayPal, Western Union y más\n"
                text += "🤝 Atención premium: Opciones de concierge, traducción y guía turístico\n"
                text += "🌎 Hablamos tu idioma - Inglés, Español y Ruso. Te guiamos en cada paso\n"
                text += "🏆 Experiencia local: 3 años de reputación y cientos de clientes satisfechos\n\n"
                text += "Viaja seguro, viaja a tu manera.\n"
                text += "¡Descubre Chile sin límites con Rent Car Chile!\n\n"
                text += "📱 WhatsApp: +56921701913\n"
                text += "🌐 www.rentcarchile.com\n"
                text += "📸 Instagram: rent.carchile"

                keyboard = [
                    [InlineKeyboardButton("🌐 Sitio web", url="http://www.rentcarchile.com")],
                    [InlineKeyboardButton("📸 Instagram", url="https://instagram.com/rent.carchile")],
                    [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/56921701913")],
                    [InlineKeyboardButton("🔙 Volver al Menú", callback_data="main_menu")]
                ]

            else:  # English
                text = "About Us\n\n"
                text += "Rent Car Chile\n"
                text += "🚗 Your journey, your pace. Our promise, your peace of mind.\n\n"
                text += "With over 3 years of experience serving travelers and locals across Chile, we offer more than just cars—we deliver freedom, flexibility, and truly personal service every mile of the way.\n\n"
                text += "Why choose us?\n\n"
                text += "🕐 24/7 support for long-term clients\n"
                text += "✈️ Pick-up and drop-off wherever you need: Airport, Viña del Mar, Concón, Reñaca, and more\n"
                text += "🔄 Flexible terms: Collect and return your car on your schedule\n"
                text += "💵 Multiple payment options: CLP, USD, RUB, USDT, PayPal, Western Union, and more\n"
                text += "🤝 Premium attention: Concierge, translation, and tour guide options\n"
                text += "🌎 We speak your language—English, Spanish, and Russian. We guide you at every step\n"
                text += "🏆 Local expertise: 3 years of reputation and hundreds of happy clients\n\n"
                text += "Travel safe, travel your way.\n"
                text += "Discover Chile without limits with Rent Car Chile!\n\n"
                text += "📱 WhatsApp: +56921701913\n"
                text += "🌐 www.rentcarchile.com\n"
                text += "📸 Instagram: rent.carchile"

                keyboard = [
                    [InlineKeyboardButton("🌐 Website", url="http://www.rentcarchile.com")],
                    [InlineKeyboardButton("📸 Instagram", url="https://instagram.com/rent.carchile")],
                    [InlineKeyboardButton("📱 WhatsApp", url="https://wa.me/56921701913")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
                ]

            try:
                await query.message.edit_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as edit_error:
                logger.error(f"Error editing message: {edit_error}")
                await query.message.reply_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                try:
                    await query.message.delete()
                except Exception as delete_error:
                    logger.error(f"Error deleting old message: {delete_error}")

        except Exception as e:
            logger.error(f"Error showing about us: {e}")
            try:
                if query and query.message:
                    await query.message.reply_text(
                        "Sorry, there was an error displaying the About Us information. Please try again.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]])
                    )
            except Exception as e2:
                logger.error(f"Error sending error message: {e2}")
            pass

    async def start_booking_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the booking process by showing car categories"""
        try:
            query = update.callback_query
            try:
                await query.answer()
            except Exception as e:
                logger.error(f"Error answering callback query: {e}")
                # Continue even if answering the query fails
            
            language = self.get_user_language(query.from_user.id)
            
            # Check if booking was started from a specific car
            if query.data.startswith("book_car_"):
                car_id = query.data.split("_")[2]
                context.user_data['selected_car'] = car_id
                
                messages = {
                    'en': """*📅 Select Dates*

Please enter your desired rental dates in the format:
DD.MM.YYYY - DD.MM.YYYY

Example: 25.12.2023 - 30.12.2023

Note: Duration is calculated in full 24-hour periods.""",
                    'es': """*📅 Seleccionar Fechas*

Por favor ingrese las fechas deseadas en el formato:
DD.MM.YYYY - DD.MM.YYYY

Ejemplo: 25.12.2023 - 30.12.2023

Nota: La duración se calcula en períodos completos de 24 horas.""",
                    'ru': """*📅 Выбор Дат*

Пожалуйста, введите желаемые даты аренды в формате:
DD.MM.YYYY - DD.MM.YYYY

Пример: 25.12.2023 - 30.12.2023

Примечание: Продолжительность рассчитывается полными 24-часовыми периодами."""
                }
                
                keyboard = [[InlineKeyboardButton(MENU_TRANSLATIONS['back_to_menu'][language], callback_data="main_menu")]]
                
                try:
                    await query.message.edit_text(
                        messages[language],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except Exception as edit_error:
                    logger.error(f"Error editing message: {edit_error}")
                    # If editing fails, send a new message
                    await query.message.reply_text(
                        messages[language],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                
                return SELECTING_DATES
            
            # Show categories for regular booking flow
            messages = {
                'en': """*🚗 Car Categories*

Please select a category to view available cars.

*Discounts:*
• From 3 days - 15% off
• From 30 days - 25% off
• From 90 days - 35% off""",
                'es': """*🚗 Categorías de Autos*

Por favor seleccione una categoría para ver los autos disponibles.

*Descuentos:*
• Desde 3 días - 15% desc.
• Desde 30 días - 25% desc.
• Desde 90 días - 35% desc.""",
                'ru': """*🚗 Категории Автомобилей*

Пожалуйста, выберите категорию для просмотра доступных автомобилей.

*Скидки:*
• От 3 дней - скидка 15%
• От 30 дней - скидка 25%
• От 90 дней - скидка 35%"""
            }
            
            # Create keyboard with car categories
            keyboard = []
            for category, info in CAR_CATEGORIES.items():
                keyboard.append([InlineKeyboardButton(
                    f"{info['name'][language]} - {info['price_per_day']} CLP/day",
                    callback_data=f"category_{category}"
                )])
            keyboard.append([InlineKeyboardButton(MENU_TRANSLATIONS['back_to_menu'][language], callback_data="main_menu")])
            
            try:
                await query.message.edit_text(
                    messages[language],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as edit_error:
                logger.error(f"Error editing message: {edit_error}")
                # If editing fails, send a new message
                await query.message.reply_text(
                    messages[language],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
            return CHOOSING_CATEGORY
            
        except Exception as e:
            logger.error(f"Error in start_booking_process: {e}")
            print(f"❌ Error in start_booking_process: {str(e)}")
            if update.effective_chat:
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Please use /start to show the menu.",
                        reply_markup=get_main_menu_keyboard('en')
                    )
                except Exception as e2:
                    logger.error(f"Error sending error message: {e2}")
            return ConversationHandler.END

    async def show_privacy_policy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show privacy policy"""
        try:
            query = update.callback_query
            if query:
                try:
                    await query.answer()
                except Exception as e:
                    logger.error(f"Error answering callback query: {e}")

            language = self.get_user_language(update.effective_user.id)
            
            messages = {
                'en': """*Privacy Policy*

We value your privacy and protect your personal data. By using our service, you agree to the following:

*Data We Collect:*
• Full name
• Phone number
• Email address
• Telegram username
• Booking preferences and history

*How We Use Your Data:*
• Process your car rental requests
• Contact you about your bookings
• Send important updates about your rental
• Improve our service

*Data Protection:*
• We store your data securely
• We never share your data with third parties
• We keep your data only as long as necessary
• You can request data deletion at any time

*Your Rights:*
• Access your personal data
• Request data correction
• Request data deletion
• Withdraw consent

*Contact Us:*
For privacy concerns, contact us through:
• Telegram: @rentcar_chile
• Email: privacy@rentcarchile.com

By proceeding with the booking, you agree to our privacy policy.""",

                'es': """*Política de Privacidad*

Valoramos su privacidad y protegemos sus datos personales. Al usar nuestro servicio, usted acepta lo siguiente:

*Datos que Recopilamos:*
• Nombre completo
• Número de teléfono
• Correo electrónico
• Usuario de Telegram
• Preferencias e historial de reservas

*Cómo Usamos sus Datos:*
• Procesar sus solicitudes de alquiler
• Contactarlo sobre sus reservas
• Enviar actualizaciones importantes
• Mejorar nuestro servicio

*Protección de Datos:*
• Almacenamos sus datos de forma segura
• Nunca compartimos sus datos con terceros
• Conservamos sus datos solo el tiempo necesario
• Puede solicitar la eliminación de datos

*Sus Derechos:*
• Acceder a sus datos personales
• Solicitar corrección de datos
• Solicitar eliminación de datos
• Retirar el consentimiento

*Contáctenos:*
Para consultas de privacidad, contáctenos a través de:
• Telegram: @rentcar_chile
• Email: privacy@rentcarchile.com

Al continuar con la reserva, acepta nuestra política de privacidad.""",

                'ru': """*Политика Конфиденциальности*

Мы ценим вашу конфиденциальность и защищаем ваши личные данные. Используя наш сервис, вы соглашаетесь со следующим:

*Данные, которые мы собираем:*
• Полное имя
• Номер телефона
• Электронная почта
• Имя пользователя Telegram
• Предпочтения и история бронирований

*Как мы используем ваши данные:*
• Обработка запросов на аренду
• Связь с вами по поводу бронирований
• Отправка важных обновлений
• Улучшение нашего сервиса

*Защита данных:*
• Безопасное хранение данных
• Никогда не передаем данные третьим лицам
• Храним данные только необходимое время
• Вы можете запросить удаление данных

*Ваши права:*
• Доступ к личным данным
• Запрос на исправление данных
• Запрос на удаление данных
• Отзыв согласия

*Свяжитесь с нами:*
По вопросам конфиденциальности:
• Telegram: @rentcar_chile
• Email: privacy@rentcarchile.com

Продолжая бронирование, вы соглашаетесь с нашей политикой конфиденциальности."""
            }

            keyboard = [
                [InlineKeyboardButton(MENU_TRANSLATIONS['back_to_menu'][language], callback_data="main_menu")]
            ]

            if update.message:
                await update.message.reply_text(
                    messages[language],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            elif query and query.message:
                try:
                    await query.message.edit_text(
                        messages[language],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except Exception as edit_error:
                    logger.error(f"Error editing message: {edit_error}")
                    await query.message.reply_text(
                        messages[language],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )

        except Exception as e:
            logger.error(f"Error showing privacy policy: {e}")
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Error showing privacy policy. Please try again.",
                    reply_markup=get_main_menu_keyboard('en')
                )

    async def handle_privacy_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle privacy policy response"""
        try:
            query = update.callback_query
            print(f"🔍 Privacy response: {query.data}")
            await query.answer()
            
            language = self.get_user_language(query.from_user.id)
            print(f"🌐 User language: {language}")
            
            if query.data == "view_privacy":
                print("📋 Showing privacy policy")
                await self.show_privacy_policy(update, context)
                return VIEWING_PRIVACY
                
            elif query.data == "accept_privacy":
                print("✅ Privacy policy accepted")
                # Show personal info form
                messages = {
                    'en': """*👤 Personal Information*

Please provide your contact information in the following format:

Name: [your full name]
Phone: [your phone number]
Email: [your email]

Example:
Name: John Smith
Phone: +1234567890
Email: john@email.com""",
                    'es': """*👤 Información Personal*

Por favor proporcione su información de contacto en el siguiente formato:

Nombre: [su nombre completo]
Teléfono: [su número de teléfono]
Email: [su email]

Ejemplo:
Nombre: Juan Pérez
Teléfono: +1234567890
Email: juan@email.com""",
                    'ru': """*👤 Личная Информация*

Пожалуйста, предоставьте вашу контактную информацию в следующем формате:

Имя: [ваше полное имя]
Телефон: [ваш номер телефона]
Email: [ваш email]

Пример:
Имя: Иван Петров
Телефон: +1234567890
Email: ivan@email.com"""
                }

                keyboard = [[InlineKeyboardButton(MENU_TRANSLATIONS['back_to_menu'][language], callback_data="main_menu")]]

                print("📤 Sending personal info form")
                await query.message.edit_text(
                    messages[language],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                print("✅ Personal info form sent")
                return ENTERING_PERSONAL_INFO
            else:
                print("❌ Privacy policy rejected or cancelled")
                return await self.show_main_menu(update, context)

        except Exception as e:
            print(f"❌ Error in handle_privacy_response: {str(e)}")
            logger.error(f"Error handling privacy response: {e}")
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Error processing your response. Please try again.",
                    reply_markup=get_main_menu_keyboard('en')
                )
            return ConversationHandler.END

def main():
    """Start the bot"""
    try:
        bot = CarRentalBot()
        application = Application.builder().token(BOT_TOKEN).build()

        # Debug handler to print all updates
        async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            print("🔍 DEBUG INFO:")
            print(f"Chat ID: {update.effective_chat.id}")
            print(f"User: {update.effective_user.username if update.effective_user else 'Unknown'}")
            print(f"Message type: {'callback_query' if update.callback_query else 'message'}")
            if update.message:
                print(f"Message text: {update.message.text}")
            if update.callback_query:
                print(f"Callback data: {update.callback_query.data}")
            print("------------------------")
            return False

        # Add debug handler first
        application.add_handler(MessageHandler(filters.ALL, debug_handler), group=-1)

        # Add language selection handler
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CallbackQueryHandler(bot.handle_language_selection, pattern="^lang_"))

        # Add booking handler
        booking_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(bot.start_booking_process, pattern="^make_reservation$"),
                CallbackQueryHandler(bot.start_booking_process, pattern="^book_car_")
            ],
            states={
                CHOOSING_CATEGORY: [
                    CallbackQueryHandler(bot.show_cars_in_category, pattern="^category_"),
                    CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$")
                ],
                CHOOSING_CAR: [
                    CallbackQueryHandler(bot.handle_car_selection, pattern="^car_"),
                    CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$")
                ],
                SELECTING_DATES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_dates_input),
                    CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$")
                ],
                VIEWING_PRIVACY: [
                    CallbackQueryHandler(bot.handle_privacy_response),
                    CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$")
                ],
                ENTERING_PERSONAL_INFO: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_personal_info),
                    CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$")
                ],
                CONFIRMING_BOOKING: [
                    CallbackQueryHandler(bot.confirm_booking, pattern="^confirm_booking$"),
                    CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$")
                ]
            },
            fallbacks=[
                CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$"),
                CommandHandler("cancel", lambda u, c: ConversationHandler.END)
            ],
            per_message=False
        )

        # Add review handler
        review_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(bot.start_review_process, pattern="^leave_review$")],
            states={
                SELECTING_RATING: [
                    CallbackQueryHandler(bot.handle_rating_selection, pattern="^rate_[1-4]$"),
                    CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$")
                ],
                ENTERING_REVIEW: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_review_text),
                    CallbackQueryHandler(bot.start_review_process, pattern="^change_rating$"),
                    CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$")
                ]
            },
            fallbacks=[
                CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$"),
                CommandHandler("cancel", lambda u, c: ConversationHandler.END)
            ],
            per_message=False
        )

        # Add handlers
        application.add_handler(booking_handler)
        application.add_handler(review_handler)
        
        # Add menu handlers
        application.add_handler(CallbackQueryHandler(bot.show_car_fleet, pattern="^car_fleet$"))
        application.add_handler(CallbackQueryHandler(bot.show_conditions, pattern="^conditions$"))
        application.add_handler(CallbackQueryHandler(bot.show_payment_methods, pattern="^payment_methods$"))
        application.add_handler(CallbackQueryHandler(bot.show_contact_info, pattern="^contact_us$"))
        application.add_handler(CallbackQueryHandler(bot.show_about_us, pattern="^about_us$"))
        application.add_handler(CallbackQueryHandler(bot.show_privacy_policy, pattern="^privacy_policy$"))
        application.add_handler(CallbackQueryHandler(bot.show_main_menu, pattern="^main_menu$"))
        application.add_handler(CallbackQueryHandler(bot.start, pattern="^change_language$"))

        # Add error handler
        application.add_error_handler(bot.error_handler)

        print("🚗 CarRental Bot is starting...")
        application.run_polling()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main() 