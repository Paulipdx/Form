import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")

# --- CORRECTED NETWORK SOLUTIONS CONFIGURATION ---
# Note: Network Solutions default SMTP server string is listed below
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.networksolutionsemail.com") 
SMTP_PORT = int(os.getenv("SMTP_PORT", 465)) # Port 465 requires Implicit SSL initialization
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "pablo@tactuswellness.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "Tactu$massage2002")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "pablo@tactuswellness.com")

@app.get("/healthz")
def healthz():
    return "ok", 200

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
    # Handle HTML form submissions and AJAX requests
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            message = data.get('message')
            is_ajax = True
        else:
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')
            is_ajax = False

        if not name or not email or not message:
            if is_ajax:
                return jsonify({'ok': False, 'error': 'All fields are required'}), 400
            flash('All fields are required!', 'danger')
            return render_template('contact.html')

        # Draft the email content
        email_content = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        msg = MIMEText(email_content)
        msg['Subject'] = f"New Contact Form Submission from {name}"
        msg['From'] = SMTP_USERNAME
        msg['To'] = RECEIVER_EMAIL

        # --- CORRECTED SMTP CONNECTION METHOD ---
        try:
            # CRITICAL FIX: Swapped to SMTP_SSL to match Port 465 criteria
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

            if is_ajax:
                return jsonify({'ok': True, 'message': 'Email sent successfully!'})
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact'))

        except Exception as e:
            print(f"SMTP Error: {e}")
            if is_ajax:
                return jsonify({'ok': False, 'error': f'Failed to send email: {str(e)}'}), 500
            flash('An error occurred while sending your message.', 'danger')
            return render_template('contact.html')

    # GET request: Render the contact page
    return render_template('contact.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
