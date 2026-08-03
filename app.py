import os
from nicegui import ui
import sqlite3

# Fake "database" - stored in memory (resets when server restarts)
#users = {}  # {email: password}

conn = sqlite3.connect("users.db",
check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT
)
""")

GREEN = "#0f9d78"


def notify_error(msg):
    ui.notify(msg, type="negative")


def notify_success(msg):
    ui.notify(msg, type="positive")


@ui.page("/")
def index():
    ui.navigate.to("/login")


@ui.page("/login")
def login_page():
    ui.query("body").style(f"background-color: {GREEN};")

    with ui.column().classes("absolute-center items-center"):
        with ui.card().classes("p-8").style("width: 340px; border-radius: 8px;"):
            ui.label("Login").classes("text-2xl font-bold text-center w-full").style("margin-bottom: 15px;")

            email = ui.input(placeholder="Enter your email").classes("w-full").props("outlined dense")
            password = ui.input(placeholder="Enter your password", password=True, password_toggle_button=True).classes("w-full").props("outlined dense").style("margin-top: 10px;")

            with ui.row().classes("w-full justify-start").style("margin-top: 5px;"):
                ui.link("Forgot password?", "#").style(f"color:{GREEN}; font-size:13px; text-decoration:none;")

            def do_login():
                cursor.execute(
                    "SELECT * FROM users WHERE email=? AND password=?",
                    (email.value, password.value)
                )

                user = cursor.fetchone()

                if user:
                    notify_success(f"Welcome back, {email.value}!")
                    ui.navigate.to("/dashboard")
                else:
                    notify_error("Invalid email or password")

            ui.button("Login", on_click=do_login).classes("w-full text-white font-bold").style(
                f"background-color:{GREEN} !important; margin-top:15px; padding:10px;"
            )

            with ui.row().classes("w-full justify-center").style("margin-top: 15px;"):
                ui.label("Don't have an account?").style("font-size:13px;")
                ui.link("Signup", "/signup").style(f"color:{GREEN}; font-weight:bold; font-size:13px; text-decoration:none;")


@ui.page("/signup")
def signup_page():
    ui.query("body").style(f"background-color: {GREEN};")

    with ui.column().classes("absolute-center items-center"):
        with ui.card().classes("p-8").style("width: 340px; border-radius: 8px;"):
            ui.label("Signup").classes("text-2xl font-bold text-center w-full").style("margin-bottom: 15px;")

            email = ui.input(placeholder="Enter your email").classes("w-full").props("outlined dense")
            password = ui.input(placeholder="Create a password", password=True, password_toggle_button=True).classes("w-full").props("outlined dense").style("margin-top: 10px;")
            confirm = ui.input(placeholder="Confirm your password", password=True, password_toggle_button=True).classes("w-full").props("outlined dense").style("margin-top: 10px;")

            def do_signup():
                if not email.value or not password.value:
                    notify_error("Please fill all fields")
                    return
                if password.value != confirm.value:
                    notify_error("Passwords do not match")
                    return
                cursor.execute(
                    "SELECT * FROM users WHERE email=?",
                    (email.value,)
                )
                if cursor.fetchone():
                    notify_error("Account already exists")
                    return
                cursor.execute(
                    "INSERT INTO users (email, password) VALUES (?, ?)",
                    (email.value, password.value)
                )

                conn.commit()
                notify_success("Account created! Please login.")
                ui.navigate.to("/login")

            ui.button("Signup", on_click=do_signup).classes("w-full text-white font-bold").style(
                f"background-color:{GREEN} !important; margin-top:15px; padding:10px;"
            )

            with ui.row().classes("w-full justify-center").style("margin-top: 15px;"):
                ui.label("Already have an account?").style("font-size:13px;")
                ui.link("Login", "/login").style(f"color:{GREEN}; font-weight:bold; font-size:13px; text-decoration:none;")


@ui.page("/dashboard")
def dashboard_page():
    with ui.column().classes("absolute-center items-center"):
        ui.label("You are logged in!").classes("text-2xl font-bold")
        ui.link("Logout", "/login").style(f"color:{GREEN}; margin-top:10px;")


ui.run(title="Login / Signup",
       host="0.0.0.0",
       port = int(os.environ.get("PORT", 8080))
)
