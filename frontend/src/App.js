import {BrowserRouter as Router, Route, Routes, Navigate} from 'react-router-dom';
import Login from './pages/login/login';
import Register from './pages/register/register';
import Dashboard from './pages/journal/journal';
import { useState } from 'react';

function App(){
  const [userId, setUserId] = useState(() => {
    const storedUserId = localStorage.getItem('userId');
    return storedUserId ? Number(storedUserId) : null;
  });
  return(
    <Router>
      <Routes>
        <Route path ="/" element={<Login setUserId={setUserId} />} />
        <Route path ="/login" element={<Navigate to="/" replace />} />
        <Route path ="/register" element={<Register />} />
        <Route path ="/dashboard" element={userId ? <Dashboard userId={userId} /> : <Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;