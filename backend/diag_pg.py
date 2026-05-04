import psycopg2

passwords = ["B#@rathi-"]
users = ["postgres", "Bharathi", "bharathi"]

for user in users:
    for pwd in passwords:
        try:
            print(f"Trying user: {user} with provided password...")
            conn = psycopg2.connect(
                dbname="postgres",
                user=user,
                password=pwd,
                host="127.0.0.1",
                port=5432,
                connect_timeout=3
            )
            print(f"Connection successful for user: {user}")
            conn.close()
            exit(0)
        except Exception as e:
            print(f"Failed for user {user}: {e}")
