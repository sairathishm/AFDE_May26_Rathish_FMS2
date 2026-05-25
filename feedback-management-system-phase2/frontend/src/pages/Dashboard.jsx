import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { feedbackApi } from '../api.js';
import StarRating from '../components/StarRating.jsx';

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [s, list] = await Promise.all([
          feedbackApi.stats(),
          feedbackApi.list({ limit: 5 }),
        ]);
        if (!cancelled) {
          setStats(s);
          setRecent(list);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err?.response?.data?.detail ||
              'Could not reach the API. Is the backend running on port 8000?'
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <div className="loading">Loading dashboard…</div>;
  if (error) return <div className="banner banner-error">{error}</div>;

  const total = stats?.total_feedback || 0;
  const dist = stats?.rating_distribution || {};

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <div className="subtitle">An overview of all feedback collected.</div>
        </div>
        <Link to="/submit" className="btn btn-primary">
          + Submit feedback
        </Link>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total feedback</div>
          <div className="stat-value">{total}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Average rating</div>
          <div className="stat-value">
            {stats?.average_rating?.toFixed?.(2) ?? '0.00'}
          </div>
          <StarRating value={stats?.average_rating || 0} />
        </div>
        <div className="stat-card">
          <div className="stat-label">5-star count</div>
          <div className="stat-value">{dist[5] || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Low ratings (1–2)</div>
          <div className="stat-value">{(dist[1] || 0) + (dist[2] || 0)}</div>
        </div>
      </div>

      <div className="card">
        <h3>Rating distribution</h3>
        <div className="distribution">
          {[5, 4, 3, 2, 1].map((r) => {
            const count = dist[r] || 0;
            const pct = total ? Math.round((count / total) * 100) : 0;
            return (
              <div className="distribution-row" key={r}>
                <div>{r} ★</div>
                <div className="distribution-bar">
                  <div style={{ width: `${pct}%` }} />
                </div>
                <div className="muted">{count}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card">
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 12,
          }}
        >
          <h3 style={{ margin: 0 }}>Recent feedback</h3>
          <Link to="/feedback">View all →</Link>
        </div>
        {recent.length === 0 ? (
          <div className="empty-state">No feedback yet. Submit the first one!</div>
        ) : (
          <table className="feedback-table">
            <thead>
              <tr>
                <th>Participant</th>
                <th>Program</th>
                <th>Rating</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((f) => (
                <tr key={f.feedback_id}>
                  <td>
                    <Link to={`/feedback/${f.feedback_id}`}>{f.participant_name}</Link>
                  </td>
                  <td>{f.program_name}</td>
                  <td>
                    <StarRating value={f.rating} />
                  </td>
                  <td className="muted">{formatDate(f.submitted_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
