from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------ APP CONFIG ------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ------------------ MODELS ------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    tasks = db.relationship('Task', backref='user', lazy=True)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    tasks = db.relationship('Task', backref='subject', lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(300))
    deadline = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Pending")

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)


# ------------------ LOGIN HANDLER ------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------ ROUTES ------------------

@app.route('/')
def home():
    return render_template('index.html')


# ------------------ REGISTER ------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validation
        if not username or not email or not password:
            flash("Please fill all fields", "danger")
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists", "warning")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ------------------ LOGIN ------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "danger")

    return render_template('login.html')


# ------------------ DASHBOARD ------------------

@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    subjects = Subject.query.all()
    return render_template('dashboard.html', tasks=tasks, subjects=subjects)


# ------------------ ADD TASK ------------------

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    subjects = Subject.query.all()

    if request.method == 'POST':

        title = request.form.get('title')
        description = request.form.get('description')
        deadline = request.form.get('deadline')
        subject_id = request.form.get('subject_id')

        if not title or not deadline:
            flash("Title and deadline are required!", "danger")
            return redirect(url_for('add_task'))

        new_task = Task(
            title=title,
            description=description,
            deadline=deadline,
            user_id=current_user.id,
            subject_id=subject_id
        )

        db.session.add(new_task)
        db.session.commit()

        flash("Task added successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_task.html', subjects=subjects)


# ------------------ EDIT TASK ------------------

@app.route('/edit_task/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    subjects = Subject.query.all()

    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.deadline = request.form.get('deadline')
        task.subject_id = request.form.get('subject_id')

        db.session.commit()

        flash("Task updated successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('edit_task.html', task=task, subjects=subjects)


# ------------------ COMPLETE TASK ------------------

@app.route('/complete_task/<int:id>')
@login_required
def complete_task(id):
    task = Task.query.get_or_404(id)
    task.status = "Completed"
    db.session.commit()

    flash("Task marked as completed!", "success")
    return redirect(url_for('dashboard'))


# ------------------ DELETE TASK ------------------

@app.route('/delete_task/<int:id>')
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()

    flash("Task deleted successfully!", "warning")
    return redirect(url_for('dashboard'))


# ------------------ LOGOUT ------------------

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))


# ------------------ INIT DB ------------------

def create_default_subjects():
    subjects = ["Math", "Science", "Programming", "Business", "English"]
    for s in subjects:
        if not Subject.query.filter_by(name=s).first():
            db.session.add(Subject(name=s))
    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_default_subjects()

    app.run(debug=True)