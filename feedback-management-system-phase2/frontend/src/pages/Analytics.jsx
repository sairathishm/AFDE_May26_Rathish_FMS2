import { useEffect, useState } from 'react';
import { analyticsApi } from '../api.js';

const fmtDate = (iso) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
};

export default function Analytics() {
  const [overview, setOverview] = useState(null);
  const [programs, setPrograms] = useState([]);
  const [ratings, setRatings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [ov, progs, rts] = await Promise.all([
        analyticsApi.overview(),
        analyticsApi.programs(),
        analyticsApi.ratings(),
      ]);
      setOverview(ov);
      setPrograms(progs);
      setRatings(rts);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await analyticsApi.refresh();
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Refresh failed');
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) return <p>Loading analytics…</p>;

  const maxRatingCount = Math.max(1, ...ratings.map((r) => r.count));
  const maxProgramCount = Math.max(1, ...programs.map((p) => p.total_feedback));

  return (
    <section className="stack">
      <header className="page-header">
        <div>
          <h1>Analytics Dashboard</h1>
          <p className="muted">
            Live numbers from the analytics tables — refreshed after every ETL run.
            {overview?.last_etl_run_at && (
              <> Last ETL run: <strong>{fmtDate(overview.last_etl_run_at)}</strong>.</>
            )}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className="btn"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing…' : 'Refresh analytics'}
          </button>
          <a className="btn" href={analyticsApi.downloads.cleanedCsv}>Download cleaned CSV</a>
          <a className="btn btn-primary" href={analyticsApi.downloads.programsCsv}>Download programs CSV</a>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Headline stats */}
      {overview && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total feedback</div>
            <div className="stat-value">{overview.total_feedback}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Programs</div>
            <div className="stat-value">{overview.total_programs}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Average rating</div>
            <div className="stat-value">★ {overview.average_rating.toFixed(2)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Positive / Neutral / Negative</div>
            <div className="stat-value" style={{ fontSize: 20 }}>
              <span style={{ color: 'var(--color-success)' }}>{overview.positive_pct}%</span>
              {' / '}
              <span style={{ color: 'var(--color-warning)' }}>{overview.neutral_pct}%</span>
              {' / '}
              <span style={{ color: 'var(--color-danger)' }}>{overview.negative_pct}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Top / bottom program */}
      {overview && (overview.top_program || overview.bottom_program) && (
        <div className="card-grid">
          <div className="card">
            <h3>Top program</h3>
            {overview.top_program ? (
              <p style={{ marginBottom: 0 }}>
                <strong>{overview.top_program}</strong> · ★ {overview.top_program_rating?.toFixed(2)}
              </p>
            ) : (
              <p className="muted" style={{ marginBottom: 0 }}>No data yet.</p>
            )}
          </div>
          <div className="card">
            <h3>Needs attention</h3>
            {overview.bottom_program ? (
              <p style={{ marginBottom: 0 }}>
                <strong>{overview.bottom_program}</strong> · ★ {overview.bottom_program_rating?.toFixed(2)}
              </p>
            ) : (
              <p className="muted" style={{ marginBottom: 0 }}>No data yet.</p>
            )}
          </div>
        </div>
      )}

      {/* Rating distribution bar chart (CSS-only) */}
      <div className="card">
        <h3>Rating distribution</h3>
        <div className="bar-chart">
          {ratings.map((r) => (
            <div className="bar-row" key={r.rating}>
              <div className="bar-label">
                {'★'.repeat(r.rating)}
                <span className="muted" style={{ marginLeft: 6 }}>
                  ({r.rating})
                </span>
              </div>
              <div className="bar-track">
                <div
                  className={`bar-fill rating-${r.rating}`}
                  style={{ width: `${(r.count / maxRatingCount) * 100}%` }}
                />
              </div>
              <div className="bar-meta">
                {r.count} · {r.percent_of_total}%
              </div>
            </div>
          ))}
          {ratings.length === 0 && <p className="muted">No ratings yet.</p>}
        </div>
      </div>

      {/* Per-program table */}
      <div className="card">
        <h3>Per-program summary</h3>
        {programs.length === 0 ? (
          <p className="muted">No programs yet. Trigger an ETL run to import data.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Program</th>
                  <th>Total</th>
                  <th>Avg</th>
                  <th>Positive</th>
                  <th>Neutral</th>
                  <th>Negative</th>
                  <th>Share</th>
                </tr>
              </thead>
              <tbody>
                {programs.map((p) => (
                  <tr key={p.program_name}>
                    <td>{p.program_name}</td>
                    <td>{p.total_feedback}</td>
                    <td>★ {p.average_rating.toFixed(2)}</td>
                    <td style={{ color: 'var(--color-success)' }}>{p.positive_count}</td>
                    <td style={{ color: 'var(--color-warning)' }}>{p.neutral_count}</td>
                    <td style={{ color: 'var(--color-danger)' }}>{p.negative_count}</td>
                    <td>
                      <div className="bar-track" style={{ minWidth: 100 }}>
                        <div
                          className="bar-fill rating-4"
                          style={{ width: `${(p.total_feedback / maxProgramCount) * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
