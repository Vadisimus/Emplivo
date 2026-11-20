CREATE TABLE IF NOT EXISTS submissions (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('apply', 'employer')),
  status TEXT NOT NULL CHECK (status IN ('pending', 'sent', 'failed', 'unknown')),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS submissions_updated ON submissions (updated_at);
