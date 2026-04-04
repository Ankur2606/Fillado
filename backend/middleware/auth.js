const connectDB = require('../config/db');

const authMiddleware = async (req, res, next) => {
    const sessionId = req.headers['x-session-id'];
    if (!sessionId) return res.status(401).json({ error: "No session found" });

    const db = await connectDB();
    const user = await db.collection('users').findOne({ "sessions.sessionId": sessionId });

    if (!user) return res.status(403).json({ error: "Invalid session" });

    req.user = user; // Attach user data to request
    next();
};

module.exports = authMiddleware;