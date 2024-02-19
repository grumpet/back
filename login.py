import sqlite3
from passlib.context import CryptContext

def create_users_table():
    conn_users, c_users = connect_users_db()
    c_users.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, lat TEXT, long TEXT, phone TEXT ,token TEXT ,token_expiry TEXT)''')
    conn_users.commit()
    conn_users.close()
    
def connect_users_db():
    conn_users = sqlite3.connect('users.db')
    c_users = conn_users.cursor()
    return conn_users, c_users

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

create_users_table()

def get_user(username: str):
    conn_users, c_users = connect_users_db()  
    c_users.execute('SELECT * FROM users WHERE username=?', (username,))
    user_data = c_users.fetchone()
    conn_users.close()
    if user_data:
        return user_data
    
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user[2]):
        return False
    return user

a = authenticate_user('4444','4444')
print(a)