from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey123"

# -----------------------------
# DATABASE PATH (WORKS LOCAL + RENDER)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# -----------------------------
# DATABASE SETUP
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        answer TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
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

# ⭐ IMPORTANT: create DB when app starts (Render needs this)
init_db()

# -----------------------------
# ADMIN LOGIN
# -----------------------------
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="1234"

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form["username"]==ADMIN_USERNAME and request.form["password"]==ADMIN_PASSWORD:
            session["admin"]=True
            return redirect("/admin")
        return "Wrong credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin",None)
    return redirect("/login")

# -----------------------------
# ADMIN ADD QUESTION
# -----------------------------
@app.route("/admin", methods=["GET","POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    if request.method=="POST":
        conn=sqlite3.connect(DB_PATH)
        conn.execute("""INSERT INTO questions(question,option1,option2,option3,option4,answer)
                        VALUES(?,?,?,?,?,?)""",
                        (request.form["question"],request.form["option1"],request.form["option2"],
                         request.form["option3"],request.form["option4"],request.form["answer"]))
        conn.commit()
        conn.close()

    return render_template("admin.html")

# -----------------------------
# MANAGE QUESTIONS
# -----------------------------
@app.route("/admin/questions")
def view_questions():
    if not session.get("admin"):
        return redirect("/login")
    conn=sqlite3.connect(DB_PATH)
    questions=conn.execute("SELECT * FROM questions").fetchall()
    conn.close()
    return render_template("manage_questions.html", questions=questions)

@app.route("/delete_question/<int:id>")
def delete_question(id):
    if not session.get("admin"):
        return redirect("/login")
    conn=sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM questions WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin/questions")

@app.route("/edit_question/<int:id>", methods=["GET","POST"])
def edit_question(id):
    if not session.get("admin"):
        return redirect("/login")

    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()

    if request.method=="POST":
        c.execute("""UPDATE questions SET question=?,option1=?,option2=?,option3=?,option4=?,answer=? WHERE id=?""",
                  (request.form["question"],request.form["option1"],request.form["option2"],
                   request.form["option3"],request.form["option4"],request.form["answer"],id))
        conn.commit()
        conn.close()
        return redirect("/admin/questions")

    c.execute("SELECT * FROM questions WHERE id=?", (id,))
    q=c.fetchone()
    conn.close()
    return render_template("edit_question.html", q=q)

# -----------------------------
# USER FLOW
# -----------------------------
@app.route("/")
def register():
    return render_template("register.html")

@app.route("/instructions", methods=["POST"])
def instructions():
    return render_template("instructions.html",
                           name=request.form["name"],
                           email=request.form["email"])

@app.route("/quiz", methods=["POST"])
def quiz():
    conn=sqlite3.connect(DB_PATH)
    questions=conn.execute("SELECT * FROM questions").fetchall()
    conn.close()
    return render_template("quiz.html",
                           questions=questions,
                           name=request.form["name"],
                           email=request.form["email"],
                           total_time=len(questions)*30)

@app.route("/result", methods=["POST"])
def result():
    conn=sqlite3.connect(DB_PATH)
    questions=conn.execute("SELECT * FROM questions").fetchall()
    conn.close()

    score=sum(1 for i,q in enumerate(questions) if request.form.get(f"q{i}")==q[6])
    percentage=(score/len(questions))*100 if questions else 0
    status="PASS" if percentage>=60 else "FAIL"

    conn=sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO users(name,email,score,percentage,status) VALUES(?,?,?,?,?)",
                 (request.form["name"],request.form["email"],score,percentage,status))
    conn.commit()
    conn.close()

    return render_template("result.html",
                           score=score,percentage=percentage,status=status,
                           name=request.form["name"],email=request.form["email"])

# -----------------------------
# ANALYTICS + LEADERBOARD
# -----------------------------
@app.route("/leaderboard")
def leaderboard():
    conn=sqlite3.connect(DB_PATH)
    leaders=conn.execute("SELECT name,email,score,percentage FROM users ORDER BY percentage DESC LIMIT 10").fetchall()
    conn.close()
    return render_template("leaderboard.html", leaders=leaders)

@app.route("/results")
def view_results():
    if not session.get("admin"):
        return redirect("/login")
    conn=sqlite3.connect(DB_PATH)
    users=conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("results.html", users=users)

@app.route("/clear_results")
def clear_results():
    if not session.get("admin"):
        return redirect("/login")
    conn=sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM users")
    conn.commit()
    conn.close()
    return redirect("/results")

if __name__ == "__main__":
    app.run()