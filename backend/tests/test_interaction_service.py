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

    def list_by_user(self, user_id: str) -> list[UserInteraction]:
        return [item for item in self.items if item.user_id == user_id]


class InteractionServiceTests(unittest.TestCase):
    def test_records_every_supported_interaction(self) -> None:
        timestamp = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)
        cases = [
            InteractionCreate(
                interaction_type="click",
                interaction_action="record",
                movie_id="1",
                interaction_value=1,
                timestamp=timestamp,
                session_id="session-1",
            ),
            InteractionCreate(
                interaction_type="watch",
                interaction_action="record",
                movie_id="2",
                interaction_value=0.6,
                timestamp=timestamp,
                session_id="session-1",
            ),
            InteractionCreate(
                interaction_type="rating",
                interaction_action="set",
                movie_id="3",
                interaction_value=4.5,
                timestamp=timestamp,
                session_id="session-1",
            ),
            InteractionCreate(
                interaction_type="reaction",
                interaction_action="set",
                movie_id="4",
                interaction_value=1,
                timestamp=timestamp,
                session_id="session-1",
            ),
            InteractionCreate(
                interaction_type="share",
                interaction_action="record",
                movie_id="5",
                interaction_value=1,
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
                interaction_action=InteractionAction.SET,
                movie_id="1",
                timestamp="2026-07-28T12:00:00Z",
                session_id="session-1",
            )

    def test_accepts_legacy_interaction_input_aliases(self) -> None:
        interaction = InteractionCreate(
            event_type="rating",
            interaction_action="set",
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
                interaction_action="set",
                movie_id="1",
                interaction_value=1,
                timestamp="2026-07-28T12:00:00Z",
                session_id="session-1",
            )

    def test_reaction_set_and_clear_values(self) -> None:
        like = InteractionCreate(
            interaction_type="reaction",
            interaction_action="set",
            interaction_value=1,
            movie_id="1",
            timestamp="2026-07-28T12:00:00Z",
            session_id="session-1",
        )
        dislike = InteractionCreate(
            interaction_type="reaction",
            interaction_action="set",
            interaction_value=-1,
            movie_id="1",
            timestamp="2026-07-28T12:00:00Z",
            session_id="session-1",
        )
        cleared = InteractionCreate(
            interaction_type="reaction",
            interaction_action="clear",
            interaction_value=0,
            movie_id="1",
            timestamp="2026-07-28T12:00:00Z",
            session_id="session-1",
        )

        self.assertEqual(like.interaction_value, 1)
        self.assertEqual(dislike.interaction_value, -1)
        self.assertEqual(cleared.interaction_value, 0)

        with self.assertRaises(ValueError):
            InteractionCreate(
                interaction_type="reaction",
                interaction_action="clear",
                interaction_value=1,
                movie_id="1",
                timestamp="2026-07-28T12:00:00Z",
                session_id="session-1",
            )

    def test_rejects_noncanonical_interaction_values(self) -> None:
        cases = [
            ("click", "record", 0),
            ("watch", "record", 1.1),
            ("share", "record", 0),
            ("rating", "clear", 1),
            ("rating", "set", 3.7),
            ("reaction", "set", 0),
        ]

        for interaction_type, interaction_action, value in cases:
            with self.subTest(
                interaction_type=interaction_type,
                interaction_action=interaction_action,
            ):
                with self.assertRaises(ValueError):
                    InteractionCreate(
                        interaction_type=interaction_type,
                        interaction_action=interaction_action,
                        interaction_value=value,
                        movie_id="1",
                        timestamp="2026-07-28T12:00:00Z",
                        session_id="session-1",
                    )

    def test_returns_latest_rating_for_movie(self) -> None:
        repository = RecordingRepository()
        service = InteractionService(repository=repository)
        ratings = [
            ("2026-07-28T12:00:00Z", 2.0, "00000000-0000-4000-8000-000000000001"),
            ("2026-07-28T13:00:00Z", 4.0, "00000000-0000-4000-8000-000000000002"),
        ]
        for timestamp, rating, event_id_text in ratings:
            interaction = InteractionCreate(
                interaction_type="rating",
                interaction_action="set",
                movie_id="movie-1",
                interaction_value=rating,
                timestamp=timestamp,
                session_id="session-1",
            )
            service.record(
                user_id="user-1",
                username="viewer",
                event_id=UUID(event_id_text),
                interaction=interaction,
            )

        repository.items.append(
            UserInteraction(
                user_id="user-1",
                interaction_key=(
                    "2026-07-28T14:00:00.000Z#movie-2"
                    "#00000000-0000-4000-8000-000000000003"
                ),
                event_id=UUID("00000000-0000-4000-8000-000000000003"),
                movie_id="movie-2",
                interaction_type=InteractionType.RATING,
                interaction_action=InteractionAction.RATING_SUBMIT,
                interaction_value=5.0,
                timestamp="2026-07-28T14:00:00Z",
                session_id="session-1",
            )
        )

        response = service.get_latest_rating(
            user_id="user-1",
            movie_id="movie-1",
        )

        self.assertEqual(response.movie_id, "movie-1")
        self.assertEqual(response.rating, 4.0)

        service.record(
            user_id="user-1",
            username="viewer",
            event_id=UUID("00000000-0000-4000-8000-000000000004"),
            interaction=InteractionCreate(
                interaction_type="rating",
                interaction_action="clear",
                movie_id="movie-1",
                interaction_value=0,
                timestamp="2026-07-28T15:00:00Z",
                session_id="session-1",
            ),
        )

        self.assertIsNone(
            service.get_latest_rating(
                user_id="user-1",
                movie_id="movie-1",
            ).rating
        )

    def test_returns_latest_reaction_and_honors_clear(self) -> None:
        repository = RecordingRepository()
        service = InteractionService(repository=repository)
        service.record(
            user_id="user-1",
            username="viewer",
            event_id=UUID("00000000-0000-4000-8000-000000000005"),
            interaction=InteractionCreate(
                interaction_type="reaction",
                interaction_action="set",
                movie_id="movie-1",
                interaction_value=-1,
                timestamp="2026-07-28T12:00:00Z",
                session_id="session-1",
            ),
        )

        self.assertEqual(
            service.get_latest_reaction(
                user_id="user-1",
                movie_id="movie-1",
            ).reaction,
            "dislike",
        )

        service.record(
            user_id="user-1",
            username="viewer",
            event_id=UUID("00000000-0000-4000-8000-000000000006"),
            interaction=InteractionCreate(
                interaction_type="reaction",
                interaction_action="clear",
                movie_id="movie-1",
                interaction_value=0,
                timestamp="2026-07-28T13:00:00Z",
                session_id="session-1",
            ),
        )

        self.assertIsNone(
            service.get_latest_reaction(
                user_id="user-1",
                movie_id="movie-1",
            ).reaction
        )

    def test_returns_empty_rating_when_user_has_not_rated_movie(self) -> None:
        service = InteractionService(repository=RecordingRepository())

        response = service.get_latest_rating(
            user_id="user-1",
            movie_id="movie-1",
        )

        self.assertEqual(response.movie_id, "movie-1")
        self.assertIsNone(response.rating)


if __name__ == "__main__":
    unittest.main()
