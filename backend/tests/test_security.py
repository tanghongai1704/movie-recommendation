import unittest

from app.core.security import JWTService, PasswordHasher, TokenValidationError


class PasswordHasherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hasher = PasswordHasher(iterations=10_000)

    def test_hashes_use_unique_salts_and_verify(self) -> None:
        first = self.hasher.hash_password("correct horse battery staple")
        second = self.hasher.hash_password("correct horse battery staple")

        self.assertNotEqual(first, second)
        self.assertTrue(
            self.hasher.verify_password(
                "correct horse battery staple",
                first,
            )
        )
        self.assertFalse(self.hasher.verify_password("wrong password", first))
        self.assertNotIn("correct horse battery staple", first)


class JWTServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = JWTService(
            secret="test-secret-with-at-least-thirty-two-bytes",
            issuer="test-issuer",
            audience="test-audience",
            access_token_minutes=5,
        )

    def test_issues_and_validates_access_token(self) -> None:
        issued = self.service.issue_access_token("user-1")
        claims = self.service.decode_access_token(issued.token)

        self.assertEqual(claims.user_id, "user-1")
        self.assertTrue(claims.token_id)
        self.assertEqual(issued.expires_in, 300)
        self.assertGreater(claims.expires_at, claims.issued_at)

    def test_rejects_tampered_token(self) -> None:
        issued = self.service.issue_access_token("user-1")
        header, payload, signature = issued.token.split(".")
        replacement = "a" if signature[0] != "a" else "b"
        tampered = f"{header}.{payload}.{replacement}{signature[1:]}"

        with self.assertRaises(TokenValidationError):
            self.service.decode_access_token(tampered)

    def test_rejects_token_for_another_audience(self) -> None:
        issued = self.service.issue_access_token("user-1")
        other_service = JWTService(
            secret="test-secret-with-at-least-thirty-two-bytes",
            issuer="test-issuer",
            audience="other-audience",
            access_token_minutes=5,
        )

        with self.assertRaises(TokenValidationError):
            other_service.decode_access_token(issued.token)


if __name__ == "__main__":
    unittest.main()
