from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# USER MODEL
class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )


# STUDENT MODEL
class Student(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    course = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    mobile = db.Column(
        db.String(15),
        nullable=False
    )

    photo = db.Column(db.String(200))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


# HOME
@app.route('/')
def home():

    return redirect('/login')


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        password = generate_password_hash(
            request.form['password']
        )

        # CHECK EXISTING USER

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:

            flash('Username already exists')

            return redirect('/register')

        # CREATE NEW USER

        user = User(
            username=username,
            password=password
        )

        db.session.add(user)
        db.session.commit()

        flash('Registration Successful')

        return redirect('/login')

    return render_template('register.html')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            flash('Login Successful')

            return redirect('/dashboard')

        flash('Invalid Credentials')

    return render_template('login.html')


# LOGOUT
@app.route('/logout')
@login_required
def logout():

    logout_user()

    flash('Logged Out')

    return redirect('/login')


# DASHBOARD
@app.route('/dashboard')
@login_required
def dashboard():

    search = request.args.get('search')

    if search:

        students = Student.query.filter(
            (Student.name.contains(search)) |
            (Student.course.contains(search)) |
            (Student.email.contains(search))
        ).all()

    else:

        students = Student.query.all()

    return render_template(
        'dashboard.html',
        students=students
    )


# ADD STUDENT
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():

    if request.method == 'POST':

        name = request.form['name']
        course = request.form['course']
        email = request.form['email']
        mobile = request.form['mobile']

        # VALIDATION

        if not name or not course or not email or not mobile:

            flash('All fields are required')

            return redirect('/add')

        # DUPLICATE EMAIL CHECK

        existing_student = Student.query.filter_by(
            email=email
        ).first()

        if existing_student:

            flash('Email already exists')

            return redirect('/add')

        # MOBILE VALIDATION

        if len(mobile) != 10 or not mobile.isdigit():

            flash('Invalid mobile number')

            return redirect('/add')

        # PHOTO

        photo = request.files['photo']

        filename = 'default.png'

        if photo and photo.filename != '':

            filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename
                )
            )

        # CREATE STUDENT

        student = Student(
            name=name,
            course=course,
            email=email,
            mobile=mobile,
            photo=filename
        )

        db.session.add(student)
        db.session.commit()

        flash('Student Added Successfully')

        return redirect('/dashboard')

    return render_template('add_student.html')


# EDIT STUDENT
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):

    student = Student.query.get(id)

    if request.method == 'POST':

        student.name = request.form['name']
        student.course = request.form['course']
        student.email = request.form['email']
        student.mobile = request.form['mobile']

        db.session.commit()

        flash('Student Updated')

        return redirect('/dashboard')

    return render_template(
        'edit_student.html',
        student=student
    )


# DELETE STUDENT
@app.route('/delete/<int:id>')
@login_required
def delete_student(id):

    student = Student.query.get(id)

    db.session.delete(student)

    db.session.commit()

    flash('Student Deleted')

    return redirect('/dashboard')


if __name__ == '__main__':

    with app.app_context():

        db.create_all()

    app.run(debug=True)