# Interaction Pipeline

## Purpose

The interaction pipeline records user behavior only. It never requests or
calculates recommendations. DynamoDB and future ML export jobs consume the
canonical events independently.

Editable FigJam versions of both sequence diagrams are available in the
[Interaction pipeline board](https://www.figma.com/board/4i9DFePMmbbdOhEdgCzhSg).

Supported interaction types and actions:

| `interaction_type` | Allowed `interaction_action` | `interaction_value` |
|---|---|---|
| `click` | `open_detail` | Optional |
| `watch` | `start`, `progress`, `complete` | Optional non-negative progress value |
| `rating` | `submit` | Required value from 0.5 through 5.0 |
| `reaction` | `like`, `dislike` | Optional |
| `share` | `native_share`, `copy_link` | Optional |

## Canonical record

Every newly persisted item contains:

```text
user_id
interaction_key
event_id
movie_id
interaction_type
interaction_action
interaction_value
timestamp
session_id
```

The sort key is:

```text
timestamp#movie_id#event_id
```

The timestamp is normalized to UTC and rendered with millisecond precision.
The API generates `event_id`; clients cannot provide it.

## Idempotency contract

Clients must send an `Idempotency-Key` header and keep the same request body
when retrying. The request body includes a stable timestamp. At the API
boundary, UUID v5 deterministically derives `event_id` from:

```text
authenticated user_id + Idempotency-Key + canonical request payload
```

This produces the same event ID and interaction key for an identical retry.
`UserInteractionsRepository.create` uses a conditional put. If the item already
exists, the repository reads and returns that identical record. Concurrent or
response-loss retries therefore leave only one DynamoDB item.

## New interaction sequence

```mermaid
sequenceDiagram
    title Record a user interaction
    participant User
    participant MovieUI
    participant InteractionHook
    participant FrontendService
    participant FastAPI
    participant InteractionService
    participant Repository
    participant DynamoDB

    User->>MovieUI: Perform protected action
    MovieUI->>InteractionHook: Forward movie action
    InteractionHook->>FrontendService: createInteraction
    FrontendService->>FastAPI: POST interaction with idempotency key
    FastAPI->>FastAPI: Generate deterministic event ID
    FastAPI->>InteractionService: Record canonical request
    InteractionService->>Repository: Create interaction
    Repository->>DynamoDB: Conditional PutItem
    DynamoDB-->>Repository: Item created
    Repository-->>InteractionService: UserInteraction
    InteractionService-->>FastAPI: InteractionResponse
    FastAPI-->>FrontendService: 201 Created
    FrontendService-->>InteractionHook: Stored interaction
    InteractionHook-->>MovieUI: Update interaction state
```

## Retry sequence

```mermaid
sequenceDiagram
    title Idempotent interaction retry
    participant FrontendService
    participant FastAPI
    participant InteractionService
    participant Repository
    participant DynamoDB

    FrontendService->>FastAPI: Retry same body and idempotency key
    FastAPI->>FastAPI: Regenerate same event ID
    FastAPI->>InteractionService: Record same canonical request
    InteractionService->>Repository: Create same interaction key
    Repository->>DynamoDB: Conditional PutItem
    DynamoDB-->>Repository: Conditional conflict
    Repository->>DynamoDB: GetItem by user and interaction key
    DynamoDB-->>Repository: Existing identical item
    Repository-->>InteractionService: Existing UserInteraction
    InteractionService-->>FastAPI: Same InteractionResponse
    FastAPI-->>FrontendService: 201 Created with same event ID
```

## Boundaries

- The router owns authentication, idempotency header validation, and event ID
  generation.
- `InteractionService` owns canonical key construction and interaction
  semantics.
- `UserInteractionsRepository` owns DynamoDB operations and retry conflict
  resolution.
- Frontend components only render state and forward user actions.
- `interactionService` is the only frontend module that submits interaction
  requests.
- Recommendation services and providers are not called by this pipeline.
