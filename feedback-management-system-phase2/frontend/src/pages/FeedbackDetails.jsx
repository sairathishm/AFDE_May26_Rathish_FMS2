import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { feedbackApi } from '../api.js';
import { RatingInput, RatingPill } from '../components/StarRating.jsx';

function formatDateTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString();
}

export default function FeedbackDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const flash = location.state?.flash;

  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(flash || null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await feedbackApi.get(id);
        if (!cancelled) {
          setFeedback(data);
          setForm({
            participant_name: data.participant_name,
            program_name: data.program_name,
            rating: data.rating,
            comments: data.comments || '',
          });
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err?.response?.status === 404
              ? `Feedback #${id} was not found.`
              : err?.response?.data?.detail || 'Could not load feedback.'
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
  }, [id]);

  const startEdit = () => {
    setEditing(true);
    setSaveError(null);
    setSuccessMessage(null);
  };

  const cancelEdit = () => {
    setEditing(false);
    setSaveError(null);
    setForm({
      participant_name: feedback.participant_name,
      program_name: feedback.program_name,
      rating: feedback.rating,
      comments: feedback.comments || '',
    });
  };

  const save = async (e) => {
    e.preventDefault();
    setSaveError(null);
    if (!form.participant_name.trim() || !form.program_name.trim()) {
      setSaveError('Name and program are required.');
      return;
    }
    if (!form.rating || form.rating < 1 || form.rating > 5) {
      setSaveError('Rating must be between 1 and 5.');
      return;
    }
    setSaving(true);
    try {
      const updated = await feedbackApi.update(id, {
        participant_name: form.participant_name.trim(),
        program_name: form.program_name.trim(),
        rating: Number(form.rating),
        comments: form.comments.trim(),
      });
      setFeedback(updated);
      setEditing(false);
      setSuccessMessage('Feedback updated.');
    } catch (err) {
      setSaveError(err?.response?.data?.detail || 'Could not update feedback.');
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!window.confirm('Delete this feedback? This cannot be undone.')) return;
    try {
      await feedbackApi.remove(id);
      navigate('/feedback', { state: { flash: `Feedback #${id} deleted.` } });
    } catch (err) {
      alert(err?.response?.data?.detail || 'Could not delete feedback.');
    }
  };

  if (loading) return <div className="loading">Loading feedback…</div>;
  if (error)
    return (
      <>
        <div className="banner banner-error">{error}</div>
        <Link to="/feedback" className="btn">
          ← Back to list
        </Link>
      </>
    );
  if (!feedback) return null;

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Feedback #{feedback.feedback_id}</h1>
          <div className="subtitle">Submitted by {feedback.participant_name}</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link to="/feedback" className="btn">
            ← Back
          </Link>
          {!editing && (
            <>
              <button className="btn" onClick={startEdit}>
                Edit
              </button>
              <button className="btn btn-danger" onClick={remove}>
                Delete
              </button>
            </>
          )}
        </div>
      </div>

      {successMessage && <div className="banner banner-success">{successMessage}</div>}
      {saveError && <div className="banner banner-error">{saveError}</div>}

      <div className="card">
        {!editing ? (
          <div className="detail-grid">
            <div className="detail-label">Participant</div>
            <div className="detail-value">{feedback.participant_name}</div>

            <div className="detail-label">Program / Event</div>
            <div className="detail-value">{feedback.program_name}</div>

            <div className="detail-label">Rating</div>
            <div className="detail-value">
              <RatingPill rating={feedback.rating} />
            </div>

            <div className="detail-label">Submitted at</div>
            <div className="detail-value muted">{formatDateTime(feedback.submitted_at)}</div>

            <div className="detail-label">Comments</div>
            <div className="detail-value" style={{ whiteSpace: 'pre-wrap' }}>
              {feedback.comments || <span className="muted">No comments provided.</span>}
            </div>
          </div>
        ) : (
          <form className="form-grid" onSubmit={save}>
            <div className="form-row">
              <div className="form-field">
                <label htmlFor="edit-name">Participant name *</label>
                <input
                  id="edit-name"
                  type="text"
                  value={form.participant_name}
                  onChange={(e) =>
                    setForm({ ...form, participant_name: e.target.value })
                  }
                  maxLength={150}
                />
              </div>
              <div className="form-field">
                <label htmlFor="edit-program">Program / Event *</label>
                <input
                  id="edit-program"
                  type="text"
                  value={form.program_name}
                  onChange={(e) => setForm({ ...form, program_name: e.target.value })}
                  maxLength={200}
                />
              </div>
            </div>
            <div className="form-field">
              <label>Rating *</label>
              <RatingInput
                value={form.rating}
                onChange={(v) => setForm({ ...form, rating: v })}
              />
            </div>
            <div className="form-field">
              <label htmlFor="edit-comments">Comments</label>
              <textarea
                id="edit-comments"
                value={form.comments}
                onChange={(e) => setForm({ ...form, comments: e.target.value })}
                maxLength={2000}
              />
            </div>
            <div className="form-actions">
              <button type="button" className="btn" onClick={cancelEdit} disabled={saving}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Saving…' : 'Save changes'}
              </button>
            </div>
          </form>
        )}
      </div>
    </>
  );
}
