# Phase 1 Domain Model Migration Summary

## Scope

This phase changed backend domain names and persistence mapping only.

- Frontend files were not modified.
- Existing API URL paths were not modified.
- No new product feature or endpoint was added.
- SageMaker was not implemented or invoked.
- The cache-first recommendation flow remains intact.
- InteractionService continues to record behavior only.

## Added

- Strict Pydantic domain models for all five DynamoDB tables.
- Canonical schemas for movies, users, popular lists, interactions, and
  recommendations.
- Typed DynamoDB repositories under `app/repositories`.
- Repository pagination for scan-based list operations.
- Normalized RecommendationCache serialization.
- Movie enrichment after a recommendation cache hit.
- Backend tests that assert canonical field sets.
- Documentation for domain models, data flow, entity mapping, and naming.

## Renamed or normalized

- All movie identifiers are now `movie_id: str`.
- All user identifiers are now `user_id: str`.
- Movie response fields now match the Movies table.
- Interaction records now use `interaction_type`, `interaction_value`,
  `timestamp`, and `session_id`.
- Interaction sort keys now use `timestamp#movie_id`.
- Recommendation cache records now use `items`, `model_version`,
  `generated_at`, and `expire_at`.

## Removed from new persisted records

- Movie aliases: `id`, `year`, `genre`, `rating`, `description`, `image_url`.
- Interaction fields: `event_id`, `event_type`, `rating`, `metadata`,
  `created_at`, `username`, `schema_version`.
- Cache fields: `movie_ids`, full `movies` snapshots, `cached_at`,
  `expires_at`, `provider`, and `schema_version`.

## Backward compatibility

- API URL paths are unchanged.
- Login and token request/response fields are unchanged.
- `/auth/me` keeps the derived `role` field and now also returns canonical
  `user_id`.
- Interaction requests temporarily accept `event_type` as an alias for
  `interaction_type`.
- Interaction requests temporarily accept `rating` as an alias for
  `interaction_value`.
- Numeric legacy movie IDs in interaction requests are normalized to strings.
- Missing legacy `session_id` values receive `legacy-session`.
- The old DynamoDB repository import path re-exports the new repository
  classes temporarily.

All new JSON output and all new persisted records use canonical field names.

## API response compatibility note

URL paths did not change, but response entity fields intentionally moved to the
canonical contract. Clients still expecting legacy movie or interaction field
names must be updated in a later frontend milestone. No frontend file was
changed in this phase.

The affected response changes are:

- Movie payloads now use the complete Movies field set.
- Movie and user identifiers are serialized as strings.
- Interaction responses now use canonical interaction fields.
- Recommendation items now contain canonical movie metadata plus `score` and
  `reason_code`.

## Existing DynamoDB data migration required

This phase changes application models; it does not rewrite deployed records.
Before deploying the backend against existing data:

1. Back up UserInteractions and RecommendationCache.
2. Transform existing UserInteractions records into the canonical schema.
3. Rebuild `interaction_key` as `timestamp#movie_id`.
4. Transform cache records into normalized `items`.
5. Remove duplicated movie snapshots from cache.
6. Rename cache expiration to `expire_at`.
7. Enable DynamoDB TTL on `expire_at`.
8. Validate every referenced movie ID against Movies.
9. Invalidate any record that cannot be migrated safely.

## Deferred intentionally

- Real authentication, registration, and Users persistence.
- Guest route authorization changes.
- New API endpoints and pages.
- Full replacement of the in-memory movie source.
- Watchlist architecture.
- SageMaker provider implementation.
- DynamoDB infrastructure changes and live data migration.
- Removal date for request aliases and the repository import shim.
