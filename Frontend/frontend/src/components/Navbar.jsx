import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    
    <nav className="bg-blue-600 text-white shadow-md">
      {/* This div keeps everything centered and spaced out nicely */}
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        
        {/* Left side: Logo or App Name */}
        <div className="text-xl font-bold tracking-wide">
          Medicare
        </div>
        
        {/* Right side: Navigation Links */}
        <ul className="flex space-x-6">
          <li className="hover:text-blue-200 cursor-pointer transition-colors">
            <Link to="/">Home</Link>
          </li>
          <li className="hover:text-blue-200 cursor-pointer transition-colors">
            <Link to="/dashboard">Dashboard</Link>
          </li>
          <li className="hover:text-blue-200 cursor-pointer transition-colors">
            <Link to="/departments">Department Registry</Link>
          </li>
        </ul>

      </div>
    </nav>
  );
}

export default Navbar
