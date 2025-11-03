from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, text

app = Flask(__name__)

server = 'DESKTOP-R92IV14\\BI'
database = 'TestDB'
driver = 'ODBC Driver 17 for SQL Server'
connection_string = f"mssql+pyodbc://@{server}/{database}?driver={driver}&trusted_connection=yes"
engine = create_engine(connection_string)

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    records = []

    # اضافه کردن رکورد
    if request.method == "POST" and "text_value" in request.form:
        text_value = request.form.get("text_value")
        if text_value:
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text("INSERT INTO Clicks (TextValue) VALUES (:val)"),
                        {"val": text_value}
                    )
                message = f"'{text_value}' با موفقیت اضافه شد!"
            except Exception as e:
                message = f"خطا در ذخیره‌سازی: {str(e)}"

    # جستجو رکوردها
    search_value = request.args.get("search_value")
    try:
        with engine.connect() as conn:
            if search_value:
                result = conn.execute(
                    text("SELECT * FROM Clicks WHERE TextValue LIKE :val ORDER BY CreatedAt DESC"),
                    {"val": f"%{search_value}%"}
                )
            else:
                result = conn.execute(
                    text("SELECT * FROM Clicks ORDER BY CreatedAt DESC")
                )
            records = result.fetchall()
    except Exception as e:
        message = f"خطا در خواندن رکوردها: {str(e)}"

    return render_template("index.html", message=message, records=records)

# ویرایش رکورد
@app.route("/edit/<int:record_id>", methods=["POST"])
def edit_record(record_id):
    new_value = request.form.get("new_value")
    if new_value:
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE Clicks SET TextValue = :val WHERE Id = :id"),
                    {"val": new_value, "id": record_id}
                )
        except Exception as e:
            print("خطا در ویرایش:", e)
    return redirect(url_for('index'))

# حذف رکورد
@app.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    try:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM Clicks WHERE Id = :id"),
                {"id": record_id}
            )
    except Exception as e:
        print("خطا در حذف:", e)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True , port = 5008)
