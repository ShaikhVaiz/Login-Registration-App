import os
import re
import bcrypt
import random
import time
from nicegui import ui
import mysql.connector
import resend
import dashboard

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
resend.api_key = RESEND_API_KEY

def get_db_connection():
    conn = mysql.connector.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="2axaGUcuFZV4H9Q.root",
        password=os.environ.get("DB_PASSWORD"),
        database="test"
    )

    conn.ping(reconnect=True, attempts=3, delay=2)

    cursor = conn.cursor()
    cursor.execute("SET time_zone = '+05:30'")
    cursor.close()

    return conn


GREEN = "#0f9d78"

otp_storage = {}
otp_time = {}
otp_verified = False


def valid_email(email):
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email)

def valid_password(password):
    if len(password) < 8:
        return False

    if not re.search(r'[A-Z]', password):
        return False

    if not re.search(r'[a-z]', password):
        return False

    if not re.search(r'[0-9]', password):
        return False

    if not re.search(r'[^A-Za-z0-9]', password):
        return False

    return True


def notify_error(msg):
    ui.notify(msg, type="negative")


def notify_success(msg):
    ui.notify(msg, type="positive")


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def send_otp(receiver_email, otp):
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [receiver_email],
            "subject": "Password Reset OTP",
            "html": f"""
                <h2>Password Reset</h2>

                <p>Your OTP is:</p>

                <h1>{otp}</h1>

                <p>This OTP is valid for <strong>5 minutes</strong>.</p>

                <p>If you did not request this password reset,
                please ignore this email.</p>
            """
        }

        email = resend.Emails.send(params)

        print("OTP email sent:", email)
        return True

    except Exception as e:
        print("OTP email failed:", e)
        return False




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
                ui.link("Forgot password?", "/forgot-password").style(f"color:{GREEN}; font-size:13px; text-decoration:none;")

            def do_login():
                db_conn = None
                cursor = None

                try:
                    db_conn = get_db_connection()
                    cursor = db_conn.cursor()

                    cursor.execute(
                        "SELECT * FROM users WHERE email=%s",
                        (email.value,)
                    )

                    user = cursor.fetchone()

                    if user and check_password(password.value, user[3]):
                        notify_success(f"Welcome back, {user[1]}!")
                        ui.navigate.to("/dashboard")
                    else:
                        notify_error("Invalid email or password")

                except Exception as e:
                    print("Login database error:", e)
                    notify_error("Database connection error. Please try again.")

                finally:
                    if cursor:
                        cursor.close()
                    if db_conn:
                        db_conn.close()

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

            username = ui.input(placeholder="Create your username").classes("w-full").props("outlined dense")
            email = ui.input(placeholder="Enter your email").classes("w-full").props("outlined dense").style("margin-top: 10px;")
            password = ui.input(placeholder="Create a password",password=True,password_toggle_button=True).classes("w-full").props("outlined dense").style("margin-top: 10px;")
            confirm = ui.input(placeholder="Confirm your password",password=True,password_toggle_button=True).classes("w-full").props("outlined dense").style("margin-top: 10px;")

            def do_signup():
                if not username.value or not email.value or not password.value:
                    notify_error("Please fill all fields")
                    return

                if not valid_email(email.value):
                    notify_error("Please enter a valid email address")
                    return

                
                if not valid_password(password.value):
                    notify_error(
                        "Password must be at least 8 characters and contain uppercase, lowercase, number and special character."
                    )
                    return

                if password.value != confirm.value:
                   notify_error("Passwords do not match")
                   return
                
                db_conn = None
                cursor = None

                try:
                    db_conn = get_db_connection()
                    cursor = db_conn.cursor()

                    cursor.execute(
                        "SELECT * FROM users WHERE email=%s",
                        (email.value,)
                    )

                    if cursor.fetchone():
                        notify_error("Email is already registered")
                        return

                    cursor.execute(
                        "SELECT * FROM users WHERE username=%s",
                        (username.value,)
                    )

                    if cursor.fetchone():
                        notify_error("Username is already taken")
                        return

                    hashed_password = hash_password(password.value)

                    cursor.execute(
                        "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                        (username.value, email.value, hashed_password)
                    )

                    db_conn.commit()

                    notify_success("Account created! Please login.")
                    ui.navigate.to("/login")

                except Exception as e:
                    print("Signup database error:", e)
                    notify_error("Database connection error. Please try again.")

                finally:
                    if cursor:
                        cursor.close()

                    if db_conn:
                        db_conn.close()

            ui.button("Signup", on_click=do_signup).classes("w-full text-white font-bold").style(
                f"background-color:{GREEN} !important; margin-top:15px; padding:10px;"
            )

            with ui.row().classes("w-full justify-center").style("margin-top: 15px;"):
                ui.label("Already have an account?").style("font-size:13px;")
                ui.link("Login", "/login").style(f"color:{GREEN}; font-weight:bold; font-size:13px; text-decoration:none;")


@ui.page("/forgot-password")
def forgot_password_page():
    ui.query("body").style(f"background-color: {GREEN};")

    with ui.column().classes("absolute-center items-center"):
        with ui.card().classes("p-8").style("width: 340px; border-radius: 8px;"):

            ui.label("Forgot Password").classes(
                "text-2xl font-bold text-center w-full"
            ).style("margin-bottom:15px;")

            email = ui.input(
                placeholder="Enter your registered email"
            ).classes("w-full").props("outlined dense")

            otp = ui.input(placeholder="Enter 6-digit OTP").classes("w-full").props("outlined dense").style("margin-top:10px;")
            otp.set_visibility(False)

            countdown = ui.label("").style("color:red; font-size:13px;")
            countdown.set_visibility(False)

            new_password = ui.input(
                placeholder="New Password",
                password=True,
                password_toggle_button=True
            ).classes("w-full").props("outlined dense").style("margin-top:10px;")
            new_password.set_visibility(False)

            confirm_password = ui.input(
                placeholder="Confirm New Password",
                password=True,
                password_toggle_button=True
            ).classes("w-full").props("outlined dense").style("margin-top:10px;")
            confirm_password.set_visibility(False)

            countdown = ui.label("").style("color:red; font-size:13px;")
            countdown.set_visibility(False)

            def send_otp_clicked():

                if otp_verified:
                    notify_success("You have already verified the OTP.")
                    return
                
                if not valid_email(email.value):
                    notify_error("Please enter a valid email")
                    return

                db_conn = None
                cursor = None

                try:
                    db_conn = get_db_connection()
                    cursor = db_conn.cursor()

                    cursor.execute(
                        "SELECT * FROM users WHERE email=%s",
                        (email.value,)
                    )

                    user = cursor.fetchone()

                except Exception as e:
                    print("OTP database error:", e)
                    notify_error("Database connection error. Please try again.")
                    return

                finally:
                    if cursor:
                        cursor.close()

                    if db_conn:
                        db_conn.close()


                if not user:
                    notify_error("Email not found")
                    return

                if email.value in otp_time:
                    elapsed = time.time() - otp_time[email.value]

                    if elapsed < 300:
                        remaining = int((300 - elapsed) / 60) + 1

                        notify_error(
                            f"Please wait {remaining} minute(s) before requesting another OTP."
                        )
                        return

    
                generated_otp = str(random.randint(100000, 999999))    
                success = send_otp(email.value, generated_otp)

                if not success:
                    notify_error("Failed to send OTP. Please try again later.")
                    return

                otp_storage[email.value] = generated_otp
                otp_time[email.value] = time.time()

                otp.set_visibility(True)
                countdown.set_visibility(True)

                notify_success("OTP sent successfully!")


            def verify_otp():
                global otp_verified


                if not otp.value:
                    notify_error("Please enter the OTP.")
                    return

    
                if otp_verified:
                   notify_success("You have already verified the OTP.")
                   return


                if email.value not in otp_storage:
                   notify_error("Please request an OTP first.")
                   return


                if time.time() - otp_time[email.value] > 300:
                    del otp_storage[email.value]
                    del otp_time[email.value]

                    notify_error("OTP has expired. Please request a new OTP.")
                    return


                if otp.value != otp_storage[email.value]:
                    notify_error("Incorrect OTP")
                    return

    
                otp_verified = True

                send_otp_button.set_text("OTP Already Verified")

                notify_success("OTP verified successfully!")

                send_otp_button.set_visibility(False)
                verify_otp_button.set_visibility(False)

                email.disable()
                otp.disable()

                new_password.set_visibility(True)
                confirm_password.set_visibility(True)
                reset_button.set_visibility(True)

                countdown.set_text("OTP Verified ✓")
                countdown_timer.cancel()

            def reset_password():
                if new_password.value != confirm_password.value:
                    notify_error("Passwords do not match")
                    return

                if not valid_password(new_password.value):
                    notify_error(
                    "Password must contain uppercase, lowercase, number, special character and be at least 8 characters."
                    )
                    return

                hashed = hash_password(new_password.value)

                db_conn = None
                cursor = None

                try:
                    db_conn = get_db_connection()
                    cursor = db_conn.cursor()

                    cursor.execute(
                        "UPDATE users SET password=%s WHERE email=%s",
                        (hashed, email.value)
                    )

                    db_conn.commit()

                except Exception as e:
                    print("Reset password database error:", e)
                    notify_error("Database connection error. Please try again.")
                    return

                finally:
                    if cursor:
                        cursor.close()

                    if db_conn:
                        db_conn.close()
                        
                del otp_storage[email.value]

                if email.value in otp_time:
                    del otp_time[email.value]

                notify_success("Password updated successfully!")

                ui.navigate.to("/login")

            def update_countdown():
                if otp_verified:
                    return

                if email.value not in otp_time:
                    countdown.set_text("")
                    return

                remaining = 300 - int(time.time() - otp_time[email.value])

                if remaining <= 0:
                    countdown.set_text("OTP Expired")
                    return

                minutes = remaining // 60
                seconds = remaining % 60

                countdown.set_text(
                    f"OTP expires in {minutes:02d}:{seconds:02d}"
                )

            send_otp_button = ui.button("Send OTP",on_click=send_otp_clicked).classes("w-full text-white font-bold").style(f"background-color:{GREEN} !important; margin-top:15px;")
            verify_otp_button = ui.button("Verify OTP",on_click=verify_otp).classes("w-full text-white font-bold").style(f"background-color:{GREEN} !important; margin-top:15px;")
            reset_button = ui.button("Reset Password",on_click=reset_password).classes("w-full text-white font-bold").style(f"background-color:{GREEN} !important; margin-top:10px;")
            reset_button.set_visibility(False)
            countdown_timer = ui.timer(1.0, update_countdown)
            ui.link("Back to Login","/login").style(f"color:{GREEN}; margin-top:15px;")

ui.run(title="Login / Signup",
       host="0.0.0.0",
       port = int(os.environ.get("PORT", 8080))
)
