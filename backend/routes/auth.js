const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');
const connectDB = require('../config/db');

router.post('/login', async (req, res) => {
    const { email, password } = req.body;
    const db = await connectDB();
    const user = await db.collection('users').findOne({ email });

    if (user && await bcrypt.compare(password, user.passwordHash)) {
        const sessionId = uuidv4();
        await db.collection('users').updateOne(
            { _id: user._id },
            { $push: { sessions: { sessionId, createdAt: new Date() } } }
        );
        res.json({ sessionId, voices: user.voices });
    } else {
        res.status(401).json({ error: "Invalid credentials" });
    }
});
router.post('/register', async (req, res) => {
    try {
        const { name, email, password } = req.body;

        const db = await connectDB();

        // Check if user already exists
        const existingUser = await db.collection('users').findOne({ email });

        if (existingUser) {
            return res.status(400).json({ error: "User already exists" });
        }

        // Hash password
        const passwordHash = await bcrypt.hash(password, 10);

        // Create user
        const newUser = {
            name,
            email,
            passwordHash,
            sessions: [],
            voices: [],
            createdAt: new Date()
        };

        await db.collection('users').insertOne(newUser);

        res.json({ message: "User registered successfully" });

    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Server error" });
    }
});
module.exports = router;