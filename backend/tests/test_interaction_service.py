import unittest

from app.models.user_interaction import InteractionType, UserInteraction
from app.schemas.interaction import InteractionCreate
from app.services.interaction_service import InteractionService


class RecordingRepository:
    def __init__(self) -> None:
        self.items: list[UserInteraction] = []

    def put_item(self, item: UserInteraction) -> UserInteraction:
        self.items.append(item)
        return item


class InteractionServiceTests(unittest.TestCase):
    def test_records_every_supported_interaction(self) -> None:
        cases = [
            InteractionCreate(
                interaction_type="click",
                movie_id="1",
                session_id="session-1",
            ),
            InteractionCreate(
                interaction_type="watch",
                movie_id="2",
                session_id="session-1",
            ),
            InteractionCreate(
                interaction_type="rating",
                movie_id="3",
                interaction_value=4.5,
                session_id="session-1",
            ),
        ]

        for interaction in cases:
            with self.subTest(interaction_type=interaction.interaction_type):
                repository = RecordingRepository()
                service = InteractionService(repository=repository)

                response = service.record(
                    user_id="1",
                    username="demo",
                    interaction=interaction,
                )

                self.assertEqual(len(repository.items), 1)
                stored = repository.items[0]
                self.assertEqual(stored.user_id, "1")
                self.assertEqual(
                    stored.interaction_type,
                    interaction.interaction_type,
                )
                self.assertEqual(stored.movie_id, interaction.movie_id)
                self.assertEqual(
                    stored.interaction_value,
                    interaction.interaction_value,
                )
                self.assertEqual(stored.timestamp, response.timestamp)
                self.assertEqual(stored.session_id, interaction.session_id)
                self.assertEqual(
                    stored.interaction_key,
                    (
                        f"{response.timestamp.isoformat().replace('+00:00', 'Z')}"
                        f"#{response.movie_id}"
                    ),
                )

    def test_rating_event_requires_a_rating(self) -> None:
        with self.assertRaises(ValueError):
            InteractionCreate(
                interaction_type=InteractionType.RATING,
                movie_id="1",
            )

    def test_accepts_legacy_interaction_input_aliases(self) -> None:
        interaction = InteractionCreate(
            event_type="rating",
            movie_id=1,
            rating=4.0,
        )

        self.assertEqual(interaction.interaction_type, InteractionType.RATING)
        self.assertEqual(interaction.movie_id, "1")
        self.assertEqual(interaction.interaction_value, 4.0)
        self.assertEqual(interaction.session_id, "legacy-session")


if __name__ == "__main__":
    unittest.main()
