-- Enables similarity search for Incident Memory (D-010: pgvector chosen over
-- a standalone vector DB service). Table schema for incidents/hypotheses/etc.
-- is added when Phase 1/3 agents start persisting state.
CREATE EXTENSION IF NOT EXISTS vector;
