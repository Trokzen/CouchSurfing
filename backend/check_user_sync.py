import psycopg2

def check_user():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="1234",
        database="postgres",
        options="-c search_path=couchsurfing"
    )
    cur = conn.cursor()
    cur.execute("SELECT id, email, full_name FROM users WHERE email = %s", ("testuser@example.com",))
    row = cur.fetchone()
    if row:
        print(f"User found: id={row[0]}, email={row[1]}, name={row[2]}")
    else:
        print("User not found")
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_user()