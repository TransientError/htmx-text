from flask import Flask, redirect, render_template, request, Response
from dataclasses import dataclass
from typing import Optional
import bcrypt


@dataclass
class TodoItem:
    done: bool
    desc: str

    def __init__(self, desc):
        self.done = False
        self.desc = desc


@dataclass
class User:
    username: str
    salted_hash: bytes
    todos: list[TodoItem]

    def __init__(self, username, password) -> None:
        self.todos = []
        self.username = username
        password_bytes = password.encode("UTF-8")
        salt = bcrypt.gensalt()
        self.salted_hash = bcrypt.hashpw(password_bytes, salt)


signedIn: Optional[User] = None
users: dict[str, User] = {}


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    @app.route("/")
    def root():
        if signedIn is not None:
            return render_template(
                "index.html.j2", todos=signedIn.todos, signedIn=signedIn.username
            )
        else:
            return redirect("/login")

    @app.route("/login")
    def login():
        return render_template("login.html.j2")

    @app.route("/sign-in", methods=["POST"])
    def signIn():
        username = request.form["username"]
        password = request.form["password"]
        if username in users:
            user = users[username]
            password_bytes = password.encode("UTF-8")
            if bcrypt.checkpw(password_bytes, user.salted_hash):
                global signedIn
                signedIn = user
                return Response(headers={"HX-Redirect": "/"})
            else:
                return Response(
                    "Password does not match",
                    headers={"HX-Retarget": "#password-error-dialog"},
                )
        return Response(
            "User not found", headers={"HX-Retarget": "#username-error-dialog"}
        )

    @app.route("/sign-out", methods=["POST"])
    def signOut():
        global signedIn
        signedIn = None
        response = Response()
        response.headers["HX-Redirect"] = "/login"
        return response

    @app.route("/register", methods=["POST"])
    def register():
        global signedIn
        username = request.form["username"]
        password = request.form["password"]
        users[username] = User(username, password)
        signedIn = users[username]
        return Response(headers={"HX-Redirect": "/"})

    @app.route("/create_todo", methods=["POST"])
    def createTodo():
        description = request.form["description"]
        todos = signedIn.todos
        todos.append(TodoItem(description))
        return render_template("todo_container.html.j2", todos=todos)

    @app.route("/toggleCheck", methods=["PATCH"])
    def toggleCheck():
        index = int(request.form["i"])
        todos = signedIn.todos
        todos[index - 1].done = not todos[index - 1].done
        return ""

    @app.route("/clearDone", methods=["POST"])
    def clearDone():
        todos = [todo for todo in signedIn.todos if not todo.done]
        return render_template("todo_container.html.j2", todos=todos)

    return app
