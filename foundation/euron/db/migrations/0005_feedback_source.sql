-- Record which configured provider kind generated a score. Older records remain
-- unknown rather than being incorrectly labelled as real or simulated.
ALTER TABLE answers ADD COLUMN evaluator_kind provider_kind;
