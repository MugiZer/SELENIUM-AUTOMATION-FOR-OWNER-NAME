require('dotenv').config();
const express = require('express');
const session = require('express-session');
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const path = require('path');
const cors = require('cors');
const app = express();

// Middleware
app.use(cors({
  origin: [
    'http://localhost:5173',
    'https://ownernameenrichment-lj904tt3a-mugizers-projects.vercel.app'
  ],
  credentials: true
}));
app.use(express.json());

// Session configuration
app.use(session({
  secret: process.env.SESSION_SECRET || 'your-session-secret',
  resave: false,
  saveUninitialized: false,
  cookie: { 
    secure: process.env.NODE_ENV === 'production',
    sameSite: process.env.NODE_ENV === 'production' ? 'none' : 'lax',
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Initialize Passport
app.use(passport.initialize());
app.use(passport.session());

// Google OAuth Strategy
passport.use(new GoogleStrategy({
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL: process.env.NODE_ENV === 'production' 
      ? 'https://ownernameenrichment-lj904tt3a-mugizers-projects.vercel.app/auth/google/callback'
      : 'http://localhost:3000/auth/google/callback',
    scope: ['profile', 'email', 'https://www.googleapis.com/auth/spreadsheets'],
    accessType: 'offline',
    prompt: 'consent'
  },
  (accessToken, refreshToken, profile, done) => {
    // Store tokens in user profile
    profile.accessToken = accessToken;
    if (refreshToken) {
      profile.refreshToken = refreshToken;
    }
    return done(null, profile);
  }
));

// Serialize/deserialize user
passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((user, done) => done(null, user));

// Auth routes
app.get('/auth/google',
  passport.authenticate('google', { 
    scope: ['profile', 'email', 'https://www.googleapis.com/auth/spreadsheets'] 
  })
);

app.get('/auth/google/callback', 
  passport.authenticate('google', { 
    failureRedirect: '/login',
    successRedirect: process.env.NODE_ENV === 'production'
      ? 'https://ownernameenrichment-lj904tt3a-mugizers-projects.vercel.app/dashboard'
      : 'http://localhost:5173/dashboard'
  })
);

// Check authentication status
app.get('/api/auth/status', (req, res) => {
  res.json({ 
    isAuthenticated: req.isAuthenticated(),
    user: req.user || null 
  });
});

// Logout route
app.post('/auth/logout', (req, res) => {
  req.logout(() => {
    res.json({ success: true });
  });
});

// Protected API route example
app.get('/api/user', (req, res) => {
  if (!req.isAuthenticated()) {
    return res.status(401).json({ error: 'Not authenticated' });
  }
  res.json(req.user);
});

// Serve static files from the UI build
app.use(express.static(path.join(__dirname, 'ui/dist')));

// API status endpoint
app.get('/api/status', (req, res) => {
  res.json({ 
    status: 'Server is running',
    environment: process.env.NODE_ENV || 'development'
  });
});

// All other requests go to the React app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'ui/dist/index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`API available at http://localhost:${PORT}/api/status`);
  console.log(`Google OAuth callback: ${process.env.NODE_ENV === 'production' 
    ? 'https://ownernameenrichment-lj904tt3a-mugizers-projects.vercel.app/auth/google/callback'
    : 'http://localhost:3000/auth/google/callback'}`);
});
