// server.js
require('dotenv').config(); // Load environment variables from .env file
const express = require('express');
const cors = require('cors');
// const bcrypt = require('bcrypt'); // No longer needed for login if using Supabase Auth methods
const { createClient } = require('@supabase/supabase-js');

// Check if Supabase credentials are loaded
if (!process.env.SUPABASE_URL || !process.env.SUPABASE_ANON_KEY) {
    console.error("Error: Supabase URL or Anon Key not found in .env file. Make sure .env is populated.");
    process.exit(1); // Stop the server if credentials are missing
}

// Initialize Supabase client
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

const app = express();
const port = process.env.PORT || 3001;

// Middleware
app.use(cors()); // Enable Cross-Origin Resource Sharing for requests from your frontend
app.use(express.json()); // Enable parsing of JSON request bodies

// Basic Route to check if server is running
app.get('/', (req, res) => {
    res.send('Auth Backend is running!');
});


// --- Authentication Route (Using Supabase Auth) ---
app.post('/api/auth/login', async (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({ error: 'Email and password are required' });
    }

    try {
        // Use Supabase built-in function to sign in
        const { data, error } = await supabase.auth.signInWithPassword({
            email: email,
            password: password,
        });

        // Handle sign-in errors (e.g., invalid credentials)
        if (error) {
            console.error('Supabase login error:', error.message); // Log the error message from Supabase
            // Send a generic error to the client for security
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        // Login successful!
        // 'data.user' contains user information (id, email, etc.)
        // 'data.session' contains session information (access_token, refresh_token)
        console.log(`Login successful for: ${data.user.email}`);

        // Send back relevant user data (AVOID sending session/tokens unless your frontend needs them explicitly)
        // You might only need to send the user object or just a success message.
        res.status(200).json({
            message: 'Login successful',
            user: { // Only send non-sensitive user info needed by the frontend
                id: data.user.id,
                email: data.user.email,
                // Add other safe properties if needed
            }
            // Avoid sending data.session unless your frontend specifically handles token management
        });

    } catch (err) {
        // Catch unexpected server errors
        console.error('Server error during login:', err);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// --- End of Authentication Route ---

// Start the server
app.listen(port, () => {
    console.log(`Auth backend server listening on port ${port}`); // Use port variable
});