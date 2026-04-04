import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await login(email, password);
            navigate('/dashboard'); // Go to the Trading Floor
        } catch (err) {
            alert("Login Failed: Check your credentials");
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white">
            <form onSubmit={handleSubmit} className="bg-slate-800 p-8 rounded-lg shadow-xl w-96 border border-slate-700">
                <h2 className="text-3xl font-bold mb-6 text-blue-400">Fillado Login</h2>
                <input 
                    type="email" placeholder="Email" 
                    className="w-full p-3 mb-4 bg-slate-700 rounded border border-slate-600 focus:outline-none focus:border-blue-500"
                    onChange={(e) => setEmail(e.target.value)} 
                />
                <input 
                    type="password" placeholder="Password" 
                    className="w-full p-3 mb-6 bg-slate-700 rounded border border-slate-600 focus:outline-none focus:border-blue-500"
                    onChange={(e) => setPassword(e.target.value)} 
                />
                <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 p-3 rounded font-bold transition">
                    Enter Trading Floor
                </button>
            </form>
        </div>
    );
};

export default Login;