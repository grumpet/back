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
    print(user ,"\n")
c.close()
# Close the database connection
print('events.db')
# testing events
# write a query to fetch all events
conn = sqlite3.connect('events.db')
c = conn.cursor()
c.execute('SELECT * FROM events')
events_data = c.fetchall()
for event in events_data:
    print(event ,"\n")
    
conn = sqlite3.connect('user_events.db')
c = conn.cursor()
c.execute('SELECT * FROM user_events')
user_events_data = c.fetchall()
print('user_events.db')
for user_event in user_events_data:
    print(user_event ,"\n")
    
conn = sqlite3.connect('messages.db')
c = conn.cursor()
c.execute('SELECT * FROM messages')
messages_data = c.fetchall()
print('messages.db')
for message in messages_data:
    print(message ,"\n")
    

c.close()
conn.close()