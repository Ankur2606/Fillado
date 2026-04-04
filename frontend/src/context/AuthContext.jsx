import { createContext, useState, useContext, useEffect } from 'react';
import API from '../api/axios';



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
        // Optional: Redirect to login or refresh page
        window.location.href = '/login'; 
    };

    useEffect(() => {
        const checkAuth = async () => {
            const sessionId = localStorage.getItem('sessionId');
            
            if (!sessionId) {
                setLoading(false);
                return;
            }

            try {
                // Ensure your FastAPI has a GET route for /auth/me
                const { data } = await API.get('/auth/me'); 
                setUser(data);
            } catch (err) {
                console.error("Auth check failed:", err);
                localStorage.removeItem('sessionId');
                setUser(null);
            } finally {
                setLoading(false); 
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