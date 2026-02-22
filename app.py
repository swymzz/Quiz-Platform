from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)
app.secret_key = "supersecretkey123"
# -----------------------------
# DATABASE SETUP
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Questions table
    c.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        answer TEXT
    )
    """)

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        score INTEGER,
        percentage REAL,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------------
# ADMIN CREDENTIALS
# -----------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

# -----------------------------
# LOGIN ROUTE
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        else:
            return "Wrong credentials!"

    return render_template("login.html")

# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")

# -----------------------------
# ADMIN PANEL
# -----------------------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        question = request.form["question"]
        option1 = request.form["option1"]
        option2 = request.form["option2"]
        option3 = request.form["option3"]
        option4 = request.form["option4"]
        answer = request.form["answer"]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            INSERT INTO questions (question, option1, option2, option3, option4, answer)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (question, option1, option2, option3, option4, answer))

        conn.commit()
        conn.close()

    return render_template("admin.html")

# -----------------------------
# VIEW RESULTS (Admin Only)
# -----------------------------
@app.route("/results")
def view_results():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # all users
    c.execute("SELECT * FROM users")
    users = c.fetchall()

    # analytics
    c.execute("SELECT COUNT(*) FROM users")
    total_attempts = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE status='PASS'")
    passed = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE status='FAIL'")
    failed = c.fetchone()[0]

    avg = 0
    if total_attempts > 0:
        c.execute("SELECT AVG(percentage) FROM users")
        avg = round(c.fetchone()[0],2)

    conn.close()

    return render_template("results.html",
                           users=users,
                           total_attempts=total_attempts,
                           passed=passed,
                           failed=failed,
                           avg=avg)

# -----------------------------
# USER ROUTES
# -----------------------------
# -----------------------------
# VIEW ALL QUESTIONS (ADMIN)
# -----------------------------
@app.route("/admin/questions")
def view_questions():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM questions")
    questions = c.fetchall()
    conn.close()

    return render_template("manage_questions.html", questions=questions)

# -----------------------------
# DELETE QUESTION
# -----------------------------
@app.route("/delete_question/<int:id>")
def delete_question(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM questions WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin/questions")

# -----------------------------
# EDIT QUESTION
# -----------------------------
@app.route("/edit_question/<int:id>", methods=["GET","POST"])
def edit_question(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == "POST":
        q = request.form["question"]
        o1 = request.form["option1"]
        o2 = request.form["option2"]
        o3 = request.form["option3"]
        o4 = request.form["option4"]
        ans = request.form["answer"]

        c.execute("""
        UPDATE questions SET question=?, option1=?, option2=?, option3=?, option4=?, answer=?
        WHERE id=?
        """, (q,o1,o2,o3,o4,ans,id))

        conn.commit()
        conn.close()
        return redirect("/admin/questions")

    c.execute("SELECT * FROM questions WHERE id=?", (id,))
    question = c.fetchone()
    conn.close()

    return render_template("edit_question.html", q=question)

@app.route("/")
def register():
    return render_template("register.html")

@app.route("/instructions", methods=["POST"])
def instructions():
    name = request.form["name"]
    email = request.form["email"]
    return render_template("instructions.html", name=name, email=email)

@app.route("/quiz", methods=["POST"])
def quiz():
    name = request.form["name"]
    email = request.form["email"]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM questions")
    questions = c.fetchall()
    conn.close()

    total_time = len(questions) * 30  # GLOBAL TIMER

    return render_template("quiz.html",
                           questions=questions,
                           name=name,
                           email=email,
                           total_time=total_time)

@app.route("/result", methods=["POST"])
def result():
    name = request.form["name"]
    email = request.form["email"]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM questions")
    questions = c.fetchall()
    conn.close()

    score = 0

    for i in range(len(questions)):
        user_answer = request.form.get(f"q{i}")
        correct_answer = questions[i][6]

        if user_answer == correct_answer:
            score += 1

    percentage = (score / len(questions)) * 100 if len(questions) > 0 else 0
    status = "PASS" if percentage >= 60 else "FAIL"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (name, email, score, percentage, status)
        VALUES (?, ?, ?, ?, ?)
    """, (name, email, score, percentage, status))
    conn.commit()
    conn.close()

    return render_template("result.html",
                           score=score,
                           percentage=percentage,
                           status=status,
                           name=name,
                           email=email)

# -----------------------------
# DELETE SINGLE RESULT
# -----------------------------
@app.route("/delete_result/<int:id>")
def delete_result(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/results")


# -----------------------------
# LEADERBOARD PAGE
# -----------------------------
@app.route("/leaderboard")
def leaderboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT name, email, score, percentage
        FROM users
        ORDER BY percentage DESC
        LIMIT 10
    """)

    leaders = c.fetchall()
    conn.close()

    return render_template("leaderboard.html", leaders=leaders)

# -----------------------------
# CLEAR ALL RESULTS / RESET LEADERBOARD
# -----------------------------
@app.route("/clear_results")
def clear_results():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users")
    conn.commit()
    conn.close()

    return redirect("/results")

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run()



