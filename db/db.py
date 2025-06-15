import sqlite3


def get_count(query: str, params: tuple = ()) -> int:
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    return row[0] if row else 0


# Global database connection object
conn: sqlite3.Connection = None


def init_db(db_path: str = "database.db"):
    """Initialize the SQLite database, creating tables if they do not exist."""
    global conn
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Create users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            points INTEGER DEFAULT 0,
            premium INTEGER DEFAULT 0,
            invited_by INTEGER,
            ref_bonus_given INTEGER DEFAULT 0,
            challenge_progress INTEGER DEFAULT 0,
            submitted_story INTEGER DEFAULT 0
        )
        """
    )
    try:
        cur.execute("ALTER TABLE users ADD COLUMN submitted_story INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # column already exists

    try:
        cur.execute("ALTER TABLE users ADD COLUMN invite_link TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists

    try:
        cur.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # column already exists

    try:
        cur.execute("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # column already exists

    # Create index on invited_by for faster queries (optional)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_invited_by ON users(invited_by)")

    # Create payments table for pending YooMoney payments
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            label TEXT PRIMARY KEY,
            user_id INTEGER,
            amount INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
        """
    )

    # Create table for storing one-time promo codes
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            user_id INTEGER,
            type TEXT,
            used INTEGER DEFAULT 0
        )
        """
    )

    # Create table for storing video file_ids by lesson index
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS lessons_files (
            lesson_index INTEGER PRIMARY KEY,
            file_id TEXT
        )
        """
    )

    conn.commit()


def add_user(
    user_id: int,
    username: str = None,
    first_name: str = None,
    last_name: str = None,
    invited_by: int = None,
) -> bool:
    """
    Add a new user to the database. If user already exists, update username and names.
    If invited_by is provided for a new user, store it.
    Returns True if a new user was added, False if user already existed.
    """
    cur = conn.cursor()
    # Проверяем, существует ли пользователь с таким user_id
    cur.execute("SELECT user_id, invited_by FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row:
        # User exists, do not insert or update invited_by
        cur.execute(
            "UPDATE users SET username=?, first_name=?, last_name=? WHERE user_id=?",
            (username, first_name, last_name, user_id),
        )
        conn.commit()
        return False

    # Insert new user
    cur.execute(
        "INSERT INTO users (user_id, username, first_name, last_name, invited_by) VALUES (?, ?, ?, ?, ?)",
        (user_id, username, first_name, last_name, invited_by),
    )
    conn.commit()
    return True


def get_user(user_id: int):
    """Retrieve user record by user_id. Returns a dict with user fields or None if not found."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row:
        return dict(row)
    return None


def update_points(user_id: int, delta: int):
    """Add or subtract points for a user by delta amount."""
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET points = points + ? WHERE user_id = ?", (delta, user_id)
    )
    conn.commit()


def set_points(user_id: int, points: int):
    """Set points for a user to an absolute value."""
    cur = conn.cursor()
    cur.execute("UPDATE users SET points = ? WHERE user_id = ?", (points, user_id))
    conn.commit()


def set_premium(user_id: int, flag):
    """
    Set premium status for a user.
    Supports boolean flags (True/False -> 1/0) and integer flags >=2 for permanent discounts.
    """
    cur = conn.cursor()
    # Determine stored value: preserve integer >=2, else store 1 for truthy, 0 for falsy
    if isinstance(flag, int) and flag >= 2:
        value = flag
    else:
        value = 1 if flag else 0
    cur.execute("UPDATE users SET premium = ? WHERE user_id = ?", (value, user_id))
    conn.commit()


def increment_progress(user_id: int):
    """Increment the challenge progress of a user by 1 (for completing a code word)."""
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET challenge_progress = challenge_progress + 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()


def set_ref_bonus_given(user_id: int):
    """Mark that referral bonus has been given for this user."""
    cur = conn.cursor()
    cur.execute("UPDATE users SET ref_bonus_given = 1 WHERE user_id = ?", (user_id,))
    conn.commit()


def get_top_users(limit: int = 10):
    """Get top users by points. Returns list of tuples (user_id, username, first_name, points)."""
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, username, first_name, points FROM users ORDER BY points DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    return [tuple(row) for row in rows] if rows else []


def get_user_count() -> int:
    """Return total number of users."""
    return get_count("SELECT COUNT(*) FROM users")


def get_premium_count() -> int:
    """Return number of premium users."""
    return get_count("SELECT COUNT(*) FROM users WHERE premium = 1")


def get_referral_count() -> int:
    """Return total number of successful referrals (users who were invited by someone)."""
    return get_count("SELECT COUNT(*) FROM users WHERE invited_by IS NOT NULL")


def add_payment(label: str, user_id: int, amount: int):
    """Add a new pending payment record."""
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO payments (label, user_id, amount, status, created_at) VALUES (?, ?, ?, 'pending', datetime('now'))",
        (label, user_id, amount),
    )
    conn.commit()


def set_payment_status(label: str, status: str):
    """Update status of a payment (e.g., 'paid' or 'expired')."""
    cur = conn.cursor()
    cur.execute("UPDATE payments SET status = ? WHERE label = ?", (status, label))
    conn.commit()


def get_pending_payments():
    """Get all pending payments records."""
    cur = conn.cursor()
    cur.execute(
        "SELECT label, user_id, amount, created_at FROM payments WHERE status = 'pending'"
    )
    rows = cur.fetchall()
    return [tuple(row) for row in rows] if rows else []


def delete_user(user_id: int):
    """Delete a user from the database."""
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()


def ban_user(user_id: int) -> None:
    """
    Ban a user by setting the banned flag.
    """
    set_banned(user_id, True)


# --- Banning and unbanning functions ---
def set_banned(user_id: int, banned: bool) -> None:
    """
    Set or clear the banned flag for a user.
    """
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET banned = ? WHERE user_id = ?",
        (1 if banned else 0, user_id),
    )
    conn.commit()


def is_banned(user_id: int) -> bool:
    """
    Check if a user is banned.
    """
    cur = conn.cursor()
    cur.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return bool(row["banned"]) if row else False


def unban_user(user_id: int) -> None:
    """
    Unban a user by clearing the banned flag.
    """
    set_banned(user_id, False)


# --- New functions for lessons_files table ---
def get_lesson_file_id(lesson_index: int) -> str | None:
    """
    Retrieve stored file_id for a given lesson index.
    Returns the file_id string if it exists, or None otherwise.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT file_id FROM lessons_files WHERE lesson_index = ?", (lesson_index,)
    )
    row = cur.fetchone()
    return row[0] if row else None


def set_lesson_file_id(lesson_index: int, file_id: str) -> None:
    """
    Insert or update the file_id for a given lesson index.
    """
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO lessons_files (lesson_index, file_id)
        VALUES (?, ?)
        ON CONFLICT(lesson_index) DO UPDATE SET file_id = excluded.file_id
        """,
        (lesson_index, file_id),
    )
    conn.commit()


# --- Promo code functions ---
def add_promo_code(code: str, user_id: int, code_type: str) -> None:
    """
    Store a new promo code (randomly generated) for a user and given type (e.g., 'top2', 'top3').
    """
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO promo_codes (code, user_id, type, used) VALUES (?, ?, ?, 0)",
        (code, user_id, code_type),
    )
    conn.commit()


def get_promo(code: str):
    """
    Retrieve a promo record by its code. Returns a dict with keys ('code', 'user_id', 'type', 'used') or None.
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM promo_codes WHERE code = ?", (code,))
    row = cur.fetchone()
    return dict(row) if row else None


def mark_promo_used(code: str) -> None:
    """
    Mark a promo code as used.
    """
    cur = conn.cursor()
    cur.execute("UPDATE promo_codes SET used = 1 WHERE code = ?", (code,))
    conn.commit()


# Alias for get_promo
def get_promo_code(code: str):
    """
    Alias for get_promo, returns promo record by its code.
    """
    return get_promo(code)


def reset_top_statuses():
    """
    Сброс премиум статусов для топов (top1, top2, top3) в начале месяца.
    """
    cur = conn.cursor()
    cur.execute("UPDATE users SET premium = 0 WHERE premium = 1")
    conn.commit()


def has_submitted_story(user_id: int) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT submitted_story FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return row and row["submitted_story"] == 1


def mark_story_submitted(user_id: int):
    cur = conn.cursor()
    cur.execute("UPDATE users SET submitted_story = 1 WHERE user_id = ?", (user_id,))
    conn.commit()


# --- Invite link functions ---
def get_invite_link(user_id: int) -> str | None:
    """
    Retrieve the stored invite_link for a user if it exists.
    """
    cur = conn.cursor()
    cur.execute("SELECT invite_link FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return row["invite_link"] if row else None


def set_invite_link(user_id: int, invite_link: str) -> None:
    """
    Store or update the one-time invite link for the given user.
    """
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET invite_link = ? WHERE user_id = ?",
        (invite_link, user_id),
    )
    conn.commit()


def set_referral_count(user_id: int, count: int):
    """
    Устанавливает количество приглашенных пользователей (рефералов) у заданного пользователя.
    """
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET referral_count = ? WHERE user_id = ?", (count, user_id)
    )
    conn.commit()
