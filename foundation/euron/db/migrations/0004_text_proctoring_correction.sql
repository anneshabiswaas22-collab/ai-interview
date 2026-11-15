-- Existing text-practice sessions never use a camera or produce proctoring events.
-- Correct the inherited plan flag so their reports do not imply monitoring occurred.
UPDATE interviews AS i
SET proctoring = false, updated_at = now()
WHERE i.proctoring = true
  AND EXISTS (SELECT 1 FROM text_practice_sessions AS t WHERE t.interview_id = i.id);
