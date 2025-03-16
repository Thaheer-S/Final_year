from flask import Flask, request, jsonify
import requests
import sqlite3
from flask_cors import CORS
from auth import auth_bp  # Import authentication routes

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication
app.register_blueprint(auth_bp, url_prefix="/auth")  # ✅ Keep authentication routes

# ✅ Database Connection
def get_db_connection():
    try:
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database Error: {e}")  # ✅ Log error
        return None

# ✅ Create Employees Table (Run Once)
def create_employees_table():
    conn = get_db_connection()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL, 
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )"""
    )
    conn.commit()
    conn.close()

create_employees_table()


# 📌 **Add Employee API**
@app.route("/employees", methods=["POST"])
def add_employee():
    data = request.json
    user_email = data.get("user_email")
    name = data.get("name")
    username = data.get("username")
    password = data.get("password")

    if not user_email or not name or not username or not password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    try:
        conn = get_db_connection()
        if conn:
            conn.execute("INSERT INTO employees (user_email, name, username, password) VALUES (?, ?, ?, ?)",
                         (user_email, name, username, password))
            conn.commit()
            conn.close()
            return jsonify({"success": True, "message": "Employee added successfully!"})
        else:
            return jsonify({"success": False, "message": "Database connection failed"}), 500
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists!"}), 400

# 📌 **Get Employees for Logged-in User**
@app.route("/employees/<user_email>", methods=["GET"])
def get_employees(user_email):
    conn = get_db_connection()
    if conn:
        employees = conn.execute("SELECT * FROM employees WHERE user_email = ?", (user_email,)).fetchall()
        conn.close()
        employees_list = [{"id": emp["id"], "name": emp["name"], "username": emp["username"]} for emp in employees]
        return jsonify(employees_list)
    else:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

# 📌 **Delete Employee API**
@app.route("/employees/<int:id>", methods=["DELETE"])
def delete_employee(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employees WHERE id = ?", (id,))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "Employee not found"}), 404
        return jsonify({"success": True, "message": "Employee deleted successfully!"})
    else:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

# 📌 **AI API Configuration**
API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = "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"  # Store in .env for security

# ✅ Function to estimate project budget
def estimate_budget(team_members, duration):
    skill_rates = {
        "Python": 40, "Machine Learning": 50, "Data Science": 55,
        "Cloud Computing": 60, "Project Management": 45, "Software Development": 50
    }
    cloud_cost_per_month = 200
    software_licenses = 100
    misc_costs = 500

    total_salary = 0
    for name, skills in team_members.items():
        avg_rate = sum(skill_rates.get(skill, 30) for skill in skills) / len(skills)
        total_salary += avg_rate * 160 * duration  # 160 hours per month

    return total_salary + (cloud_cost_per_month * duration) + (software_licenses * len(team_members)) + misc_costs

# 📌 **Generate AI Project Plan**
@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    try:
        data = request.json
        problem_statement = data.get("problem_statement")
        team_members = data.get("team_members")
        duration = data.get("duration")

        if not problem_statement or not team_members or not duration:
            return jsonify({"error": "Missing required fields"}), 400

        estimated_budget = estimate_budget(team_members, duration)

        prompt = f"""
        Analyze the project details and generate the following **in order**:

        1. **Rephrase the Problem Statement** (Concisely and clearly).
        2. **Skills and Technologies Required** for the project.
        3. **Assign Work to Team Members** (Based on their existing skills).
        
           - If all required skills are available in the team:
             4. **Week-wise Milestones** (Break down the project into weekly tasks).
             5. **Total Duration of the Project** (Based on the milestones and deadline).

           - If some required skills are missing in the team:
             4. **Identify Missing Skills** (Compare required vs. team skills).
             5. **Approach to Address Missing Skills**:
                - 📌 Train (if skills are learnable within the timeline)
                - 📌 Hire (if critical expertise is missing)
                - 📌 Use Alternative Tech (if possible)
             6. **Week-wise Milestones** (Adjust milestones based on skill gaps and training/hiring).
             7. **Total Duration of the Project** (Include adjustments for training/hiring).

        📌 **Project Details**:
        - **Problem Statement:** {problem_statement}
        - **Team Members & Skills:** {team_members}
        - **Deadline:** {duration}
        """

        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are an AI project consultant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9
        }

        response = requests.post(API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            project_plan = response_data["choices"][0]["message"]["content"]
        else:
            return jsonify({"error": f"API Error: {response.status_code}, {response.text}"}), 500

        return jsonify({"project_plan": project_plan, "budget": estimated_budget})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)  # ✅ Merged API running on port 5001
