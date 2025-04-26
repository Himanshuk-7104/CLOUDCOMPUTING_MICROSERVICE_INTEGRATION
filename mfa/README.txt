README - Multi-Factor Authentication Microservice

This project is a basic implementation of an MFA (Multi-Factor Authentication) microservice using Flask and MySQL.

Tools and Frameworks Used:
1. Python 3.12
2. Flask
3. Flask-Mail
4. MySQL
5. Gmail SMTP (for sending OTP emails)
6. Postman (for testing the API endpoints)

Description:
- The user sends a request to generate an OTP.
- The OTP is sent to the user's email and stored in the MySQL database.
- The user verifies the OTP through another API endpoint.
- OTPs are valid for 5 minutes.

Screenshots and code are included to show that the microservice has been tested and is working.
