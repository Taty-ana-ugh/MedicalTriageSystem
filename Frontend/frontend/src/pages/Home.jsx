import React from 'react'
import Navbar from '../components/Navbar'
import TriageForm from '../components/TriageForm';

const Home = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar/>
     <div className="container mx-auto px-4 py-8"></div>
      <TriageForm/>
      </div>
   
  );
};


   
export default Home
