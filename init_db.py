import sqlite3
import os

# Ensure 'instance' directory exists
os.makedirs('instance', exist_ok=True)

# Path to database
DB_PATH = os.path.join('instance', 'tourism.db')


def setup_database():
    # Remove old DB if exists (clean reset during development)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🗑️ Old database removed.")

    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute('PRAGMA foreign_keys = ON')

    # --- Create Tables ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        phone TEXT,
        location TEXT,
        registration_date TEXT DEFAULT (datetime('now', 'localtime'))
    )
    ''')
    print("✅ Created table: users")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        registration_date TEXT DEFAULT (datetime('now', 'localtime'))
    )
    ''')
    print("✅ Created table: admin")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        destination TEXT NOT NULL,
        description TEXT NOT NULL,
        price INTEGER NOT NULL,
        duration TEXT NOT NULL,
        image_url TEXT,
        status TEXT DEFAULT 'Available'
    )
    ''')
    print("✅ Created table: packages")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        package_id INTEGER NOT NULL,
        booked_on DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE
    )
    ''')
    print("✅ Created table: bookings")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        user_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        submitted_on DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ Created table: feedback")

    # --- Insert Default Data ---
    try:
        cursor.execute("""
        INSERT INTO admin (name, email, password) 
        VALUES ('Super Admin', 'admin@example.com', 'admin123')
        """)
        print("👑 Default admin inserted.")

        cursor.execute("""
        INSERT INTO users (name, email, password, role, phone, location)
        VALUES ('Test User', 'user@example.com', 'user123', 'user', '9876543210', 'Delhi')
        """)
        print("🙋 Test user inserted.")

        cursor.execute("""
        INSERT INTO packages (title, destination, description, price, duration, image_url)
        VALUES (
            'Goa Beach Tour',
            'Goa',
            'Relax on the beaches of Goa with 3 nights stay and fun activities.',
            12000,
            '4 Days / 3 Nights',
            'https://images.unsplash.com/photo-1507525428034-b723cf961d3e'
        )
        """)
        print("🌴 Sample package inserted.")
    except sqlite3.IntegrityError:
        print("⚠️ Default data already exists, skipping inserts.")

    conn.commit()
    conn.close()
    print("🎉 Database setup completed successfully.")


if __name__ == "__main__":
    setup_database()
