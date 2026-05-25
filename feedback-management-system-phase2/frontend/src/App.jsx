import { Navigate, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import Dashboard from './pages/Dashboard.jsx';
import FeedbackList from './pages/FeedbackList.jsx';
import FeedbackDetails from './pages/FeedbackDetails.jsx';
import SubmitFeedback from './pages/SubmitFeedback.jsx';
import Analytics from './pages/Analytics.jsx';
import EtlImport from './pages/EtlImport.jsx';

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="container">
        <Routes>
          {/* Phase 1 */}
          <Route path="/" element={<Dashboard />} />
          <Route path="/feedback" element={<FeedbackList />} />
          <Route path="/feedback/:id" element={<FeedbackDetails />} />
          <Route path="/submit" element={<SubmitFeedback />} />
          {/* Phase 2 */}
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/etl" element={<EtlImport />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
