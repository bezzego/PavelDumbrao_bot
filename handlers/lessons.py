from aiogram import types
from aiogram import Router
import asyncio
import db.db as db
from db.db import get_lesson_file_id, set_lesson_file_id
from aiogram.types import FSInputFile

router = Router()


@router.message(lambda message: message.text and message.text.lower() == "уроки")
async def lessons_button_handler(message: types.Message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    if not user_data:
        db.add_user(
            user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        user_data = db.get_user(user_id)

    progress = user_data.get("challenge_progress", 0)
    if progress >= len(CODE_WORDS):
        await message.answer("🎉 Вы уже прошли все уроки челленджа!")
        return

    await message.answer(
        "🚨 **Важная информация перед уроком!** 🚨\n\n"
        "В каждом уроке ты увидишь **большие буквы**, которые будут на экране. Они будут **случайными**, но если ты соберёшь из них правильное слово — сможешь перейти к следующему уроку! \n\n"
        "✅ **Что нужно сделать:**\n\n"
        "1. В каждом уроке на экрчане появятся **большие буквы**.\n"
        "2. **Собери их в правильное слово**.\n"
        "3. Введи это слово в бот, чтобы получить доступ к следующему уроку.\n\n"
        "❗️ **Важно**: без правильного слова следующий урок не откроется! Так что будь внимателен и не пропусти!\n\n"
        "🎯 Готов? Вперёд, на новый уровень! 💥\n\n",
        parse_mode="Markdown",
    )
    await asyncio.sleep(10)

    code_index = progress

    if code_index == 0:
        lesson_text = LESSON_TEXTS[0]
        existing_file_id = get_lesson_file_id(code_index)
        if existing_file_id:
            sent = await message.answer_video(video=existing_file_id)
        else:
            video_path = VIDEO_FILES[code_index]
            sent = await message.answer_video(video=FSInputFile(video_path))
            set_lesson_file_id(code_index, sent.video.file_id)
        await message.answer(lesson_text, parse_mode="Markdown")
    elif code_index == 1:
        lesson_text = LESSON_TEXTS[1]
        existing_file_id = get_lesson_file_id(code_index)
        if existing_file_id:
            sent = await message.answer_video(video=existing_file_id)
        else:
            video_path = VIDEO_FILES[code_index]
            sent = await message.answer_video(video=FSInputFile(video_path))
            set_lesson_file_id(code_index, sent.video.file_id)
        await message.answer(lesson_text, parse_mode="Markdown")
        return
    elif code_index == 2:
        lesson_text = LESSON_TEXTS[2]
        existing_file_id = get_lesson_file_id(code_index)
        if existing_file_id:
            sent = await message.answer_video(video=existing_file_id)
        else:
            video_path = VIDEO_FILES[code_index]
            sent = await message.answer_video(video=FSInputFile(video_path))
            set_lesson_file_id(code_index, sent.video.file_id)
        await message.answer(lesson_text, parse_mode="Markdown")
        return
    elif code_index == 3:
        lesson_text = LESSON_TEXTS[3]
        existing_file_id = get_lesson_file_id(code_index)
        if existing_file_id:
            sent = await message.answer_video(video=existing_file_id)
        else:
            video_path = VIDEO_FILES[code_index]
            sent = await message.answer_video(video=FSInputFile(video_path))
            set_lesson_file_id(code_index, sent.video.file_id)
        await message.answer(lesson_text, parse_mode="Markdown")
        return
    elif code_index == 4:
        lesson_text = LESSON_TEXTS[4]
        existing_file_id = get_lesson_file_id(code_index)
        if existing_file_id:
            sent = await message.answer_video(video=existing_file_id)
        else:
            video_path = VIDEO_FILES[code_index]
            sent = await message.answer_video(video=FSInputFile(video_path))
            set_lesson_file_id(code_index, sent.video.file_id)
        await message.answer(lesson_text, parse_mode="Markdown")
        return
    elif code_index == 5:
        lesson_text = LESSON_TEXTS[5]
        existing_file_id = get_lesson_file_id(code_index)
        if existing_file_id:
            sent = await message.answer_video(video=existing_file_id)
        else:
            video_path = VIDEO_FILES[code_index]
            sent = await message.answer_video(video=FSInputFile(video_path))
            set_lesson_file_id(code_index, sent.video.file_id)
        await message.answer(lesson_text, parse_mode="Markdown")
        return
    elif code_index == 6:
        lesson_text = LESSON_TEXTS[6]
        existing_file_id = get_lesson_file_id(code_index)
        if existing_file_id:
            sent = await message.answer_video(video=existing_file_id)
        else:
            video_path = VIDEO_FILES[code_index]
            sent = await message.answer_video(video=FSInputFile(video_path))
            set_lesson_file_id(code_index, sent.video.file_id)
        await message.answer(lesson_text, parse_mode="Markdown")
        return
    else:
        lesson_text = (
            LESSON_TEXTS[code_index] if code_index < len(LESSON_TEXTS) else "Урок..."
        )
        # Convert Markdown-style bold/links to HTML for the caption if needed
        html_caption = (
            lesson_text.replace("**", "<b>")
            .replace("<b>", "</b>", 1)  # crude, only if needed
            .replace("[", "")
            .replace("]", "")  # crude, only for fallback
        )
        # If you want to support Markdown links in LESSON_TEXTS, use a more robust conversion.
        existing_file_id = get_lesson_file_id(code_index)
        if existing_file_id:
            sent = await message.answer_video(
                video=existing_file_id, caption=lesson_text, parse_mode="HTML"
            )
        else:
            video_path = VIDEO_FILES[code_index]
            sent = await message.answer_video(
                video=FSInputFile(video_path),
                caption=lesson_text,
                parse_mode="HTML",
            )
            set_lesson_file_id(code_index, sent.video.file_id)

    await message.answer(
        "⚙️ Сделай задание, отправь промокод (СЛОВО, которое ты собрал из букв) — и забирай баллы.\n\n"
        "Всё просто: сделал → подтвердил → пошёл дальше.\n\n"
        "🎯 Выполняй в темпе — так больше шансов выиграть призы и реально встроить GPT в работу.\n\n"
        "📌 Если что — поддержка и движуха в чате:\n\n"
        "[💬 Войти в чат (после подписки)](https://t.me/...)",
        parse_mode="Markdown",
    )


# Handler for receiving video files and returning their file_id
@router.message(lambda message: message.video is not None)
async def video_receiver(message: types.Message):
    """
    При отправке видео боту вручную этот хэндлер вернёт file_id видео.
    """
    file_id = message.video.file_id
    await message.answer(f"File_id этого видео: {file_id}")


CODE_WORDS = ["Brain", "Logic", "Think", "Learn", "Smart", "Profit", "Agent"]
LESSON_TEXTS = [
    """День 0. ВВодный. Поехали.🧠

Йоу, кожаный.😎 [Я Павел Думбрао Ai](https://t.me/c/2466104577/69)

Если ты это читаешь — значит, ты уже не просто наблюдатель, а участник. А значит, у нас есть 7 дней, чтобы ты перестал играть в выживание и начал пользоваться мозгом 2.0 — искусственным.

Этот курс — не лекции и не “послушай эксперта”.
Это мой личный стиль жизни, который теперь может стать и твоим.
GPT для меня — не игрушка, а второй мозг. И через 7 дней ты поймёшь, почему я без него даже кофе не завариваю.

Что тебя ждёт:

- 7 дней — 7 заданий
- короткие видео и конкретика
- не теоретика, а практика
- бот, баллы, чат и движ
- и да, я тут не гуру, а твой партнёр по апгрейду

Задание на сегодня (День 0):

1. [Зарегистрируй GPT](https://t.me/c/2466104577/69) — бесплатную версию или лучше сразу платную (если хочешь по‑взрослому)
2. [Установи VPN](https://t.me/c/2466104577/69) на комп или телефон (если ты из России — без этого никак)
3. [Изучи правила и инструкции](https://t.me/c/2466104577/69) канала — да, внимательно
4. Когда всё сделаешь — напиши в чате: "Сделал(а) или свой вопрос"

Тут нет неправильных ответов.
Есть движение. Есть привычка. Есть результат.

Пиши в чат, если уже посмотрел вводный.
И запомни: ты — не один.
У тебя теперь есть AI.
И ты не представляешь, на что вы вдвоём способны.""",
    """ДЕНЬ 1. Погнали в мир ИИ 🚀
Сегодня не просто Zoom — сегодня ты официально вступил в секту людей, которые больше не делают всё вручную. GPT теперь твой партнёр, стажёр и креативный отдел в одном флаконе. И да, он не просит отпуск 😎

Тема: Пример: как продвигать психолога, ничего не делая, и при этом выглядеть как гений 🧠💼

1. Зачем всё это 🤔

- Чтобы GPT начал реально помогать, а не просто “привет, чем могу помочь?”
- Чтобы ты делал контент, как будто у тебя команда из трёх маркетологов, двух дизайнеров и одного шамана 🧙‍♂️
- Чтобы экономить время, нервы и не выпадать в чаты с фразой “ну мы подумаем” 🕳️

2. Пример задачи 🎯
   Ты маркетолог. ЦА — психологи. Пишешь GPT:
   Сделай пошаговый план вирусного контента для психолога. Внимание, доверие, продажа. Примеры постов, тем, визуалов. Я — ленивая жопа, делать ничего не хочу. Просто копипаст и в путь 🛋️📲

Или:
Представь, что я — табула раса с Wi-Fi. Дай лучший вопрос, чтобы всё сработало само 🔄

3. Что GPT реально умеет 💪

- Пишет офферы, сторисы, посты, лендинги — быстрее, чем ты открываешь Google Docs ⚡
- Может говорить как твой бро, как профессор, как строгая мама — выбирай сам 🎭
- Понимает, что такое воронка, и не наливает её в баре 🍸

4. Как не вызывать у него баг в мозгу 🧩

- Скажи, кто ты, что продаёшь и кому
- Укажи цель: хочу клиентов, прибыль или трафик 💰
- После ответа пиши “докрути” 🔁
  Это как “ещё чашечку” в кофейне — пока не проснёшься ☕️

5. Превращаем GPT в помощника 🤖

- Расскажи, кто ты и чем занимаешься
- Пропиши стиль общения и что не нужно “официальщины” 🧾
- Не жди, что он всё запомнит — он нейросеть, а не твоя бабушка 🧓

6. Собираем AI-команду 🛠️

- GPT может быть CEO, маркетологом и дизайнером в одном лице 🧑‍💼🎨
- Каждому агенту — чёткую роль
- Главное — не забывай, кто тут босс (спойлер: ты) 👑

7. Проверка гипотез (магия, но рабочая) ✨

- GPT может симулировать 100 000 человек 👥
- Тест оффера за 15 минут — без бюджета, без боли 🧪
- Получил результат → докрутил → вперёд 🚀

8. Что делать тебе 📋
9. Напиши, кто ты и чего хочешь
10. Закинь GPT эту инфу
11. Жми “докрути”, пока не появится “ВАУ” 😮
12. Делись результатами — это как чих: заразно, но полезно 🤧🔥

Финалка с прищуром 😏

- GPT — не просто ИИ. Это как нанять Стива Джобса, только за 0 рублей 🧠💼
- Кто игнорит ИИ — через 2 года будет просить у нейросети сделать резюме 📉
- Что ты делал 15 минут назад? А GPT уже проверил идею на толпе
- “Докрути” — твоя новая кнопка “усиль мозг” 🧠💥""",
    """День 2. Освобождаем время с GPT ⚡️🤖

Сегодня не философия, а чистая практика. Разбираем, как делегировать рутину GPT и выигрывать десятки часов в неделю ⏳🔥

Вот о чём был Zoom:

1. Домашка — обязательна 📌
   Если не сделал День 1 — дальше смысла нет. Рост идёт по ступенькам 🪜

2. Главная идея 💡
   GPT — это твой новый виртуальный сотрудник. Делает отчёты, отвечает за тебя, формулирует задачи, думает, советует и приоритизирует 🧠🧾

3. Примеры, что делегировать:
   🟢 отчёты по Wildberries
   🟢 Excel-таблицы
   🟢 ответы клиентам
   🟢 написание постов
   🟢 оформление офферов
   🟢 инструкции (как для тупых)
   🟢 резюме Zoom-созвонов
   🟢 анализ идей и гипотез
   🟢 симуляции с целевой аудиторией
   🟢 приоритизация задач
   🟢 постановка ТЗ команде
   🟢 планирование действий
   🟢 создание лендингов, презентаций

4. Как делегировать 🤝
   Объясни GPT, что тебе нужно. Один раз. Дальше он делает сам — быстрее и понятнее, чем большинство живых сотрудников 🚀

5. Ты не просто используешь GPT — ты строишь систему 🛠
   🔹 Придумываешь проект
   🔹 Проверяешь идею через GPT
   🔹 Получаешь возражения, фидбек, офферы
   🔹 Прогоняешь от лица клиентов, сотрудников, инвесторов
   🔹 Собираешь MVP — бесплатно и за час

6. Автоматизация next-level ⚙️
   Ты диктуешь задачу голосом → она летит в GPT → формируется ТЗ → летит в Google Диск → ассистент работает.
   Ты не участвуешь. А дела — делаются 💼🤫

7. Подсказка 👇
   Не тяни. Применяй прямо сейчас. Делай. Делай. Делай. GPT не даст тебе результата, если ты просто смотришь 🧐

Домашка на сегодня 📒

1️⃣ Найди 1 задачу, которую ты регулярно делаешь вручную
2️⃣ Пропиши GPT, что ты хочешь, чтобы он сделал за тебя
3️⃣ Делегируй
4️⃣ Посчитай, сколько времени сэкономил
5️⃣ Напиши в чат: что делегировал и сколько времени реально выиграл
6️⃣ Подумай: куда ещё можно внедрить GPT, чтобы освободить часы на прокачку себя и бизнеса ⏱️📈

Завтра будет сложнее 💣 Будь готов.
Если было полезно — отмечай в Telegram @PavelDumbrao, выложи сторис, реакцию, огонёк 🔥 или отзыв 🙏""",
    """🔥 День 3. Промпт-инжиниринг: не фишка — фундамент

Что такое промпт? (ссылка тут)
Это язык общения с GPT. Чем чётче ты — тем умнее он.
GPT не читает мысли. Он не понимает, что ты "имел в виду" — только то, что ты сказал.

📌 Формула сильного промпта:
🎭 Роль — кто GPT сейчас: маркетолог, коуч, директор
📍 Контекст — тема, ниша, ты сам
🎯 Цель — зачем тебе это
🧾 Формат — куда вставлять (ТГ, лендинг, оффер)

👨‍💻 Пример:
Будь моим AI-продюсером и стратегом по деньгам. Твоя задача — привести меня к 1 млн рублей за 30 дней. Моя ниша — […]. Аудитория — […]. Я уже делал […].

🔁 Один и тот же промпт — разные роли:

🧠 Стратег/фаундер — схемы, деньги, решения
🧘 Коуч — смыслы, мотивация, застревания
🧑‍💼 Директор — задачи, контроль, порядок
⚙️ Автоматизатор — пайплайны, боты, CRM
🎬 Продюсер — упаковка, запуск, контент
📐 Архитектор — структура, декомпозиция

Не мешай всё в одном. Лучше 1–2 роли за раз.

💼 Кейс: AGENT X

Цель: заработать 1 млн за 30 дней без продукта
Решение:
🕸 Используем окружение — предпринимателей
📦 Упаковываем их продукты под GPT и Telegram
🤖 GPT пишет тексты, автоворонки, боты
💸 Ты соединяешь и берёшь процент

AI-команда:
🧑‍💼 AI-директор
📦 AI-пакетолог
✍️ AI-копирайтер
🎯 AI-оффермейкер
🧭 AI-навигатор по связям
📬 AI-аутричер
🛠 AI-автоматизатор

📚 Домашка:

1. Возьми свою задачу или идею
2. Напиши промпт: Ты — [роль]. Моя цель — […]. Помоги мне […]. 
3. Прогони один и тот же промпт от 3–5 разных ролей
4. На каждый ответ жми: "Докрути" — пока не станет сильно
5. Напиши GPT: "Какие роли ещё предложишь?"
6. Заведи отдельные чаты под ключевые роли: директор, маркетолог, копирайтер и т.д.

⚡ Лайфхак:

Записывай Zoom через Fathom или аналог — он сразу делает текст, видео и чеклист. Уже через 5 минут можно раздавать задачи команде. Без менеджеров.

🔥 Финалка

ИИ — не игрушка. Это новый способ думать.
Ты не должен стать технарём. Ты должен стать постановщиком задач.
Вся магия — в том, насколько метко ты спрашиваешь.

Внедряй. Пробуй. Нажимай. GPT — это твой доп.мозг на стероидах.
Поехали! ✊""",
    """День 4. GPT в твоей системе и бизнесе

⚙️ GPT — это не просто помощник, а операционный рычаг. Он должен быть встроен в повседневку: автоматизация, делегирование, систематизация.
📂 Создавай проекты прямо в GPT — по темам. Это папки с контекстом, где он всё помнит.
🗂 Храни всё в понятных местах:
– Notion — для больших задач
– Заметки — для быстрых мыслей
– Google Docs / Telegraph — как временное хранилище или для шаринга
🪓 Делай проекты по кускам. Делишь на части — GPT не путается.
🧑‍💻 Делегируй не только GPT, но и людям. Один агент — одна задача. Один сотрудник — один GPT-помощник.
⏱ Отслеживай выгоду: сколько времени освободилось, куда оно ушло, стал ли зарабатывать больше.
🧠 GPT формирует мышление. Он не просто решает — он обучает думать структурно.

📚 ДОМАШКА

1. Выбери 3 задачи, которые ты делаешь каждый день — и можешь отдать GPT
2. Пропиши мини-сценарии: что делает GPT, как, зачем
3. Создай проект-папку в GPT
4. Добавь в заметки раздел: GPT делает за меня — что делегировал, как это работает, сколько времени сэкономил
5. Найди 5 задач, которые можешь скинуть сотрудникам или родным — и добавь туда GPT
6. Напиши в чат:
   – Что уже автоматизировал
   – Кто теперь делает задачи (GPT, сотрудник, семья)
   – Сколько времени освободилось и куда ты его перенаправляешь

💡 ВАЖНОЕ

– Если GPT тупит — спрашивай: почему ты так решил? Разложи по шагам
– Учись формулировать задачи. GPT может помочь докрутить твой вопрос
– Не смешивай всё в одном чате. Один проект — один диалог
– Цель на месяц: освободить минимум 40 часов
– Начни вести реестр: где GPT реально помогает и как ты становишься эффективнее

🧠 Стратегия начинается с головы. GPT — твой виртуальный стратег. Делай, докручивай, применяй.

Обещал Notion показать - вот как пример Ссылка""",
    """💸 Урок 5. Монетизация ИИ

Как начать зарабатывать на ChatGPT — просто, быстро, по шагам.

👣 С чего начать:

1. Выпиши все задачи, которые ты делаешь каждый день.
2. Прогони их через GPT — где можно автоматизировать или ускорить?
   ⏳ Экономишь время → берешь больше задач → зарабатываешь больше.

💰 Прямая монетизация:
🔧 Используй GPT как исполнителя, а не просто как советника.
🔁 Подключи его к N8N, Make или Zapier — GPT начнет делать задачи сам.
👨‍💻 Даже без кода — собираешь цепочку и запускаешь.

🤖 Что умеет GPT:
📝 Писать тексты, посты, сценарии
📸 Генерировать фото и видео
📅 Работать как ассистент: встречи, напоминания, идеи
🍝 Распознавать фото (например, еда → калории)
🗣️ Принимать голосовые команды и всё записывать

🔍 Где брать заказы:
🛠 Kwork, Workzilla, Upwork и другие биржи
💡 GPT делает задачи за 3 минуты → по 500₽ каждый
📦 Масштабируешь через ассистента или бота

📱 Telegram-бот с GPT:
⚙️ Раньше стоил 250К и месяц разработки
🚀 Сейчас — промт + N8N → бот готов
📈 Быстро запускается, легко масштабируется

💼 Для продвинутых:
🚀 Делай AI-продукты, ботов, автоматизированные системы
💡 GPT = генератор идей + ассистент + кодер
🔎 Ищи партнёрки, делай системы под бизнес

📌 Домашка:
✍️ Выпиши все свои задачи
🔍 Найди, что можно делегировать GPT
📊 Посчитай экономию времени и денег
🎯 Спроси GPT: где деньги в твоей нише?

⏳ Время = сейчас
🏃‍♂️ Через год будет поздно
📲 GPT — это не магия, это инструмент
💎 Кто приносит пользу — тот зарабатывает""",
    """🔥 День 6 — Прокачка эффективности

🎥 Тема видео:
Как GPT реально помогает работать, думать, планировать

🎯 Фокус:
Убираем туман в голове, включаем стратегию, начинаем ДЕЛАТЬ

🤖 GPT — это не чатик. Это твой стратег

У него есть память, руки, ноги

Он может:
• писать посты
• считать бюджет
• ставить задачи
• вносить встречи в календарь
• делать всё, что у тебя в голове висит как "потом"

👉 Я собрал себе такого помощника — Telegram-бот, с памятью и встроенной логикой. Работает

📌 Что ты можешь сделать уже сейчас:

1. Поставь цель
   Например: Хочу 1 млн ₽ в месяц на обучении

2. Попроси GPT сделать стратегию
   Напиши: Сделай пошаговую стратегию под эту цель

3. Попроси декомпозицию
   Напиши: Разбей на недели. Что делать в первую, вторую, третью?

4. Сохрани это в Notion или Заметки
   Утром просыпаешься — чек-лист перед глазами. Просто жми галочки
   Думать не надо — делать надо

🧠 Лайфхаки из эфира:

– Не опирайся на мотивацию — она флуктуирует
– Мозгу нужна ясность: план, контроль, фокус
– Чем чётче формулируешь — тем лучше GPT помогает
– Добавь примерное время на каждую задачу
– Фиксируй прогресс, хвали себя, отмечай, что сделано

🏡 Домашка:

Ответь письменно (можно в GPT или в заметке):

Что GPT упростил лично тебе?
Что стало быстрее? Что яснее?
В чём реально помог? Где сдвинул?
Цель: Обрести
Ясность в действиях! ( Ответ в чате: Построил Стратегию/Декомпозицию на месяц) ✅

📍 Мини-инструкция:

1. Создай проект в Notion: Цель месяца
2. Попроси GPT:
   Ты мой коуч. Помогаешь дойти до цели. Без сюсюканья. Давай пошагово
3. Добавь задачи с галочками
4. Начинай делать

Не хочешь в Notion — делай в Заметках, Excel, хоть на стене. Главное — чтобы была система

⚡️ Цитаты из эфира:

Я встал — и знаю, что делать. Спасибо тебе, GPT
Ты не в яме. Ты складываешь. Вдох. Выдох. Чек-лист. Погнали
Развитие требует жертвы. И жертва — это твоё время. Дай себе этот фокус

[СОВЕТЫ ПО ПРОМПТАМ](https://t.me/c/2466104577/75)""",
]

# Пути до видеофайлов, соответствующие CODE_WORDS (имена файлов взять из папки video)
VIDEO_FILES = [
    "video/Урок0.mp4",
    "video/Урок1.mp4",
    "video/Урок2.mp4",
    "video/Урок3.mp4",
    "video/Урок4.mp4",
    "video/Урок5.mp4",
    "video/Урок6.mp4",
]


@router.message(lambda m: m.text and m.text.lower() in [c.lower() for c in CODE_WORDS])
async def code_word_handler(message: types.Message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    if not user_data:
        # If somehow user not in DB (should not happen after /start), add them
        db.add_user(
            user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        user_data = db.get_user(user_id)
    progress = user_data.get("challenge_progress", 0)
    text_lower = message.text.strip().lower()
    # If already completed all lessons
    if progress >= len(CODE_WORDS):
        await message.answer("🎉 Вы уже прошли все уроки челленджа!")
        return
    # Determine the index of the code word
    code_index = None
    for i, code in enumerate(CODE_WORDS):
        if code.lower() == text_lower:
            code_index = i
            break
    if code_index is None:
        # Not a recognized code (should not happen due to filter)
        return
    # Check if this is the expected next code word
    if code_index == progress:
        next_index = code_index + 1
        if next_index < len(LESSON_TEXTS):
            await message.answer(
                "**Через пару минут прилетит новый видеоурок.**\n\n"
                "Будь готов!\n\n"
                "Если идёшь в темпе — получаешь баллы и двигаешься вверх по рейтингу.\n\n"
                "**1. Подпишись на канал Павла Думбрао:**\n\n"
                "[👉 Перейти в канал](https://t.me/...)\n\n"
                "**2. Только после подписки тебя пустит в чат участников:**\n\n"
                "[💬 Войти в чат](https://t.me/...)",
                parse_mode="Markdown",
            )
            await asyncio.sleep(10)

            lesson_text = (
                LESSON_TEXTS[next_index]
                if next_index < len(LESSON_TEXTS)
                else "Урок..."
            )
            existing_file_id = get_lesson_file_id(next_index)
            if existing_file_id:
                await message.answer_video(video=existing_file_id)
            else:
                video_path = VIDEO_FILES[next_index]
                sent = await message.answer_video(video=FSInputFile(video_path))
                set_lesson_file_id(next_index, sent.video.file_id)
            await message.answer(lesson_text, parse_mode="Markdown")

            await message.answer(
                "⚙️ Сделай задание, отправь промокод (СЛОВО, которое ты собрал из букв) — и забирай баллы.\n\n"
                "Всё просто: сделал → подтвердил → пошёл дальше.\n\n"
                "🎯 Выполняй в темпе — так больше шансов выиграть призы и реально встроить GPT в работу.\n\n"
                "📌 Если что — поддержка и движуха в чате:\n\n"
                "[💬 Войти в чат (после подписки)](https://t.me/...)",
                parse_mode="Markdown",
            )

            db.update_points(user_id, 10)
            db.increment_progress(user_id)
        else:
            # If that was the last lesson
            await message.answer("🎉 Поздравляем! Вы прошли все 7 уроков челленджа.")

    else:
        # Code word is either already used or out of order
        if code_index < progress:
            # Already used this code word
            await message.answer("⚠️ Это кодовое слово уже было использовано ранее.")
        else:
            # code_index > progress (they are trying a later code without doing previous ones)
            await message.answer(
                "⚠️ Вы забегаете вперед. Сначала введите кодовое слово предыдущего урока."
            )
