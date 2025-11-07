'use client';

import { useState } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';
import Dashboard from '../components/Dashboard';
import ManualRun from '../components/ManualRun';
import ScheduleConfig from '../components/ScheduleConfig';
import AdminPanel from '../components/AdminPanel';

type Tab = 'dashboard' | 'manual' | 'schedule' | 'admin';

export default function Home() {
  const { data: session, status } = useSession();
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loggingIn, setLoggingIn] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setLoggingIn(true);

    try {
      const result = await signIn('credentials', {
        email,
        password,
        redirect: false,
      });

      if (result?.error) {
        setLoginError('Invalid credentials');
      }
    } catch (err) {
      setLoginError('An error occurred during login');
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLogout = async () => {
    await signOut({ redirect: false });
    setEmail('');
    setPassword('');
    setActiveTab('dashboard');
  };

  if (status === 'loading') {
    return (
      <main className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-navy text-lg">Loading...</div>
      </main>
    );
  }

  if (!session?.user) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-full max-w-md">
          <div className="bg-white shadow-lg rounded-lg p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-navy mb-2">
                Generations Automation
              </h1>
              <p className="text-brand-gray">
                Client notes extraction and processing
              </p>
            </div>

            <form onSubmit={handleLogin}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-brand-gray mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="admin@example.com"
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-brand-gray mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="Enter password"
                />
              </div>

              {loginError && (
                <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-sm">
                  {loginError}
                </div>
              )}

              <button
                type="submit"
                disabled={loggingIn}
                className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {loggingIn ? 'Logging in...' : 'Login'}
              </button>
            </form>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background">
      <nav className="bg-navy text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold">Generations Automation</h1>
            <div className="flex items-center gap-4">
              <span className="text-sm">
                {session.user.email} ({session.user.role})
              </span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-white text-navy rounded hover:bg-gray-100 transition font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6 border-b border-gray-300">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                activeTab === 'dashboard'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-brand-gray hover:text-primary hover:border-gray-300'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('manual')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                activeTab === 'manual'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-brand-gray hover:text-primary hover:border-gray-300'
              }`}
            >
              Manual Run
            </button>
            <button
              onClick={() => setActiveTab('schedule')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                activeTab === 'schedule'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-brand-gray hover:text-primary hover:border-gray-300'
              }`}
            >
              Schedule
            </button>
            {session.user.role === 'admin' && (
              <button
                onClick={() => setActiveTab('admin')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                  activeTab === 'admin'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-brand-gray hover:text-primary hover:border-gray-300'
                }`}
              >
                Admin
              </button>
            )}
          </nav>
        </div>

        <div>
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'manual' && <ManualRun />}
          {activeTab === 'schedule' && <ScheduleConfig />}
          {activeTab === 'admin' && session.user.role === 'admin' && <AdminPanel />}
        </div>
      </div>
    </main>
  );
}
