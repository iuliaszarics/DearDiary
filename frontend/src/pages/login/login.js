import React, {useState} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../../config';
import styles from './login.module.css';

export default function Login({setUserId}) {
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const navigate = useNavigate();
    const handleLogin = async() => {
        try{
            const response = await axios.post(`${API_URL}/login`, formData);
            const nextUserId = response.data.user_id;
            localStorage.setItem('userId', String(nextUserId));
            setUserId(nextUserId);
            navigate('/dashboard');
        } catch (error) {
            alert('Login failed. Please check your credentials and try again.');
        }
    }
    return (
        <div className={styles.container}>
            <h1 className={styles.appName}>Dear Diary, </h1>
            <div className={styles.card}>
                <h2 style={{marginBottom:'20px',textAlign:'center'}}>Login</h2>
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
                <button className={styles.loginBtn} onClick={handleLogin}>Login</button>
                <p className={styles.registerText}>
                    Don't have an account? 
                    <Link className={styles.registerLink} to="/register">
                        Register here
                    </Link>
                         </p>
            </div>
        </div>
    );
}