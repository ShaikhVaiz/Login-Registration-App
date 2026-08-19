from nicegui import ui
from urllib.parse import urlparse
import ipaddress

GREEN = "#0f9d78"

def analyze_url(url):
    if not url:
        return "Please enter a URL."

    url = url.strip()

    # Add https:// if it is missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)

        if not parsed.netloc or "." not in parsed.netloc:
            return "Please enter a valid URL."

        domain = parsed.netloc.lower()
        path = parsed.path.lower()

        score = 0
        reasons = []

         # 5. Check if the URL uses an IP address instead of a domain
        try:
            ipaddress.ip_address(parsed.hostname)
            score += 25
            reasons.append(
                "The website uses an IP address instead of a normal domain name."
            )
        except ValueError:
            pass

        # 1. HTTP instead of HTTPS
        if parsed.scheme == "http":
            score += 20
            reasons.append("The website is using HTTP instead of HTTPS.")

        # 2. Suspicious words
        suspicious_words = [
            "login",
            "verify",
            "verification",
            "secure",
            "account",
            "update",
            "confirm",
            "password",
            "bank",
            "payment"
        ]

        found_words = []

        for word in suspicious_words:
            if word in domain or word in path:
                found_words.append(word)

        if found_words:
            score += min(len(found_words) * 10, 30)

            reasons.append(
                "The URL contains suspicious words: "
                + ", ".join(found_words)
                + "."
            )

        # 3. @ symbol
        if "@" in url:
            score += 25
            reasons.append(
                "The URL contains an @ symbol, which can hide the real destination."
            )

        # 4. Very long URL
        if len(url) > 100:
            score += 15
            reasons.append("The URL is unusually long.")

        # Don't allow score above 100
        score = min(score, 100)

        # Decide risk level
        if score <= 30:
            result = "🟢 SAFE"
        elif score <= 60:
            result = "🟡 SUSPICIOUS"
        else:
            result = "🔴 RISKY"

        # Create result message
        message = f"{result}\n\nRisk Score: {score}/100"

        if reasons:
            message += "\n\nWhy?\n"
            message += "\n".join("• " + reason for reason in reasons)
        else:
            message += "\n\nNo basic phishing indicators were detected."

        return message

    except Exception:
        return "Unable to analyze this URL."

@ui.page("/dashboard")
def dashboard():

    # Page background
    ui.query("body").style("background-color: #f5f7f9;")

    # Header
    with ui.row().classes(
        "w-full items-center justify-between"
    ).style(
        "background-color: white; padding: 15px 30px; "
        "box-shadow: 0 2px 8px rgba(0,0,0,0.08);"
    ):

        ui.label("🛡️ AI Phishing Detector").style(
            f"font-size:24px; font-weight:bold; color:{GREEN};"
        )

        with ui.row().classes("items-center"):
            ui.label("Welcome, User").style(
                "font-size:15px; margin-right:15px;"
            )

            ui.button(
                "Logout",
                on_click=lambda: ui.navigate.to("/login")
            ).props("outline").style(
                f"color:{GREEN};"
            )

    # Main content
    with ui.column().classes(
        "w-full items-center"
    ).style(
        "padding:40px 20px;"
    ):

        ui.label("Welcome back! 👋").style(
            "font-size:32px; font-weight:bold;"
        )

        ui.label(
            "Check suspicious links and email security with AI."
        ).style(
            "font-size:16px; color:#666; margin-bottom:30px;"
        )

        # Cards
        with ui.row().classes(
            "w-full justify-center items-stretch"
        ).style(
            "gap:25px; max-width:1000px;"
        ):

            # URL Checker
            with ui.card().style(
                "width:450px; padding:25px; border-radius:15px;"
            ):

                ui.label("🔗 URL Checker").style(
                    "font-size:22px; font-weight:bold;"
                )

                ui.label(
                    "Check whether a website URL is safe or suspicious."
                ).style(
                    "color:#666; margin-bottom:15px;"
                )

                url_input = ui.input(
                    label="Enter URL",
                    placeholder="https://example.com"
                ).props("outlined").classes("w-full")

                result_label = ui.label("").style("margin-top:15px; font-weight:bold;")
                ui.button("Analyze URL",on_click=lambda: result_label.set_text(analyze_url(url_input.value))
                ).classes("w-full text-white font-bold").style(f"background-color:{GREEN}; margin-top:15px;")

            # Email Checker
            with ui.card().style(
                "width:450px; padding:25px; border-radius:15px;"
            ):

                ui.label("📧 Email Breach Checker").style(
                    "font-size:22px; font-weight:bold;"
                )

                ui.label(
                    "Check whether your email appeared in known data breaches."
                ).style(
                    "color:#666; margin-bottom:15px;"
                )

                email_input = ui.input(
                    label="Enter Email",
                    placeholder="example@gmail.com"
                ).props("outlined").classes("w-full")

                ui.button(
                    "Check Email"
                ).classes(
                    "w-full text-white font-bold"
                ).style(
                    f"background-color:{GREEN}; margin-top:15px;"
                )

        # Recent checks
        with ui.column().style(
            "width:100%; max-width:925px; margin-top:40px;"
        ):

            ui.label("Recent Security Checks").style(
                "font-size:22px; font-weight:bold; margin-bottom:10px;"
            )

            with ui.card().classes("w-full").style(
                "border-radius:12px;"
            ):

                ui.label(
                    "No security checks yet."
                ).style(
                    "color:#777; padding:10px;"
                )
                