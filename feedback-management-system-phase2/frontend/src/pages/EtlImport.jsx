import { useEffect, useRef, useState } from 'react';
import { etlApi } from '../api.js';

const fmtDate = (iso) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
};

const ACCEPT = '.csv,.tsv,.txt,.xlsx,.xls,.xlsm';

export default function EtlImport() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [running, setRunning] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [error, setError] = useState('');
  const [runs, setRuns] = useState([]);

  const loadRuns = async () => {
    try {
      const list = await etlApi.runs(20);
      setRuns(list);
    } catch (err) {
      // Non-fatal — leave the table empty
      console.error(err);
    }
  };

  useEffect(() => { loadRuns(); }, []);

  const onFileChosen = (f) => {
    setFile(f || null);
    setError('');
    setLastResult(null);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer?.files?.[0];
    if (f) onFileChosen(f);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please choose a CSV or Excel file first.');
      return;
    }
    setRunning(true);
    setError('');
    setLastResult(null);
    try {
      const result = await etlApi.run(file);
      setLastResult(result);
      await loadRuns();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (detail && typeof detail === 'object') {
        setLastResult(detail);
        setError(detail.error_message || 'ETL pipeline reported a failure.');
      } else {
        setError(detail || err.message || 'ETL run failed');
      }
      await loadRuns();
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className="stack">
      <header className="page-header">
        <div>
          <h1>ETL Import</h1>
          <p className="muted">
            Upload a CSV or Excel file containing feedback. The pipeline cleans,
            de-duplicates and loads the data, then refreshes the analytics tables.
          </p>
        </div>
      </header>

      <form
        className={'drop-zone' + (dragging ? ' dragging' : '')}
        onSubmit={onSubmit}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <p className="drop-zone-title">Drop a CSV / Excel file here</p>
        <p className="muted">or</p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          style={{ display: 'none' }}
          onChange={(e) => onFileChosen(e.target.files?.[0])}
        />
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn"
            onClick={() => inputRef.current?.click()}
          >
            Choose file
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!file || running}
          >
            {running ? 'Running ETL…' : 'Run ETL pipeline'}
          </button>
        </div>
        {file && (
          <p style={{ marginTop: 12 }}>
            Selected: <strong>{file.name}</strong>{' '}
            <span className="muted">({Math.ceil(file.size / 1024)} KB)</span>
          </p>
        )}
        <p className="muted" style={{ marginTop: 12, fontSize: 13 }}>
          Expected columns: <code>participant_name, program_name, rating (1–5), comments, submitted_date</code>
        </p>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      {lastResult && (
        <div className={'alert ' + (lastResult.status === 'success' ? 'alert-success' : 'alert-error')}>
          <h3 style={{ marginTop: 0 }}>
            ETL run #{lastResult.run_id} — {lastResult.status.toUpperCase()}
          </h3>
          <ul style={{ margin: '6px 0 0 18px' }}>
            <li>Source file: <strong>{lastResult.source_file}</strong></li>
            <li>Rows extracted: <strong>{lastResult.rows_extracted}</strong></li>
            <li>Rows invalid (dropped): <strong>{lastResult.rows_invalid}</strong></li>
            <li>Rows duplicates (removed): <strong>{lastResult.rows_duplicates}</strong></li>
            <li>Rows loaded: <strong>{lastResult.rows_loaded}</strong></li>
            {lastResult.issues?.length > 0 && (
              <li>
                Issues:
                <ul>
                  {lastResult.issues.map((i, idx) => <li key={idx}>{i}</li>)}
                </ul>
              </li>
            )}
          </ul>
        </div>
      )}

      <div className="card">
        <h3>Recent ETL runs</h3>
        {runs.length === 0 ? (
          <p className="muted">No ETL runs yet.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>File</th>
                  <th>Started</th>
                  <th>Status</th>
                  <th>Extract</th>
                  <th>Invalid</th>
                  <th>Dupes</th>
                  <th>Loaded</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.run_id}>
                    <td>{r.run_id}</td>
                    <td>{r.source_file}</td>
                    <td>{fmtDate(r.started_at)}</td>
                    <td>
                      <span className={'status status-' + r.status}>{r.status}</span>
                    </td>
                    <td>{r.rows_extracted}</td>
                    <td>{r.rows_invalid}</td>
                    <td>{r.rows_duplicates}</td>
                    <td>{r.rows_loaded}</td>
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
