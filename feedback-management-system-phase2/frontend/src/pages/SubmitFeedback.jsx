import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { feedbackApi } from '../api.js';
import { RatingInput } from '../components/StarRating.jsx';

const EMPTY = {
  participant_name: '',
  program_name: '',
  rating: 0,
  comments: '',
};

export default function SubmitFeedback() {
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState(null);

  const update = (field) => (event) =>
    setForm((f) => ({ ...f, [field]: event.target.value }));

  const validate = () => {
    const next = {};
    if (!form.participant_name.trim()) next.participant_name = 'Name is required';
    if (!form.program_name.trim()) next.program_name = 'Program is required';
    if (!form.rating || form.rating < 1 || form.rating > 5)
      next.rating = 'Select a rating from 1 to 5';
    if (form.comments && form.comments.length > 2000)
      next.comments = 'Comments must be 2000 characters or less';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (e) => {
    e.preventDefault();
    setServerError(null);
    if (!validate()) return;
    setSubmitting(true);
    try {
      const created = await feedbackApi.create({
        participant_name: form.participant_name.trim(),
        program_name: form.program_name.trim(),
        rating: Number(form.rating),
        comments: form.comments.trim(),
      });
      navigate(`/feedback/${created.feedback_id}`, {
        state: { flash: 'Feedback submitted — thanks!' },
      });
    } catch (err) {
      setServerError(
        err?.response?.data?.detail || 'Could not submit feedback. Try again.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Submit Feedback</h1>
          <div className="subtitle">Tell us how the program went.</div>
        </div>
      </div>

      {serverError && <div className="banner banner-error">{serverError}</div>}

      <div className="card">
        <form className="form-grid" onSubmit={submit} noValidate>
          <div className="form-row">
            <div className="form-field">
              <label htmlFor="participant_name">Participant name *</label>
              <input
                id="participant_name"
                type="text"
                value={form.participant_name}
                onChange={update('participant_name')}
                maxLength={150}
                placeholder="e.g. Priya Iyer"
                required
              />
              {errors.participant_name && (
                <div className="form-error">{errors.participant_name}</div>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="program_name">Training / Event / Product *</label>
              <input
                id="program_name"
                type="text"
                value={form.program_name}
                onChange={update('program_name')}
                maxLength={200}
                placeholder="e.g. React Crash Course"
                required
              />
              {errors.program_name && (
                <div className="form-error">{errors.program_name}</div>
              )}
            </div>
          </div>

          <div className="form-field">
            <label>Rating *</label>
            <RatingInput
              value={form.rating}
              onChange={(v) => setForm((f) => ({ ...f, rating: v }))}
            />
            <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
              1 = Poor · 2 = Fair · 3 = Good · 4 = Very Good · 5 = Excellent
            </div>
            {errors.rating && <div className="form-error">{errors.rating}</div>}
          </div>

          <div className="form-field">
            <label htmlFor="comments">Comments</label>
            <textarea
              id="comments"
              value={form.comments}
              onChange={update('comments')}
              maxLength={2000}
              placeholder="What stood out? What could be better?"
            />
            <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
              {form.comments.length} / 2000
            </div>
            {errors.comments && <div className="form-error">{errors.comments}</div>}
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn"
              onClick={() => {
                setForm(EMPTY);
                setErrors({});
              }}
              disabled={submitting}
            >
              Clear
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit feedback'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
