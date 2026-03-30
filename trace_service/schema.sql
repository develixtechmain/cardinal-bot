-- Message trace storage (same PostgreSQL as main app; created on startup if missing)

CREATE TABLE IF NOT EXISTS message_trace_roots (
    correlation_id UUID PRIMARY KEY,
    source_chat_id TEXT,
    source_message_id BIGINT,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_event_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_message_trace_roots_last_event
    ON message_trace_roots (last_event_at DESC);

CREATE INDEX IF NOT EXISTS idx_message_trace_roots_source
    ON message_trace_roots (source_chat_id, source_message_id);

CREATE TABLE IF NOT EXISTS message_trace_events (
    id BIGSERIAL PRIMARY KEY,
    correlation_id UUID NOT NULL REFERENCES message_trace_roots (correlation_id) ON DELETE CASCADE,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service TEXT NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_ms INTEGER,
    parent_event_id BIGINT REFERENCES message_trace_events (id) ON DELETE SET NULL,
    detail JSONB NOT NULL DEFAULT '{}',
    recommendation_id UUID,
    otel_trace_id TEXT,
    otel_span_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_message_trace_events_correlation
    ON message_trace_events (correlation_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_message_trace_events_recommendation
    ON message_trace_events (recommendation_id)
    WHERE recommendation_id IS NOT NULL;
