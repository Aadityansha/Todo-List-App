# importing python modules
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from datetime import datetime

# app instance
app = Flask(__name__)

# app configurations
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"  # database path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisasecretkey'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# login code
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# defining database schema

class Todo(db.Model):  # schema for todo items
    sno = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    added = db.Column(db.DateTime, default=datetime.utcnow())
    status = db.Column(db.String(15), default="incomplete-task")

    def __repr__(self) -> str:
        return f"{self.sno}, {self.title}, {self.description}, {self.added}, {self.status}"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)


# creating form

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=15)], render_kw={"placeholder": "Pick Username"})

    password = PasswordField(validators=[InputRequired(), Length(
        min=8, max=20)], render_kw={"placeholder": "Create Password"})

    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Your Username"})

    password = PasswordField(validators=[InputRequired(), Length(
        min=8, max=20)], render_kw={"placeholder": "Your Password"})

    submit = SubmitField('Sign In')


# defining app routes

@app.route("/", methods=['GET', 'POST'])  # route for index page
@login_required
def index():
    user_id = current_user.id
    if request.method == 'POST':
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        todo = Todo(title=title, description=description, user_id=user_id)
        db.session.add(todo)
        db.session.commit()
    todos = Todo.query.filter_by(user_id=user_id).limit(50).all()
    return render_template("index.html", todos=todos)


@app.route("/update/<int:sno>", methods=['GET', 'POST'])  # route for updating tasks
@login_required
def update(sno):
    user_id = current_user.id
    if request.method == 'POST':
        todo = Todo.query.filter_by(sno=sno).first()
        if todo.user_id == user_id:
            title = request.form["title"]
            description = request.form["description"]
            status = request.form["status"]
            todo.title = title
            todo.description = description
            todo.status = status
            db.session.add(todo)
            db.session.commit()
            return redirect("/")
        else:
            return redirect("/not-found")
    todo = Todo.query.filter_by(sno=sno).first()
    if todo == None:
        return redirect("/not-found")
    elif todo.user_id != user_id:
        return redirect("/not-found")
    else:
        return render_template("update.html", todo=todo)


@app.route("/delete/<int:sno>")  # route for deleting tasks
@login_required
def delete(sno):
    user_id = current_user.id
    try:
        todo = Todo.query.filter_by(sno=sno).first()
        if todo.user_id == user_id:
            db.session.delete(todo)
            db.session.commit()
            return redirect("/")
        else:
            return redirect("/not-found")
    except:
        return redirect("/not-found")


@app.route("/status/<int:sno>")  # route for updating tasks status
@login_required
def update_status(sno):
    user_id = current_user.id
    todo = Todo.query.filter_by(sno=sno).first()
    if todo == None:
        return redirect("/not-found")
    elif todo.user_id != user_id:
        return redirect("/not-found")
    else:
        if todo.status == "incomplete-task":
            status = "completed-task"
        else:
            status = "incomplete-task"
        todo.status = status
        db.session.add(todo)
        db.session.commit()
        return redirect("/")


@app.route("/task/<string:category>")  # route for task page
@login_required
def complete_tasks(category):
    user_id = current_user.id
    if category == "complete":
        title = "completed tasks"
        todos = Todo.query.filter_by(status="completed-task", user_id=user_id).limit(50).all()
    elif category == "incomplete":
        title = "incomplete tasks"
        todos = Todo.query.filter_by(status="incomplete-task", user_id=user_id).limit(50).all()
    elif category == "all":
        todos = Todo.query.filter_by(user_id=user_id).all()
        if len(todos) > 0:
            title = "All Todos"
        else:
            title = "Tasks"
    else:
        return redirect("/not-found")
    return render_template("task.html", title=title, todos=todos)


@app.route("/search/", methods=['GET'])  # route for search feature
@login_required
def search():
    user_id = current_user.id
    query = request.args.get("query")
    if query == '':
        return redirect("/not-found")
    search = "%{}%".format(query)
    todos = Todo.query.filter(Todo.title.like(search)).filter_by(user_id=user_id).all()
    return render_template("search.html", query=query, todos=todos)


@app.route("/sign-in", methods=['GET', 'POST'])  # route for login page
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            password_match = bcrypt.check_password_hash(user.password, form.password.data)
            if password_match == True:
                login_user(user)
                return redirect('/')
    return render_template("login.html", form=form)


@app.route('/logout', methods=['GET', 'POST'])  # route for logout
@login_required
def logout():
    logout_user()
    return redirect("/sign-in")


@app.route("/sign-up", methods=['GET', 'POST'])  # route for register page
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/sign-in')

    return render_template("register.html", form=form)


@app.errorhandler(404)  # "not found" error handling
def not_found(e):
    return render_template("404.html")


# running app
if __name__ == "__main__":
    #error = login password not match but user logins ?
    app.run(debug=True, port=8000)
