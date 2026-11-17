"""Recipe Box API — BE104 course skeleton.

A working Flask + SQLite CRUD API for recipes. It stores data perfectly —
and it trusts everyone. There is no authentication and no authorization yet.
That is the point: you will add both, lesson by lesson, in Units 2 and 3.
"""

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, g, jsonify, request
import os
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
from pathlib import Path

DATABASE = "recipes.db"

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET")
print(f"Debug JWT_SECRET in app.py: {JWT_SECRET}")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def recipe_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "ingredients": row["ingredients"],
        "instructions": row["instructions"],
        "is_public": bool(row["is_public"]),
    }


@app.get("/")
def hello():
    return jsonify({"message": "Recipe Box API", "recipes": "/recipes"})


@app.get("/recipes")
def list_recipes():
    # read auth header
    auth_header = request.headers.get("Authorization", "")

    # check bearer format
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "auth token required"}), 401
    token = auth_header.split(" ", 1)[1]

    # verfiy token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired. Please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    
    # get authenticated identity
    user_id = payload.get("sub")
    print(f"Authenticated user: {user_id}")

    rows = get_db().execute("SELECT * FROM recipes ORDER BY id").fetchall()
    return jsonify([recipe_to_dict(r) for r in rows])


@app.get("/recipes/<int:recipe_id>")
def get_recipe(recipe_id):
    # read auth header
    auth_header = request.headers.get("Authorization", "")

    # check bearer format
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "auth token required"}), 401
    token = auth_header.split(" ", 1)[1]

    # verfiy token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired. Please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    
    # get authenticated identity
    user_id = payload.get("sub")
    print(f"Authenticated user: {user_id}")

    row = get_db().execute(
        "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "recipe not found"}), 404
    return jsonify(recipe_to_dict(row))


@app.post("/recipes")
def create_recipe():
    # read auth header
    auth_header = request.headers.get("Authorization", "")

    # check bearer format
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "auth token required"}), 401
    token = auth_header.split(" ", 1)[1]

    # verfiy token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired. Please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    
    # get authenticated identity
    user_id = payload.get("sub")
    print(f"Authenticated user: {user_id}")

    data = request.get_json(silent=True)
    if not data or not data.get("title") or not data.get("ingredients"):
        return jsonify({"error": "title and ingredients are required"}), 400
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO recipes (title, ingredients, instructions, is_public)"
            " VALUES (?, ?, ?, ?)",
            (
                data["title"],
                data["ingredients"],
                data.get("instructions", ""),
                1 if data.get("is_public", True) else 0,
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "a recipe with that title already exists"}), 409
    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return jsonify(recipe_to_dict(row)), 201


@app.patch("/recipes/<int:recipe_id>")
def update_recipe(recipe_id):
    # read auth header
    auth_header = request.headers.get("Authorization", "")

    # check bearer format
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "auth token required"}), 401
    token = auth_header.split(" ", 1)[1]

    # verfiy token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired. Please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    
    # get authenticated identity
    user_id = payload.get("sub")
    print(f"Authenticated user: {user_id}")

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "a JSON body is required"}), 400
    fields, values = [], []
    for column in ("title", "ingredients", "instructions"):
        if column in data:
            fields.append(f"{column} = ?")
            values.append(data[column])
    if "is_public" in data:
        fields.append("is_public = ?")
        values.append(1 if data["is_public"] else 0)
    if not fields:
        return jsonify({"error": "nothing to update"}), 400
    values.append(recipe_id)
    db = get_db()
    try:
        cur = db.execute(
            f"UPDATE recipes SET {', '.join(fields)} WHERE id = ?", values
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "a recipe with that title already exists"}), 409
    if cur.rowcount == 0:
        return jsonify({"error": "recipe not found"}), 404
    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()
    return jsonify(recipe_to_dict(row))


@app.delete("/recipes/<int:recipe_id>")
def delete_recipe(recipe_id):
    # read auth header
    auth_header = request.headers.get("Authorization", "")

    # check bearer format
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "auth token required"}), 401
    token = auth_header.split(" ", 1)[1]

    # verfiy token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired. Please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    # get authenticated identity
    user_id = payload.get("sub")
    print(f"Authenticated user: {user_id}")

    db = get_db()
    cur = db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "recipe not found"}), 404
    return "", 204

@app.post("/register")
def register():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "email and password are required"}, 400

    db = get_db()
    password_hash = generate_password_hash(password)
    try:
        db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password_hash)
        )
        db.commit()
    except sqlite3.IntegrityError:
        return {"error": "account with that email already exists"}, 409

    return {"email": email}, 201

@app.post("/login")
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "email and password are required"}, 400
    
    db = get_db()

    user = db.execute(
        "SELECT id, email, password_hash FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if user is None:
        return {"error": "Invalid credentials"}, 401
    if not check_password_hash(user["password_hash"], password):
        return {"error": "Invalid credentials"}, 401
    
    user_id = user["id"]

    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return {
        "id": user_id,
        "email": user["email"],
        "token": token
    }, 200


if __name__ == "__main__":
    app.run(debug=True)
