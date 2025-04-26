# notification-service/app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import threading
import time
import random
import os

app = Flask(__name__)
CORS(app)

# --- Configuration ---
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME') # Removed default for safety
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD') # MUST be set in .env/docker-compose
SENDER_EMAIL = os.getenv('SENDER_EMAIL', SMTP_USERNAME)

# --- In-memory storage ---
reminders = []
otp_storage = {}
# -------------------------

# --- Email Sending Function (Modified Error Return) ---
def send_email(recipient_email, subject, body):
    # Check for missing credentials FIRST
    if not SMTP_USERNAME:
        error_msg = "Error: SMTP_USERNAME environment variable not set."
        print(error_msg)
        return error_msg # Return error message string
    if not SMTP_PASSWORD:
        error_msg = "Error: SMTP_PASSWORD environment variable not set."
        print(error_msg)
        return error_msg # Return error message string
    if not SENDER_EMAIL:
        # Fallback to username if sender email specifically isn't set
        sender = SMTP_USERNAME
        print(f"Warning: SENDER_EMAIL not set, falling back to SMTP_USERNAME ({sender})")
    else:
        sender = SENDER_EMAIL


    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient_email

        print(f"Attempting SMTP connection to {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.set_debuglevel(1) # Add more detailed SMTP logs
            print("Starting TLS...")
            server.starttls()
            print("Logging in...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print("Sending mail...")
            server.sendmail(sender, recipient_email, msg.as_string())
            print(f"Successfully sent email to {recipient_email}")
        return True # Indicate success
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP Authentication Error: Login failed for {SMTP_USERNAME}. Check username/App Password. (Code: {e.smtp_code} Detail: {e.smtp_error})"
        print(error_msg)
        return error_msg # Return error message string
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(error_msg)
        return error_msg # Return error message string
# ----------------------------------------------------

# --- Reminder Background Thread (Keep as is) ---
def check_reminders():
    while True:
        now = datetime.now()
        current_reminders = list(reminders)
        for reminder in current_reminders:
            if 'datetime' in reminder and reminder['datetime'] <= now and not reminder.get('sent', False):
                print(f"Processing reminder for {reminder['email']} for: {reminder['subject']}")
                email_result = send_email(reminder['email'], reminder['subject'], reminder['message'])
                if email_result is True:
                    reminder['sent'] = True
                    print(f"Reminder sent to {reminder['email']} for: {reminder['subject']}")
                else:
                    # Log the specific error if sending failed
                    print(f"Failed to send reminder email to {reminder['email']}: {email_result}")
        time.sleep(60)

reminder_thread = threading.Thread(target=check_reminders, daemon=True)
reminder_thread.start()
# -------------------------------------------

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html', reminder_count=len(reminders))

@app.route('/send_notification', methods=['POST'])
def handle_send_notification():
    # Keep this route as it was in your previous version
    student_email = request.form.get('student_email')
    email_subject = request.form.get('email_subject')
    email_body = request.form.get('email_body')
    reminder_datetime_str = request.form.get('reminder_datetime')
    reminder_subject = request.form.get('reminder_subject')
    reminder_message = request.form.get('reminder_message')

    email_sent_status = "No email requested or missing details."
    if student_email and email_subject and email_body:
        email_result = send_email(student_email, email_subject, email_body)
        if email_result is True:
             email_sent_status = f"Email sent successfully to {student_email}."
        else:
             # Include the specific error reason
             email_sent_status = f"Failed to send email to {student_email}: {email_result}"

    reminder_set_status = "No reminder requested or missing details."
    if reminder_datetime_str and reminder_subject and reminder_message and student_email:
        try:
            reminder_datetime = datetime.strptime(reminder_datetime_str, '%Y-%m-%dT%H:%M')
            if reminder_datetime > datetime.now():
                reminders.append({
                    'email': student_email, 'datetime': reminder_datetime,
                    'subject': reminder_subject, 'message': reminder_message, 'sent': False
                })
                reminder_set_status = f"Reminder set for {student_email} at {reminder_datetime} for: {reminder_subject}"
                print(reminder_set_status)
            else:
                 reminder_set_status = "Reminder time must be in the future."
        except ValueError:
            reminder_set_status = "Invalid reminder datetime format provided."
            print(reminder_set_status)

    return render_template('index.html', email_status=email_sent_status, reminder_status=reminder_set_status, reminder_count=len(reminders))


# --- MFA Routes (Modified Error Handling) ---

@app.route('/generate-otp', methods=['POST'])
def generate_otp():
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 415

    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"message": "Email is required"}), 400

    email = data['email']
    otp = str(random.randint(100000, 999999))
    expiration_time = datetime.now() + timedelta(minutes=5)
    otp_storage[email] = (otp, expiration_time)

    print(f"Generated OTP {otp} for {email}, expires at {expiration_time}")

    subject = "Your MFA OTP Code"
    body = f"Your One-Time Password (OTP) for login is: {otp}\nIt is valid for 5 minutes."

    # Call send_email and check its return value
    email_result = send_email(email, subject, body)

    if email_result is True:
        # Success
        print(f"MFA OTP email sent successfully to {email}")
        return jsonify({"message": "OTP sent successfully"}), 200
    else:
        # Failure - email_result contains the error message string
        print(f"Error sending MFA OTP email to {email}")
        # Return the specific error message from send_email in the response
        return jsonify({"message": f"Failed to send OTP email: {email_result}"}), 500 # Keep 500 status


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
     # Keep verify logic as before
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 415

    data = request.get_json()
    if not data or 'email' not in data or 'otp' not in data:
        return jsonify({"message": "Email and OTP are required"}), 400

    email = data['email']
    submitted_otp = data['otp']
    stored_data = otp_storage.get(email)

    if stored_data:
        stored_otp, expiration_time = stored_data
        if datetime.now() > expiration_time:
            print(f"OTP verification failed for {email}: OTP expired at {expiration_time}")
            otp_storage.pop(email, None)
            return jsonify({"message": "OTP has expired"}), 400
        elif stored_otp == submitted_otp:
            otp_storage.pop(email, None)
            print(f"OTP verified successfully for {email}")
            return jsonify({"message": "Verification successful"}), 200
        else:
             print(f"OTP verification failed for {email}. Submitted: {submitted_otp}, Stored: {stored_otp}")
             return jsonify({"message": "Invalid OTP"}), 400
    else:
        print(f"OTP verification failed for {email}: No OTP found in storage.")
        return jsonify({"message": "Invalid or expired OTP"}), 400

# --- End Routes ---


if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True)