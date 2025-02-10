import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./components/LandingPage";
import LearningPathwayPage from "./components/LearningPathwayPage";
import TestHarness from "./components/TestHarness";

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/learning-pathway" element={<LearningPathwayPage />} />
        <Route path="/test" element={<TestHarness />} /> {/* Add this line */}
      </Routes>
    </BrowserRouter>
  );
};

export default App;
