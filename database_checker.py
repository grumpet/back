import sqlite3

# Establish a connection to the SQLite database
conn = sqlite3.connect('users.db')

# Check if the connection is closed
if conn:
    print("Database connection is open")
else:
    print("Database connection is closed")

# Close the database connection
conn.close()

# Check if the connection is closed after closing
try:
    # Attempt to perform an operation on the closed connection
    conn.execute("SELECT * FROM table_name")
except sqlite3.ProgrammingError:
    print("Database connection is closed")
