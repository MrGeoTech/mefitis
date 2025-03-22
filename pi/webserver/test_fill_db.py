import sqlite3
import random
import time
from faker import Faker

def create_database():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE data")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Sound_Engine REAL,
        Sound_Operator REAL,
        Emissions_Engine REAL,
        Emissions_Operator REAL,
        Temp_Engine REAL,
        Temp_Exhaust REAL,
        RPM INTEGER
    )
    """)
    
    conn.commit()
    conn.close()

def populate_database():
    fake = Faker()
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    
    for _ in range(600):
        sound_engine = round(random.uniform(50.0, 120.0), 2)
        sound_operator = round(random.uniform(40.0, 110.0), 2)
        emissions_engine = round(random.uniform(0.1, 5.0), 2)
        emissions_operator = round(random.uniform(0.1, 4.0), 2)
        temp_engine = round(random.uniform(60.0, 200.0), 2)
        temp_exhaust = round(random.uniform(100.0, 600.0), 2)
        rpm = random.randint(500, 8000)
        
        cursor.execute("""
        INSERT INTO data (Sound_Engine, Sound_Operator, Emissions_Engine, Emissions_Operator, Temp_Engine, Temp_Exhaust, RPM)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (sound_engine, sound_operator, emissions_engine, emissions_operator, temp_engine, temp_exhaust, rpm))
        conn.commit()
        time.sleep(1)
    
    conn.close()

if __name__ == "__main__":
    create_database()
    populate_database()
    print("Database populated with 60 rows of fake data.")
