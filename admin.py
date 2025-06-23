import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import ADMIN_USER_ID, CAR_CATEGORIES, CURRENCY, CURRENCY_SYMBOL
from database import Database
from utils import format_price, format_date

class AdminPanel:
    def __init__(self):
        self.db = Database()
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == ADMIN_USER_ID
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        if update.effective_user.id != ADMIN_USER_ID:
            await update.message.reply_text("❌ Acceso denegado. Este comando es solo para administradores.")
            return

        stats = self.db.get_rental_statistics()
        
        message = f"""
🎛 *Panel de Administración*

📊 *Estadísticas Generales:*
• Reservas Totales: {stats['total_bookings']}
• Ingresos Totales: {format_price(stats['total_revenue'])}
• Clientes Totales: {stats['total_customers']}

💰 *Ingresos por Categoría:*
"""
        for category, rentals, revenue in stats['revenue_by_category']:
            message += f"• {CAR_CATEGORIES[category]['name']}: {format_price(revenue)} ({rentals} rentas)\n"

        message += "\n🚗 *Vehículos Más Populares:*\n"
        for brand, model, count in stats['popular_cars']:
            message += f"• {brand} {model}: {count} rentas\n"

        message += "\n⭐ *Calificación Promedio por Categoría:*\n"
        for category, rating in stats['ratings_by_category']:
            stars = "⭐" * int(rating)
            message += f"• {CAR_CATEGORIES[category]['name']}: {stars} ({rating:.1f})\n"

        keyboard = [
            [InlineKeyboardButton("🚗 Gestionar Vehículos", callback_data="admin_cars")],
            [InlineKeyboardButton("📅 Ver Reservas", callback_data="admin_bookings")],
            [InlineKeyboardButton("⚙️ Mantenimiento", callback_data="admin_maintenance")],
            [InlineKeyboardButton("💾 Backup Database", callback_data="admin_backup")]
        ]

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_admin_cars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle car management"""
        query = update.callback_query
        await query.answer()

        cars = self.db.get_cars()
        message = "*🚗 Gestión de Vehículos*\n\n"

        for car in cars:
            car_id, model, brand, year, category, price, available, image_url, description = car
            status = "✅ Disponible" if available else "❌ No Disponible"
            message += f"""
• *{brand} {model}* ({year})
  Precio: {format_price(price)}/día
  Estado: {status}
  Categoría: {CAR_CATEGORIES[category]['name']}
            """

        keyboard = [
            [InlineKeyboardButton("➕ Agregar Vehículo", callback_data="admin_add_car")],
            [InlineKeyboardButton("🔄 Actualizar Estado", callback_data="admin_update_car")],
            [InlineKeyboardButton("🔙 Volver", callback_data="admin_menu")]
        ]

        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_admin_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle booking management"""
        query = update.callback_query
        await query.answer()

        bookings = self.db.get_all_bookings()
        message = "*📅 Gestión de Reservas*\n\n"

        for booking in bookings[:10]:  # Show last 10 bookings
            booking_id, user_id, car_id, start_date, end_date, total_price, status, payment_method, payment_status = booking
            car = self.db.get_car(car_id)
            user = self.db.get_user(user_id)

            message += f"""
🎫 *Reserva #{booking_id}*
👤 Cliente: {user[2]} {user[3]}
🚗 Vehículo: {car[2]} {car[1]}
📅 {format_date(start_date)} - {format_date(end_date)}
💰 Total: {format_price(total_price)}
📊 Estado: {status}
💳 Pago: {payment_status} ({payment_method})
            """

        keyboard = [
            [InlineKeyboardButton("✅ Confirmar Reservas", callback_data="admin_confirm_bookings")],
            [InlineKeyboardButton("📊 Ver Estadísticas", callback_data="admin_booking_stats")],
            [InlineKeyboardButton("🔙 Volver", callback_data="admin_menu")]
        ]

        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_admin_maintenance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle maintenance management"""
        query = update.callback_query
        await query.answer()

        cars = self.db.get_cars()
        message = "*⚙️ Mantenimiento de Vehículos*\n\n"

        for car in cars:
            car_id, model, brand, year, category, price, available, image_url, description = car
            maintenance_history = self.db.get_maintenance_history(car_id)
            last_maintenance = maintenance_history[0] if maintenance_history else None

            message += f"""
🚗 *{brand} {model}*
📅 Último mantenimiento: {format_date(last_maintenance[2]) if last_maintenance else 'No registrado'}
💰 Costo: {format_price(last_maintenance[4]) if last_maintenance else 'N/A'}
📝 Notas: {last_maintenance[3] if last_maintenance else 'N/A'}
            """

        keyboard = [
            [InlineKeyboardButton("➕ Registrar Mantenimiento", callback_data="admin_add_maintenance")],
            [InlineKeyboardButton("📊 Historial", callback_data="admin_maintenance_history")],
            [InlineKeyboardButton("🔙 Volver", callback_data="admin_menu")]
        ]

        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_admin_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle database backup"""
        query = update.callback_query
        await query.answer()

        backup_path = self.db.backup_database()
        
        if backup_path:
            message = f"""
✅ *Backup Creado Exitosamente*

📁 Archivo: `{os.path.basename(backup_path)}`
📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📦 Tamaño: {os.path.getsize(backup_path) / 1024:.1f} KB

El backup incluye:
• Información de vehículos
• Historial de reservas
• Reseñas de usuarios
• Registros de mantenimiento
            """
            
            # Send the backup file
            with open(backup_path, 'rb') as backup_file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=backup_file,
                    filename=os.path.basename(backup_path),
                    caption="📦 Database Backup"
                )
        else:
            message = "❌ Error al crear el backup. Por favor intente nuevamente."

        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="admin_menu")]]
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def setup_admin_handlers(application: Application):
    """Setup admin command handlers"""
    admin = AdminPanel()
    
    application.add_handler(CommandHandler("admin", admin.admin_command))
    application.add_handler(CallbackQueryHandler(admin.handle_admin_cars, pattern="^admin_cars$"))
    application.add_handler(CallbackQueryHandler(admin.handle_admin_bookings, pattern="^admin_bookings$"))
    application.add_handler(CallbackQueryHandler(admin.handle_admin_maintenance, pattern="^admin_maintenance$"))
    application.add_handler(CallbackQueryHandler(admin.handle_admin_backup, pattern="^admin_backup$")) 