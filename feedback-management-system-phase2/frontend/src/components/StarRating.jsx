// Read-only star display. For input use RatingInput.
export default function StarRating({ value, max = 5, ariaLabel }) {
  const rounded = Math.round(value || 0);
  return (
    <span className="rating" aria-label={ariaLabel || `${value} out of ${max}`}>
      {Array.from({ length: max }, (_, i) => (
        <span key={i} className={'star' + (i < rounded ? '' : ' dim')}>
          ★
        </span>
      ))}
    </span>
  );
}

export function RatingPill({ rating }) {
  const labels = { 1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very Good', 5: 'Excellent' };
  return (
    <span className="rating-pill" title={labels[rating]}>
      ★ {rating} · {labels[rating] || ''}
    </span>
  );
}

export function RatingInput({ value, onChange, name = 'rating' }) {
  return (
    <div className="rating-input" role="radiogroup" aria-label="Rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          type="button"
          key={star}
          aria-label={`${star} star${star === 1 ? '' : 's'}`}
          aria-checked={value === star}
          role="radio"
          className={value >= star ? 'active' : ''}
          onClick={() => onChange(star)}
        >
          ★
        </button>
      ))}
      <input type="hidden" name={name} value={value || ''} />
    </div>
  );
}
