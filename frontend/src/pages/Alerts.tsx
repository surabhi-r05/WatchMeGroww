import { useEffect, useState } from 'react';
import Panel from '../components/Panel';
import StockSearch from '../components/StockSearch';
import { api, json } from '../lib/api';
import {
  Bell,
  Pause,
  Play,
  Trash2,
  Plus,
  X,
  Check,
} from 'lucide-react';

type AlertType =
  | 'PRICE_ABOVE'
  | 'PRICE_BELOW'
  | 'PCT_MOVE'
  | 'VOLUME_SPIKE';

type AlertForm = {
  symbol: string;
  type: AlertType;
  threshold: string;
};

export default function Alerts() {
  const [rows, setRows] = useState<any[]>([]);
  const [notes, setNotes] = useState<any[]>([]);

  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState('');

  const [form, setForm] = useState<AlertForm>({
    symbol: '',
    type: 'PRICE_ABOVE',
    threshold: '',
  });

  const load = () =>
    Promise.all([
      api('/alerts'),
      api('/notifications'),
    ]).then(([alerts, notifications]) => {
      setRows(alerts);
      setNotes(notifications);
    });

  useEffect(() => {
    load();
  }, []);

  const resetForm = () => {
    setForm({
      symbol: '',
      type: 'PRICE_ABOVE',
      threshold: '',
    });
    setFormError('');
  };

  const openCreate = () => {
    resetForm();
    setShowCreate(true);
  };

  const closeCreate = () => {
    if (creating) return;

    resetForm();
    setShowCreate(false);
  };

  const create = async () => {
    setFormError('');

    if (!form.symbol.trim()) {
      setFormError('Select a stock first.');
      return;
    }

    const threshold = Number(form.threshold);

    if (!form.threshold.trim() || !Number.isFinite(threshold)) {
      setFormError('Enter a valid threshold.');
      return;
    }

    if (threshold < 0) {
      setFormError('Threshold cannot be negative.');
      return;
    }

    setCreating(true);

    try {
      await api(
        '/alerts',
        json({
          symbol: form.symbol.trim().toUpperCase(),
          alert_type: form.type,
          threshold,
        })
      );

      await load();

      resetForm();
      setShowCreate(false);
    } catch (e: any) {
      setFormError(e?.message || 'Could not create alert.');
    } finally {
      setCreating(false);
    }
  };

  const typeLabel = (type: AlertType) => {
    switch (type) {
      case 'PRICE_ABOVE':
        return 'Price rises above';

      case 'PRICE_BELOW':
        return 'Price falls below';

      case 'PCT_MOVE':
        return 'Daily move reaches';

      case 'VOLUME_SPIKE':
        return 'Volume spike reaches';

      default:
        return String(type).replace(/_/g, ' ');
    }
  };

  const thresholdLabel = () => {
    switch (form.type) {
      case 'PRICE_ABOVE':
      case 'PRICE_BELOW':
        return 'Price threshold';

      case 'PCT_MOVE':
        return 'Percentage move';

      case 'VOLUME_SPIKE':
        return 'Volume multiplier';

      default:
        return 'Threshold';
    }
  };

  const thresholdPlaceholder = () => {
    switch (form.type) {
      case 'PRICE_ABOVE':
        return 'e.g. 1500';

      case 'PRICE_BELOW':
        return 'e.g. 1200';

      case 'PCT_MOVE':
        return 'e.g. 5';

      case 'VOLUME_SPIKE':
        return 'e.g. 2';

      default:
        return 'Enter threshold';
    }
  };

  const thresholdHint = () => {
    switch (form.type) {
      case 'PRICE_ABOVE':
        return 'Create a notification when the stock moves above this price.';

      case 'PRICE_BELOW':
        return 'Create a notification when the stock moves below this price.';

      case 'PCT_MOVE':
        return 'For example, 5 means notify when the daily move reaches ±5%.';

      case 'VOLUME_SPIKE':
        return 'For example, 2 means volume reaches 2× its normal level.';

      default:
        return '';
    }
  };

  return (
    <div className="space-y-6">
      <header className="topbar">
        <div>
          <div className="eyebrow">PERSISTENT MONITORING</div>

          <h1 className="page-title">
            Alerts & notifications
          </h1>

          <p className="muted">
            Set conditions once and let Watch Me Groww keep an eye
            on them for you.
          </p>
        </div>

        <button
          className="primary-btn"
          onClick={openCreate}
        >
          <Plus size={16} />
          Create alert
        </button>
      </header>

      {/* =====================================================
          INLINE CREATE ALERT
         ===================================================== */}

      {showCreate && (
        <Panel>
          <div className="alert-builder">
            <div className="alert-builder-header">
              <div>
                <div className="eyebrow">
                  NEW ALERT
                </div>

                <h2>Create an alert</h2>

                <p className="muted">
                  Choose a stock and the condition you want to
                  keep watching.
                </p>
              </div>

              <button
                type="button"
                className="icon-btn"
                onClick={closeCreate}
                disabled={creating}
                aria-label="Close"
              >
                <X size={17} />
              </button>
            </div>

            <div className="alert-builder-grid">
              {/* STOCK */}

              <div className="alert-field alert-stock-field">
                <label>Stock</label>

                {form.symbol ? (
                  <div className="selected-stock">
                    <div>
                      <b>{form.symbol}</b>

                      <span>
                        Alert will be created for this stock
                      </span>
                    </div>

                    <button
                      type="button"
                      className="icon-btn"
                      onClick={() =>
                        setForm((current) => ({
                          ...current,
                          symbol: '',
                        }))
                      }
                    >
                      <X size={15} />
                    </button>
                  </div>
                ) : (
                  <StockSearch
                    onAdd={(symbol) =>
                      setForm((current) => ({
                        ...current,
                        symbol,
                      }))
                    }
                  />
                )}
              </div>

              {/* CONDITION */}

              <div className="alert-field">
                <label htmlFor="alert-type">
                  Alert me when
                </label>

                <select
                  id="alert-type"
                  value={form.type}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      type: event.target.value as AlertType,
                    }))
                  }
                >
                  <option value="PRICE_ABOVE">
                    Price rises above
                  </option>

                  <option value="PRICE_BELOW">
                    Price falls below
                  </option>

                  <option value="PCT_MOVE">
                    Daily move reaches
                  </option>

                  <option value="VOLUME_SPIKE">
                    Volume spike reaches
                  </option>
                </select>
              </div>

              {/* THRESHOLD */}

              <div className="alert-field">
                <label htmlFor="alert-threshold">
                  {thresholdLabel()}
                </label>

                <div className="threshold-input">
                  <span>
                    {form.type === 'PRICE_ABOVE' ||
                    form.type === 'PRICE_BELOW'
                      ? '₹'
                      : form.type === 'PCT_MOVE'
                        ? '%'
                        : '×'}
                  </span>

                  <input
                    id="alert-threshold"
                    type="number"
                    min="0"
                    step="any"
                    value={form.threshold}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        threshold: event.target.value,
                      }))
                    }
                    placeholder={thresholdPlaceholder()}
                  />
                </div>

                <small>
                  {thresholdHint()}
                </small>
              </div>
            </div>

            {formError && (
              <div className="alert-form-error">
                {formError}
              </div>
            )}

            <div className="alert-builder-footer">
              <button
                type="button"
                className="secondary-btn"
                onClick={closeCreate}
                disabled={creating}
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary-btn"
                onClick={create}
                disabled={creating}
              >
                <Check size={16} />

                {creating
                  ? 'Creating…'
                  : 'Create alert'}
              </button>
            </div>
          </div>
        </Panel>
      )}

      {/* =====================================================
          ALERTS + NOTIFICATIONS
         ===================================================== */}

      <div className="grid xl:grid-cols-2 gap-6">
        <Panel title="Your alerts">
          <div className="space-y-3 mt-4">
            {rows.map((x) => (
              <div
                className="alert-row"
                key={x.id}
              >
                <div>
                  <b>{x.symbol}</b>

                  <span className="muted block text-xs">
                    {typeLabel(x.type as AlertType)}
                    {' · '}
                    {x.threshold}
                  </span>
                </div>

                <div className="flex gap-2">
                  <button
                    className="icon-btn"
                    title={
                      x.active
                        ? 'Pause alert'
                        : 'Resume alert'
                    }
                    onClick={() =>
                      api(
                        `/alerts/${x.id}?active=${!x.active}`,
                        { method: 'PATCH' }
                      ).then(load)
                    }
                  >
                    {x.active ? (
                      <Pause size={15} />
                    ) : (
                      <Play size={15} />
                    )}
                  </button>

                  <button
                    className="icon-btn"
                    title="Delete alert"
                    onClick={() =>
                      api(
                        `/alerts/${x.id}`,
                        { method: 'DELETE' }
                      ).then(load)
                    }
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}

            {!rows.length && (
              <div className="empty-state">
                <Bell size={20} />

                <b>No alerts yet</b>

                <p>
                  Create an alert and we'll watch the
                  condition for you.
                </p>

                <button
                  className="secondary-btn"
                  onClick={openCreate}
                >
                  <Plus size={15} />
                  Create your first alert
                </button>
              </div>
            )}
          </div>
        </Panel>

        <Panel
          title="Notifications"
          action={
            <button
              className="secondary-btn"
              onClick={() =>
                api(
                  '/notifications/read-all',
                  { method: 'POST' }
                ).then(load)
              }
            >
              Mark all read
            </button>
          }
        >
          <div className="space-y-3 mt-4">
            {notes.map((x) => (
              <button
                className={`notification ${
                  x.read ? 'read' : ''
                }`}
                key={x.id}
                onClick={() =>
                  api(
                    `/notifications/${x.id}/read`,
                    { method: 'POST' }
                  ).then(load)
                }
              >
                <Bell size={16} />

                <div>
                  <b>{x.title}</b>

                  <p>{x.body}</p>

                  <small>
                    {new Date(
                      x.created_at
                    ).toLocaleString()}
                  </small>
                </div>
              </button>
            ))}

            {!notes.length && (
              <p className="muted">
                Notifications will appear here when
                alert conditions trigger.
              </p>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}