ALTER TYPE answer_kind ADD VALUE 'TEXT';

-- Text practice shares interview ownership and lifecycle with the existing engine.
-- A session's presence locks an interview to text; voice interviews cannot become text.
CREATE TABLE text_practice_sessions (
  interview_id text PRIMARY KEY REFERENCES interviews(id) ON DELETE CASCADE,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  consented_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE text_practice_events (
  id text PRIMARY KEY,
  interview_id text NOT NULL REFERENCES text_practice_sessions(interview_id) ON DELETE CASCADE,
  sequence integer NOT NULL CHECK (sequence > 0),
  kind text NOT NULL CHECK (kind IN ('QUESTION', 'ANSWER', 'COMPLETED')),
  round_index integer NOT NULL CHECK (round_index >= 0),
  question_index integer NOT NULL CHECK (question_index >= 0),
  text text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (interview_id, sequence)
);

CREATE TABLE text_practice_requests (
  interview_id text NOT NULL REFERENCES text_practice_sessions(interview_id) ON DELETE CASCADE,
  request_id uuid NOT NULL,
  fingerprint text NOT NULL,
  PRIMARY KEY (interview_id, request_id)
);
