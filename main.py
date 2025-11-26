import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# Получаем токен из переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8398487910:AAE77HSHMK43QVh8kA6xEYKZUQJgp8aNEiQ")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AntiScamBot:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect('scam_reports.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                reason TEXT,
                reports_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scam_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER,
                scammer_username TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована")

    async def start(self, update: Update, context: CallbackContext):
        """Команда /start"""
        user = update.effective_user
        
        welcome_text = f"""
🎮 Roblox Zona | Anti Scam Base 🛡️

Привет, {user.first_name}! 
Я бот для защиты сообщества Roblox от мошенников.

Команды:
🔍 /check @username - Проверить пользователя
🚨 /report @username причина - Пожаловаться
📊 /stats - Статистика бота

💎 Безопасность сообщества - наша общая задача!
        """
        
        keyboard = [
            [InlineKeyboardButton("🔍 Проверить пользователя", callback_data="check")],
            [InlineKeyboardButton("🚨 Сообщить о скамере", callback_data="report")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def report(self, update: Update, context: CallbackContext):
        """Команда /report"""
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Использование: /report @username причина")
            return
        
        target = context.args[0]
        description = ' '.join(context.args[1:])
        
        conn = sqlite3.connect('scam_reports.db')
        cursor = conn.cursor()
        
        # Добавляем жалобу
        cursor.execute(
            'INSERT INTO scam_reports (reporter_id, scammer_username, description) VALUES (?, ?, ?)',
            (update.effective_user.id, target, description)
        )
        
        # Обновляем черный список
        cursor.execute('SELECT * FROM blacklist WHERE username = ?', (target,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                'UPDATE blacklist SET reports_count = reports_count + 1 WHERE username = ?',
                (target,)
            )
        else:
            cursor.execute(
                'INSERT INTO blacklist (username, reason) VALUES (?, ?)',
                (target, description)
            )
        
        conn.commit()
        conn.close()
        
        await update.message.reply_text(f"✅ Жалоба на {target} принята!")

    async def check(self, update: Update, context: CallbackContext):
        """Команда /check"""
        if not context.args:
            await update.message.reply_text("Использование: /check @username")
            return
        
        target = context.args[0]
        
        conn = sqlite3.connect('scam_reports.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM blacklist WHERE username = ?', (target,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            await update.message.reply_text(f"🚨 {target} В ЧЕРНОМ СПИСКЕ!\nПричина: {result[2]}")
        else:
            await update.message.reply_text(f"✅ {target} не найден в черном списке")

    async def stats(self, update: Update, context: CallbackContext):
        """Команда /stats"""
        conn = sqlite3.connect('scam_reports.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM scam_reports')
        total_reports = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM blacklist')
        total_blacklisted = cursor.fetchone()[0]
        conn.close()
        
        await update.message.reply_text(f"📊 Статистика:\nЖалоб: {total_reports}\nВ черном списке: {total_blacklisted}")

    async def button_handler(self, update: Update, context: CallbackContext):
        """Обработчик кнопок"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "check":
            await query.edit_message_text("Отправь: /check @username")
        elif query.data == "report":
            await query.edit_message_text("Отправь: /report @username причина")
        elif query.data == "stats":
            await self.stats(update, context)

    def run(self):
        """Запуск бота"""
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("report", self.report))
        application.add_handler(CommandHandler("check", self.check))
        application.add_handler(CommandHandler("stats", self.stats))
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        logger.info("🎮 Roblox Zona | Anti Scam Base запущен!")
        application.run_polling()

if __name__ == '__main__':
    bot = AntiScamBot()
    bot.run()
