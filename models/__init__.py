# models/__init__.py
from .user import create_user_table, get_user_by_username, add_user, get_db_connection
from .exercise import create_exercises_table, add_exercise, get_exercises_by_user
