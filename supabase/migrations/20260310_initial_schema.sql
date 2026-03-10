-- Listings table
CREATE TABLE IF NOT EXISTS listings (
  id TEXT PRIMARY KEY,
  property_data JSONB NOT NULL,
  ai_copy JSONB,
  pdf_storage_path TEXT,
  video_storage_path TEXT,
  photo_paths TEXT[] DEFAULT '{}',
  status TEXT DEFAULT 'processing',
  video_status TEXT DEFAULT 'pending',
  video_error TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Template settings singleton
CREATE TABLE IF NOT EXISTS template_settings (
  id TEXT PRIMARY KEY DEFAULT 'default',
  settings JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Auto-update triggers
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER listings_updated_at BEFORE UPDATE ON listings FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER settings_updated_at BEFORE UPDATE ON template_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX IF NOT EXISTS idx_listings_created_at ON listings (created_at DESC);
