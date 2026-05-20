import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../../config';
import styles from './register.module.css';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async () => {
    const payload = {
      username: formData.username.trim(),
      password: formData.password,
    };

    if (!payload.username || !payload.password) {
      alert('Please enter both username and password.');
      return;
    }

    try {
      setIsLoading(true);
      await axios.post(`${API_URL}/register`, payload);
      alert('Registration successful. Please log in.');
      navigate('/login');
    } catch (error) {
      const backendDetail = error?.response?.data?.detail;
      const message = backendDetail || error.message || 'Registration failed.';
      alert(`Registration failed: ${message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.appName}>Dear Diary,</h1>
      <div className={styles.card}>
        <h2>Register</h2>
        <input
          className={styles.inputField}
          placeholder="Username"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
        />
        <input
          className={styles.inputField}
          type="password"
          placeholder="Password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
        />
        <button className={styles.registerButton} type="button" onClick={handleRegister} disabled={isLoading}>
          {isLoading ? 'Registering...' : 'Register'}
        </button>
        <p className={styles.registerText}>
          Already have an account?
          <Link className={styles.registerLink} to="/">
            Login here.
          </Link>
        </p>
      </div>
    </div>
  );
}
