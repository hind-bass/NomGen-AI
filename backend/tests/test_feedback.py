"""
Tests du système de feedback (generations, feedback, favoris).
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models.feedback_models import Favori, Feedback, Generation

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session():
    with Session(TEST_ENGINE) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    SQLModel.metadata.create_all(TEST_ENGINE)
    yield
    SQLModel.metadata.drop_all(TEST_ENGINE)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture
def sample_generation(client):
    """Insère une génération de test directement en base."""
    with Session(TEST_ENGINE) as session:
        gen = Generation(
            prompt="test marque luxe",
            langue="fr",
            categorie="LUXE",
            type_nom="marque",
            nom_genere="TestLux",
            score=80.0,
            mode="A",
        )
        session.add(gen)
        session.commit()
        session.refresh(gen)
        return gen.id


class TestFeedbackEndpoints:

    def test_like_generation(self, client, sample_generation):
        resp = client.post("/feedback/like", json={"generation_id": sample_generation})
        assert resp.status_code == 200
        data = resp.json()
        assert data["vote_type"] == "like"
        assert data["likes"] == 1
        assert data["score"] == 1

    def test_dislike_generation(self, client, sample_generation):
        client.post("/feedback/like", json={"generation_id": sample_generation})
        resp = client.post("/feedback/dislike", json={"generation_id": sample_generation})
        assert resp.status_code == 200
        data = resp.json()
        assert data["vote_type"] == "dislike"
        assert data["dislikes"] >= 1

    def test_like_invalid_generation(self, client):
        resp = client.post("/feedback/like", json={"generation_id": 99999})
        assert resp.status_code == 404

    def test_like_invalid_id_zero(self, client):
        resp = client.post("/feedback/like", json={"generation_id": 0})
        assert resp.status_code == 422

    def test_feedback_stats(self, client, sample_generation):
        client.post("/feedback/like", json={"generation_id": sample_generation})
        resp = client.get("/feedback/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_generations"] >= 1
        assert data["total_likes"] >= 1
        assert "plus_apprecies" in data
        assert "plus_rejetes" in data


class TestFavorisEndpoints:

    def test_add_favori(self, client, sample_generation):
        resp = client.post("/favorites/add", json={"generation_id": sample_generation})
        assert resp.status_code == 201
        data = resp.json()
        assert data["nom"] == "TestLux"
        assert data["generation_id"] == sample_generation

    def test_add_favori_duplicate(self, client, sample_generation):
        client.post("/favorites/add", json={"generation_id": sample_generation})
        resp = client.post("/favorites/add", json={"generation_id": sample_generation})
        assert resp.status_code == 409

    def test_list_favoris(self, client, sample_generation):
        client.post("/favorites/add", json={"generation_id": sample_generation})
        resp = client.get("/favorites")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestFeedbackService:

    def test_score_calculation(self, client, sample_generation):
        client.post("/feedback/like", json={"generation_id": sample_generation})
        client.post("/feedback/like", json={"generation_id": sample_generation})
        resp = client.get("/feedback/stats?top_n=10")
        data = resp.json()
        assert data["score_global"] >= 1

    def test_most_liked_in_stats(self, client):
        with Session(TEST_ENGINE) as session:
            gen = Generation(
                prompt="popular name",
                langue="fr",
                categorie="TECH",
                type_nom="marque",
                nom_genere="TopName",
                score=90.0,
                mode="B",
            )
            session.add(gen)
            session.commit()
            session.refresh(gen)
            gen_id = gen.id
            for _ in range(3):
                session.add(Feedback(generation_id=gen_id, vote_type="like"))
            session.commit()

        resp = client.get("/feedback/stats")
        data = resp.json()
        top = data["plus_apprecies"]
        assert any(item["nom_genere"] == "TopName" for item in top)
