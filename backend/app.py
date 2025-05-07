from flask import Flask, request, jsonify
import requests
import sqlite3
from flask_cors import CORS
from auth import auth_bp  
import json
from datetime import datetime
# from datetime import datetime



app = Flask(__name__)
CORS(app)  
app.register_blueprint(auth_bp, url_prefix="/auth")  

# ✅ Database Connection
def get_db_connection():
    try:
        conn = sqlite3.connect("users.db", timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"🔥 Database Error: {e}")  
        return None

# ✅ Create Tables
def create_tables():
    conn = get_db_connection()
    
    # ✅ Create Employees Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL, 
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # ✅ Create Tasks Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            task TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

        # ✅ Create Table to Store Login & Logout Time
    conn.execute("""
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        login_time TEXT,
        logout_time TEXT,
        date TEXT
    )
""")
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ps TEXT NOT NULL,
            skills_tech TEXT NOT NULL,
            assignwork TEXT NOT NULL,
            missingskill TEXT,
            approachmissingskill TEXT,
            milestone TEXT,
            duration TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS Team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_name TEXT NOT NULL,
            plan_id INTEGER,
            assignwork TEXT,
            email TEXT,
            status TEXT,
            ps TEXT,
            FOREIGN KEY (plan_id) REFERENCES Plans(id)
        )
    """)

    

    # Add this to your create_tables() function
    conn.execute("""
        CREATE TABLE IF NOT EXISTS PlanRecords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            ps TEXT NOT NULL,
            skills_tech TEXT NOT NULL,
            assignwork TEXT NOT NULL,
            missingskill TEXT,
            approachmissingskill TEXT,
            milestone TEXT,
            duration TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_email) REFERENCES users(email)
        )
    """)

    conn.commit()
    conn.close()

create_tables()  # ✅ Run at startup

# 📌 **Function to Estimate Budget**
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

# 📌 **AI API Configuration**
API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = "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"  # Store in .env for security

@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    try:
        data = request.json
        print("🔍 Received Data:", data)

        problem_statement = data.get("problem_statement")
        team_members = data.get("team_members")
        duration = data.get("duration")
        email = data.get("email")
        print(email)

        if not problem_statement or not team_members or not duration:
            return jsonify({"error": "Missing required fields"}), 400

        estimated_budget = estimate_budget(team_members, duration)


        # 📌 **AI Prompt to Generate Plan**
        
        prompt = f"""
        Analyze the project details and generate the following **in order**. 
        Label each section with `##` followed by the section name.

        ##Rephrased Problem Statement
        1. Rephrase the Problem Statement (Concisely and clearly).

        ##Skills and Technologies Required
        2. Skills and Technologies Required for the project.

        ##Assign Work to Team Members
        3. Assign Work to Team Members (Based on their existing skills).

            - If all required skills are available in the team:

            ##Milestones
            4. Week-wise Milestones (Break down the project into weekly tasks).

            ##Duration
            5. Total Duration of the Project (Based on the milestones and deadline).

            - If some required skills are missing in the team:

            ##Missing Skills
            4. Identify Missing Skills (Compare required vs. team skills).

            ##Approach to Address Missing Skills
            5. Approach to Address Missing Skills:
            - 📌 Train (if skills are learnable within the timeline)
            - 📌 Hire (if critical expertise is missing)
            - 📌 Use Alternative Tech (if possible)

            ##Adjusted Milestones
            6. Week-wise Milestones (Adjust milestones based on skill gaps and training/hiring).

            ##Adjusted Duration
            7. Total Duration of the Project (Include adjustments for training/hiring).


            📌 **Project Details**:
            - **Problem Statement:** {problem_statement}
            - **Team Members & Skills:** {team_members}
            - **Deadline:** {duration}
            """
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}  # ✅ Fixed API Key
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
        response_data = response.json()

        if response.status_code != 200:
            return jsonify({"error": f"API Error: {response.status_code}, {response.text}"}), 500

        if "choices" not in response_data or not response_data["choices"]:
            return jsonify({"error": "AI response is empty"}), 500

        project_plan = response_data["choices"][0]["message"]["content"]
        
        # Split by sections
        sections =project_plan.split("##")
        ps = sections[1].strip() if len(sections) > 1 else ""
        skills_tech = sections[2].strip() if len(sections) > 2 else ""
        assignwork = sections[3].strip() if len(sections) > 3 else ""
        missingskill = sections[4].strip() if "Missing Skills" in sections[4] else ""
        approachmissingskill = sections[5].strip() if "Approach to Address Missing Skills" in sections[5] else ""
        milestone = sections[6].strip() if len(sections) > 6 else ""
        duration = sections[7].strip() if len(sections) > 7 else ""

        # Insert into Plans table
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Plans (
                ps, skills_tech, assignwork, missingskill,
                approachmissingskill, milestone, duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (  
            ps,
            skills_tech,
            assignwork,
            missingskill,
            approachmissingskill,
            milestone,
            duration
        ))

        plan_id = cursor.lastrowid  

        # Insert into Team table
        
        if isinstance(team_members, str):
            team_list = json.loads(team_members)
        else:
             team_list = team_members

        print("🧪 team_members type:", type(team_members))


        for name, skills in team_members.items():
            cursor.execute("""
            INSERT INTO Team (emp_name, plan_id, assignwork, email, ps)
            VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                plan_id,
                assignwork,
                email,
                ps,
            ))


        conn.commit()
        conn.close()


        # ✅ **Extract "Assign Work to Team Members" Prompt**
        assign_work_prompt = "**Assign Work to Team Members** (Based on their existing skills)."

        # ✅ **Format Assigned Tasks**
        assigned_tasks = []
        for name, skills in team_members.items():
            task = f"Work on {problem_statement} using {', '.join(skills)}"
            assigned_tasks.append({"employee": name, "task": task})

        # ✅ **Store in Database**
        conn = get_db_connection()
        for task in assigned_tasks:
            conn.execute(
                "INSERT INTO tasks (employee_name, task) VALUES (?, ?)",
                (task["employee"], task["task"])
            )
        
        # ✅ **Also store the Assign Work Prompt**
        conn.execute(
            "INSERT INTO tasks (employee_name, task) VALUES (?, ?)",
            ("SYSTEM", assign_work_prompt)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "project_plan": project_plan,
            "budget": estimated_budget,
            "assigned_tasks": assigned_tasks
        })

    except Exception as e:
        print(f"🔥 Server Error: {e}")
        return jsonify({"error": str(e)}), 500

    
@app.route("/assign-work", methods=["POST"])
def assign_work():
    try:
        data = request.json
        assigned_tasks = data.get("assigned_tasks")

        if not assigned_tasks:
            return jsonify({"success": False, "message": "No tasks to assign"}), 400

        conn = get_db_connection()

        for task in assigned_tasks:
            employee_name = task.get("employee")
            task_desc = task.get("task")

            conn.execute(
                "INSERT INTO tasks (employee_name, task) VALUES (?, ?)",
                (employee_name, task_desc)
            )

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Tasks assigned successfully!"})

    except Exception as e:
        print(f"🔥 Server Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/assign-work/<email>", methods=["GET"])
def get_assigned_tasks(email):
    try:
        conn = get_db_connection()
        tasks = conn.execute("SELECT * FROM Team where email = ?", (email,)).fetchall()
        conn.close()

        task_list = [
            {"id": task["id"], "employee_name": task["emp_name"], "task": task["assignwork"]}
            
            for task in tasks
        ]
        return jsonify(task_list)
    except Exception as e:
        return jsonify({"error": f"Error fetching tasks: {str(e)}"}), 500
    
@app.route("/delete-task/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    try:
        conn = get_db_connection()

        # Check if the task exists
        task = conn.execute("SELECT * FROM Team WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return jsonify({"success": False, "message": "Task not found"}), 404

        # Delete the task
        conn.execute("DELETE FROM Team WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Task deleted successfully!"})

    except Exception as e:
        print(f"🔥 Server Error: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/employees/<int:id>", methods=["DELETE"])
def delete_employee(id):
    try:
        conn = get_db_connection()

        # Check if the employee exists
        employee = conn.execute("SELECT * FROM employees WHERE id = ?", (id,)).fetchone()
        
        if not employee:
            return jsonify({"error": "Employee not found"}), 404

        # Delete the employee
        conn.execute("DELETE FROM employees WHERE id = ?", (id,))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Employee deleted successfully!"})

    except Exception as e:
        print(f"🔥 Server Error: {e}")
        return jsonify({"error": str(e)}), 500
    

@app.route("/employees", methods=["POST"])
def add_employee():
    try:
        data = request.json
        user_email = data.get("user_email")
        name = data.get("name")
        username = data.get("username")
        password = data.get("password")

        if not user_email or not name or not username or not password:
            return jsonify({"error": "All fields are required"}), 400

        conn = get_db_connection()
        
        # Check for existing username
        existing = conn.execute("SELECT * FROM employees WHERE username = ?", (username,)).fetchone()

        if existing:
            conn.close()
            return jsonify({"error": "Username already exists"}), 409
        

        # Insert new employee
        conn.execute(
            "INSERT INTO employees (user_email, name, username, password) VALUES (?, ?, ?, ?)",
            (user_email, name, username, password)
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Employee added successfully!"})

    except Exception as e:
        print(f"🔥 Server Error: {e}")
        return jsonify({"error": str(e)}), 500




@app.route("/employees/<user_email>", methods=["GET"])
def get_employees(user_email):
    conn = get_db_connection()
    employees = conn.execute("SELECT * FROM employees WHERE user_email = ?", (user_email,)).fetchall()
    conn.close()
    
    if not employees:
        return jsonify({"error": "User not found"}), 404
    
    employees_list = [{"id": emp["id"], "name": emp["name"], "username": emp["username"]} for emp in employees]
    return jsonify(employees_list)

# @app.route("/get-assignwork", methods=["GET"])
# def get_assignwork():
#     try:
#         name = request.args.get("name")
#         conn = get_db_connection()
#         print()
#         cursor = conn.cursor()
#         cursor.execute("SELECT assignwork FROM Team WHERE emp_name = ?", (name,))
#         row = cursor.fetchone()
#         print(name, row)
#         conn.close()

#         if row:
#             return jsonify({"assignwork": row[0]})
#         else:
#             return jsonify({"assignwork": ""})
#     except Exception as e:
#         print("❌ Error:", e)
#         return jsonify({"error": str(e)}), 500


@app.route("/get-assignwork", methods=["GET"])
def get_assignwork():
    try:
        name = request.args.get("name")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT assignwork FROM Team WHERE emp_name = ?", (name,))
        rows = cursor.fetchall()
        conn.close()

        # Extract assignwork from all rows
        assignworks = [row[0] for row in rows]  # or row['assignwork'] if row_factory is set

        if assignworks:
            return jsonify({"assignwork": assignworks})
        else:
            return jsonify({"assignwork": []})  # Empty list if no work found

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500
    
@app.route("/get-status", methods=["GET"])
def get_status():
    name = request.args.get("name")
    conn = get_db_connection()
    tasks = conn.execute(
        "SELECT ps, status FROM Team WHERE emp_name = ?", 
        (name,)
    ).fetchall()
    conn.close()
    return jsonify({"assignwork": [dict(task) for task in tasks]})

# @app.route("/get-assignPlan/", methods=["GET"])
# def get_assignPlan():
#     try:
#         name = request.args.get("name")

#         if not name:
#             return jsonify({"error": "Name parameter is required"}), 400

#         conn = get_db_connection()
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()

#         # Step 1: Get the plan_id for the given employee name
#         cursor.execute("SELECT plan_id FROM Team WHERE emp_name = ?", (name,))
#         team_row = cursor.fetchone()

#         if not team_row:
#             return jsonify({"error": f"No plan found for employee: {name}"}), 404

#         plan_id = team_row["plan_id"]

#         # Step 2: Get the plan from the Plans table using plan_id
#         cursor.execute("SELECT * FROM Plans WHERE id = ?", (plan_id,))
#         plan_row = cursor.fetchone()
#         conn.close()

#         if not plan_row:
#             return jsonify({"error": f"No plan found with id: {plan_id}"}), 404

#         # Convert to dictionary and return
#         print(dict(plan_row))
#         return jsonify({"assignwork": dict(plan_row)})

#     except Exception as e:
#         print("❌ Error:", e)
#         return jsonify({"error": str(e)}), 500

@app.route("/get-assignPlan/", methods=["GET"])
def get_assignPlan():
    try:
        name = request.args.get("name")

        if not name:
            return jsonify({"error": "Name parameter is required"}), 400

        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Step 1: Get all plan_ids for the given employee
        cursor.execute("SELECT plan_id FROM Team WHERE emp_name = ?", (name,))
        team_rows = cursor.fetchall()

        if not team_rows:
            return jsonify({"assignwork": []})  # No plans found

        plan_ids = [row["plan_id"] for row in team_rows]

        # Step 2: Fetch all plans for the collected plan_ids
        placeholders = ','.join('?' for _ in plan_ids)
        query = f"SELECT * FROM Plans WHERE id IN ({placeholders})"
        cursor.execute(query, plan_ids)
        plans = cursor.fetchall()
        conn.close()

        # Convert rows to list of dictionaries
        assignwork = [dict(plan) for plan in plans]

        return jsonify({"assignwork": assignwork})

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500
    
# @app.route("/update-status", methods=["POST"])
# def update_status():
#     data = request.json
#     conn = get_db_connection()
#     name = data.get("name")
#     new_status = data.get("status")
#     print(name, new_status)

#     if not name or not new_status:
#         return jsonify({"success": False, "message": "Missing parameters"}), 400

#     try:
#         cursor = conn.cursor()
#         cursor.execute("UPDATE Team SET status = ? WHERE emp_name = ?", (new_status, name))
#         conn.commit()
#         return jsonify({"success": True, "message": "Status updated successfully"})
#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)}), 500

# @app.route('/update-status', methods=['POST'])
# def update_status():
#     data = request.get_json()
#     name = data.get('name')
#     task = data.get('task')
#     status = data.get('status')
#     print(task)

#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("UPDATE Team SET status = ? WHERE emp_name = ? AND task = ?", (status, name, task))
#     conn.commit()
#     conn.close()

#     return jsonify({"success": True, "message": "Status updated"})

@app.route("/update-status", methods=["POST"])
def update_status():
    data = request.json
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE Team SET status = ? WHERE emp_name = ? AND ps = ?",
            (data["status"], data["name"], data["task"])
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()




    
# @app.route("/assign-work/<user_email>", methods=["GET"])
# def get_tasks(user_email):
#     try:
#         conn = get_db_connection()
#         print(f"🔍 Fetching tasks for user: {user_email}")  # Debug log

#         tasks = conn.execute("SELECT * FROM tasks WHERE user_email = ?", (user_email,)).fetchall()
#         conn.close()

#         if not tasks:
#             print("⚠️ No tasks found!")  # Debug log
#             return jsonify([])  # Return empty list instead of error

#         tasks_list = [{"id": task["id"], "employee_name": task["employee_name"], "task": task["task"]} for task in tasks]
#         print("✅ Successfully fetched tasks:", tasks_list)  # Debug log
#         return jsonify(tasks_list)

#     except Exception as e:
#         print(f"🔥 Error fetching tasks: {e}")  # Debug log
#         return jsonify({"error": f"Error fetching tasks: {str(e)}"}), 500
    
    
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Missing email or password"}), 400

        conn = get_db_connection()
        # ✅ Try to log in as admin
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()
        if user:
            conn.close()
            return jsonify({
                "success": True,
                "role": "admin",
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"]
                }
            })

        # ✅ Try to log in as employee if admin fails
        employee = conn.execute(
            "SELECT * FROM employees WHERE username = ? AND password = ?",
            (email, password)
        ).fetchone()

        conn.close()

        if employee:
            return jsonify({
                "success": True,
                "role": "employee",
                "employee": {
                    "id": employee["id"],
                    "username": employee["username"],
                    "name": employee["name"]
                }
            })

        # ❌ If neither admin nor employee login succeeds
        return jsonify({"success": False, "message": "Invalid credentials!"}), 401

    except Exception as e:
        print(f"🔥 Server Error: {e}")
        return jsonify({"error": str(e)}), 500
    



    
    


@app.route("/log-login", methods=["POST"])
def log_login():
    data = request.json
    username = data["username"]
    login_time = datetime.now().strftime("%H:%M:%S")
    date = datetime.now().strftime("%Y-%m-%d")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if a record already exists for today
        cursor.execute("""
            SELECT login_time FROM login_logs 
            WHERE username = ? AND date = ?
        """, (username, date))
        existing = cursor.fetchone()

        if existing:
            # Update only if this is earlier than the stored login
            if login_time < existing["login_time"]:
                cursor.execute("""
                    UPDATE login_logs SET login_time = ?
                    WHERE username = ? AND date = ?
                """, (login_time, username, date))
        else:
            # Insert new record with first login
            cursor.execute("""
                INSERT INTO login_logs (username, date, login_time)
                VALUES (?, ?, ?)
            """, (username, date, login_time))
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()



@app.route("/log-logout", methods=["POST"])
def log_logout():
    data = request.json
    username = data["username"]
    logout_time = datetime.now().strftime("%H:%M:%S")
    date = datetime.now().strftime("%Y-%m-%d")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if a record exists for today
        cursor.execute("""
            SELECT logout_time FROM login_logs 
            WHERE username = ? AND date = ?
        """, (username, date))
        existing = cursor.fetchone()

        if existing:
            # Update only if this logout is later than the stored one
            if not existing["logout_time"] or logout_time > existing["logout_time"]:
                cursor.execute("""
                    UPDATE login_logs SET logout_time = ?
                    WHERE username = ? AND date = ?
                """, (logout_time, username, date))
        else:
            # Create new record (unlikely but handles edge cases)
            cursor.execute("""
                INSERT INTO login_logs (username, date, logout_time)
                VALUES (?, ?, ?)
            """, (username, date, logout_time))
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    finally:
        conn.close()

@app.route("/visualization/<string:email>", methods=["GET"])
def get_visualization_data(email):
    try:
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Only fetch employees with login records
        query = """
        SELECT 
            t.emp_name,
            l.date,
            l.login_time,
            l.logout_time,
            t.ps,
            t.status
        FROM Team t
        JOIN login_logs l ON t.emp_name = l.username
        WHERE t.email = ? AND l.login_time IS NOT NULL
        ORDER BY l.date DESC, t.emp_name
        """
        cursor.execute(query, (email,))
        rows = cursor.fetchall()

        return jsonify([dict(row) for row in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# Get current user endpoint
@app.route('/get-current-user', methods=['GET'])
def get_current_user():
    # In a real app, you would get this from session/token
    # This is a simplified version - replace with your auth logic
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Example: Get the first user (replace with your actual auth logic)
        cursor.execute('SELECT email FROM users LIMIT 1')
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'No users found'}), 404
            
        return jsonify({
            'success': True,
            'user': {
                'email': user['email']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/save-plan-record', methods=['POST'])
def save_plan_record():
    conn = None
    try:
        data = request.get_json()
        # Only require truly essential fields
        required_fields = ['user_email', 'ps', 'skills_tech', 'assignwork']
        
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO PlanRecords (
                user_email, ps, skills_tech, assignwork,
                missingskill, approachmissingskill, milestone, duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['user_email'],
            data['ps'],
            data['skills_tech'],
            data['assignwork'],
            data.get('missingskill', ''),
            data.get('approachmissingskill', ''),
            data.get('milestone', ''),
            data.get('duration', '')
        ))
        
        conn.commit()
        return jsonify({
            'success': True,
            'message': 'Plan saved successfully',
            'plan_id': cursor.lastrowid
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()
            
# Get all plans for a user
@app.route('/get-plan-records', methods=['POST'])
def get_plan_records():
    try:
        data = request.get_json()
        if 'user_email' not in data:
            return jsonify({'success': False, 'message': 'user_email required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, ps, skills_tech, assignwork, created_at
            FROM PlanRecords
            WHERE user_email = ?
            ORDER BY created_at DESC
        ''', (data['user_email'],))
        
        plans = [dict(row) for row in cursor.fetchall()]
        return jsonify({'success': True, 'plans': plans})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Delete a plan
@app.route('/delete-plan-record', methods=['POST'])
def delete_plan_record():
    try:
        data = request.get_json()
        if 'plan_id' not in data or 'user_email' not in data:
            return jsonify({'success': False, 'message': 'plan_id and user_email required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM PlanRecords
            WHERE id = ? AND user_email = ?
        ''', (data['plan_id'], data['user_email']))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Plan deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)



    
