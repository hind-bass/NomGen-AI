import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.seeder import seed_admin

# ─── Base de données en mémoire pour les tests ───────────────────────────────

TEST_ENGINE = create_engine(
    "sqlite://",                          # SQLite en mémoire
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session():
    with Session(TEST_ENGINE) as session:
        yield session


# Surcharge de la dépendance DB pour les tests
app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Crée les tables + l'admin avant tous les tests."""
    SQLModel.metadata.create_all(TEST_ENGINE)
    with Session(TEST_ENGINE) as session:
        from app.models.db_models import User
        from app.services.auth_service import hash_password
        admin = User(
            email="admin@nomgen.ai",
            hashed_password=hash_password("admin123456"),
            role="admin",
        )
        session.add(admin)
        session.commit()
    yield
    SQLModel.metadata.drop_all(TEST_ENGINE)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def register_and_login(client, email="test@nomgen.ai", password="Test123456"):
    """Inscrit un utilisateur et retourne son token JWT."""
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login échoué: {resp.text}"
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def admin_token(client):
    resp = client.post("/auth/login",
                       json={"email": "admin@nomgen.ai", "password": "admin123456"})
    return resp.json()["access_token"]


# ═══════════════════════════════════════════════════════════════════════════════
# BLOC 1 — Authentification (5 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuth:

    def test_register_success(self, client):
        """Test : inscription réussie."""
        resp = client.post("/auth/register",
                           json={"email": "newuser@test.ai", "password": "Pass1234"})
        assert resp.status_code == 201
        assert "email" in resp.json()

    def test_register_duplicate_email(self, client):
        """Test : email déjà utilisé → 409."""
        data = {"email": "dup@test.ai", "password": "Pass1234"}
        client.post("/auth/register", json=data)
        resp = client.post("/auth/register", json=data)
        assert resp.status_code == 409

    def test_register_short_password(self, client):
        """Test : mot de passe trop court → 422."""
        resp = client.post("/auth/register",
                           json={"email": "short@test.ai", "password": "123"})
        assert resp.status_code == 422

    def test_login_success(self, client):
        """Test : connexion réussie — retourne token."""
        client.post("/auth/register",
                    json={"email": "login@test.ai", "password": "Pass1234"})
        resp = client.post("/auth/login",
                           json={"email": "login@test.ai", "password": "Pass1234"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "user"

    def test_login_wrong_password(self, client):
        """Test : mauvais mot de passe → 401."""
        client.post("/auth/register",
                    json={"email": "wrongpw@test.ai", "password": "Pass1234"})
        resp = client.post("/auth/login",
                           json={"email": "wrongpw@test.ai", "password": "WRONG"})
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# BLOC 2 — Génération Mode A nanoGPT (3 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerate:

    def test_generate_fr_basic(self, client):
        """Test : génération FR basique — retourne des noms."""
        resp = client.post("/api/generate", json={
            "prompt": "startup technologique innovante",
            "secteur": "TECH",
            "langue": "fr",
            "n": 5,
            "temperature": 0.9,
            "top_k": 20,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "noms" in data
        assert "duree_ms" in data

    def test_generate_ar_basic(self, client):
        """Test : génération AR — retourne une réponse valide."""
        resp = client.post("/api/generate", json={
            "prompt": "شركة تقنية في الرياض",
            "secteur": "TECH",
            "langue": "ar",
            "n": 5,
            "temperature": 0.9,
            "top_k": 20,
        })
        assert resp.status_code == 200

    def test_generate_incoherent_prompt(self, client):
        """Test : prompt incohérent → liste vide (pas d'erreur)."""
        resp = client.post("/api/generate", json={
            "prompt": "aaaa",          # trop court / sans espace
            "secteur": "TECH",
            "langue": "fr",
            "n": 5,
            "temperature": 1.0,
            "top_k": 20,
        })
        assert resp.status_code == 200
        assert resp.json()["noms"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# BLOC 3 — Favoris persistants (4 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFavorites:

    def test_add_favorite(self, client):
        """Test : ajout d'un favori."""
        token = register_and_login(client, "fav@test.ai")
        resp = client.post("/api/favorites/",
                           json={"nom": "Lumora", "score": 82.0,
                                 "langue": "fr", "secteur": "LUXE"},
                           headers=auth_headers(token))
        assert resp.status_code == 201
        assert resp.json()["nom"] == "Lumora"

    def test_add_favorite_duplicate(self, client):
        """Test : doublon favori → 409."""
        token = register_and_login(client, "fav2@test.ai")
        data  = {"nom": "TechAI", "score": 75.0, "langue": "fr", "secteur": "TECH"}
        client.post("/api/favorites/", json=data, headers=auth_headers(token))
        resp = client.post("/api/favorites/", json=data, headers=auth_headers(token))
        assert resp.status_code == 409

    def test_get_favorites(self, client):
        """Test : récupérer la liste des favoris."""
        token = register_and_login(client, "fav3@test.ai")
        client.post("/api/favorites/",
                    json={"nom": "Veloria", "score": 78.0,
                          "langue": "fr", "secteur": "LUXE"},
                    headers=auth_headers(token))
        resp = client.get("/api/favorites/", headers=auth_headers(token))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_delete_favorite(self, client):
        """Test : suppression d'un favori."""
        token = register_and_login(client, "fav4@test.ai")
        add_resp = client.post("/api/favorites/",
                               json={"nom": "Nexoria", "score": 70.0,
                                     "langue": "fr", "secteur": "TECH"},
                               headers=auth_headers(token))
        fav_id = add_resp.json()["id"]
        del_resp = client.delete(f"/api/favorites/{fav_id}",
                                 headers=auth_headers(token))
        assert del_resp.status_code == 204


# ═══════════════════════════════════════════════════════════════════════════════
# BLOC 4 — Suggestions communautaires (5 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSuggestions:

    def test_submit_suggestion(self, client):
        """Test : soumission d'une suggestion."""
        token = register_and_login(client, "sugg@test.ai")
        resp = client.post("/api/suggestions/",
                           json={"nom": "Zephyra", "categorie": "tech",
                                 "langue": "fr", "type_nom": "marque"},
                           headers=auth_headers(token))
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"

    def test_submit_suggestion_too_short(self, client):
        """Test : nom trop court → 422."""
        token = register_and_login(client, "sugg2@test.ai")
        resp = client.post("/api/suggestions/",
                           json={"nom": "X", "categorie": "tech",
                                 "langue": "fr", "type_nom": "marque"},
                           headers=auth_headers(token))
        assert resp.status_code == 422

    def test_approve_suggestion(self, client):
        """Test : approbation par admin → statut 'approved'."""
        user_token  = register_and_login(client, "sugg3@test.ai")
        admin_tok   = admin_token(client)

        # Soumettre
        add_resp = client.post("/api/suggestions/",
                               json={"nom": "Approvator", "categorie": "general",
                                     "langue": "fr", "type_nom": "marque"},
                               headers=auth_headers(user_token))
        sugg_id = add_resp.json()["id"]

        # Approuver
        approve_resp = client.patch(f"/api/suggestions/{sugg_id}/approve",
                                    headers=auth_headers(admin_tok))
        assert approve_resp.status_code == 200
        assert "approuvé" in approve_resp.json()["message"].lower()

    def test_reject_suggestion(self, client):
        """Test : rejet par admin → statut 'rejected'."""
        user_token = register_and_login(client, "sugg4@test.ai")
        admin_tok  = admin_token(client)

        add_resp = client.post("/api/suggestions/",
                               json={"nom": "Rejector", "categorie": "general",
                                     "langue": "fr", "type_nom": "marque"},
                               headers=auth_headers(user_token))
        sugg_id = add_resp.json()["id"]

        reject_resp = client.patch(f"/api/suggestions/{sugg_id}/reject",
                                   headers=auth_headers(admin_tok))
        assert reject_resp.status_code == 200
        assert "rejeté" in reject_resp.json()["message"].lower()

    def test_non_admin_cannot_approve(self, client):
        """Test : user normal ne peut pas approuver → 403."""
        user_token = register_and_login(client, "sugg5@test.ai")
        add_resp = client.post("/api/suggestions/",
                               json={"nom": "BlockedApprove", "categorie": "general",
                                     "langue": "fr", "type_nom": "marque"},
                               headers=auth_headers(user_token))
        sugg_id = add_resp.json()["id"]
        resp = client.patch(f"/api/suggestions/{sugg_id}/approve",
                            headers=auth_headers(user_token))
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# BLOC 5 — Réservations (3 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestReservations:

    def test_create_reservation(self, client):
        """Test : créer une réservation."""
        token = register_and_login(client, "resa@test.ai")
        resp  = client.post("/api/reservations/",
                            json={"nom": "LuxeLabel", "langue": "fr", "secteur": "LUXE"},
                            headers=auth_headers(token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["nom"] == "LuxeLabel"
        assert data["is_paid"] == False
        assert "stripe_url" in data

    def test_get_reservations(self, client):
        """Test : lister ses réservations."""
        token = register_and_login(client, "resa2@test.ai")
        client.post("/api/reservations/",
                    json={"nom": "TechBrand", "langue": "fr", "secteur": "TECH"},
                    headers=auth_headers(token))
        resp = client.get("/api/reservations/", headers=auth_headers(token))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_delete_reservation(self, client):
        """Test : annuler une réservation non payée."""
        token = register_and_login(client, "resa3@test.ai")
        add_resp = client.post("/api/reservations/",
                               json={"nom": "FoodName", "langue": "fr", "secteur": "FOOD"},
                               headers=auth_headers(token))
        resa_id = add_resp.json()["id"]
        del_resp = client.delete(f"/api/reservations/{resa_id}",
                                 headers=auth_headers(token))
        assert del_resp.status_code == 204


# ═══════════════════════════════════════════════════════════════════════════════
# BLOC 5b — Admin Réservations (4 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminReservations:

    def test_admin_list_reservations(self, client):
        """Test : admin peut lister toutes les réservations."""
        user_token = register_and_login(client, "adminresa_user@test.ai")
        client.post(
            "/api/reservations/",
            json={"nom": "AdminTestName", "langue": "fr", "secteur": "TECH"},
            headers=auth_headers(user_token),
        )
        admin_tok = admin_token(client)
        resp = client.get("/api/admin/reservations", headers=auth_headers(admin_tok))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any(r["nom"] == "AdminTestName" for r in data)

    def test_admin_reservation_stats(self, client):
        """Test : statistiques des réservations."""
        admin_tok = admin_token(client)
        resp = client.get("/api/admin/reservations/stats", headers=auth_headers(admin_tok))
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "pending" in data
        assert "paid" in data
        assert "expired" in data

    def test_admin_mark_paid(self, client):
        """Test : admin marque une réservation comme payée."""
        user_token = register_and_login(client, "adminresa_pay@test.ai")
        add_resp = client.post(
            "/api/reservations/",
            json={"nom": "PayTestName", "langue": "fr", "secteur": "LUXE"},
            headers=auth_headers(user_token),
        )
        resa_id = add_resp.json()["id"]
        admin_tok = admin_token(client)
        resp = client.patch(
            f"/api/admin/reservations/{resa_id}",
            json={"action": "mark_paid"},
            headers=auth_headers(admin_tok),
        )
        assert resp.status_code == 200
        assert resp.json()["is_paid"] is True
        assert resp.json()["status"] == "paid"

    def test_admin_reservations_forbidden_for_user(self, client):
        """Test : un utilisateur normal ne peut pas accéder aux réservations admin."""
        user_token = register_and_login(client, "adminresa_forbidden@test.ai")
        resp = client.get("/api/admin/reservations", headers=auth_headers(user_token))
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# BLOC 6 — Profil & Santé (2 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestProfileAndHealth:

    def test_get_profile(self, client):
        """Test : profil retourne les bonnes clés."""
        token = register_and_login(client, "profile@test.ai")
        resp  = client.get("/api/profile/", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "email" in data
        assert "nb_generations" in data
        assert "nb_favoris" in data
        assert "nb_suggestions" in data

    def test_health_check(self, client):
        """Test : endpoint /api/health retourne status ok."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"




        