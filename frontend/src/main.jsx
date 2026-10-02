import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import Dashboard from './components/Dashboard.jsx';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));

if (window.location.pathname === '/dashboard') {
  root.render(<Dashboard />);
} else {
  root.render(<App />);
}
