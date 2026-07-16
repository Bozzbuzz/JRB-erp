import sqlite3
import os

def upgrade():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'erp.db')
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN return_date DATE;")
        print("Kolom return_date berhasil ditambahkan ke tabel orders.")
    except Exception as e:
        print("Error atau kolom sudah ada:", e)
    finally:
        conn.commit()
        conn.close()

if __name__ == '__main__':
    upgrade()
