from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    added = db.Column(db.DateTime, default=datetime.utcnow())
    status = db.Column(db.String(15), default="incomplete-task")

    def __repr__(self) -> str:
        return f"{self.sno}, {self.title}, {self.description}, {self.added}, {self.status}"


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form["title"]
        description = request.form["description"]
        todo = Todo(title=title, description=description)
        db.session.add(todo)
        db.session.commit()
    todos = Todo.query.limit(50).all()
    return render_template("index.html", todos=todos)


@app.route("/update/<int:sno>", methods=['GET', 'POST'])
def update(sno):
    if request.method == 'POST':
        title = request.form["title"]
        description = request.form["description"]
        status = request.form["status"]
        todo = Todo.query.filter_by(sno=sno).first()
        todo.title = title
        todo.description = description
        todo.status = status
        db.session.add(todo)
        db.session.commit()
        return redirect("/")
    todo = Todo.query.filter_by(sno=sno).first()
    if todo == None:
        return redirect("/not-found")
    else:
        return render_template("update.html", todo=todo)


@app.route("/delete/<int:sno>")
def delete(sno):
    try:
        todo = Todo.query.filter_by(sno=sno).first()
        db.session.delete(todo)
        db.session.commit()
        return redirect("/")
    except:
        return redirect("/not-found")


@app.route("/status/<int:sno>")
def update_status(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    if todo == None:
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


@app.route("/task/<string:category>")
def complete_tasks(category):
    if category == "complete":
        title = "completed tasks"
        todos = Todo.query.filter_by(status="completed-task").limit(50).all()
    elif category == "incomplete":
        title = "incomplete tasks"
        todos = Todo.query.filter_by(status="incomplete-task").limit(50).all()
    elif category == "all":
        todos = Todo.query.all()
        if len(todos) > 0:
            title = "All Todos"
        else:
            title = "Tasks"
    else:
        return redirect("/not-found")
    return render_template("task.html", title=title, todos=todos)


@app.route("/search/", methods=['GET'])
def search():
    query = request.args.get("query")
    if query == '':
        return redirect("/not-found")
    search = "%{}%".format(query)
    todos = todos = Todo.query.filter(Todo.title.like(search)).all()
    return render_template("search.html", query=query, todos=todos)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


if __name__ == "__main__":
    app.run(debug=True, port=8000)
