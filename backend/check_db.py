import psycopg2
import sys

def test_connection(host, port, dbname, user, password):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=dbname,
            user=user,
            password=password
        )
        print(f"Connected successfully to {dbname}!")
        cur = conn.cursor()
        cur.execute("SELECT current_database();")
        print(f"Database: {cur.fetchone()[0]}")
        cur.execute("SELECT version();")
        print(f"PostgreSQL version: {cur.fetchone()[0]}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Test with default config (password 1234, database postgres)
    print("Testing connection with config.py defaults:")
    test_connection("localhost", 5432, "postgres", "postgres", "1234")
    print("\nTesting connection with .env.example (password postgres, database couchsurfing):")
    test_connection("localhost", 5432, "couchsurfing", "postgres", "postgres")