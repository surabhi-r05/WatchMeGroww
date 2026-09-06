import { useState } from 'react';
import {
  Activity,
  ArrowRight,
  Bell,
  BarChart3,
  CheckCircle2,
  Eye,
  Newspaper,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { login, register } from '../lib/api';

export default function Login({ onDone }: { onDone: () => void }) {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('demo@watchmegroww.app');
  const [password, setPassword] = useState('demo1234');
  const [confirm, setConfirm] = useState('demo1234');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setErr('');
    if (password.length < 6) {
      setErr('Password must be at least 6 characters.');
      return;
    }
    if (mode === 'signup' && password !== confirm) {
      setErr('Passwords do not match.');
      return;
    }

    setBusy(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password);
      }
      onDone();
    } catch (e: any) {
      setErr(e.message || 'Something went wrong');
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="auth-shell">
      <section className="auth-left">
        <div className="brand-row">
          <img
            src="/bear.png"
            className="brand-bear"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).style.display = 'none';
            }}
          />
          <span>
            Watch Me <em>Groww</em>
          </span>
        </div>

        <div className="auth-copy">
          <div className="eyebrow">
            <Sparkles size={13} /> MARKET WATCHLIST, MADE USEFUL
          </div>

          <h1>
            Your stocks.
            <br />
            <span>What changed.</span>
          </h1>

          <p className="auth-lead">
            Keep the stocks you care about in flexible watchlists and quickly
            understand what happened while you were away — from price and
            volume moves to technical signals, news, alerts and market context.
          </p>

          <div className="auth-value-strip">
            <div>
              <Eye size={17} />
              <span>See what you missed</span>
            </div>
            <div>
              <TrendingUp size={17} />
              <span>Understand the move</span>
            </div>
            <div>
              <Bell size={17} />
              <span>Keep watching</span>
            </div>
          </div>

          <div className="feature-grid">
            <div className="auth-feature">
              <div className="feature-icon"><Activity /></div>
              <div>
                <b>Flexible watchlists</b>
                <small>
                  Create lists and groups, add notes, and keep the stocks that
                  matter to you together.
                </small>
              </div>
            </div>

            <div className="auth-feature">
              <div className="feature-icon"><Eye /></div>
              <div>
                <b>Since your last check</b>
                <small>
                  Pick up where you left off with meaningful price, volume,
                  signal and event changes.
                </small>
              </div>
            </div>

            <div className="auth-feature">
              <div className="feature-icon"><BarChart3 /></div>
              <div>
                <b>Indicators & context</b>
                <small>
                  Track RSI, moving averages, MACD, Bollinger Bands, volume,
                  support/resistance and more.
                </small>
              </div>
            </div>

            <div className="auth-feature">
              <div className="feature-icon"><Newspaper /></div>
              <div>
                <b>News, events & alerts</b>
                <small>
                  See relevant news and corporate events alongside persistent
                  alerts for the conditions you care about.
                </small>
              </div>
            </div>
          </div>

          <div className="auth-foot">
            <ShieldCheck size={15} />
            Decision support, not financial advice.
          </div>
        </div>
      </section>

      <section className="auth-right">
        <div className="auth-card">
          <div className="mobile-brand">
            <img
              src="/bear.png"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).style.display = 'none';
              }}
            />
            Watch Me <em>Groww</em>
          </div>

          <div className="auth-card-intro">
            <div className="auth-card-icon"><Activity size={19} /></div>
            <div>
              <span className="auth-kicker">YOUR MARKET WORKSPACE</span>
              <h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
            </div>
          </div>

          <p className="muted auth-subtitle">
            {mode === 'login'
              ? 'Your watchlists, alerts and market context are ready when you are.'
              : 'Build watchlists, track stocks and keep your market state in one place.'}
          </p>

          <div className="tabs">
            <button
              type="button"
              className={mode === 'login' ? 'active' : ''}
              onClick={() => {
                setMode('login');
                setErr('');
              }}
            >
              Log in
            </button>
            <button
              type="button"
              className={mode === 'signup' ? 'active' : ''}
              onClick={() => {
                setMode('signup');
                setErr('');
              }}
            >
              Create account
            </button>
          </div>

          <label htmlFor="auth-email">Email</label>
          <input
            id="auth-email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            type="email"
            autoComplete="email"
          />

          <label htmlFor="auth-password">Password</label>
          <input
            id="auth-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            onKeyDown={(e) => {
              if (e.key === 'Enter') submit();
            }}
          />

          {mode === 'signup' && (
            <>
              <label htmlFor="auth-confirm">Confirm password</label>
              <input
                id="auth-confirm"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                type="password"
                autoComplete="new-password"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') submit();
                }}
              />
            </>
          )}

          {err && <div className="error-box">{err}</div>}

          <button
            type="button"
            className="primary-btn w-full auth-submit"
            disabled={busy}
            onClick={submit}
          >
            {busy
              ? 'Please wait…'
              : mode === 'login'
                ? 'Open my watchlist'
                : 'Create my workspace'}
            <ArrowRight size={17} />
          </button>

          {mode === 'login' && (
            <div className="demo-box">
              <div className="demo-heading">
                <CheckCircle2 size={15} />
                <b>Ready-to-explore demo</b>
              </div>
              <p>Use the prefilled demo account to explore the full workspace.</p>
              <div className="demo-credentials">
                <span><small>Email</small>demo@watchmegroww.app</span>
                <span><small>Password</small>demo1234</span>
              </div>
            </div>
          )}

          <div className="auth-bottom-note">
            <ShieldCheck size={14} />
            <span>
              Watchlists, alerts, notes and your “since last checked” state are
              persisted in the database.
            </span>
          </div>
        </div>
      </section>
    </main>
  );
}
