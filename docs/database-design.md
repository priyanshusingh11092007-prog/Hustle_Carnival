# Database Design

## users

Stores protected staff/admin accounts.

Passwords are stored as hashes.

## services

Stores available service counters.

## tokens

Stores queue entries, token numbers, status and timestamps.

## audit_events

Records important token status changes.

## Relationships

services.id -> tokens.service_id

users.id -> audit_events.actor_id

tokens.id -> audit_events.token_id

## Important Constraints

Token public IDs must be unique.

Token numbers must be unique.

Sequence numbers must be unique per service.

Foreign keys are enforced in SQLite connections.
