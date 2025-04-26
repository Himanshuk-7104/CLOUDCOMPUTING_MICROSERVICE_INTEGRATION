// src/Login.jsx
import React, { useState } from 'react';
import axios from 'axios';

function Login() {
    // State variables for login, MFA, and status messages
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState(''); // For password login status
    const [isPasswordVerified, setIsPasswordVerified] = useState(false);
    const [userEmail, setUserEmail] = useState(''); // Store email after successful password login
    const [showMfaSection, setShowMfaSection] = useState(false); // Control visibility of OTP input
    const [otp, setOtp] = useState(''); // Store the OTP entered by user
    const [mfaMessage, setMfaMessage] = useState(''); // For MFA status/error messages
    const [isFullyLoggedIn, setIsFullyLoggedIn] = useState(false); // Final success state

    // Handle initial password login
    const handleSubmit = async (event) => {
        event.preventDefault();
        // Reset states on new login attempt
        setMessage(''); setMfaMessage(''); setIsPasswordVerified(false);
        setIsFullyLoggedIn(false); setShowMfaSection(false);

        try {
            // Call auth-backend via Nginx proxy (path configured in nginx.conf)
            const response = await axios.post('/api/auth/login', { email, password });
            console.log('Password Login successful:', response.data);
            // Extract email from response if possible, otherwise use input email
            setUserEmail(response.data.user?.email || email);
            setIsPasswordVerified(true);
            setMessage(''); // Clear login message on success
        } catch (error) {
            console.error('Login error:', error);
            // Display error from backend response or a generic message
            setMessage(error.response?.data?.error || 'Invalid credentials or server error');
            setIsPasswordVerified(false);
            setPassword(''); // Clear password field on error
        }
    };

    // Handle initiation of MFA (sending OTP)
    const handleInitiateMfa = async () => {
        if (!userEmail) { setMfaMessage('Error: User email not found.'); return; }
        setMfaMessage('Sending OTP...'); setShowMfaSection(false); // Hide OTP input while sending

        try {
            // Call notification-service API (accessible via host port mapping)
            const response = await axios.post('http://localhost:5001/generate-otp', { email: userEmail });
            console.log('Generate OTP response:', response.data);
            // Use message from backend response if available
            setMfaMessage(response.data.message || 'OTP sent successfully.');
            setShowMfaSection(true); // Show OTP input section
        } catch (error) {
            console.error('Generate OTP error:', error);
            setShowMfaSection(false);
            // Display detailed error from backend or a generic fallback
            const errorDetail = error.response?.data?.message || error.message || 'Cannot reach MFA service. Is it running on port 5001?';
            setMfaMessage(`Failed to send OTP: ${errorDetail}`);
        }
    };

    // Handle verification of the entered OTP
    const handleVerifyOtp = async (event) => {
        event.preventDefault();
        setMfaMessage('Verifying OTP...');
        if (!userEmail || !otp) { setMfaMessage('Email or OTP missing.'); return; }

        try {
            // Call notification-service API
            const response = await axios.post('http://localhost:5001/verify-otp', { email: userEmail, otp: otp });
            console.log('Verify OTP response:', response.data);
            // Use message from backend response
            setMfaMessage(response.data.message || 'MFA Verification Successful!');
            setIsFullyLoggedIn(true); // Set final logged-in state
            setShowMfaSection(false); // Hide MFA section on success
        } catch (error) {
            console.error('Verify OTP error:', error);
            // Display error from backend or a generic message
            setMfaMessage(`Verification failed: ${error.response?.data?.message || 'Invalid or expired OTP'}`);
            setIsFullyLoggedIn(false); // Ensure not marked as logged in on failure
            setOtp(''); // Clear OTP input on failure
        }
    };


    // --- Function to handle redirection to Notification Service ---
    const goToNotificationService = () => {
        // Opens notification service page (running on host port 5001) in a new tab
        window.open('http://localhost:5001', '_blank');
    };

    // --- Function to handle redirection to Feedback Service ---
    const goToFeedbackService = () => {
        // Opens feedback service page (running on host port 8000) in a new tab
        window.open('http://localhost:8000/docs', '_blank');
    };


    // --- Render Logic ---
    return (
        <div>
            <h2>Login</h2>

            {/* --- Login Form (Show if password not verified AND not fully logged in) --- */}
            {!isPasswordVerified && !isFullyLoggedIn && (
                 <form onSubmit={handleSubmit}>
                     <div><label htmlFor="email">Email:</label><input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
                     <div><label htmlFor="password">Password:</label><input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
                     <button type="submit">Login</button>
                     {/* Display password login status/error messages */}
                     {message && <p style={{ color: 'red' }}>{message}</p>}
                 </form>
            )}

            {/* --- Initiate MFA Button (Show if password verified, but MFA not initiated/verified) --- */}
            {isPasswordVerified && !showMfaSection && !isFullyLoggedIn && (
                 <div>
                     <p>Password verified! Click below to send MFA code to {userEmail}.</p>
                     <button onClick={handleInitiateMfa}>Send MFA Code</button>
                     {/* Display MFA initiation status/error messages */}
                     {mfaMessage && <p>{mfaMessage}</p>}
                 </div>
            )}

             {/* --- Verify MFA Form (Show if MFA initiated, but not verified) --- */}
             {isPasswordVerified && showMfaSection && !isFullyLoggedIn && (
                  <div>
                    <h3>Enter MFA Code</h3>
                    {/* Display MFA status/error messages */}
                    <p>{mfaMessage || `Enter the OTP sent to ${userEmail}.`}</p>
                    <form onSubmit={handleVerifyOtp}>
                        <div><label htmlFor="otp">OTP:</label><input type="text" id="otp" value={otp} onChange={(e) => setOtp(e.target.value)} required maxLength="6"/></div>
                        <button type="submit">Verify OTP</button>
                    </form>
                  </div>
             )}


            {/* --- Fully Logged In Section (Show only after successful MFA) --- */}
            {isFullyLoggedIn && (
                <div>
                    <h3 style={{ color: 'green' }}>Login and MFA Successful!</h3>
                    <p>Welcome, {userEmail}!</p>

                    {/* Button to navigate to the Notification Service Page */}
                    <button onClick={goToNotificationService} style={{ marginTop: '20px', marginRight: '10px' }}>
                        Go to Notification Service Page
                    </button>

                    {/* Button to navigate to the Feedback Service */}
                    <button onClick={goToFeedbackService} style={{ marginTop: '20px' }}>
                        Go to Feedback Service
                    </button>
                </div>
            )}
        </div>
    );
}

export default Login;