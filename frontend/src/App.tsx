import { Route, Routes, Navigate, useLocation } from 'react-router-dom';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { AuthCallback } from './pages/AuthCallback';
import { Dashboard } from './pages/Dashboard';
import { Vehicles } from './pages/Vehicles';
import { Drivers } from './pages/Drivers';
import { Bookings } from './pages/Bookings';
import { Calendar } from './pages/Calendar';
import { Dispatch } from './pages/Dispatch';
import { Maintenance } from './pages/Maintenance';
import { Expenses } from './pages/Expenses';
import { Profit } from './pages/Profit';
import { Invoices } from './pages/Invoices';
import { Renewals } from './pages/Renewals';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { Documents } from './pages/Documents';
import { Sidebar } from './components/layout/Sidebar';

function App() {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/signup';

  if (isAuthPage) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 text-slate-900">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Routes>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 text-slate-900">
      <div className="lg:flex">
        <Sidebar />
        <main className="flex-1 p-4 pt-20 lg:p-8 lg:pt-8">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/auth/callback" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/vehicles" element={<Vehicles />} />
            <Route path="/vehicles/:vehicleId/documents" element={<Documents />} />
            <Route path="/drivers" element={<Drivers />} />
            <Route path="/bookings" element={<Bookings />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/dispatch" element={<Dispatch />} />
            <Route path="/maintenance" element={<Maintenance />} />
            <Route path="/expenses" element={<Expenses />} />
            <Route path="/profit" element={<Profit />} />
            <Route path="/invoices" element={<Invoices />} />
            <Route path="/renewals" element={<Renewals />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;
