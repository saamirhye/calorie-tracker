-- The weekly report filters entries by user and a consumed_at range.
-- One index serves both, and also covers lookups by user_id alone.
CREATE INDEX entries_user_consumed_at_idx ON entries (user_id, consumed_at);
