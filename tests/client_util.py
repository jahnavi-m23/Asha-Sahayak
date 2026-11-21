"""
Direct In-Memory TestClient for FastAPI on Windows
Executes route handlers directly without Starlette's anyio blocking portal.
"""

from urllib.parse import urlparse, parse_qs
from fastapi import HTTPException
from pydantic import ValidationError

from backend.main import app, health_check
from backend.routes.visits import (
    confirm_and_save_visit,
    list_visits,
    ConfirmedVisitRequest
)
from backend.routes.beneficiaries import list_beneficiaries, get_beneficiary_by_id
from backend.routes.followups import list_followups, change_followup_status, FollowupStatusUpdate
from backend.routes.reports import get_dashboard_reports
from backend.routes.auth import (
    login,
    forgot_password,
    get_current_user,
    LoginRequest,
    ForgotPasswordRequest
)
from backend.routes.households import (
    list_households,
    get_household,
    create_household,
    get_analytics,
    HouseholdRegistrationSchema
)

class MockResponse:
    def __init__(self, status_code: int, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data

class DirectTestClient:
    def __init__(self, app=None):
        self.app = app

    def _get_user(self, headers: dict = None):
        if not headers or "Authorization" not in headers:
            return None
        return get_current_user(headers["Authorization"])

    def get(self, url: str, headers: dict = None):
        parsed = urlparse(url)
        path = parsed.path
        qs = parse_qs(parsed.query)

        try:
            if path == "/api/health":
                return MockResponse(200, health_check())

            if path == "/api/reports":
                return MockResponse(200, get_dashboard_reports())

            if path == "/api/visits":
                ben_id = qs.get("beneficiary_id", [None])[0]
                return MockResponse(200, list_visits(beneficiary_id=ben_id, limit=100, offset=0))

            if path == "/api/beneficiaries":
                search = qs.get("search", [None])[0]
                return MockResponse(200, list_beneficiaries(search=search, limit=100))

            if path.startswith("/api/beneficiaries/"):
                ben_id = path.replace("/api/beneficiaries/", "")
                return MockResponse(200, get_beneficiary_by_id(ben_id))

            if path == "/api/followups":
                status_filter = qs.get("status", [None])[0]
                return MockResponse(200, list_followups(status=status_filter))

            if path == "/api/households":
                user = self._get_user(headers)
                pincode = qs.get("pincode", [None])[0]
                village = qs.get("village", [None])[0]
                return MockResponse(200, list_households(
                    pincode=pincode,
                    village=village,
                    area_id=None,
                    status=None,
                    search=None,
                    limit=100,
                    offset=0,
                    current_user=user
                ))

            if path.startswith("/api/households/"):
                hh_id = path.replace("/api/households/", "")
                user = self._get_user(headers)
                return MockResponse(200, get_household(hh_id, current_user=user))

            if path == "/api/surveys/analytics":
                user = self._get_user(headers)
                pincode = qs.get("pincode", [None])[0]
                village = qs.get("village", [None])[0]
                worker_id = qs.get("worker_id", [None])[0]
                return MockResponse(200, get_analytics(
                    pincode=pincode,
                    village=village,
                    worker_id=worker_id,
                    current_user=user
                ))

            return MockResponse(404, {"detail": "Endpoint not found in DirectTestClient"})

        except HTTPException as he:
            return MockResponse(he.status_code, {"detail": he.detail})
        except Exception as e:
            return MockResponse(500, {"detail": str(e)})

    def post(self, url: str, json: dict = None, headers: dict = None):
        parsed = urlparse(url)
        path = parsed.path
        body = json or {}

        try:
            if path == "/api/visits/confirm":
                try:
                    req = ConfirmedVisitRequest(**body)
                except (ValidationError, TypeError, ValueError) as ve:
                    return MockResponse(400, {"detail": str(ve)})
                res = confirm_and_save_visit(req)
                return MockResponse(201, res)

            if path == "/api/auth/login":
                res = login(LoginRequest(**body))
                return MockResponse(200, res)

            if path == "/api/auth/forgot-password":
                res = forgot_password(ForgotPasswordRequest(**body))
                return MockResponse(200, res)

            if path == "/api/households":
                user = self._get_user(headers)
                try:
                    schema = HouseholdRegistrationSchema(**body)
                except (ValidationError, TypeError, ValueError) as ve:
                    return MockResponse(400, {"detail": str(ve)})
                res = create_household(schema, current_user=user)
                return MockResponse(201, res)

            return MockResponse(404, {"detail": "Endpoint not found in DirectTestClient"})

        except HTTPException as he:
            return MockResponse(he.status_code, {"detail": he.detail})
        except Exception as e:
            return MockResponse(500, {"detail": str(e)})

    def patch(self, url: str, json: dict = None, headers: dict = None):
        parsed = urlparse(url)
        path = parsed.path
        body = json or {}

        try:
            if path.startswith("/api/followups/") and path.endswith("/status"):
                fol_id = path.replace("/api/followups/", "").replace("/status", "")
                req = FollowupStatusUpdate(**body)
                res = change_followup_status(fol_id, req)
                return MockResponse(200, res)

            return MockResponse(404, {"detail": "Endpoint not found"})
        except HTTPException as he:
            return MockResponse(he.status_code, {"detail": he.detail})
        except Exception as e:
            return MockResponse(500, {"detail": str(e)})
