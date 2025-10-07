CREATE TABLE IF NOT EXISTS observations (
  id SERIAL PRIMARY KEY,
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL,
  ts  TIMESTAMPTZ NOT NULL,
  temp_c DOUBLE PRECISION,
  aqi INTEGER
);

CREATE INDEX IF NOT EXISTS idx_obs_time_geo
ON observations (ts, lat, lon);

CREATE TABLE IF NOT EXISTS forecasts (
  id SERIAL PRIMARY KEY,
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL,
  ts  TIMESTAMPTZ NOT NULL,
  temp_c DOUBLE PRECISION,
  aqi INTEGER
);

CREATE INDEX IF NOT EXISTS idx_fc_time_geo
ON forecasts (ts, lat, lon);

-- Optional demo table to show persistence across restarts
CREATE TABLE IF NOT EXISTS queries_history (
  id SERIAL PRIMARY KEY,
  qtype TEXT NOT NULL,           -- 'point' | 'trip'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  payload JSONB,
  summary JSONB
);
