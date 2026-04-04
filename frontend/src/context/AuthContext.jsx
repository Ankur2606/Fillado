import { createContext, useState, useContext, useEffect } from 'react';
import API from '../api/axios';
import {useAuth} from react-router-dom;
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const login = async (email, password) => {
        const { data } = await API.post('/auth/login', { email, password });
        localStorage.setItem('sessionId', data.sessionId);
        setUser({ voices: data.voices });
        return data;
    };

    const logout = () => {
        localStorage.removeItem('sessionId');
        setUser(null);
    };
    useEffect(() => {
    const checkAuth = async () => {
        const sessionId = localStorage.getItem('sessionId');
        
        if (!sessionId) {
            setLoading(false); // No session? Stop loading and show login.
            return;
        }

        try {
            // Ensure this URL matches your FastAPI address (8000 vs 5000)
            const { data } = await API.get('/auth/me'); 
            setUser(data);
        } catch (err) {
            console.error("Auth check failed:", err);
            localStorage.removeItem('sessionId');
        } finally {
            setLoading(false); // THIS MUST RUN NO MATTER WHAT
        }
    };
    checkAuth();
}, []);

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);