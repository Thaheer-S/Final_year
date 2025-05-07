from flask import Blueprint, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)  # ✅ Authentication blueprint

# ✅ Function to connect to SQLite
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

# ✅ Create Users Table (Only Runs Once)
def create_users_table():
    conn = get_db_connection()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )"""
    )
    conn.commit()
    conn.close()

create_users_table()  # Ensure the table exists

# ✅ Register Route (POST)
@auth_bp.route("/register", methods=["POST"])
def register():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"}), 400

    hashed_password = generate_password_hash(password)  # ✅ Hash password

    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "User registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "User already exists"}), 400

# ✅ Login Route (POST)
# @auth_bp.route("/login", methods=["POST"])
# def login():
#     if not request.is_json:
#         return jsonify({"error": "Request must be JSON"}), 415

#     data = request.get_json()
#     email = data.get("email")
#     password = data.get("password")

#     if not email or not password:
#         return jsonify({"error": "Missing email or password"}), 400

#     conn = get_db_connection()
#     user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
#     conn.close()

#     if user and check_password_hash(user["password"], password):  # ✅ Verify hashed password
#         return jsonify({"success": True, "user": {"id": user["id"], "email": user["email"]}})
#     else:
#         return jsonify({"success": False, "message": "Invalid credentials"}), 401

# @auth_bp.route("/login", methods=["POST"])
# def login():
#     if not request.is_json:
#         return jsonify({"error": "Request must be JSON"}), 415

#     data = request.json
#     email = data.get("email")
#     password = data.get("password")

#     conn = get_db_connection()
#     user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
#     conn.close()

#     if user:
#         stored_password = user["password"]
#         print("User found:", user["email"])  # ✅ Debug: Check if user is found
#         print("Stored Password Hash:", stored_password)  # ✅ Debug: Check stored hash
#         print("Entered Password:", password)  # ✅ Debug: Check entered password

#         if check_password_hash(stored_password, password):
#             print("✅ Password Matched!")  # ✅ Debugging success
#             return jsonify({"success": True, "user": {"id": user["id"], "email": user["email"]}})
#         else:
#             print("❌ Password does not match!")  # Debug failure reason
#             return jsonify({"success": False, "message": "Invalid password"}), 401
#     else:
#         print("❌ User not found!")  # Debug failure reason
#         return jsonify({"success": False, "message": "User not found"}), 404


@auth_bp.route("/login", methods=["POST"])
def login():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    data = request.json
    email = data.get("email")
    username = data.get("email")
    password = data.get("password")
    print(data)
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user:
        stored_password = user["password"]
        
        if check_password_hash(stored_password, password):
            print("✅ Password Matched!")  # ✅ Debugging success
            return jsonify({"success": True,"type": "manager", "user": {"id": user["id"], "email": user["email"]}})
        else:
            print("❌ Password does not match!")  # Debug failure reason
            return jsonify({"success": False, "message": "Invalid password"}), 401
    employee = conn.execute("SELECT * FROM employees WHERE username = ?", (username,)).fetchone()
    conn.close()

    if employee:
        stored_password = employee["password"]
        print("✅ Employee found:", employee["username"])
        print("Password:", stored_password)

        if password == stored_password:
            print("🔑 Password Matched!")
            return jsonify({"success": True, "type": "employee", "user": {"id": employee["id"], "username": employee["username"]}})
        else:
            print("❌ Password does not match!")
            return jsonify({"success": False, "message": "Invalid password"}), 401
    else:
        print("❌ User not found!")  # Debug failure reason
        return jsonify({"success": False, "message": "User not found"}), 404