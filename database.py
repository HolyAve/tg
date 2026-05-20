import sqlite3
from datetime import datetime

DB_NAME = "referral.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            join_date TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points (
            user_id INTEGER PRIMARY KEY,
            score INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных готова")

def register_user(user_id, referrer_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Проверяем, существует ли пользователь
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    
    if not exists:
        # Новый пользователь - регистрируем
        cursor.execute('''
            INSERT INTO users (user_id, referrer_id, join_date, is_active)
            VALUES (?, ?, ?, 1)
        ''', (user_id, referrer_id, datetime.now()))
        
        cursor.execute('''
            INSERT OR IGNORE INTO points (user_id, score)
            VALUES (?, 0)
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        # Начисляем очки пригласителю за нового пользователя
        if referrer_id and referrer_id != user_id:
            add_points(referrer_id, 2)
            print(f"🎉 +2 очка пригласителю {referrer_id} от нового пользователя {user_id}")
        
        return True
    else:
        # Пользователь уже существует - обновляем пригласителя, если он пришёл по ссылке
        if referrer_id and referrer_id != user_id:
            # Проверяем, был ли уже у пользователя пригласитель
            cursor.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
            current_referrer = cursor.fetchone()[0]
            
            if current_referrer is None or current_referrer == 0:
                # У пользователя нет пригласителя - добавляем
                cursor.execute('''
                    UPDATE users SET referrer_id = ?, is_active = 1 WHERE user_id = ?
                ''', (referrer_id, user_id))
                conn.commit()
                
                add_points(referrer_id, 2)
                print(f"🎉 +2 очка пригласителю {referrer_id} от существующего пользователя {user_id}")
        
        conn.close()
        return False
    
   

def add_points(user_id, points):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE points SET score = score + ? WHERE user_id = ?
    ''', (points, user_id))
    
    conn.commit()
    conn.close()

def get_points(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT score FROM points WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else 0

def get_referrer(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else None

def deactivate_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        referrer_id = result[0]
        add_points(referrer_id, -2)
        print(f"📉 -2 очко у пригласителя {referrer_id} (вышел {user_id})")
    
    cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_top_users(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT points.user_id, points.score 
        FROM points 
        ORDER BY points.score DESC 
        LIMIT ?
    ''', (limit,))
    
    result = cursor.fetchall()
    conn.close()
    return result

def user_exists(user_id):
    """Проверяет, существует ли пользователь в базе"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def update_user_active_status(user_id, is_active):
    """Обновляет статус активности пользователя в канале"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET is_active = ? WHERE user_id = ?
    ''', (1 if is_active else 0, user_id))
    conn.commit()
    conn.close()