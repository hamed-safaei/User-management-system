from flask import Flask, request, jsonify

app = Flask(__name__)

# Sample data
people = [
    {
        'id': 1,
        'name': 'Ali',
        'age': 25,
        'job': 'Engineer',
    },
    {
        'id': 2,
        'name': 'Sara',
        'age': 30,
        'job': 'Manager',
    }
]

# GET: دریافت لیست افراد
@app.route('/people', methods=['GET'])
def get_people():
    return jsonify(people)

# POST: اضافه کردن فرد جدید
@app.route('/people/new', methods=['POST'])
def create_person():
    new_person = {
        "id": len(people) + 1,
        "name": request.json['name'],
        "age": request.json['age'],
        "job": request.json['job'],
    }
    people.append(new_person)
    return jsonify(new_person), 201

if __name__ == '__main__':
    app.run(debug=True)
