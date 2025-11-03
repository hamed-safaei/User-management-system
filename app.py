from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import bcrypt
import os

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your-super-secret-key-change-in-production-123456'  # حتماً تغییر بده!

# --- تنظیمات دیتابیس ---
server = 'DESKTOP-R92IV14\\BI'
database = 'TestDB'
driver = 'ODBC Driver 17 for SQL Server'
connection_string = f"mssql+pyodbc://@{server}/{database}?driver={driver}&trusted_connection=yes"
engine = create_engine(connection_string)

# --- صفحه لاگین ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("لطفاً نام کاربری و رمز عبور را وارد کنید.", "danger")
            return render_template("login.html")

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT ID, Username, Password FROM LogIn WHERE Username = :user"),
                    {"user": username}
                ).fetchone()

                if not result:
                    flash("نام کاربری یا رمز عبور اشتباه است.", "danger")
                    return render_template("login.html")

                db_password = result.Password.encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), db_password):
                    session['user_id'] = result.ID
                    session['username'] = result.Username
                    return redirect(url_for('dashboard'))
                else:
                    flash("رمز عبور اشتباه است.", "danger")

        except Exception as e:
            flash("خطا در ارتباط با سرور.", "danger")
            print("Login error:", e)

    return render_template("login.html")

# --- داشبورد (پنل مدیریت) ---
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        flash("لطفاً ابتدا وارد شوید.", "danger")
        return redirect(url_for('login'))
    return render_template("index.html")

# --- خروج ---
@app.route("/logout")
def logout():
    session.clear()
    flash("با موفقیت خارج شدید.", "success")
    return redirect(url_for('login'))

# --- API: دریافت لیست کاربران ---
@app.route("/api/users", methods=["GET"])
def get_users():
    if 'user_id' not in session:
        return jsonify({"error": "دسترسی غیرمجاز"}), 401

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT ID, [User], Email, [Password], AccessLevel FROM Users ORDER BY ID DESC"))
            users = []
            for row in result:
                users.append({
                    "id": f"u_{row.ID}",
                    "username": row.User,
                    "email": row.Email or "",
                    "password": row.Password,
                    "role": row.AccessLevel or ""
                })
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API: افزودن کاربر ---
@app.route("/api/users", methods=["POST"])
def add_user():
    if 'user_id' not in session:
        return jsonify({"error": "دسترسی غیرمجاز"}), 401

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    access_level = data.get("role")

    if not all([username, password, email, access_level]):
        return jsonify({"error": "همه فیلدها الزامی هستند."}), 400
    if len(username) < 3:
        return jsonify({"error": "نام کاربری باید حداقل ۳ کاراکتر باشد."}), 400
    if len(password) < 6:
        return jsonify({"error": "رمز عبور باید حداقل ۶ کاراکتر باشد."}), 400
    if "@" not in email:
        return jsonify({"error": "ایمیل نامعتبر است."}), 400

    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO Users ([User], [Password], Email, AccessLevel)
                    VALUES (:username, :password, :email, :access_level)
                """),
                {"username": username, "password": password, "email": email, "access_level": access_level}
            )
        return jsonify({"success": "کاربر با موفقیت اضافه شد."}), 201
    except IntegrityError as e:
        if 'UNIQUE' in str(e.orig):
            return jsonify({"error": "این نام کاربری قبلاً ثبت شده است."}), 409
        return jsonify({"error": "خطا در ذخیره‌سازی."}), 500
    except Exception as e:
        return jsonify({"error": f"خطای سرور: {str(e)}"}), 500

# --- API: ویرایش کاربر ---
@app.route("/api/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "دسترسی غیرمجاز"}), 401

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    access_level = data.get("role")

    if not all([username, password, email, access_level]):
        return jsonify({"error": "همه فیلدها الزامی هستند."}), 400
    if len(username) < 3:
        return jsonify({"error": "نام کاربری باید حداقل ۳ کاراکتر باشد."}), 400
    if len(password) < 6:
        return jsonify({"error": "رمز عبور باید حداقل ۶ کاراکتر باشد."}), 400
    if "@" not in email:
        return jsonify({"error": "ایمیل نامعتبر است."}), 400

    try:
        db_id = int(user_id.replace("u_", ""))
    except:
        return jsonify({"error": "شناسه کاربر نامعتبر است."}), 400

    try:
        with engine.begin() as conn:
            check = conn.execute(
                text("SELECT ID FROM Users WHERE [User] = :username AND ID != :id"),
                {"username": username, "id": db_id}
            ).fetchone()
            if check:
                return jsonify({"error": "این نام کاربری قبلاً استفاده شده است."}), 409

            conn.execute(
                text("""
                    UPDATE Users 
                    SET [User] = :username, [Password] = :password, 
                        Email = :email, AccessLevel = :access_level
                    WHERE ID = :id
                """),
                {"username": username, "password": password, "email": email, 
                 "access_level": access_level, "id": db_id}
            )
        return jsonify({"success": "کاربر با موفقیت ویرایش شد."}), 200
    except Exception as e:
        return jsonify({"error": f"خطا در ویرایش: {str(e)}"}), 500

# --- API: حذف کاربر ---
@app.route("/api/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "دسترسی غیرمجاز"}), 401

    try:
        db_id = int(user_id.replace("u_", ""))
    except:
        return jsonify({"error": "شناسه کاربر نامعتبر است."}), 400

    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM Users WHERE ID = :id"),
                {"id": db_id}
            )
            if result.rowcount == 0:
                return jsonify({"error": "کاربر یافت نشد."}), 404
        return jsonify({"success": "کاربر با موفقیت حذف شد."}), 200
    except Exception as e:
        return jsonify({"error": f"خطا در حذف: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5008)