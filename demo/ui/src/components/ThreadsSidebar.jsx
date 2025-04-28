import React, { useState, useEffect } from 'react';
import './ThreadsSidebar.css';

const API_URL = 'http://localhost:8000';

const ThreadsSidebar = ({ onSelectThread, currentThreadId }) => {
  const [threads, setThreads] = useState([]);
  const [availableTrees, setAvailableTrees] = useState([]);
  const [availableModels, setAvailableModels] = useState([]); // New state for models
  const [selectedModel, setSelectedModel] = useState(''); // New state for selected model
  const [selectedTreeType, setSelectedTreeType] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Fetch threads and available trees
  const fetchThreads = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_URL}/api/threads`);
      
      if (!response.ok) {
        throw new Error(`Error fetching threads: ${response.status}`);
      }
      
      const data = await response.json();
      setThreads(data.threads || []);
      setAvailableTrees(data.available_trees || []);
      setAvailableModels(data.available_models || []); // Set available models
      
      // Set default selected tree type if available
      if (data.available_trees && data.available_trees.length > 0 && !selectedTreeType) {
        setSelectedTreeType(data.available_trees[0]);
      }
      
      // Set default selected model if available
      if (data.available_models && data.available_models.length > 0 && !selectedModel) {
        setSelectedModel(data.available_models[0]);
      }

      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching threads:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Change model function
  const changeModel = async (modelName) => {
    try {
      const response = await fetch(`${API_URL}/api/threads/${currentThreadId}/model`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: modelName })
      });
      
      if (!response.ok) {
        throw new Error(`Error changing model: ${response.status}`);
      }
      
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error changing model:', err);
    }
  };

  // Handle model selection change
  const handleModelChange = (e) => {
    const newModel = e.target.value;
    setSelectedModel(newModel);
    changeModel(newModel); // Call change model API
  };

  // Create a new thread
  const createThread = async () => {
    if (!selectedTreeType) {
      setError('Please select a tree type');
      return;
    }
    
    try {
      setIsLoading(true);
      const response = await fetch(`${API_URL}/api/threads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          tree_type: selectedTreeType,
          model_name: selectedModel // Add model_name to the request body
        })
      });
      
      if (!response.ok) {
        throw new Error(`Error creating thread: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Refresh the threads list
      fetchThreads();
      
      // Select the newly created thread
      if (onSelectThread && data.thread_id) {
        onSelectThread(data.thread_id);
      }
      
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error creating thread:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Delete a thread
  const deleteThread = async (threadId, e) => {
    e.stopPropagation(); // Prevent thread selection
    
    try {
      setIsLoading(true);
      const response = await fetch(`${API_URL}/api/threads/${threadId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`Error deleting thread: ${response.status}`);
      }
      
      // Refresh the threads list
      fetchThreads();
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error deleting thread:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Format timestamp to readable date
  const formatDate = (timestamp) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp * 1000).toLocaleString();
  };

  // Toggle sidebar collapse
  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  // Load threads on component mount
  useEffect(() => {
    fetchThreads();
    // Set up a timer to refresh threads list every 10 seconds
    const refreshTimer = setInterval(fetchThreads, 10000);
    
    return () => clearInterval(refreshTimer);
  }, []);

  return (
    <div className={`threads-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="left-sidebar-toggle" onClick={toggleSidebar}>
        {isCollapsed ? '→' : '←'}
      </div>
      
      {!isCollapsed && (
        <div className="sidebar-content">
          <h2>Behavioral</h2>
          
          {error && <div className="error-message">{error}</div>}

          <div className="create-thread-section">
            <h3>New Conversation</h3>
            <div className="create-thread-form">
              <select 
                value={selectedTreeType} 
                onChange={(e) => setSelectedTreeType(e.target.value)}
                disabled={isLoading || availableTrees.length === 0}
              >
                {availableTrees.length === 0 && <option value="">No trees available</option>}
                {availableTrees.map(tree => (
                  <option key={tree} value={tree}>{tree}</option>
                ))}
              </select>
              
              {/* Model selection for new thread creation */}
              <input 
                type="text"
                value={selectedModel} 
                onChange={(e) => setSelectedModel(e.target.value)} 
                placeholder="Model name" 
                list="model-options"
              />
              <datalist id="model-options"> 
                {availableModels.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </datalist>
              
              <button 
                onClick={createThread} 
                disabled={isLoading || !selectedTreeType}
              >
                {isLoading ? '...' : 'Create'}
              </button>
            </div>
          </div>
          
          <div className="threads-list-section">
            <h3>Active Threads</h3>
            {isLoading && <div className="loading">Loading...</div>}
            
            {!isLoading && threads.length === 0 && (
              <div className="no-threads">No active threads</div>
            )}
            
            <ul className="threads-list">
              {threads.map(thread => (
                <li 
                  key={thread.id} 
                  className={`thread-item ${currentThreadId === thread.id ? 'selected' : ''}`}
                  onClick={() => onSelectThread(thread.id)}
                >
                  <div className="thread-info">
                    <span className="thread-type">{thread.type}</span>
                    <span className="thread-date">{formatDate(thread.last_update || thread.created_at)}</span>
                  </div>
                  <button 
                    className="delete-button" 
                    onClick={(e) => deleteThread(thread.id, e)}
                    title="Delete thread"
                  >
                    ×
                  </button>
                  <select 
                    className="model-selector" 
                    value={thread.model || ''} 
                    onChange={(e) => changeModel(e.target.value)} // Call change model API for the specific thread
                    disabled={isLoading}
                  >
                    {availableModels.length === 0 && <option value="">No models available</option>}
                    {availableModels.map(model => (
                      <option key={model} value={model}>{model}</option>
                    ))}
                  </select>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreadsSidebar; 