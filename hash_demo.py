from werkzeug.security import generate_password_hash, check_password_hash
from app import app, get_db

with app.app_context():
    password = "demo1234"
    password_hash = generate_password_hash(password)

    db = get_db()
    # db.execute(
    #     "INSERT INTO users (email, password_hash) VALUES (?, ?)",
    #     ("test2@test.com", password_hash)
    # )
    # db.commit()

    user = db.execute(
        "SELECT email, password_hash FROM users WHERE email = ?", 
        ("test2@test.com",),
    ).fetchone()

    stored_hash = user["password_hash"]
    print(f"Stored Hash: {stored_hash}")

    print("correct candidate matches?",
          check_password_hash(stored_hash, "demo1234")
          )
    print("Wrong candidate matches?",
          check_password_hash(stored_hash, "wrong-password")
          )
