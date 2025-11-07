import { BrowserRouter, Routes, Route } from "react-router-dom";

// Simple Home component
const Home = () => (
  <div className="min-h-screen flex items-center justify-center">
    <h1 className="text-3xl font-bold">Welcome to the App</h1>
  </div>
);

// Simple About component
const About = () => (
  <div className="min-h-screen flex items-center justify-center">
    <h1 className="text-3xl font-bold">About Page</h1>
  </div>
);

const AppContent = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="*" element={<div>Page not found</div>} />
      </Routes>
    </BrowserRouter>
  );
};

const App = () => {
  return <AppContent />;
};

export default App;
