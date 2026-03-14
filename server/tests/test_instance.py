
import pytest
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import get_db
from app.models.ec2_instance import EC2Instance
from app.models.finding_status import FindingStatus



# ── Test DB setup ────────────────────────────────────────────────

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/rightsizer"

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def db_session():
    """Yield a real DB session; clean up test rows after."""
    session = TestingSessionLocal()
    created_ids = []

    yield session, created_ids

    for resource_id in created_ids:
        session.query(EC2Instance).filter(EC2Instance.resource_id == resource_id).delete()
    session.commit()
    session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with the DB dependency overridden."""
    session, created_ids = db_session

    def _override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    test_client = TestClient(app)
    original_post = test_client.post

    def tracked_post(*args, **kwargs):
        resp = original_post(*args, **kwargs)
        if resp.status_code == 201 and "resource_id" in resp.json():
            created_ids.append(resp.json()["resource_id"])
        return resp

    test_client.post = tracked_post

    yield test_client
    app.dependency_overrides.clear()


class TestCreateInstances:
    def test_create(self, client):

        payload = {
            "arn": "arn:aws:ec2:us-east-1:1:instances/i-abc123",
            "region": "us-east-1",
            "owner_id": 1,
            "architecture": "x86_64",
            "platform": "Linux/UNIX",
            "tenancy": "default",
            "tags": ["env:dev", "team:infra"],
        }

         
        resp = client.post("/api/instances/", json=payload)

        assert resp.status_code == 201
        body = resp.json()
        assert "resource_id" in body
        assert isinstance(body["resource_id"], int)

        for key, value in payload.items():
            assert body[key] == value, f"Mismatch on {key}: {body[key]} != {value}"

                    
class TestListInstances:
    """Tests for GET /api/instances/"""

    def _create_instance(self, client, **overrides):
        """Helper to POST an instance and return the response body."""
        defaults = {
            "arn": "arn:aws:ec2:us-east-1:1:instances/i-default",
            "region": "us-east-1",
            "owner_id": 1,
            "architecture": "x86_64",
            "platform": "Linux/UNIX",
            "tenancy": "default",
            "tags": [],
        }
        defaults.update(overrides)
        resp = client.post("/api/instances/", json=defaults)
        assert resp.status_code == 201
        return resp.json()

    # ── Filter tests ─────────────────────────────────────────────

    def test_filter_by_owner_id(self, client):
        self._create_instance(client, owner_id=111, arn="arn:aws:ec2:us-east-1:111:instances/i-aaa")
        self._create_instance(client, owner_id=222, arn="arn:aws:ec2:us-east-1:222:instances/i-bbb")
        self._create_instance(client, owner_id=111, arn="arn:aws:ec2:us-east-1:111:instances/i-ccc")

        resp = client.get("/api/instances/", params={"owner_id": 111})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        for item in body["items"]:
            assert item["owner_id"] == 111

    def test_filter_by_region(self, client):
        self._create_instance(client, region="us-east-1", arn="arn:aws:ec2:us-east-1:1:instances/i-east1")
        self._create_instance(client, region="us-west-2", arn="arn:aws:ec2:us-west-2:1:instances/i-west2")
        self._create_instance(client, region="us-east-1", arn="arn:aws:ec2:us-east-1:1:instances/i-east2")

        resp = client.get("/api/instances/", params={"region": "us-west-2"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        for item in body["items"]:
            assert item["region"] == "us-west-2"

    def test_filter_by_resource_id(self, client):
        created = self._create_instance(client, arn="arn:aws:ec2:us-east-1:1:instances/i-lookup")
        target_id = created["resource_id"]

        # create another so there's more than one row
        self._create_instance(client, arn="arn:aws:ec2:us-east-1:1:instances/i-other")

        resp = client.get("/api/instances/", params={"resource_id": target_id})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["resource_id"] == target_id

    # ── Field verification ───────────────────────────────────────

    def test_response_fields(self, client):
        payload = {
            "arn": "arn:aws:ec2:eu-west-1:999:instances/i-fields",
            "region": "eu-west-1",
            "owner_id": 999,
            "architecture": "arm64",
            "platform": "Windows",
            "tenancy": "dedicated",
            "tags": ["env:prod", "team:backend"],
        }
        created = self._create_instance(client, **payload)

        resp = client.get("/api/instances/", params={"resource_id": created["resource_id"]})
        assert resp.status_code == 200
        item = resp.json()["items"][0]

        assert isinstance(item["resource_id"], int)
        assert item["arn"] == payload["arn"]
        assert item["region"] == payload["region"]
        assert item["owner_id"] == payload["owner_id"]
        assert item["architecture"] == payload["architecture"]
        assert item["platform"] == payload["platform"]
        assert item["tenancy"] == payload["tenancy"]
        assert item["tags"] == payload["tags"]

    # ── Pagination / count ───────────────────────────────────────

    def test_item_count_and_pagination(self, client):
        for i in range(5):
            self._create_instance(
                client,
                owner_id=777,
                arn=f"arn:aws:ec2:us-east-1:777:instance/i-page{i}",
            )

        resp = client.get("/api/instances/", params={"owner_id": 777, "page_size": 2, "page": 1})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 5
        assert len(body["items"]) == 2
        assert body["page"] == 1
        assert body["page_size"] == 2

        # second page
        resp2 = client.get("/api/instances/", params={"owner_id": 777, "page_size": 2, "page": 2})
        body2 = resp2.json()
        assert len(body2["items"]) == 2
        assert body2["page"] == 2

        # no overlap between pages
        ids_page1 = {item["resource_id"] for item in body["items"]}
        ids_page2 = {item["resource_id"] for item in body2["items"]}
        assert ids_page1.isdisjoint(ids_page2)

class TestGetInstance:
    """Tests for GET /api/instances/{resource_id}"""

    def _create_instance(self, client, **overrides):
        defaults = {
            "arn": "arn:aws:ec2:us-east-1:1:instances/i-default",
            "region": "us-east-1",
            "owner_id": 1,
            "architecture": "x86_64",
            "platform": "Linux/UNIX",
            "tenancy": "default",
            "tags": [],
        }
        defaults.update(overrides)
        resp = client.post("/api/instances/", json=defaults)
        assert resp.status_code == 201
        return resp.json()

    def test_get_by_id(self, client):
        created = self._create_instance(client, arn="arn:aws:ec2:us-east-1:1:instances/i-getone")
        resource_id = created["resource_id"]

        resp = client.get(f"/api/instances/{resource_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["resource_id"] == resource_id

    def test_response_fields(self, client):
        payload = {
            "arn": "arn:aws:ec2:eu-west-1:42:instances/i-fields",
            "region": "eu-west-1",
            "owner_id": 42,
            "architecture": "arm64",
            "platform": "Windows",
            "tenancy": "dedicated",
            "tags": ["env:staging", "team:data"],
        }
        created = self._create_instance(client, **payload)

        resp = client.get(f"/api/instances/{created['resource_id']}")
        assert resp.status_code == 200
        body = resp.json()

        assert isinstance(body["resource_id"], int)
        assert body["arn"] == payload["arn"]
        assert body["region"] == payload["region"]
        assert body["owner_id"] == payload["owner_id"]
        assert body["architecture"] == payload["architecture"]
        assert body["platform"] == payload["platform"]
        assert body["tenancy"] == payload["tenancy"]
        assert body["tags"] == payload["tags"]

    def test_not_found(self, client):
        resp = client.get("/api/instances/999999999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_returns_correct_instance(self, client):
        first = self._create_instance(client, arn="arn:aws:ec2:us-east-1:1:instance/i-first", region="us-east-1")
        second = self._create_instance(client, arn="arn:aws:ec2:us-west-2:1:instances/i-second", region="us-west-2")

        resp = client.get(f"/api/instances/{second['resource_id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["resource_id"] == second["resource_id"]
        assert body["region"] == "us-west-2"
        assert body["resource_id"] != first["resource_id"]



class TestUpsertInstance:
    """Tests for upsert behavior on POST /api/instances/"""

    def test_duplicate_arn_updates_instead_of_duplicating(self, client):
        payload = {
            "arn": "arn:aws:ec2:us-east-1:1:instance/i-upsert",
            "region": "us-east-1",
            "owner_id": 1,
            "architecture": "x86_64",
            "platform": "Linux/UNIX",
            "tenancy": "default",
            "tags": ["env:dev"],
        }
        first = client.post("/api/instances/", json=payload)
        assert first.status_code == 201
        original_id = first.json()["resource_id"]

        # same ARN, different fields
        payload["region"] = "us-west-2"
        payload["architecture"] = "arm64"
        payload["tags"] = ["env:prod"]
        second = client.post("/api/instances/", json=payload)
        assert second.status_code == 201

        body = second.json()
        assert body["resource_id"] == original_id
        assert body["region"] == "us-west-2"
        assert body["architecture"] == "arm64"
        assert body["tags"] == ["env:prod"]

    def test_different_arns_create_separate_rows(self, client):
        base = {
            "region": "us-east-1",
            "owner_id": 1,
            "architecture": "x86_64",
            "platform": "Linux/UNIX",
            "tenancy": "default",
            "tags": [],
        }
        first = client.post("/api/instances/", json={**base, "arn": "arn:aws:ec2:us-east-1:1:instance/i-aaa"})
        second = client.post("/api/instances/", json={**base, "arn": "arn:aws:ec2:us-east-1:1:instance/i-bbb"})

        assert first.json()["resource_id"] != second.json()["resource_id"]