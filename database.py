import psycopg2
from tkinter import messagebox
import os

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "loot_generator")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "1234")
DB_PORT = os.environ.get("DB_PORT", "5432")

def connect_db():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        return conn
    except psycopg2.Error as e:
        messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к базе данных: {e}")
        return None

def fetch_mobs(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, avatar_path FROM mobs")
        mobs = cur.fetchall()
        return mobs
    except psycopg2.Error as e:
        messagebox.showerror("Ошибка базы данных", f"Ошибка при получении списка мобов: {e}")
        return []

def get_loot_for_mob(conn, mob_id):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT l.name, ml.drop_chance
            FROM mob_loot ml
            JOIN loot l ON ml.loot_id = l.id
            WHERE ml.mob_id = %s
        """, (mob_id,))
        loot_data = cur.fetchall()
        return loot_data
    except psycopg2.Error as e:
        messagebox.showerror("Ошибка базы данных", f"Ошибка при получении лута для моба: {e}")
        return []

def fetch_all_loot(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM loot")
        loot_items = cur.fetchall()
        return loot_items
    except psycopg2.Error as e:
        messagebox.showerror("Ошибка базы данных", f"Ошибка при получении списка лута: {e}")
        return []

def fetch_mob_loot_config(conn, mob_id):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT l.id, l.name, ml.drop_chance
            FROM mob_loot ml
            JOIN loot l ON ml.loot_id = l.id
            WHERE ml.mob_id = %s
        """, (mob_id,))
        current_mob_loot = {item[0]: item[2] for item in cur.fetchall()} # {loot_id: drop_chance}
        return current_mob_loot
    except psycopg2.Error as e:
        messagebox.showerror("Ошибка базы данных", f"Ошибка при получении конфигурации лута: {e}")
        return {}

def execute_query(conn, query, params=None):
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return True
    except psycopg2.Error as e:
        messagebox.showerror("Ошибка базы данных", f"Ошибка выполнения запроса: {e}")
        return False