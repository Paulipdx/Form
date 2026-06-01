import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")

# --- FIXED NETWORK SOLUTIONS CONFIGURATION ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.networksolutionsemail.com")

# Force 2525 if Coolify sends an encrypted string
raw_port = os.getenv("SMTP_PORT", "2525")
if not raw_port or "<REDACTED>" in str(raw_port) or not str(raw_port).isdigit():
    SMTP_PORT = 2525
else:
    SMTP_PORT = int(raw_port)

SMTP_USERNAME = os.getenv("SMTP_USERNAME", "pablo@tactuswellness.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "Tactu$massage2002")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "pablo@tactuswellness.com")

@app.get("/healthz")
def healthz():
    return jsonify(status="ok"), 200

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return render_template("greet.html", name=request.form.get("name", "World"))
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/services")
def services():
    return render_template('services.html')

@app.route("/shop")
def shop():
    return render_template('shop.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            first_name = data.get('firstName') or data.get('first_name') or data.get('name') or ''
            last_name = data.get('lastName') or data.get('last_name') or ''
            email = data.get('email', '')
            phone = data.get('phone') or data.get('phone_optional', '')
            subject = data.get('subject', 'Other')
            message = data.get('message', '')
            is_ajax = True
        else:
            first_name = request.form.get('first_name') or request.form.get('name') or ''
            last_name = request.form.get('last_name', '')
            email = request.form.get('email', '')
            phone = request.form.get('phone') or request.form.get('phone_optional', '')
            subject = request.form.get('subject', 'Other')
            message = request.form.get('message', '')
            is_ajax = False

        first_name = str(first_name).strip()
        email = str(email).strip()
        message = str(message).strip()

        if not first_name or not email or not message:
            if is_ajax:
                return jsonify({'ok': False, 'error': 'Required fields missing'}), 400
            flash('Name, Email, and Message are required!', 'danger')
            return render_template('contact.html')

        email_content = (
            f"New Web Inquiry\n"
            f"---------------------------\n"
            f"Name: {first_name} {last_name}\n"
            f"Email: {email}\n"
            f"Phone: {phone}\n"
            f"Topic: {subject}\n\n"
            f"Message:\n{message}"
        )

        msg = MIMEText(email_content)
        msg['Subject'] = f"Contact Form: {subject} (from {first_name})"
        msg['From'] = SMTP_USERNAME
        msg['To'] = RECEIVER_EMAIL

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            if is_ajax:
                return jsonify({'ok': True, 'message': 'Email sent successfully!'})
            flash('Your message has been sent!', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            print(f"SMTP Error: {e}")
            if is_ajax:
                return jsonify({'ok': False, 'error': str(e)}), 500
            flash('Error sending message.', 'danger')
            return render_template('contact.html')

    return render_template('contact.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
