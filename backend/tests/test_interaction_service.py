import unittest
from typing import Any

from app.schemas.interaction import InteractionCreate, InteractionEventType
from app.services.interaction_service import InteractionService


class RecordingRepository:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    def put_item(self, item: dict[str, Any]) -> dict[str, Any]:
        self.items.append(item)
        return item


class InteractionServiceTests(unittest.TestCase):
    def test_records_every_supported_interaction(self) -> None:
        cases = [
            InteractionCreate(event_type="click", movie_id=1),
            InteractionCreate(event_type="watch", movie_id=2),
            InteractionCreate(event_type="rating", movie_id=3, rating=4.5),
        ]

        for interaction in cases:
            with self.subTest(event_type=interaction.event_type):
                repository = RecordingRepository()
                service = InteractionService(repository=repository)

                response = service.record(
                    user_id=1,
                    username="demo",
                    interaction=interaction,
                )

                self.assertEqual(len(repository.items), 1)
                stored = repository.items[0]
                self.assertEqual(stored["user_id"], "1")
                self.assertEqual(stored["username"], "demo")
                self.assertEqual(stored["event_type"], interaction.event_type.value)
                self.assertEqual(stored["movie_id"], interaction.movie_id)
                self.assertEqual(stored["rating"], interaction.rating)
                self.assertEqual(stored["event_id"], response.event_id)
                self.assertEqual(stored["created_at"], response.created_at)
                self.assertEqual(
                    stored["interaction_key"],
                    f"{response.created_at}#{response.event_id}",
                )

    def test_rating_event_requires_a_rating(self) -> None:
        with self.assertRaises(ValueError):
            InteractionCreate(
                event_type=InteractionEventType.RATING,
                movie_id=1,
            )


if __name__ == "__main__":
    unittest.main()
