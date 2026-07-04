import React from 'react'

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
          <li className="hover:text-blue-200 cursor-pointer transition-colors">Home</li>
          <li className="hover:text-blue-200 cursor-pointer transition-colors">Dashboard</li>
          <li className="hover:text-blue-200 cursor-pointer transition-colors">Login</li>
        </ul>

      </div>
    </nav>
  );
}

export default Navbar
