import React, { useState, ReactElement } from 'react';
import './App.css';

// Add type for the component
const App: React.FC = (): ReactElement => {
  const [count, setCount] = useState<number>(0);

  return (
    <div className="app">
      <h1>Property Scraper</h1>
      <div className="card">
        <button onClick={() => setCount((prevCount: number) => prevCount + 1)}>
          Count is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </div>
  );
}

export default App;
