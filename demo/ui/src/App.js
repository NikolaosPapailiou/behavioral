import React, { useState, useEffect } from 'react';
import ChatUI from './components/ChatUI';
import ThreadsSidebar from './components/ThreadsSidebar';
import './App.css';

function App() {
  const [currentThreadId, setCurrentThreadId] = useState(null);

  // Select a thread to view
  const handleSelectThread = (threadId) => {
    setCurrentThreadId(threadId);
  };

  // Try to get a default thread on initial load
  useEffect(() => {
    const fetchDefaultThread = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/threads');
        if (response.ok) {
          const data = await response.json();
          // If there are threads, select the first one
          if (data.threads && data.threads.length > 0) {
            setCurrentThreadId(data.threads[0].id);
          }
        }
      } catch (error) {
        console.error('Error fetching default thread:', error);
      }
    };

    if (!currentThreadId) {
      fetchDefaultThread();
    }
  }, [currentThreadId]);

  return (
    <div className="app-container">
      <ThreadsSidebar 
        onSelectThread={handleSelectThread} 
        currentThreadId={currentThreadId}
      />
      
      {currentThreadId ? (
        <ChatUI 
          threadId={currentThreadId} 
          onBack={() => setCurrentThreadId(null)} 
        />
      ) : (
        <div className="no-thread-selected">
          <div className="welcome-message">
            <h2>Welcome to the Behavioral Trees Demo</h2>
            <p>Please select a thread from the sidebar to get started.</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App; 