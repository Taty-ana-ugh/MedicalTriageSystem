import React from 'react'
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Navbar from './components/Navbar';
import QueueDashboard from './components/QueueDashboard';
import DepartmentRegistry from './components/DepartmentRegistry';

const App = () => {
  return (
    <div>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<QueueDashboard />} />
        <Route path="/departments" element={<DepartmentRegistry />} />
      </Routes>
    </div>
  )
}

export default App
