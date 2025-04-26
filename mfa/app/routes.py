from flask import Blueprint, request, jsonify
# from app import mysql # Remove MySQL import
from . import get_supabase_client # Import function to get Supabase client
from .utils import send_otp_email
import random
from datetime import datetime, timedelta, timezone # For expiry check

mfa = Blueprint('mfa', __name__)
OTP_TABLE = 'mfa_otps' # Define table name once
OTP_VALIDITY_MINUTES = 5

@mfa.route('/generate-otp', methods=['POST'])
def generate_otp():
    supabase = get_supabase_client()
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    otp = str(random.randint(100000, 999999))
    current_time_iso = datetime.now(timezone.utc).isoformat()

    try:
        # Use upsert: inserts if email doesn't exist, updates if it does
        response = supabase.table(OTP_TABLE).upsert({
            'email': email,
            'otp': otp,
            'created_at': current_time_iso # Store creation time
        }).execute()

        # Optional: Check response for errors if needed, though upsert often handles it
        # if response.get('error'):
        #    raise Exception(f"Supabase upsert error: {response['error']['message']}")

        send_otp_email(email, otp)
        return jsonify({'message': 'OTP sent successfully'})

    except Exception as e:
        print(f"Error in /generate-otp: {e}")
        # Check if e is a Supabase specific error if supabase-py provides typed errors
        return jsonify({'message': 'Failed to generate or store OTP'}), 500


@mfa.route('/verify-otp', methods=['POST'])
def verify_otp():
    supabase = get_supabase_client()
    data = request.get_json()
    email = data.get('email')
    submitted_otp = data.get('otp')

    if not email or not submitted_otp:
        return jsonify({'message': 'Email and OTP are required'}), 400

    try:
        # 1. Fetch the stored OTP data for the email
        response = supabase.table(OTP_TABLE).select("otp, created_at").eq('email', email).maybe_single().execute()
        # maybe_single() returns data: None if not found, data: {...} if found

        if response.data is None:
             print(f"Verify attempt failed: No OTP found for email: {email}")
             return jsonify({'message': 'Invalid or expired OTP'}), 400 # Use 400 or 401

        stored_otp_data = response.data
        stored_otp = stored_otp_data.get('otp')
        created_at_str = stored_otp_data.get('created_at')

        # 2. Check if OTP matches
        if stored_otp != submitted_otp:
            print(f"Verify attempt failed: OTP mismatch for email: {email}")
            return jsonify({'message': 'Invalid or expired OTP'}), 400

        # 3. Check if OTP is expired
        try:
            # Ensure created_at_str includes timezone info for correct comparison
            created_at = datetime.fromisoformat(created_at_str)
            # Make sure current time is also timezone-aware (UTC)
            current_time = datetime.now(timezone.utc)
            if current_time > created_at + timedelta(minutes=OTP_VALIDITY_MINUTES):
                 print(f"Verify attempt failed: OTP expired for email: {email}")
                 # Optional: Delete expired OTP here as well
                 supabase.table(OTP_TABLE).delete().eq('email', email).execute()
                 return jsonify({'message': 'Invalid or expired OTP'}), 400
        except (ValueError, TypeError) as dt_error:
             print(f"Error parsing OTP timestamp for {email}: {dt_error}")
             return jsonify({'message': 'Error processing OTP timestamp'}), 500


        # 4. OTP is valid and matched! Delete it so it can't be reused.
        try:
            delete_response = supabase.table(OTP_TABLE).delete().eq('email', email).execute()
            # Optional: Check delete_response for errors
        except Exception as del_e:
             # Log the error but proceed, as verification was successful
             print(f"Warning: Failed to delete used OTP for {email}: {del_e}")


        print(f"Verify successful for email: {email}")
        return jsonify({'message': 'Verification successful'})

    except Exception as e:
        print(f"Error in /verify-otp: {e}")
        return jsonify({'message': 'Failed to verify OTP due to server error'}), 500