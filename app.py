from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Password123!'  # Ensure correct format
app.config['MYSQL_DB'] = 'mcq'
mysql = MySQL(app)

# JWT Config
app.config["JWT_SECRET_KEY"] = "supersecretkey"  # Change this to a secure key in production
jwt = JWTManager(app)

# Home Page
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")  # Ensure login.html exists in /templates

    # Getting the data sent by the frontend
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    # Check the user credentials in the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, role, password FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()

    if user:
        token = create_access_token(identity={"id": user[0], "role": user[1]}, expires_delta=datetime.timedelta(hours=1))
        return jsonify({"token": token, "role": user[1]})

    return jsonify({"message": "Invalid Credentials"}), 401

# Admin Panel Route (Fix: Added GET method to show UI)
@app.route('/admin', methods=['GET'])
@jwt_required()  # Protect route with JWT
def admin_panel():
    current_user = get_jwt_identity()  # Retrieve the current logged-in user
    if current_user['role'] != 'admin':  # Check if the user is an admin
        return jsonify({"message": "Access Denied"}), 403
    
    return render_template("admin.html")  # Ensure this file exists in /templates

# Admin: Create Test (added POST method)
@app.route('/admin/create_test', methods=['POST'])
@jwt_required()  # Protect route with JWT
def create_test():
    current_user = get_jwt_identity()  # Retrieve the current logged-in user
    if current_user['role'] != 'admin':  # Check if the user is an admin
        return jsonify({"message": "Access Denied"}), 403
    
    data = request.get_json()  # Get the test data from the request body
    test_name = data['test_name']
    start_time = data['start_time']
    end_time = data['end_time']
    
    # Insert test data into the 'tests' table
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO tests (test_name, start_time, end_time, admin_id) VALUES (%s, %s, %s, %s)", 
                (test_name, start_time, end_time, current_user['id']))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({"message": "Test Created Successfully"}), 201

# Admin: Add Question (Fixed Token Handling)
@app.route('/admin/add_question', methods=['POST'])
@jwt_required()  # Protect route with JWT
def add_question():
    current_user = get_jwt_identity()  # Retrieve the current logged-in user
    if current_user['role'] != 'admin':  # Check if the user is an admin
        return jsonify({"message": "Access Denied"}), 403
    
    data = request.get_json()  # Get the question data from the request body
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO questions (question_text, option1, option2, option3, option4, correct_option, difficulty) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                (data['question_text'], data['option1'], data['option2'], data['option3'], data['option4'], data['correct_option'], data['difficulty']))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Question Added"}), 201

# Get All Tests (Added GET method)
@app.route('/tests', methods=['GET'])
@jwt_required()  # Protect route with JWT
def get_tests():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, test_name FROM tests")
    tests = cur.fetchall()
    cur.close()
    
    return jsonify({"tests": [{"id": t[0], "name": t[1]} for t in tests]})

# Get a Single Test (Added GET method)
@app.route('/test/<int:test_id>', methods=['GET'])
@jwt_required()  # Protect route with JWT
def get_test(test_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, question_text, option1, option2, option3, option4 FROM questions WHERE id IN (SELECT question_id FROM test_questions WHERE test_id=%s)", (test_id,))
    questions = cur.fetchall()
    cur.close()
    
    return jsonify({"questions": [{"id": q[0], "question": q[1], "options": [q[2], q[3], q[4], q[5]]} for q in questions]})

@app.route('/submit_response', methods=['POST'])
@jwt_required()
def submit_response():
    data = request.get_json()
    user_id = get_jwt_identity()['id']
    test_id = data['test_id']
    question_id = data['question_id']
    selected_option = data['selected_option']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO responses (test_taker_id, test_id, question_id, selected_option) VALUES (%s, %s, %s, %s)", 
                (user_id, test_id, question_id, selected_option))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Response Submitted"}), 201

@app.route('/submit_test', methods=['POST'])
@jwt_required()
def submit_test():
    data = request.get_json()
    user_id = get_jwt_identity()['id']
    test_id = data['test_id']
    score = data['score']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO test_submissions (test_id, user_id, score) VALUES (%s, %s, %s)", 
                (test_id, user_id, score))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Test Submitted"}), 201
@app.route('/invite_user', methods=['POST'])
@jwt_required()
def invite_user():
    data = request.get_json()
    user_id = data['user_id']
    test_id = data['test_id']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO invitations (test_id, user_id, status) VALUES (%s, %s, 'invited')", 
                (test_id, user_id))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "User Invited"}), 201



# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
