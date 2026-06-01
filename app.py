import os
import urllib.request
import urllib.error
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL = os.getenv("SMTP_USERNAME", "pablo@tactuswellness.com")
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
            uploaded_file = request.files.get('attachment')
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

        payload = json.dumps({
            "personalizations": [{"to": [{"email": RECEIVER_EMAIL}]}],
            "from": {"email": FROM_EMAIL},
            "subject": f"Contact Form: {subject} (from {first_name})",
            "content": [{"type": "text/plain", "value": email_content}]
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=payload,
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:
            print(f"DEBUG: Sending via SendGrid from {FROM_EMAIL} to {RECEIVER_EMAIL}")
            with urllib.request.urlopen(req) as resp:
                print(f"DEBUG: SendGrid response {resp.status}")
            if is_ajax:
                return jsonify({'ok': True, 'message': 'Email sent successfully!'})
            flash('Your message has been sent!', 'success')
            return redirect(url_for('contact'))
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"SendGrid Error {e.code}: {body}")
            if is_ajax:
                return jsonify({'ok': False, 'error': f'SendGrid {e.code}: {body}'}), 500
            flash('Error sending message.', 'danger')
            return render_template('contact.html')
        except Exception as e:
            print(f"Error: {e}")
            if is_ajax:
                return jsonify({'ok': False, 'error': str(e)}), 500
            flash('Error sending message.', 'danger')
            return render_template('contact.html')

    return render_template('contact.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

