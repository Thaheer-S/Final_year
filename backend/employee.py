from flask import Blueprint, request, jsonify
import sqlite3
import json


employee_bp = Blueprint("employee", __name__)



# 🔹 Function to establish a database connection
def get_db_connection():
    conn = sqlite3.connect("database.db")  # Replace with your actual DB file
    conn.row_factory = sqlite3.Row  # Allows dict-like access to row data
    return conn

# 🔹 API Route to Fetch Employee Details by Username or ID
@employee_bp.route("/employee", methods=["GET"])
def get_employee_details():
    employee_id = request.args.get("id")
    username = request.args.get("username")

    if not employee_id and not username:
        return jsonify({"error": "Provide either 'id' or 'username'"}), 400

    conn = get_db_connection()

    if employee_id:
        employee = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    else:
        employee = conn.execute("SELECT * FROM employees WHERE username = ?", (username,)).fetchone()

    conn.close()

    if employee:
        return jsonify({
            "id": employee["id"],
            "name": employee["name"],
            "username": employee["username"],
            "email": employee["email"],  # If email is stored
            "role": employee["role"],    # If roles exist
        })
    else:
        return jsonify({"error": "Employee not found"}), 404
