from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_parallels_keyboard(parallels: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for p in parallels:
        row.append(InlineKeyboardButton(text=p, callback_data=f"parallel_{p}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_letters_keyboard(letters: list[str], parallel: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for letter in letters:
        full_class = parallel + letter
        row.append(InlineKeyboardButton(text=letter.upper(), callback_data=f"letter_{full_class}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_profiles_keyboard(class_name: str, profiles: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for prof in profiles:
        row.append(InlineKeyboardButton(text=prof, callback_data=f"profile_{class_name}_{prof}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_keyboard(notify_enabled: bool = True) -> InlineKeyboardMarkup:
    """Главное меню с динамической кнопкой уведомлений (без кнопки 'Сегодня')"""
    notify_text = "🔔 Уведомления: ВКЛ" if notify_enabled else "🔕 Уведомления: ВЫКЛ"
    buttons = [
        [InlineKeyboardButton(text=notify_text, callback_data="toggle_notify")],
        [InlineKeyboardButton(text="📆 Неделя", callback_data="week")],
        [InlineKeyboardButton(text="📋 Замены", callback_data="replacements")],
        [InlineKeyboardButton(text="🔄 Сменить класс", callback_data="change_class")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# (опционально) старая клавиатура, может пригодиться
def get_classes_keyboard(classes: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for cls in classes:
        row.append(InlineKeyboardButton(text=cls, callback_data=f"class_{cls}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)