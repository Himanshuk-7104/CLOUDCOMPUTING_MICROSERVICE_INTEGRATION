// src/App.jsx
import React from 'react';
import Login from './Login'; // Import the Login component
import './App.css'; // You might want to keep or modify default styling

function App() {
    return (
        <div className="App">
            <header className="App-header">
                {/* You can add a header or other layout elements here */}
            </header>
            <main>
                <Login /> {/* Render the Login component */}
            </main>
        </div>
    );
}

export default App;