from flask import Flask, request, render_template, redirect, url_for, flash
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from werkzeug.utils import secure_filename
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # for flashing

# Limit upload size (5MB)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# Email config from env
sender_email = os.getenv("EMAIL_ADDRESS")
sender_password = os.getenv("EMAIL_PASSWORD")
smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", 587))

# Load templates JSON once
with open("templates.json") as f:
    templates = json.load(f)

DEFAULT_ATTACHMENT_PATH = "Udbhav_sharma.pdf"  # default fallback file


def send_email(recipient_email, subject, body, attachment_file=None):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment_file:
        filename = secure_filename(attachment_file.filename)
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment_file.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={filename}",
        )
        msg.attach(part)
    else:
        # Attach default attachment if exists
        if os.path.exists(DEFAULT_ATTACHMENT_PATH):
            with open(DEFAULT_ATTACHMENT_PATH, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(DEFAULT_ATTACHMENT_PATH)}",
                )
                msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        recipient_email = request.form.get("recipient_email")
        recipient_name = request.form.get("recipient_name", "").strip()
        company_name = request.form.get("company_name", "").strip()
        job_link = request.form.get("job_link", "").strip()
        template_key = request.form.get("template_option")

        attachment = request.files.get("attachment")

        # Fallback to default template if key not found
        print(f"Selected template: {template_key}")
        if template_key not in templates:
            flash("Invalid email template selected.")
            return redirect(url_for("index"))
        template = templates[template_key]

        # Use subject from template, fallback to a generic if empty
        subject = template.get("subject") or "Regarding referral"

        # Prepare body template string
        body_template = template.get("body", "")

        # Replace placeholders if they exist in the template
        # Provide fallback for job_link if empty
        safe_job_link = job_link if job_link else "Not Available"

        body = body_template.format(
            recipient_name=recipient_name or "there",
            company_name=company_name or "your company",
            job_link=safe_job_link,
        )

        success, message = send_email(recipient_email, subject, body, attachment)
        if success:
            flash("Email sent successfully!")
        else:
            flash(f"Failed to send email: {message}")

        return redirect(url_for("index"))

    # GET method - render the form with template keys
    return render_template("email_form.html", templates=templates)


if __name__ == "__main__":
    app.run(debug=True)
