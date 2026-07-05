import React from 'react'
import TriageForm from '../components/TriageForm';
import QueueDashboard from '../components/QueueDashboard';

const Home = () => {
  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <TriageForm />
      <QueueDashboard />
    </div>
  );
};

export default Home
