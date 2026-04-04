const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const axios = require('axios');

// Update specific agent voice
router.patch('/update-voice', authMiddleware, async (req, res) => {
    const { agentType, newVoiceId } = req.body; // e.g. "retailTrader"
    const db = await connectDB();

    await db.collection('users').updateOne(
        { _id: req.user._id },
        { $set: { [`voices.${agentType}`]: newVoiceId } }
    );
    res.json({ message: `${agentType} voice updated!` });
});

// Fetch all voices from ElevenLabs to show in settings
router.get('/elevenlabs-voices', async (req, res) => {
    try {
        const response = await axios.get('https://api.elevenlabs.io/v1/voices', {
            headers: { 'xi-api-key': process.env.ELEVENLABS_API_KEY }
        });
        res.json(response.data.voices);
    } catch (err) {
        res.status(500).json({ error: "Failed to fetch voices" });
    }
});

module.exports = router;