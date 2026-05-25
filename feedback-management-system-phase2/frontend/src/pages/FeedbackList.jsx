import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { feedbackApi } from '../api.js';
import StarRating from '../components/StarRating.jsx';
import SearchFilter from '../components/SearchFilter.jsx';

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString();
}

export default function FeedbackList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({});

  const load = async (params = {}) => {
    setLoading(true);
    setError(null);
    try {
      // Use /search if any criterion is set, otherwise /feedback
      const hasCriteria = !!(params.keyword || params.rating || params.program);
      const data = hasCriteria
        ? await feedbackApi.search(params)
        : await feedbackApi.list();
      setItems(data);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          'Could not reach the API. Is the backend running?'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleApply = (params) => {
    setFilters(params);
    load(params);
  };

  const handleReset = () => {
    setFilters({});
    load();
  };

  const remove = async (id) => {
    if (!window.confirm('Delete this feedback? This cannot be undone.')) return;
    try {
      await feedbackApi.remove(id);
      setItems((curr) => curr.filter((f) => f.feedback_id !== id));
    } catch (err) {
      alert(err?.response?.data?.detail || 'Could not delete feedback.');
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1>All Feedback</h1>
          <div className="subtitle">Browse, search, and manage feedback records.</div>
        </div>
        <Link to="/submit" className="btn btn-primary">
          + Submit feedback
        </Link>
      </div>

      <div className="card">
        <SearchFilter initial={filters} onApply={handleApply} onReset={handleReset} />

        {error && <div className="banner banner-error">{error}</div>}

        {loading ? (
          <div className="loading">Loading feedback…</div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            No feedback matched your filters.{' '}
            <Link to="/submit">Submit the first one.</Link>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="feedback-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Participant</th>
                  <th>Program</th>
                  <th>Rating</th>
                  <th>Submitted</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((f) => (
                  <tr key={f.feedback_id}>
                    <td className="muted">#{f.feedback_id}</td>
                    <td>
                      <Link to={`/feedback/${f.feedback_id}`}>
                        {f.participant_name}
                      </Link>
                    </td>
                    <td>{f.program_name}</td>
                    <td>
                      <StarRating value={f.rating} />
                    </td>
                    <td className="muted">{formatDate(f.submitted_at)}</td>
                    <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <Link
                        to={`/feedback/${f.feedback_id}`}
                        className="btn btn-sm"
                      >
                        View
                      </Link>{' '}
                      <button
                        type="button"
                        className="btn btn-sm btn-danger"
                        onClick={() => remove(f.feedback_id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="muted" style={{ marginTop: 12, fontSize: 13 }}>
          {items.length} record{items.length === 1 ? '' : 's'}
        </div>
      </div>
    </>
  );
}
