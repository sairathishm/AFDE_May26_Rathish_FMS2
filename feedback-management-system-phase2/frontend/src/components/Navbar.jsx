import { NavLink } from 'react-router-dom';

export default function Navbar() {
  const linkClass = ({ isActive }) =>
    'navbar-link' + (isActive ? ' active' : '');

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand">
          <span aria-hidden="true">💬</span>
          <span>Feedback Manager</span>
          <span className="navbar-tag">Phase 2</span>
        </div>
        <div className="navbar-links">
          <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
          <NavLink to="/feedback" className={linkClass}>All Feedback</NavLink>
          <NavLink to="/submit" className={linkClass}>Submit Feedback</NavLink>
          <NavLink to="/analytics" className={linkClass}>Analytics</NavLink>
          <NavLink to="/etl" className={linkClass}>ETL Import</NavLink>
        </div>
      </div>
    </nav>
  );
}
