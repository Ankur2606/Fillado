import { useState } from "react";
import { Link } from "react-router-dom";
import API from "../api/axios";
import { useNavigate } from "react-router-dom";

export default function Signup() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
  });

  const [error, setError] = useState("");
  const navigate = useNavigate();

  const set = (key) => (e) =>
    setFormData({ ...formData, [key]: e.target.value });

  const handleSignup = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirm) {
      return setError("Passwords do not match");
    }

    try {
      await API.post("/api/auth/register", formData);
      navigate("/login");
    } catch {
      setError("Registration failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b1120]">

      <div className="w-full max-w-md bg-[#111827] border border-[#1f2937] rounded-2xl p-8 shadow-xl">

        <h2 className="text-2xl font-semibold text-white text-center mb-6">
          Create Account
        </h2>

        {error && (
          <p className="text-red-400 text-sm mb-3 text-center">{error}</p>
        )}

        <form onSubmit={handleSignup} className="space-y-4">

          <input className="input" placeholder="Full Name" onChange={set("name")} />

          <input className="input" placeholder="Email" onChange={set("email")} />

          <input
            className="input"
            type="password"
            placeholder="Password"
            onChange={set("password")}
          />

          <input
            className="input"
            type="password"
            placeholder="Confirm Password"
            onChange={set("confirm")}
          />

          <button className="btn">Create Account</button>
        </form>

        <p className="text-gray-400 text-sm text-center mt-5">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-400 hover:underline">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}