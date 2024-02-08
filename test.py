import sqlite3


# testing users
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Execute a query to fetch all usernames and passwords
c.execute('SELECT * FROM users')

# Fetch all results
users_data = c.fetchall()
print("users.db:")
for user in users_data:
    print(user)

# Close the database connection
print('events.db')
# testing events
# write a query to fetch all events
conn = sqlite3.connect('events.db')
c = conn.cursor()
c.execute('SELECT * FROM events')
events_data = c.fetchall()
for event in events_data:
    print(event)
