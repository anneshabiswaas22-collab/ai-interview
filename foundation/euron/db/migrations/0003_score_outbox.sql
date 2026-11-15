-- The answer and its pending score-dispatch record are committed together. The row
-- contains identifiers and a version only, never the candidate's answer or a secret.
CREATE TABLE score_dispatch_outbox (
  answer_id text PRIMARY KEY REFERENCES answers(id) ON DELETE CASCADE,
  answer_version timestamptz(3) NOT NULL,
  created_at timestamptz(3) NOT NULL DEFAULT now()
);
CREATE INDEX score_dispatch_outbox_created_idx ON score_dispatch_outbox (created_at, answer_id);
