# from flask import Flask, request, jsonify
# import sqlite3
# from flask_cors import CORS

# employee_app = Flask(__name__)
# CORS(employee_app)  # Enable CORS for frontend communication

# # ✅ Connect to Database
# def get_db_connection():
#     conn = sqlite3.connect("users.db")
#     conn.row_factory = sqlite3.Row
#     return conn

# # ✅ Create Employees Table (Run Once)
# def create_employees_table():
#     conn = get_db_connection()
#     conn.execute(
#         """CREATE TABLE IF NOT EXISTS employees (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_email TEXT NOT NULL, 
#             name TEXT NOT NULL,
#             username TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL
#         )"""
#     )
#     conn.commit()
#     conn.close()

# create_employees_table()

# # 📌 **Add Employee API**
# @employee_app.route("/employees", methods=["POST"])
# def add_employee():
#     data = request.json
#     user_email = data.get("user_email")  # Fetch the logged-in user
#     name = data.get("name")
#     username = data.get("username")
#     password = data.get("password")

#     if not user_email or not name or not username or not password:
#         return jsonify({"success": False, "message": "All fields are required"}), 400

#     try:
#         conn = get_db_connection()
#         conn.execute("INSERT INTO employees (user_email, name, username, password) VALUES (?, ?, ?, ?)",
#                      (user_email, name, username, password))
#         conn.commit()
#         conn.close()
#         return jsonify({"success": True, "message": "Employee added successfully!"})
#     except sqlite3.IntegrityError:
#         return jsonify({"success": False, "message": "Username already exists!"}), 400

# # 📌 **Get Employees for Logged-in User**
# @employee_app.route("/employees/<user_email>", methods=["GET"])
# def get_employees(user_email):
#     conn = get_db_connection()
#     employees = conn.execute("SELECT * FROM employees WHERE user_email = ?", (user_email,)).fetchall()
#     conn.close()
    
#     employees_list = [{"id": emp["id"], "name": emp["name"], "username": emp["username"]} for emp in employees]
#     return jsonify(employees_list)

# # 📌 **Delete Employee API**
# @employee_app.route("/employees/<int:id>", methods=["DELETE"])
# def delete_employee(id):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("DELETE FROM employees WHERE id = ?", (id,))
#     conn.commit()
#     conn.close()

#     if cursor.rowcount == 0:
#         return jsonify({"success": False, "message": "Employee not found"}), 404
#     return jsonify({"success": True, "message": "Employee deleted successfully!"})

# if __name__ == "__main__":
#     employee_app.run(debug=True, port=5001)  # ✅ Different Port
