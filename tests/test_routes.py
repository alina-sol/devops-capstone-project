import logging
import os
from unittest import TestCase
from service.models import db, Account
from service.common import status  # HTTP status codes
from service.routes import app
from tests.factories import AccountFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""
        db.session.remove()
        db.drop_all()

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # Clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()

    def _create_account(self, name, email):
        """Helper method to create a single account"""
        response = self.client.post(
            BASE_URL,
            json={"name": name, "email": email},
            content_type="application/json"
        )
        return response

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should create a new Account"""
        response = self._create_account("John Doe", "john.doe@example.com")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Ensure the response contains the location header
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        new_account = response.get_json()
        self.assertEqual(new_account["name"], "John Doe")
        self.assertEqual(new_account["email"], "john.doe@example.com")

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "Incomplete"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        response = self.client.post(
            BASE_URL,
            json={"name": "John Doe", "email": "john.doe@example.com"},
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_account(self):
        """It should retrieve an account"""
        account = AccountFactory(name="Jane Doe", email="jane.doe@example.com")
        db.session.add(account)
        db.session.commit()

        response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["name"], "Jane Doe")

    def test_get_account_not_found(self):
        """It should not retrieve an account that doesn't exist"""
        response = self.client.get(f"{BASE_URL}/999999")  # Non-existent account
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
