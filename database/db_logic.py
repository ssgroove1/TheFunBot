import sqlite3, time, json
from typing import Optional, Tuple, Dict, Any

class DB_Manager:
    def __init__(self, database):
        self.database = database
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.database, timeout=10)
        with conn:
            # Добавлена колонка children с текстовым типом и дефолтным пустым JSON-массивом '[]'
            conn.execute(
                """CREATE TABLE IF NOT EXISTS user_marriages (
                                first_user_id INTEGER,
                                second_user_id INTEGER,
                                created_at REAL DEFAULT 0,
                                children TEXT DEFAULT '[]'
                            )"""
            )
            conn.commit()
            
    # marriages
    def _get_connection(self) -> sqlite3.Connection:
        """Вспомогательный метод для создания и настройки подключения."""
        conn = sqlite3.connect(self.database, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def create_marriage_funbot(self, first_user_id: int, second_user_id: int) -> str:
        if first_user_id == second_user_id:
            return "❌ Нельзя жениться на самом себе!"
            
        # Защита от дублирования: проверяем статус обоих пользователей одновременно
        if self.is_married(first_user_id):
            return "❌ Вы уже состоите в браке!"
        if self.is_married(second_user_id):
            return "❌ Этот пользователь уже состоит в браке!"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_marriages (first_user_id, second_user_id, created_at)
                    VALUES (?, ?, ?)
                """, (first_user_id, second_user_id, time.time()))
                conn.commit()
            return "✅ Брак успешно заключен! 💍"
        except Exception as e:
            return f"❌ Ошибка при создании брака: {e}"
    
    def is_married(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM user_marriages 
                WHERE first_user_id = ? OR second_user_id = ? 
                LIMIT 1
            """, (user_id, user_id))
            return cursor.fetchone() is not None
    
    def get_spouse(self, user_id: int) -> Optional[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT first_user_id, second_user_id 
                FROM user_marriages 
                WHERE first_user_id = ? OR second_user_id = ?
            """, (user_id, user_id))
            row = cursor.fetchone()
            
        if row:
            return row[1] if row[0] == user_id else row[0]
        return None
    
    def get_information_marry(self, user_id: int) -> Optional[Dict[str, Any]]:
        # Используем контекстный менеджер, чтобы гарантировать закрытие
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT first_user_id, second_user_id, created_at 
                    FROM user_marriages 
                    WHERE first_user_id = ? OR second_user_id = ?
                """, (user_id, user_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        finally:
            conn.close() # row_factory требует явного закрытия исходного соединения

    def divorce_simple(self, user_id: int) -> Tuple[bool, str]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM user_marriages 
                    WHERE first_user_id = ? OR second_user_id = ?
                """, (user_id, user_id))
                conn.commit()
                rowcount = cursor.rowcount
            
            if rowcount > 0:
                return True, "Брак расторгнут. 💔"
            return False, "Вы не состояли в браке, нечего расторгать."
        except Exception as e:
            return False, f"Ошибка при разводе: {e}"

    def get_children(self, user_id: int) -> list[int]:
        conn = sqlite3.connect(self.database, timeout=10)
        cursor = conn.cursor()

        cursor.execute(
            """SELECT children FROM user_marriages 
            WHERE first_user_id = ? OR second_user_id = ?""",
            (user_id, user_id),
        )
        row = cursor.fetchone()
        conn.close()

        if row and row[0]:
            try:
                children = json.loads(row[0])
                # Возвращаем максимум первые 10 элементов
                return children[:10]
            except json.JSONDecodeError:
                return []

        return []

    def add_child(self, parent_id: int, child_id: int) -> str:
        # 1. Проверяем, состоит ли parent_id в браке
        if not self.is_married(parent_id):
            return "no_marriage"

        # 2. Получаем текущий список детей
        current_children = self.get_children(parent_id)

        # 3. Проверяем лимит
        if len(current_children) >= 10:
            return "limit_reached"

        # 4. Проверяем дубликат
        if child_id in current_children:
            return "already_exists"

        # 5. Добавляем ребёнка
        current_children.append(child_id)
        children_json = json.dumps(current_children)

        conn = sqlite3.connect(self.database, timeout=10)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE user_marriages 
                SET children = ? 
                WHERE first_user_id = ? OR second_user_id = ?""",
                (children_json, parent_id, parent_id),
            )
            updated = cursor.rowcount > 0

        return "success" if updated else "error"

    def is_child_in_any_family(self, child_id: int) -> bool:
        """Проверяет, является ли пользователь ребёнком в какой-либо семье."""
        conn = sqlite3.connect(self.database, timeout=10)
        cursor = conn.cursor()
        
        cursor.execute("SELECT children FROM user_marriages")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            if row[0]:
                try:
                    children = json.loads(row[0])
                    if child_id in children:
                        return True
                except json.JSONDecodeError:
                    continue

        return False

if __name__ == '__main__':
    manager = DB_Manager('database/fg_db.db')