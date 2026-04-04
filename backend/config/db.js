const { MongoClient } = require('mongodb');
require('dotenv').config();
const client = new MongoClient(process.env.MONGO_URI);
let db;
console.log("URI:", process.env.MONGO_URI);

const connectDB = async () => {
    if (db) return db;
    await client.connect();
    db = client.db('fillado_db');
    console.log(" MongoDB Connected");
    return db;
};


module.exports = connectDB;