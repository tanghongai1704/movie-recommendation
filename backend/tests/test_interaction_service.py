import unittest
from datetime import datetime, timezone
from uuid import UUID

from app.models.user_interaction import (
    InteractionAction,
    InteractionType,
    UserInteraction,
)
from app.schemas.interaction import InteractionCreate
from app.services.interaction_service import InteractionService


class RecordingRepository:
    def __init__(self) -> None:
        self.items: list[UserInteraction] = []

    def create(self, item: UserInteraction) -> UserInteraction:
        self.items.append(item)
        return item


class InteractionServiceTests(unittest.TestCase):
    def test_records_every_supported_interaction(self) -> None:
        timestamp = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)
        cases = [
            InteractionCreate(
                interaction_type="click",
                interaction_action="open_detail",
                movie_id="1",
                timestamp=timestamp,
                session_id="session-1",
            ),
            InteractionCreate(
                interaction_type="watch",
                interaction_action="start",
                movie_id="2",
                timestamp=timestamp,
                session_id="session-1",
            ),
            InteractionCreate(
                interaction_type="rating",
                interaction_action="submit",
                movie_id="3",
                interaction_value=4.5,
                timestamp=timestamp,
                session_id="session-1",
            ),
            InteractionCreate(
                interaction_type="reaction",
                interaction_action="like",
                movie_id="4",
                timestamp=timestamp,
                session_id="session-1",
            ),
            InteractionCreate(
                interaction_type="share",
                interaction_action="copy_link",
                movie_id="5",
                timestamp=timestamp,
                session_id="session-1",
            ),
        ]

        for index, interaction in enumerate(cases, start=1):
            with self.subTest(interaction_type=interaction.interaction_type):
                repository = RecordingRepository()
                service = InteractionService(repository=repository)
                event_id = UUID(f"00000000-0000-4000-8000-{index:012d}")

                response = service.record(
                    user_id="1",
                    username="demo",
                    event_id=event_id,
                    interaction=interaction,
                )

                self.assertEqual(len(repository.items), 1)
                stored = repository.items[0]
                self.assertEqual(stored.user_id, "1")
                self.assertEqual(
                    stored.interaction_type,
                    interaction.interaction_type,
                )
                self.assertEqual(
                    stored.interaction_action,
                    interaction.interaction_action,
                )
                self.assertEqual(stored.movie_id, interaction.movie_id)
                self.assertEqual(stored.event_id, event_id)
                self.assertEqual(
                    stored.interaction_value,
                    interaction.interaction_value,
                )
                self.assertEqual(stored.timestamp, response.timestamp)
                self.assertEqual(stored.session_id, interaction.session_id)
                self.assertEqual(
                    stored.interaction_key,
                    (
                        "2026-07-28T12:00:00.000Z"
                        f"#{response.movie_id}#{event_id}"
                    ),
                )

    def test_rating_event_requires_a_rating(self) -> None:
        with self.assertRaises(ValueError):
            InteractionCreate(
                interaction_type=InteractionType.RATING,
                interaction_action=InteractionAction.RATING_SUBMIT,
                movie_id="1",
                timestamp="2026-07-28T12:00:00Z",
                session_id="session-1",
            )

    def test_accepts_legacy_interaction_input_aliases(self) -> None:
        interaction = InteractionCreate(
            event_type="rating",
            interaction_action="submit",
            movie_id=1,
            rating=4.0,
            timestamp="2026-07-28T12:00:00Z",
            session_id="session-1",
        )

        self.assertEqual(interaction.interaction_type, InteractionType.RATING)
        self.assertEqual(interaction.movie_id, "1")
        self.assertEqual(interaction.interaction_value, 4.0)
        self.assertEqual(interaction.session_id, "session-1")

    def test_rejects_action_that_does_not_match_interaction_type(self) -> None:
        with self.assertRaises(ValueError):
            InteractionCreate(
                interaction_type="share",
                interaction_action="like",
                movie_id="1",
                timestamp="2026-07-28T12:00:00Z",
                session_id="session-1",
            )


if __name__ == "__main__":
    unittest.main()
