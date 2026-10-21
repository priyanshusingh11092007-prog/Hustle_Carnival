CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    service_name TEXT NOT NULL UNIQUE,
    service_code TEXT NOT NULL UNIQUE,
    is_open INTEGER NOT NULL DEFAULT 1,
    default_service_seconds INTEGER NOT NULL DEFAULT 300
);

CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CAST(CURRENT_TIMESTAMP AS TEXT)
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('ADMIN', 'STAFF')),
    active INTEGER NOT NULL DEFAULT 1,
    service_id INTEGER REFERENCES services(id)
);

CREATE TABLE IF NOT EXISTS tokens (
    id SERIAL PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    token_number TEXT NOT NULL UNIQUE,
    sequence_number INTEGER NOT NULL,
    queue_order INTEGER NOT NULL,
    service_id INTEGER NOT NULL REFERENCES services(id),
    student_id INTEGER REFERENCES students(id),

    status TEXT NOT NULL DEFAULT 'WAITING'
        CHECK (status IN (
            'WAITING', 'CALLED', 'SERVING', 'HOLD',
            'COMPLETED', 'CANCELLED', 'NO_SHOW'
        )),

    source TEXT NOT NULL DEFAULT 'DIGITAL'
        CHECK (source IN ('DIGITAL', 'WALK_IN')),

    created_at TEXT NOT NULL,
    called_at TEXT,
    serving_at TEXT,
    completed_at TEXT,
    cancelled_at TEXT,
    estimated_wait_seconds INTEGER,

    UNIQUE (service_id, sequence_number),
    UNIQUE (service_id, queue_order)
);

CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id),
    actor_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tokens_queue_order ON tokens(service_id, queue_order);
CREATE INDEX IF NOT EXISTS idx_tokens_student ON tokens(student_id);
CREATE INDEX IF NOT EXISTS idx_tokens_created ON tokens(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_token ON audit_events(token_id);