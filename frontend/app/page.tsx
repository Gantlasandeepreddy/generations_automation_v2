'use client';

import { useState } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';
import Dashboard from '../components/Dashboard';
import ManualRun from '../components/ManualRun';
import ScheduleConfig from '../components/ScheduleConfig';
import AdminPanel from '../components/AdminPanel';
import Image from 'next/image';

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
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <div className="text-navy text-lg font-medium">Loading...</div>
        </div>
      </main>
    );
  }

  if (!session?.user) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-8 items-center">
          {/* Left Side - Branding */}
          <div className="hidden lg:flex flex-col items-center justify-center p-12">
            <div className="mb-8">
              <Image
                src="/img.png"
                alt="Generations Automation"
                width={320}
                height={320}
                priority
              />
            </div>
            <div className="text-center">
              <h1 className="text-4xl font-bold text-navy mb-3">
                Generations Automation
              </h1>
              <p className="text-lg text-brand-gray">
                Streamline your client notes extraction and processing workflow
              </p>
            </div>
          </div>

          {/* Right Side - Login Form */}
          <div className="w-full">
            <div className="bg-white shadow-2xl rounded-3xl p-8 md:p-12 border border-gray-100">
              {/* Mobile Logo */}
              <div className="lg:hidden flex flex-col items-center mb-8">
                <div className="mb-4">
                  <Image
                    src="/img.png"
                    alt="Generations Automation"
                    width={200}
                    height={200}
                    priority
                  />
                </div>
                <h1 className="text-2xl font-bold text-navy">
                  Generations Automation
                </h1>
              </div>

              <div className="mb-8">
                <h2 className="text-3xl font-bold text-navy mb-2">Welcome Back</h2>
                <p className="text-brand-gray">Sign in to access your dashboard</p>
              </div>

              <form onSubmit={handleLogin} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-navy mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-all outline-none"
                    placeholder="admin@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-navy mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-all outline-none"
                    placeholder="Enter your password"
                  />
                </div>

                {loginError && (
                  <div className="bg-red-50 border-l-4 border-red-500 text-red-700 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    <span>{loginError}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loggingIn}
                  className="w-full px-6 py-4 bg-primary text-white rounded-xl hover:shadow-lg hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 font-semibold text-lg transition-all duration-200"
                >
                  {loggingIn ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Signing in...
                    </span>
                  ) : (
                    'Sign In'
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Modern Navigation */}
      <nav className="bg-white shadow-md border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center shadow-md">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-navy">
                  Generations Automation
                </h1>
                <p className="text-xs text-brand-gray">Client Notes Processing</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-accent rounded-full">
                <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white font-bold text-sm">
                  {session.user.email?.charAt(0).toUpperCase()}
                </div>
                <div className="text-sm">
                  <div className="font-semibold text-navy">{session.user.email}</div>
                  <div className="text-xs text-brand-gray capitalize">{session.user.role}</div>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="px-5 py-2.5 bg-navy text-white rounded-xl hover:bg-navy/90 hover:shadow-lg transition-all duration-200 font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Tab Navigation */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-1">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`relative px-6 py-4 font-semibold text-sm transition-all ${
                activeTab === 'dashboard'
                  ? 'text-primary'
                  : 'text-brand-gray hover:text-primary'
              }`}
            >
              <span className="relative z-10 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
                Dashboard
              </span>
              {activeTab === 'dashboard' && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary rounded-t-full"></div>
              )}
            </button>

            <button
              onClick={() => setActiveTab('manual')}
              className={`relative px-6 py-4 font-semibold text-sm transition-all ${
                activeTab === 'manual'
                  ? 'text-primary'
                  : 'text-brand-gray hover:text-primary'
              }`}
            >
              <span className="relative z-10 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Manual Run
              </span>
              {activeTab === 'manual' && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary rounded-t-full"></div>
              )}
            </button>

            <button
              onClick={() => setActiveTab('schedule')}
              className={`relative px-6 py-4 font-semibold text-sm transition-all ${
                activeTab === 'schedule'
                  ? 'text-primary'
                  : 'text-brand-gray hover:text-primary'
              }`}
            >
              <span className="relative z-10 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Schedule
              </span>
              {activeTab === 'schedule' && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary rounded-t-full"></div>
              )}
            </button>

            {session.user.role === 'admin' && (
              <button
                onClick={() => setActiveTab('admin')}
                className={`relative px-6 py-4 font-semibold text-sm transition-all ${
                  activeTab === 'admin'
                    ? 'text-primary'
                    : 'text-brand-gray hover:text-primary'
                }`}
              >
                <span className="relative z-10 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  Admin
                </span>
                {activeTab === 'admin' && (
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary rounded-t-full"></div>
                )}
              </button>
            )}
          </nav>
        </div>
      </div>

      {/* Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'manual' && <ManualRun />}
        {activeTab === 'schedule' && <ScheduleConfig />}
        {activeTab === 'admin' && session.user.role === 'admin' && <AdminPanel />}
      </div>
    </main>
  );
}
