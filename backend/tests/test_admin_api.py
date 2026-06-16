#!/usr/bin/env python3
"""
Script de demonstration des routes Admin API.
Exemples complets pour creer, lister et gerer les utilisateurs et suggestions.
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"


class AdminAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.admin_token: Optional[str] = None
        self.user_token: Optional[str] = None

    def _print_response(self, title: str, response):
        """Affiche une reponse formatee."""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print(f"Response: {response.text}")

    def setup_accounts(self):
        """Cree un compte user pour les tests et se connecte avec l'admin existant."""
        print("\n[SETUP] Creation des comptes de test...")

        # Utiliser l'admin par defaut (cree par seeder)
        admin_data = {
            "email": "admin@nomgen.ai",
            "password": "admin123456"
        }
        login_resp = requests.post(f"{self.base_url}/auth/login", json=admin_data)
        if login_resp.status_code == 200:
            self.admin_token = login_resp.json()["access_token"]
            print(f"[OK] Token Admin obtenu (admin@nomgen.ai)")
        else:
            print(f"[ERREUR] Impossible de se connecter avec l'admin par defaut")
            print(f"Response: {login_resp.json()}")

        # Creer un compte user
        user_data = {
            "email": "user@test.com",
            "password": "user123"
        }
        resp = requests.post(f"{self.base_url}/auth/register", json=user_data)
        if resp.status_code == 201:
            print(f"[OK] User enregistre")

        # Se connecter en tant qu'user
        login_resp = requests.post(f"{self.base_url}/auth/login", json=user_data)
        if login_resp.status_code == 200:
            self.user_token = login_resp.json()["access_token"]
            print(f"[OK] Token User obtenu")

    def test_user_management(self):
        """Teste la creation et la gestion des utilisateurs."""
        print("\n\n[TEST 1] Gestion des Utilisateurs")
        print("=" * 60)

        if not self.admin_token:
            print("[ERREUR] Token admin non disponible")
            return

        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Creer un nouvel utilisateur
        new_user = {
            "email": "newuser@test.com",
            "password": "pass123",
            "role": "user",
            "is_active": True
        }
        resp = requests.post(
            f"{self.base_url}/api/admin/users",
            json=new_user,
            headers=headers
        )
        self._print_response("[1] POST /api/admin/users (creer utilisateur)", resp)

        if resp.status_code == 201:
            user_id = resp.json()["id"]

            # Lister tous les utilisateurs
            resp = requests.get(
                f"{self.base_url}/api/admin/users",
                headers=headers
            )
            self._print_response("[2] GET /api/admin/users (lister utilisateurs)", resp)

            # Modifier le role d'un utilisateur
            update_data = {
                "role": "admin",
                "is_active": True
            }
            resp = requests.patch(
                f"{self.base_url}/api/admin/users/{user_id}",
                json=update_data,
                headers=headers
            )
            self._print_response(f"[3] PATCH /api/admin/users/{user_id} (promouvoir en admin)", resp)

            # Desactiver un utilisateur
            update_data = {
                "is_active": False
            }
            resp = requests.patch(
                f"{self.base_url}/api/admin/users/{user_id}",
                json=update_data,
                headers=headers
            )
            self._print_response(f"[4] PATCH /api/admin/users/{user_id} (desactiver)", resp)

    def test_suggestion_direct_add(self):
        """Teste l'ajout direct de suggestions par l'admin."""
        print("\n\n[TEST 2] Ajout Direct de Suggestions (Admin)")
        print("=" * 60)

        if not self.admin_token:
            print("[ERREUR] Token admin non disponible")
            return

        headers = {"Authorization": f"Bearer {self.admin_token}"}

        suggestions = [
            {
                "nom": "Luxora",
                "langue": "fr",
                "secteur": "LUXE",
                "type_nom": "marque"
            },
            {
                "nom": "TechNova",
                "langue": "fr",
                "secteur": "TECH",
                "type_nom": "marque"
            },
            {
                "nom": "EcoSmart",
                "langue": "fr",
                "secteur": "GENERAL",
                "type_nom": "societe"
            }
        ]

        for i, suggestion in enumerate(suggestions, 1):
            resp = requests.post(
                f"{self.base_url}/api/admin/suggestions/add",
                json=suggestion,
                headers=headers
            )
            self._print_response(
                f"[{i}] POST /api/admin/suggestions/add ({suggestion['nom']})",
                resp
            )

        # Tenter d'ajouter un doublon
        print("\n[TEST] Verification de Doublon:")
        duplicate = {
            "nom": "Luxora",  # Meme nom
            "langue": "fr",
            "secteur": "LUXE",
            "type_nom": "marque"
        }
        resp = requests.post(
            f"{self.base_url}/api/admin/suggestions/add",
            json=duplicate,
            headers=headers
        )
        self._print_response("[ERREUR ATTENDUE] Tentative d'ajout d'un doublon (doit echouer)", resp)

    def test_suggestion_moderation(self):
        """Teste le processus de moderation des suggestions."""
        print("\n\n[TEST 3] Moderation des Suggestions")
        print("=" * 60)

        if not self.user_token or not self.admin_token:
            print("[ERREUR] Tokens non disponibles")
            return

        user_headers = {"Authorization": f"Bearer {self.user_token}"}
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

        # User soumet une suggestion
        submission = {
            "nom": "BrandNex",
            "langue": "fr",
            "categorie": "TECH",
            "type_nom": "marque"
        }
        resp = requests.post(
            f"{self.base_url}/api/suggestions",
            json=submission,
            headers=user_headers
        )
        self._print_response("[1] User soumet une suggestion", resp)

        if resp.status_code == 201:
            suggestion_id = resp.json()["id"]

            # Admin liste les suggestions en attente
            resp = requests.get(
                f"{self.base_url}/api/admin/suggestions?status_filter=pending",
                headers=admin_headers
            )
            self._print_response("[2] Admin liste les suggestions (pending)", resp)

            # Admin approuve la suggestion
            approval = {"action": "approve"}
            resp = requests.patch(
                f"{self.base_url}/api/admin/suggestions/{suggestion_id}",
                json=approval,
                headers=admin_headers
            )
            self._print_response("[3] Admin approuve la suggestion", resp)

        # User soumet une autre suggestion pour test de rejet
        submission2 = {
            "nom": "SpamBrand",
            "langue": "fr",
            "categorie": "GENERAL",
            "type_nom": "marque"
        }
        resp = requests.post(
            f"{self.base_url}/api/suggestions",
            json=submission2,
            headers=user_headers
        )

        if resp.status_code == 201:
            suggestion_id = resp.json()["id"]

            # Admin rejette la suggestion
            rejection = {"action": "reject"}
            resp = requests.patch(
                f"{self.base_url}/api/admin/suggestions/{suggestion_id}",
                json=rejection,
                headers=admin_headers
            )
            self._print_response("[4] Admin rejette la suggestion", resp)

    def test_list_all_suggestions(self):
        """Teste la liste complete des suggestions avec filtres."""
        print("\n\n[TEST 4] Liste des Suggestions avec Filtres")
        print("=" * 60)

        if not self.admin_token:
            print("[ERREUR] Token admin non disponible")
            return

        headers = {"Authorization": f"Bearer {self.admin_token}"}

        filters = [None, "pending", "approved", "rejected"]

        for status_filter in filters:
            params = {}
            if status_filter:
                params["status_filter"] = status_filter
                desc = f"filtrees par status={status_filter}"
            else:
                desc = "toutes"

            resp = requests.get(
                f"{self.base_url}/api/admin/suggestions",
                params=params,
                headers=headers
            )
            self._print_response(f"GET /api/admin/suggestions ({desc})", resp)

    def run_all_tests(self):
        """Lance tous les tests."""
        print("\n" + "="*60)
        print("   ADMIN API TEST SUITE")
        print("="*60)

        try:
            self.setup_accounts()
            self.test_user_management()
            self.test_suggestion_direct_add()
            self.test_suggestion_moderation()
            self.test_list_all_suggestions()

            print("\n" + "="*60)
            print("   TOUS LES TESTS TERMINES")
            print("="*60)

        except requests.exceptions.ConnectionError:
            print("\n[ERREUR] Impossible de se connecter au serveur.")
            print(f"   Assurez-vous que le serveur est lance sur {self.base_url}")
        except Exception as e:
            print(f"\n[ERREUR] {e}")


if __name__ == "__main__":
    tester = AdminAPITester()
    tester.run_all_tests()
