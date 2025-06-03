# save_file_ids.py

import db.db as db

# Список пар (index, file_id) для всех уроков
lesson_file_ids = [
    (0, "BAACAgIAAxkBAAIEh2g9ZwiW0D1ixur-9YDBYZ-mRNEUAAJBawACeAToSfAmUnpgCCd1NgQ"),
    (1, "BAACAgIAAxkBAAIEjGg9auSHuAyhkfnCEylwUjGkzS9iAALjbQACDhCxSWHeo_I_xVAgNgQ"),
    (2, "BAACAgIAAxkBAAIEjmg9avxHxhiJKWmQBJnePTRHGXScAALxbQACDhCxSQy4gKD3Iue9NgQ"),
    (3, "BAACAgIAAxkBAAIEkGg9axPG5OO30UtGWGyY3zWE3E3PAAJ5bgACDhCxSQIsyiGi9TmMNgQ"),
    (4, "BAACAgIAAxkBAAIEkmg9ayaJXkiWVLyRTautS-XDgR5cAAKpbgACDhCxSfPQbEbTVLxuNgQ"),
    (5, "BAACAgIAAxkBAAIElGg9a0BWr2g2Q3dy42uQFtxi5_gJAAIFbwACDhCxSf8Z9E7nFYKzNgQ"),
    (6, "BAACAgIAAxkBAAIElmg9a0hD98x6uQYUxeF2uLAFBinlAALibgACDhCxSTWOVZ4pdNj7NgQ"),
]


def main():
    # Инициализируем подключение к базе (если ещё не инициализировано)
    # В зависимости от того, где у вас лежит файл data.db, можно передать путь явно:
    # db.init_db("data.db")
    db.init_db()

    # Записываем file_id для каждого урока
    for index, fid in lesson_file_ids:
        db.set_lesson_file_id(index, fid)
        print(f"Урок {index}: сохранён file_id")


if __name__ == "__main__":
    main()
