from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import db.db as db

# Главное меню админа (с формированием inline_keyboard вручную)
admin_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="Рассылка", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton(text="Показать ТОПОВ", callback_data="admin_show_top"),
            InlineKeyboardButton(text="Сброс топа", callback_data="admin_reset_top"),
        ],
        [InlineKeyboardButton(text="Экспорт CSV", callback_data="admin_export_csv")],
        # New admin action buttons
        [
            InlineKeyboardButton(
                text="Список пользователей", callback_data="admin_listusers"
            ),
            InlineKeyboardButton(
                text="Установить премиум", callback_data="admin_setpremium"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Установить баллы", callback_data="admin_setpoints"
            ),
            InlineKeyboardButton(text="Заблокировать", callback_data="admin_ban"),
        ],
        [
            InlineKeyboardButton(text="Приглашения", callback_data="admin_setinvites"),
            InlineKeyboardButton(text="Разблокировать", callback_data="admin_unban"),
        ],
        [InlineKeyboardButton(text="Выйти", callback_data="admin_exit")],
    ]
)


# Клавиатура для проверки скриншота
def story_review_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять", callback_data=f"story_accept:{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"story_reject:{user_id}"
                ),
            ]
        ]
    )
