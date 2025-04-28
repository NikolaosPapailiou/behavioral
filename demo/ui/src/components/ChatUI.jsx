import React, { useState, useEffect, useRef } from 'react';
import ChatWindow from './ChatWindow';
import MessageInput from './MessageInput';
import DebugPanel from './DebugPanel';
import './ChatUI.css';

const API_URL = 'http://localhost:8000';
const POLLING_INTERVAL = 1000; // Poll every second

const ChatUI = ({ threadId, onBack }) => {
  const [messages, setMessages] = useState([]);
  const [blackboardState, setBlackboardState] = useState({});
  const [treeDescription, setTreeDescription] = useState('');
  const [treeStructure, setTreeStructure] = useState({});
  const [isConnected, setIsConnected] = useState(true); // Assume connected by default
  const [lastUpdateTime, setLastUpdateTime] = useState(0);
  const [treeType, setTreeType] = useState('');
  
  // Use a ref for the polling interval to avoid unnecessary re-renders
  const pollingIntervalRef = useRef(null);
  
  // Function to send a message
  const sendMessage = async (content) => {
    try {
      console.log('Sending message:', content, 'to thread:', threadId);
      setIsConnected(true); // Assume successful connection
      
      const response = await fetch(`${API_URL}/api/send-message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, thread_id: threadId })
      });
      
      if (!response.ok) {
        console.error('Error sending message, status:', response.status);
        setIsConnected(false);
        return;
      }
      
      const data = await response.json();
      console.log('Message sent response:', data);
      
      // Fetch updated state immediately after sending a message
      fetchFullState();
    } catch (error) {
      console.error('Error sending message:', error);
      setIsConnected(false);
    }
  };

  // Function to fetch the complete state
  const fetchFullState = async () => {
    try {
      const response = await fetch(`${API_URL}/api/state?thread_id=${threadId}`);
      
      if (!response.ok) {
        console.error('Error fetching state, status:', response.status);
        setIsConnected(false);
        return;
      }
      
      const stateData = await response.json();
      console.log('Received full state update for thread:', threadId);
      
      // Update all state components
      setMessages(stateData.chat_history || []);
      setBlackboardState(stateData.blackboard || {});
      setTreeDescription(stateData.description || '');
      setTreeStructure({ html: stateData.tree_html || '' });
      setLastUpdateTime(stateData.last_update || 0);
      
      // Fetch thread type if available
      if (stateData.thread_id) {
        fetchThreadInfo();
      }
      
      setIsConnected(true);
    } catch (error) {
      console.error('Error fetching state:', error);
      setIsConnected(false);
    }
  };

  // Fetch thread info to get the tree type
  const fetchThreadInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/api/threads`);
      
      if (!response.ok) {
        console.error('Error fetching threads, status:', response.status);
        return;
      }
      
      const data = await response.json();
      const thread = data.threads.find(t => t.id === threadId);
      
      if (thread) {
        setTreeType(thread.type);
      }
    } catch (error) {
      console.error('Error fetching thread info:', error);
    }
  };

  // Function to check if there are updates
  const checkForUpdates = async () => {
    try {
      const response = await fetch(`${API_URL}/api/last-update-time?thread_id=${threadId}`);
      
      if (!response.ok) {
        console.error('Error checking for updates, status:', response.status);
        setIsConnected(false);
        return;
      }
      
      const data = await response.json();
      
      // If the server has newer data, fetch the full state
      if (data.last_update > lastUpdateTime) {
        console.log('Update detected, fetching new state');
        fetchFullState();
      }
      
      setIsConnected(true);
    } catch (error) {
      console.error('Error checking for updates:', error);
      setIsConnected(false);
    }
  };

  // Set up polling on component mount or when threadId changes
  useEffect(() => {
    console.log('Setting up polling for thread:', threadId);
    
    // Clear previous interval if it exists
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    // Reset state for new thread
    setMessages([]);
    setBlackboardState({});
    setTreeDescription('')
    setTreeStructure({});
    setLastUpdateTime(0);
    
    // Fetch initial state
    fetchFullState();
    
    // Set up polling interval
    pollingIntervalRef.current = setInterval(checkForUpdates, POLLING_INTERVAL);
    
    // Clean up interval on unmount or when threadId changes
    return () => {
      console.log('Cleaning up polling interval');
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [threadId]);

  return (
    <div className="chat-ui-container">
      <div className="chat-area">
        <ChatWindow messages={messages} />
        <MessageInput onSendMessage={sendMessage} />
      </div>
      <DebugPanel 
        blackboardState={blackboardState} 
        treeStructure={treeStructure} 
        treeDescription={treeDescription}
      />
      {!isConnected && <div className="connection-warning">Disconnected from server</div>}
    </div>
  );
};

export default ChatUI; 