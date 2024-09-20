import sqlite3
import json

DATABASE_FILE = 'ai_assistant.db'

def get_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute("PRAGMA foreign_keys = 1")  # Enable foreign key constraints
    return conn

def setup_database():
    conn = get_connection()
    cur = conn.cursor()
    
    # Create Requests table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            human_request TEXT,
            task_description TEXT,
            file_path TEXT,
            original_content TEXT
        )
    ''')
    
    # Create CodeGenerations table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS CodeGenerations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            version INTEGER,
            generated_content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES Requests(id)
        )
    ''')
    
    # Create RLData table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS RLData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            state TEXT,
            action TEXT,
            reward REAL,
            next_state TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES Requests(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_request(human_request, task_description, file_path, original_content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO Requests (human_request, task_description, file_path, original_content)
        VALUES (?, ?, ?, ?)
    ''', (human_request, task_description, file_path, original_content))
    request_id = cur.lastrowid
    conn.commit()
    conn.close()
    return request_id

def insert_code_generation(request_id, version, generated_content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO CodeGenerations (request_id, version, generated_content)
        VALUES (?, ?, ?)
    ''', (request_id, version, generated_content))
    conn.commit()
    conn.close()

def insert_rl_data(request_id, state, action, reward, next_state):
    conn = get_connection()
    cur = conn.cursor()
    # Serialize state and next_state tuples to JSON strings
    state_json = json.dumps(state)
    next_state_json = json.dumps(next_state)
    cur.execute('''
        INSERT INTO RLData (request_id, state, action, reward, next_state)
        VALUES (?, ?, ?, ?, ?)
    ''', (request_id, state_json, action, reward, next_state_json))
    conn.commit()
    conn.close()

def get_all_rl_data():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT state, action, reward, next_state FROM RLData')
    rl_data = cur.fetchall()
    conn.close()
    # Deserialize state and next_state JSON strings back to tuples
    return [(json.loads(state), action, reward, json.loads(next_state)) for state, action, reward, next_state in rl_data]