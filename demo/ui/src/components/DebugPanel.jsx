import React, { useState, useEffect, useRef } from 'react';
import './DebugPanel.css';

// Collapsible JSON component
const CollapsibleJSON = ({ data }) => {
  // Function to determine if a string is large enough to be collapsible
  const isLargeString = (str) => {
    return typeof str === 'string' && str.length > 100;
  };
  
  // Function to determine initial expanded state for a path
  const getInitialExpandedState = (obj, parentPath = '') => {
    let result = {};
    
    // Root and first level objects/arrays are expanded by default
    result[parentPath] = true;
    
    const processValue = (value, path) => {
      // Get nesting level from path
      const nestingLevel = path.split('.').filter(Boolean).length;
      
      // Large strings are collapsed by default
      if (isLargeString(value)) {
        result[path] = false;
      }
      // Anything beyond 2nd level is collapsed by default
      else if (nestingLevel > 1) {
        result[path] = false;
      }
      // First and second levels are expanded by default
      else {
        result[path] = true;
      }
      
      // Recursively process children
      if (Array.isArray(value)) {
        value.forEach((item, index) => {
          if (typeof item === 'object' && item !== null) {
            processValue(item, `${path}.${index}`);
          }
        });
      } else if (typeof value === 'object' && value !== null) {
        Object.keys(value).forEach(key => {
          if (typeof value[key] === 'object' && value[key] !== null) {
            processValue(value[key], `${path}.${key}`);
          }
        });
      }
    };
    
    if (obj !== null && typeof obj === 'object') {
      processValue(obj, parentPath);
    }
    
    return result;
  };
  
  // Initialize expanded items state with defaults
  const [expandedItems, setExpandedItems] = useState(() => getInitialExpandedState(data, 'root'));
  
  // Use ref to track user's explicit selections
  const userSelectionsRef = useRef({});
  
  // Update expanded items when data changes - but preserve user selections
  useEffect(() => {
    // Get default states for new data
    const newExpandedState = getInitialExpandedState(data, 'root');
    
    // Merge with user selections to preserve their choices
    setExpandedItems({
      ...newExpandedState,
      ...userSelectionsRef.current
    });
  }, [data]); // Only depend on data changes
  
  const toggleExpand = (path) => {
    const newValue = !expandedItems[path];
    
    // Store user selection in ref to preserve across data changes
    userSelectionsRef.current[path] = newValue;
    
    // Update expanded items for UI
    setExpandedItems(prev => ({
      ...prev,
      [path]: newValue
    }));
  };
  
  const renderValue = (value, path = '') => {
    if (value === null) return <span className="json-null">null</span>;
    if (typeof value === 'boolean') return <span className="json-boolean">{value.toString()}</span>;
    if (typeof value === 'number') return <span className="json-number">{value}</span>;
    
    // Handle large strings (collapsible)
    if (isLargeString(value)) {
      const isExpanded = expandedItems[path] === true;
      const displayValue = isExpanded ? value : value.substring(0, 80) + '...';
      
      return (
        <div className="json-string-container">
          <span 
            className={`json-toggle ${isExpanded ? 'expanded' : 'collapsed'}`}
            onClick={() => toggleExpand(path)}
          >
            {isExpanded ? '▼' : '►'} String[{value.length}]
          </span>
          <span className="json-string">"{displayValue}"</span>
        </div>
      );
    }
    
    // Handle regular strings
    if (typeof value === 'string') return <span className="json-string">"{value}"</span>;
    
    if (Array.isArray(value)) {
      const isExpanded = expandedItems[path] === true;
      
      return (
        <div className="json-array">
          <span 
            className={`json-toggle ${isExpanded ? 'expanded' : 'collapsed'}`}
            onClick={() => toggleExpand(path)}
          >
            {isExpanded ? '▼' : '►'} Array[{value.length}]
          </span>
          {isExpanded && (
            <div className="json-children">
              {value.map((item, index) => (
                <div key={index} className="json-property">
                  <span className="json-key">{index}: </span>
                  {renderValue(item, `${path}.${index}`)}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }
    
    if (typeof value === 'object') {
      const isExpanded = expandedItems[path] === true;
      const keys = Object.keys(value);
      
      return (
        <div className="json-object">
          <span 
            className={`json-toggle ${isExpanded ? 'expanded' : 'collapsed'}`}
            onClick={() => toggleExpand(path)}
          >
            {isExpanded ? '▼' : '►'} Object{keys.length > 0 ? `{${keys.length}}` : ''}
          </span>
          {isExpanded && (
            <div className="json-children">
              {keys.map(key => (
                <div key={key} className="json-property">
                  <span className="json-key">{key}: </span>
                  {renderValue(value[key], `${path}.${key}`)}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }
    
    return <span>{String(value)}</span>;
  };
  
  return (
    <div className="collapsible-json">
      {renderValue(data, 'root')}
    </div>
  );
};

const DebugPanel = ({ blackboardState, treeStructure, treeDescription }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [parsedBlackboard, setParsedBlackboard] = useState(null);

  // Parse the blackboard state
  useEffect(() => {
    try {
      let parsedState = null;
      
      if (typeof blackboardState === 'string') {
        // Try to parse as JSON
        try {
          parsedState = JSON.parse(blackboardState);
        } catch {
          // If it can't be parsed as JSON, set as is
          parsedState = blackboardState;
        }
      } else {
        // If it's already an object, use it directly
        parsedState = blackboardState;
      }
      
      setParsedBlackboard(parsedState);
    } catch (error) {
      console.error('Error parsing blackboard state:', error);
      setParsedBlackboard(blackboardState);
    }
  }, [blackboardState]);

  // Toggle sidebar collapse
  const toggleSidebar = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className={`debug-panel ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <div className="debug-panel-header">
        <h3>Debug Panel</h3>
        <div className="right-sidebar-toggle" onClick={toggleSidebar}>
          {isExpanded ? '→' : '←'}
        </div>
      </div>
      
      {isExpanded && (
        <div className="debug-content-container">
        <div className="debug-section behavior-tree-description-section">
          <div className="debug-content">
              <p>{treeDescription}</p>
          </div>
        </div>

          <div className="debug-section tree-section">
            <h4>Behavior Tree</h4>
            <div className="debug-content">
              <div dangerouslySetInnerHTML={{ __html: treeStructure.html }} />
            </div>
          </div>
          <div className="debug-section blackboard-section">
            <h4>State</h4>
            <div className="debug-content">
              {parsedBlackboard !== null ? (
                <CollapsibleJSON data={parsedBlackboard} />
              ) : (
                <pre>No data available</pre>
              )}
            </div>
          </div>
          
        </div>
      )}
    </div>
  );
};

export default DebugPanel; 