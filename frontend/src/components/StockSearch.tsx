import { useEffect, useRef, useState } from 'react';
import { Check, Search, TrendingUp } from 'lucide-react';
import { api } from '../lib/api';

type Result = {
  symbol: string;
  name: string;
  sector: string;
  sector_index?: string;
  exchange?: string;
};

type Props = {
  onAdd?: (symbol: string) => Promise<void> | void;
  onOpen?: (symbol: string) => void;
  placeholder?: string;
};

export default function StockSearch({
  onAdd,
  onOpen,
  placeholder = 'Search stocks, companies or sectors…',
}: Props) {
  const [q, setQ] = useState('');
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const value = q.trim();

    if (value.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }

    const timer = window.setTimeout(async () => {
      setLoading(true);

      try {
        const data = await api(
          `/stocks/search?q=${encodeURIComponent(value)}`
        );

        setResults(Array.isArray(data) ? data : []);
        setOpen(true);
      } catch {
        setResults([]);
        setOpen(true);
      } finally {
        setLoading(false);
      }
    }, 220);

    return () => window.clearTimeout(timer);
  }, [q]);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (!ref.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', close);

    return () => {
      document.removeEventListener('mousedown', close);
    };
  }, []);

  const choose = async (symbol: string) => {
    try {
      if (onAdd) {
        await onAdd(symbol);
      } else {
        onOpen?.(symbol);
      }
    } finally {
      setQ('');
      setOpen(false);
    }
  };

  return (
    <div className="stock-search" ref={ref}>
      <div className="stock-search-input">
        <Search size={18} />

        <input
          value={q}
          onChange={(event) => setQ(event.target.value)}
          onFocus={() => {
            if (results.length > 0) {
              setOpen(true);
            }
          }}
          onKeyDown={(event) => {
            if (event.key === 'Escape') {
              setOpen(false);
            }

            if (event.key === 'Enter' && results.length > 0) {
              choose(results[0].symbol);
            }
          }}
          placeholder={placeholder}
          aria-label="Search stocks, companies or sectors"
          autoComplete="off"
        />

        <span className="search-hint">⌘ K</span>
      </div>

      {open && (
        <div className="stock-search-menu">
          {loading && (
            <div className="search-loading">
              Searching stocks…
            </div>
          )}

          {!loading &&
            results.map((result) => (
              <button
                type="button"
                className="stock-search-result"
                key={result.symbol}
                onClick={() => choose(result.symbol)}
              >
                <span className="result-icon">
                  <TrendingUp size={16} />
                </span>

                <span className="result-copy">
                  <b>{result.name}</b>

                  <small>
                    {result.symbol}
                    {' · '}
                    {result.exchange || 'NSE'}
                    {' · '}
                    {result.sector}

                    {result.sector_index
                      ? ` · ${result.sector_index}`
                      : ''}
                  </small>
                </span>

                {onAdd && (
                  <span className="result-action">
                    <Check size={15} />
                    Add
                  </span>
                )}
              </button>
            ))}

          {!loading &&
            q.trim().length >= 2 &&
            results.length === 0 && (
              <div className="search-loading">
                No matching stocks found.
              </div>
            )}
        </div>
      )}
    </div>
  );
}