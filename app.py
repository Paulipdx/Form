import os
import smtplib
import ssl
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from datetime import date

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")

# ── SMTP CONFIG ──
SMTP_SERVER    = os.getenv("SMTP_SERVER",    "stalwart-iynj8jrknr7oz5mvd51unqiz")
SMTP_PORT      = int(os.getenv("SMTP_PORT",  "465"))
SMTP_USERNAME  = os.getenv("SMTP_USERNAME",  "hello@form.rehab")
SMTP_PASSWORD  = os.getenv("SMTP_PASSWORD",  "")
FROM_EMAIL     = os.getenv("FROM_EMAIL",     "hello@form.rehab")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "hello@form.rehab")


def send_email(subject, body, reply_to=None, attachments=None):
    try:
        msg = MIMEMultipart()
        msg['From']    = FROM_EMAIL
        msg['To']      = RECEIVER_EMAIL
        msg['Subject'] = subject
        if reply_to:
            msg['Reply-To'] = reply_to
        msg.attach(MIMEText(body, 'plain'))
        if attachments:
            for filename, mimetype, file_bytes in attachments:
                part = MIMEBase(*mimetype.split('/', 1))
                part.set_payload(file_bytes)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)

        if SMTP_PORT == 465:
            # SSL from the start — cert verification disabled for self-hosted Stalwart
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            # STARTTLS (587)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

        return True, None
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False, str(e)


@app.get("/healthz")
def healthz():
    return jsonify(status="ok"), 200

@app.route("/")
def index():
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
            data       = request.get_json()
            first_name = data.get('firstName') or data.get('first_name') or data.get('name') or ''
            last_name  = data.get('lastName') or data.get('last_name', '')
            email      = data.get('email', '')
            phone      = data.get('phone') or data.get('phone_optional', '')
            subject    = data.get('subject', 'Other')
            message    = data.get('message', '')
            uploaded_files = []
            is_ajax    = True
        else:
            first_name = request.form.get('firstName') or request.form.get('first_name') or request.form.get('name') or ''
            last_name  = request.form.get('lastName') or request.form.get('last_name', '')
            email      = request.form.get('email', '')
            phone      = request.form.get('phone') or request.form.get('phone_optional', '')
            subject    = request.form.get('subject', 'Other')
            message    = request.form.get('message', '')
            uploaded_files = request.files.getlist('attachments')
            is_ajax    = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not first_name or not email or not message:
            if is_ajax:
                return jsonify({'ok': False, 'error': 'Required fields missing'}), 400
            flash('Name, Email, and Message are required!', 'danger')
            return render_template('contact.html')

        email_body = (
            f"New Web Inquiry — Form.Rehab\n"
            f"{'─' * 40}\n"
            f"Name:    {first_name} {last_name}\n"
            f"Email:   {email}\n"
            f"Phone:   {phone or 'Not provided'}\n"
            f"Topic:   {subject}\n\n"
            f"Message:\n{message}\n"
            f"{'─' * 40}\n"
            f"Sent from form.rehab/contact"
        )

        attachments = []
        for f in uploaded_files:
            if f and f.filename:
                attachments.append((f.filename, f.mimetype, f.read()))

        ok, error = send_email(
            subject     = f"[Form.Rehab] {subject} — {first_name} {last_name}",
            body        = email_body,
            reply_to    = email,
            attachments = attachments if attachments else None
        )

        if ok:
            if is_ajax:
                return jsonify({'ok': True, 'message': 'Email sent successfully!'})
            flash('Your message has been sent!', 'success')
            return redirect(url_for('contact'))
        else:
            if is_ajax:
                return jsonify({'ok': False, 'error': 'Failed to send. Please try again.'}), 500
            flash('Error sending message. Please call us directly.', 'danger')
            return render_template('contact.html')

    return render_template('contact.html')


@app.route('/robots.txt')
def robots():
    return Response("User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /api/\nSitemap: https://form.rehab/sitemap.xml\n", mimetype='text/plain')

@app.route('/google0b875814bda86a62.html')
def google_verify():
    return Response('google-site-verification: google0b875814bda86a62.html', mimetype='text/html')

@app.route('/sitemap.xml')
def sitemap():
    today = date.today().isoformat()
    pages = [
        ('https://form.rehab/',         '1.0', 'weekly'),
        ('https://form.rehab/about',    '0.8', 'monthly'),
        ('https://form.rehab/services', '0.9', 'monthly'),
        ('https://form.rehab/shop',     '0.9', 'weekly'),
        ('https://form.rehab/contact',  '0.7', 'monthly'),
    ]
    urls = ''
    for loc, priority, changefreq in pages:
        urls += f"\n  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>{changefreq}</changefreq>\n    <priority>{priority}</priority>\n  </url>"
    return Response(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}\n</urlset>', mimetype='application/xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
