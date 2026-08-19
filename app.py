import os
import urllib.request
import urllib.error
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import base64
from datetime import date

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL = os.getenv("SMTP_USERNAME", "pablo@tactuswellness.com")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "pablo@tactuswellness.com")


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
            data = request.get_json()
            first_name = data.get('firstName') or data.get('first_name') or data.get('name') or ''
            last_name = data.get('lastName') or data.get('last_name', '')
            email = data.get('email', '')
            phone = data.get('phone') or data.get('phone_optional', '')
            subject = data.get('subject', 'Other')
            message = data.get('message', '')
            uploaded_files = []
            is_ajax = True
        else:
            first_name = request.form.get('firstName') or request.form.get('first_name') or request.form.get('name') or ''
            last_name = request.form.get('lastName') or request.form.get('last_name', '')
            email = request.form.get('email', '')
            phone = request.form.get('phone') or request.form.get('phone_optional', '')
            subject = request.form.get('subject', 'Other')
            message = request.form.get('message', '')
            uploaded_files = request.files.getlist('attachments')
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

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

        payload_dict = {
            "personalizations": [{"to": [{"email": RECEIVER_EMAIL}]}],
            "from": {"email": FROM_EMAIL},
            "subject": f"Contact Form: {subject} (from {first_name})",
            "content": [{"type": "text/plain", "value": email_content}]
        }

        attachments_list = []
        for f in uploaded_files:
            if f and f.filename:
                file_bytes = f.read()
                encoded = base64.b64encode(file_bytes).decode()
                attachments_list.append({
                    "content": encoded,
                    "type": f.mimetype,
                    "filename": f.filename,
                    "disposition": "attachment"
                })

        if attachments_list:
            payload_dict["attachments"] = attachments_list

        payload = json.dumps(payload_dict).encode("utf-8")

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
            with urllib.request.urlopen(req) as resp:
                print(f"SendGrid response {resp.status}")
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

    return render_template('contact.html')


# ─────────────────────────────────────────────
#  SEO ROUTES
# ─────────────────────────────────────────────

@app.route('/robots.txt')
def robots():
    content = """User-agent: *
Allow: /

Disallow: /admin/
Disallow: /api/

Sitemap: https://form.rehab/sitemap.xml
"""
    return Response(content, mimetype='text/plain')


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
        urls += f"""
  <url>
    <loc>{loc}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>"""
    return Response(xml, mimetype='application/xml')


# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
