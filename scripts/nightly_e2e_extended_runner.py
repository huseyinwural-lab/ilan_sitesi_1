import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "test_reports"
REPORT_FILE = REPORTS_DIR / "nightly_e2e_extended.json"

ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_base_url() -> str:
    env_value = (os.environ.get("NIGHTLY_E2E_BASE_URL") or os.environ.get("REACT_APP_BACKEND_URL") or "").strip()
    if env_value:
        return env_value.rstrip("/")

    frontend_env = ROOT / "frontend" / ".env"
    if frontend_env.exists():
        for raw in frontend_env.read_text(encoding="utf-8").splitlines():
            if raw.startswith("REACT_APP_BACKEND_URL="):
                value = raw.split("=", 1)[1].strip()
                if value:
                    return value.rstrip("/")

    return "http://127.0.0.1:8001"


class NightlyE2ERunner:
    def __init__(self, base_url: str, mode: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.mode = mode
        self.session = requests.Session()
        self.tokens: dict[str, str] = {}
        self.endpoint_events: list[dict[str, Any]] = []
        self.broken_flows: list[dict[str, Any]] = []

    def _request(
        self,
        flow: str,
        step: str,
        method: str,
        path: str,
        *,
        expected_statuses: set[int],
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        timeout: int = 45,
    ) -> tuple[bool, requests.Response | None, dict[str, Any]]:
        url = f"{self.base_url}{path}"
        started = time.perf_counter()
        try:
            response = self.session.request(
                method,
                url,
                headers=headers or {},
                json=json_body,
                timeout=timeout,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000
            status = int(response.status_code)
            ok = status in expected_statuses

            event = {
                "flow": flow,
                "step": step,
                "method": method,
                "path": path,
                "status": status,
                "expected_statuses": sorted(expected_statuses),
                "ok": ok,
                "elapsed_ms": round(elapsed_ms, 2),
            }
            self.endpoint_events.append(event)
            return ok, response, event
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            event = {
                "flow": flow,
                "step": step,
                "method": method,
                "path": path,
                "status": None,
                "expected_statuses": sorted(expected_statuses),
                "ok": False,
                "error": str(exc),
                "elapsed_ms": round(elapsed_ms, 2),
            }
            self.endpoint_events.append(event)
            return False, None, event

    def _mark_broken(self, flow_key: str, reason: str, last_event: dict[str, Any] | None) -> None:
        item = {
            "flow": flow_key,
            "reason": reason,
        }
        if last_event:
            item["endpoint"] = {
                "method": last_event.get("method"),
                "path": last_event.get("path"),
                "status": last_event.get("status"),
            }
        self.broken_flows.append(item)

    def _login_token(self, email: str, password: str, key: str) -> bool:
        ok, response, event = self._request(
            "auth",
            f"login_{key}",
            "POST",
            "/api/auth/login",
            expected_statuses={200},
            json_body={"email": email, "password": password},
        )
        if not ok or response is None:
            self._mark_broken("auth", f"{key} login failed", event)
            return False
        token = (response.json() or {}).get("access_token")
        if not token:
            self._mark_broken("auth", f"{key} access token missing", event)
            return False
        self.tokens[key] = token
        return True

    def _auth_headers(self, key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.tokens.get(key, '')}"}

    def _get_first_vehicle_category(self, country_code: str) -> str | None:
        for path in [
            f"/api/categories/children?module=vehicle&country={country_code}",
            f"/api/categories?module=vehicle&country={country_code}",
        ]:
            ok, response, _ = self._request(
                "dealer_listing",
                f"get_category_{country_code}",
                "GET",
                path,
                expected_statuses={200},
                headers=self._auth_headers("dealer"),
            )
            if not ok or response is None:
                continue
            try:
                payload = response.json()
                if isinstance(payload, list) and payload:
                    category_id = payload[0].get("id")
                    if category_id:
                        return category_id
            except Exception:
                continue
        return None

    def _ensure_invoice_pdf_for_user(self) -> str | None:
        user_headers = self._auth_headers("user")
        admin_headers = self._auth_headers("admin")

        ok, response, event = self._request(
            "user_finance",
            "account_invoices_list",
            "GET",
            "/api/account/invoices",
            expected_statuses={200},
            headers=user_headers,
        )
        if not ok or response is None:
            self._mark_broken("user_finance", "cannot list account invoices", event)
            return None

        invoice_id = None
        try:
            items = (response.json() or {}).get("items") or []
            if items:
                invoice_id = items[0].get("id")
        except Exception:
            invoice_id = None

        if not invoice_id:
            ok_user, user_me_resp, user_me_event = self._request(
                "user_finance",
                "user_me",
                "GET",
                "/api/auth/me",
                expected_statuses={200},
                headers=user_headers,
            )
            if not ok_user or user_me_resp is None:
                self._mark_broken("user_finance", "cannot resolve user profile", user_me_event)
                return None

            user_id = (user_me_resp.json() or {}).get("id")
            if not user_id:
                self._mark_broken("user_finance", "missing user id", user_me_event)
                return None

            ok_plan, plan_resp, plan_event = self._request(
                "user_finance",
                "admin_plans",
                "GET",
                "/api/admin/plans",
                expected_statuses={200},
                headers=admin_headers,
            )
            if not ok_plan or plan_resp is None:
                self._mark_broken("user_finance", "cannot load plans for invoice creation", plan_event)
                return None

            plans = (plan_resp.json() or {}).get("items") or []
            active_plans = [item for item in plans if item.get("active_flag")]
            plan_id = (active_plans[0] if active_plans else (plans[0] if plans else {})).get("id")

            payload = {"user_id": user_id, "issue_now": True}
            if plan_id:
                payload["plan_id"] = plan_id

            ok_create, create_resp, create_event = self._request(
                "user_finance",
                "admin_create_invoice",
                "POST",
                "/api/admin/invoices",
                expected_statuses={200},
                headers=admin_headers,
                json_body=payload,
            )
            if not ok_create or create_resp is None:
                self._mark_broken("user_finance", "cannot create invoice for user", create_event)
                return None

            invoice_id = ((create_resp.json() or {}).get("invoice") or {}).get("id")

        if not invoice_id:
            return None

        self._request(
            "user_finance",
            "admin_generate_pdf",
            "POST",
            f"/api/admin/invoices/{invoice_id}/generate-pdf",
            expected_statuses={200, 400, 404},
            headers=admin_headers,
        )

        return invoice_id

    def run_user_finance_flow(self) -> dict[str, Any]:
        result = {
            "flow": "user_finance",
            "pdf_download_pass": False,
            "subscription_cancel_reactivate_pass": False,
            "ok": False,
        }

        invoice_id = self._ensure_invoice_pdf_for_user()
        if invoice_id:
            ok_pdf, _, pdf_event = self._request(
                "user_finance",
                "account_invoice_pdf_download",
                "GET",
                f"/api/account/invoices/{invoice_id}/download-pdf",
                expected_statuses={200},
                headers=self._auth_headers("user"),
            )
            result["pdf_download_pass"] = ok_pdf
            if not ok_pdf:
                self._mark_broken("user_finance", "pdf download failed", pdf_event)

        ok_cancel, _, cancel_event = self._request(
            "user_finance",
            "subscription_cancel",
            "POST",
            "/api/account/subscription/cancel",
            expected_statuses={200},
            headers=self._auth_headers("user"),
        )
        ok_reactivate, _, reactivate_event = self._request(
            "user_finance",
            "subscription_reactivate",
            "POST",
            "/api/account/subscription/reactivate",
            expected_statuses={200},
            headers=self._auth_headers("user"),
        )

        if not ok_cancel:
            self._mark_broken("user_finance", "subscription cancel failed", cancel_event)
        if not ok_reactivate:
            self._mark_broken("user_finance", "subscription reactivate failed", reactivate_event)

        result["subscription_cancel_reactivate_pass"] = ok_cancel and ok_reactivate
        result["ok"] = result["pdf_download_pass"] and result["subscription_cancel_reactivate_pass"]
        return result

    def _run_listing_flow_for_country(self, country_code: str) -> tuple[bool, dict[str, Any]]:
        category_id = self._get_first_vehicle_category(country_code)
        detail = {
            "country": country_code,
            "category_id": category_id,
            "submit_track": {},
            "publish_track": {},
            "ok": False,
        }
        if not category_id:
            self._mark_broken("dealer_listing", f"category not found for {country_code}", None)
            return False, detail

        create_payload_submit = {
            "category_id": category_id,
            "country": country_code,
            "title": f"Nightly Dealer Listing Submit {country_code}",
        }
        ok_create_submit, create_submit_resp, create_submit_event = self._request(
            "dealer_listing",
            f"{country_code}_create_submit",
            "POST",
            "/api/v1/listings/vehicle",
            expected_statuses={200},
            headers=self._auth_headers("dealer"),
            json_body=create_payload_submit,
        )
        detail["submit_track"]["create"] = ok_create_submit
        if not ok_create_submit or create_submit_resp is None:
            self._mark_broken("dealer_listing", f"submit-track create failed for {country_code}", create_submit_event)
            return False, detail

        submit_listing_id = (create_submit_resp.json() or {}).get("id")
        if not submit_listing_id:
            self._mark_broken("dealer_listing", f"submit-track listing id missing for {country_code}", create_submit_event)
            return False, detail

        patch_payload_submit = {
            "core_fields": {
                "title": f"Nightly Dealer Listing Submit {country_code} Updated",
                "description": "Nightly E2E listing draft update",
                "price": {"price_type": "FIXED", "amount": 23000, "currency_primary": "EUR"},
            },
            "location": {"city": "Berlin" if country_code == "DE" else "Paris", "country": country_code},
        }
        ok_patch_submit, _, patch_submit_event = self._request(
            "dealer_listing",
            f"{country_code}_submit_track_patch_draft",
            "PATCH",
            f"/api/v1/listings/vehicle/{submit_listing_id}/draft",
            expected_statuses={200},
            headers=self._auth_headers("dealer"),
            json_body=patch_payload_submit,
        )
        detail["submit_track"]["patch"] = ok_patch_submit
        if not ok_patch_submit:
            self._mark_broken("dealer_listing", f"submit-track patch failed for {country_code}", patch_submit_event)
            return False, detail

        preview_payload_submit = {
            **patch_payload_submit,
            "contact": {"contact_name": "Nightly Dealer", "contact_phone": "+491701112233"},
        }
        ok_preview_submit, _, preview_submit_event = self._request(
            "dealer_listing",
            f"{country_code}_submit_track_preview_ready",
            "POST",
            f"/api/v1/listings/vehicle/{submit_listing_id}/preview-ready",
            expected_statuses={200},
            headers=self._auth_headers("dealer"),
            json_body=preview_payload_submit,
        )
        detail["submit_track"]["preview_ready"] = ok_preview_submit
        if not ok_preview_submit:
            self._mark_broken("dealer_listing", f"submit-track preview-ready failed for {country_code}", preview_submit_event)
            return False, detail

        ok_submit, _, submit_event = self._request(
            "dealer_listing",
            f"{country_code}_submit_track_submit_review",
            "POST",
            f"/api/v1/listings/vehicle/{submit_listing_id}/submit-review",
            expected_statuses={200},
            headers={**self._auth_headers("dealer"), "Idempotency-Key": str(uuid.uuid4())},
        )
        detail["submit_track"]["submit_review"] = ok_submit
        if not ok_submit:
            self._mark_broken("dealer_listing", f"submit-track submit-review failed for {country_code}", submit_event)
            return False, detail

        create_payload_publish = {
            "category_id": category_id,
            "country": country_code,
            "title": f"Nightly Dealer Listing Publish {country_code}",
        }
        ok_create_publish, create_publish_resp, create_publish_event = self._request(
            "dealer_listing",
            f"{country_code}_create_publish",
            "POST",
            "/api/v1/listings/vehicle",
            expected_statuses={200},
            headers=self._auth_headers("dealer"),
            json_body=create_payload_publish,
        )
        detail["publish_track"]["create"] = ok_create_publish
        if not ok_create_publish or create_publish_resp is None:
            self._mark_broken("dealer_listing", f"publish-track create failed for {country_code}", create_publish_event)
            return False, detail

        publish_listing_id = (create_publish_resp.json() or {}).get("id")
        if not publish_listing_id:
            self._mark_broken("dealer_listing", f"publish-track listing id missing for {country_code}", create_publish_event)
            return False, detail

        patch_payload_publish = {
            "core_fields": {
                "title": f"Nightly Dealer Listing Publish {country_code} Updated",
                "description": "Nightly E2E listing publish track",
                "price": {"price_type": "FIXED", "amount": 25000, "currency_primary": "EUR"},
            },
            "location": {"city": "Berlin" if country_code == "DE" else "Paris", "country": country_code},
        }
        ok_patch_publish, _, patch_publish_event = self._request(
            "dealer_listing",
            f"{country_code}_publish_track_patch_draft",
            "PATCH",
            f"/api/v1/listings/vehicle/{publish_listing_id}/draft",
            expected_statuses={200},
            headers=self._auth_headers("dealer"),
            json_body=patch_payload_publish,
        )
        detail["publish_track"]["patch"] = ok_patch_publish
        if not ok_patch_publish:
            self._mark_broken("dealer_listing", f"publish-track patch failed for {country_code}", patch_publish_event)
            return False, detail

        preview_payload_publish = {
            **patch_payload_publish,
            "contact": {"contact_name": "Nightly Dealer", "contact_phone": "+491701112233"},
        }
        ok_preview_publish, _, preview_publish_event = self._request(
            "dealer_listing",
            f"{country_code}_publish_track_preview_ready",
            "POST",
            f"/api/v1/listings/vehicle/{publish_listing_id}/preview-ready",
            expected_statuses={200},
            headers=self._auth_headers("dealer"),
            json_body=preview_payload_publish,
        )
        detail["publish_track"]["preview_ready"] = ok_preview_publish
        if not ok_preview_publish:
            self._mark_broken("dealer_listing", f"publish-track preview-ready failed for {country_code}", preview_publish_event)
            return False, detail

        ok_publish, _, publish_event = self._request(
            "dealer_listing",
            f"{country_code}_publish_track_publish",
            "POST",
            f"/api/v1/listings/vehicle/{publish_listing_id}/publish",
            expected_statuses={200},
            headers=self._auth_headers("dealer"),
        )
        detail["publish_track"]["publish"] = ok_publish
        if not ok_publish:
            self._mark_broken("dealer_listing", f"publish-track publish failed for {country_code}", publish_event)
            return False, detail

        detail["submit_track"]["listing_id"] = submit_listing_id
        detail["publish_track"]["listing_id"] = publish_listing_id
        detail["ok"] = True
        return True, detail

    def run_dealer_listing_flow(self) -> dict[str, Any]:
        de_ok, de_detail = self._run_listing_flow_for_country("DE")
        fr_ok, fr_detail = self._run_listing_flow_for_country("FR")
        return {
            "flow": "dealer_listing",
            "de": de_detail,
            "fr": fr_detail,
            "ok": de_ok and fr_ok,
        }

    def run_admin_flow(self) -> dict[str, Any]:
        admin_headers = self._auth_headers("admin")

        ok_export, _, export_event = self._request(
            "admin_ops",
            "finance_export_csv",
            "GET",
            "/api/admin/payments/export/csv",
            expected_statuses={200},
            headers=admin_headers,
            timeout=120,
        )
        if not ok_export:
            self._mark_broken("admin_ops", "finance export csv failed", export_event)

        fake_event_id = str(uuid.uuid4())
        ok_replay, _, replay_event = self._request(
            "admin_ops",
            "webhook_replay_smoke",
            "POST",
            f"/api/admin/webhooks/events/{fake_event_id}/replay",
            expected_statuses={400, 404},
            headers=admin_headers,
            json_body={},
        )
        if not ok_replay:
            self._mark_broken("admin_ops", "webhook replay smoke failed", replay_event)

        return {
            "flow": "admin_ops",
            "finance_export_pass": ok_export,
            "webhook_replay_smoke_pass": ok_replay,
            "ok": ok_export and ok_replay,
        }

    def run_once(self) -> dict[str, Any]:
        self.endpoint_events = []
        self.broken_flows = []

        auth_ok = all(
            [
                self._login_token(ADMIN_EMAIL, ADMIN_PASSWORD, "admin"),
                self._login_token(USER_EMAIL, USER_PASSWORD, "user"),
                self._login_token(DEALER_EMAIL, DEALER_PASSWORD, "dealer"),
            ]
        )

        if not auth_ok:
            return {
                "generated_at": utc_now_iso(),
                "base_url": self.base_url,
                "status": "FAIL",
                "flows": {},
                "broken_flows": self.broken_flows,
                "endpoint_events": self.endpoint_events,
                "finance_e2e_pass": False,
                "listing_e2e_pass": False,
                "merge_blocked": True,
            }

        user_flow = self.run_user_finance_flow()
        dealer_flow = self.run_dealer_listing_flow()
        admin_flow = self.run_admin_flow()

        finance_pass = bool(user_flow.get("ok") and admin_flow.get("finance_export_pass") and admin_flow.get("webhook_replay_smoke_pass"))
        listing_pass = bool(dealer_flow.get("ok"))
        overall_pass = bool(user_flow.get("ok") and dealer_flow.get("ok") and admin_flow.get("ok"))

        endpoint_4xx_5xx = [
            event
            for event in self.endpoint_events
            if event.get("status") is not None and int(event.get("status") or 0) >= 400
        ]

        return {
            "generated_at": utc_now_iso(),
            "base_url": self.base_url,
            "status": "PASS" if overall_pass else "FAIL",
            "flows": {
                "user": user_flow,
                "dealer": dealer_flow,
                "admin": admin_flow,
            },
            "broken_flows": self.broken_flows,
            "endpoint_http_4xx_5xx": endpoint_4xx_5xx,
            "endpoint_events": self.endpoint_events,
            "finance_e2e_pass": finance_pass,
            "listing_e2e_pass": listing_pass,
            "merge_blocked": not (finance_pass and listing_pass),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Nightly E2E extended runner")
    parser.add_argument("--mode", choices=["check", "nightly"], default="nightly")
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    base_url = resolve_base_url()
    runner = NightlyE2ERunner(base_url=base_url, mode=args.mode)

    run_count = max(1, int(args.runs))
    run_results = []
    for _ in range(run_count):
        run_results.append(runner.run_once())

    last_run = run_results[-1]
    last_five = run_results[-5:]
    last_five_pass = len(last_five) == 5 and all(item.get("status") == "PASS" for item in last_five)

    final_report = {
        "generated_at": utc_now_iso(),
        "mode": args.mode,
        "runs": run_count,
        "base_url": base_url,
        "latest": last_run,
        "recent_runs": [
            {
                "generated_at": item.get("generated_at"),
                "status": item.get("status"),
                "finance_e2e_pass": item.get("finance_e2e_pass"),
                "listing_e2e_pass": item.get("listing_e2e_pass"),
                "merge_blocked": item.get("merge_blocked"),
            }
            for item in run_results
        ],
        "last_five_nightly_pass": last_five_pass,
        "ci_gate": {
            "merge_blocked": bool(last_run.get("merge_blocked")),
            "finance_gate": bool(not last_run.get("finance_e2e_pass")),
            "listing_gate": bool(not last_run.get("listing_e2e_pass")),
        },
        "artifact_requirements": {
            "broken_flows": last_run.get("broken_flows") or [],
            "endpoint_http_4xx_5xx": last_run.get("endpoint_http_4xx_5xx") or [],
        },
    }

    REPORT_FILE.write_text(json.dumps(final_report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "report": str(REPORT_FILE),
                "mode": args.mode,
                "status": last_run.get("status"),
                "finance_e2e_pass": last_run.get("finance_e2e_pass"),
                "listing_e2e_pass": last_run.get("listing_e2e_pass"),
                "merge_blocked": final_report["ci_gate"]["merge_blocked"],
                "last_five_nightly_pass": final_report["last_five_nightly_pass"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if args.mode == "check":
        return 1 if final_report["ci_gate"]["merge_blocked"] else 0

    return 0 if last_run.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
