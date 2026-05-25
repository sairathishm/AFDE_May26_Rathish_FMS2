import { useState } from 'react';

export default function SearchFilter({ initial = {}, onApply, onReset }) {
  const [keyword, setKeyword] = useState(initial.keyword || '');
  const [rating, setRating] = useState(initial.rating || '');
  const [program, setProgram] = useState(initial.program || '');

  const submit = (e) => {
    e.preventDefault();
    onApply({
      keyword: keyword.trim() || undefined,
      rating: rating ? Number(rating) : undefined,
      program: program.trim() || undefined,
    });
  };

  const reset = () => {
    setKeyword('');
    setRating('');
    setProgram('');
    onReset?.();
  };

  return (
    <form className="filter-row" onSubmit={submit}>
      <div className="form-field">
        <label htmlFor="keyword">Keyword search</label>
        <input
          id="keyword"
          type="text"
          placeholder="Search name, program, or comments…"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
        />
      </div>
      <div className="form-field">
        <label htmlFor="rating">Rating</label>
        <select id="rating" value={rating} onChange={(e) => setRating(e.target.value)}>
          <option value="">All ratings</option>
          <option value="5">5 — Excellent</option>
          <option value="4">4 — Very Good</option>
          <option value="3">3 — Good</option>
          <option value="2">2 — Fair</option>
          <option value="1">1 — Poor</option>
        </select>
      </div>
      <div className="form-field">
        <label htmlFor="program">Program / Event</label>
        <input
          id="program"
          type="text"
          placeholder="e.g. FastAPI"
          value={program}
          onChange={(e) => setProgram(e.target.value)}
        />
      </div>
      <div className="filter-actions" style={{ display: 'flex', gap: 8 }}>
        <button type="submit" className="btn btn-primary">
          Apply
        </button>
        <button type="button" className="btn" onClick={reset}>
          Reset
        </button>
      </div>
    </form>
  );
}
