"""Sample loader for the UnderCover JSON data files.

Lives next to week1d2.ipynb (repo root) so the notebook can import it
as a module:

    import loader
    from loader import load_all, get_claim_context

    data = load_all()                      # loads data/*.json
    data = load_all("data")     # same, explicit path
    ctx = get_claim_context(data, "CLM-1001")

    print(ctx["claim"]["summary"])
    print(ctx["customer"]["name"])
    print(ctx["policy"]["plan"])
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_DATA_DIR = Path(__file__).parent / "data"

# filename -> key in the returned dict
FILES = {
    "company.json": "company",
    "claims.json": "claims",
    "customers.json": "customers",
    "policies.json": "policies",
    "handlers.json": "handlers",
    "knowledge.json": "knowledge",
    "plans.json": "plans",
}


def load_json(path: str | Path) -> Any:
    """Read a single JSON file and return the parsed object."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all(data_dir: str | Path = DEFAULT_DATA_DIR) -> dict[str, Any]:
    """Load every known JSON file from data_dir into a dict.

    Missing files are skipped with an empty default ({} or [])
    so notebooks keep working on partial checkouts.
    """
    data_dir = Path(data_dir)
    data: dict[str, Any] = {}
    for filename, key in FILES.items():
        path = data_dir / filename
        if not path.exists():
            data[key] = {} if key in ("company", "plans") else []
            continue
        data[key] = load_json(path)
    return data


def index_by(rows: list[dict], key: str) -> dict[str, dict]:
    """Index a list of dicts by one field, e.g. index_by(claims, 'claim_id')."""
    return {row[key]: row for row in rows if key in row}


def get_claim(data: dict, claim_id: str) -> dict | None:
    return index_by(data.get("claims", []), "claim_id").get(claim_id)


def get_customer(data: dict, customer_id: str) -> dict | None:
    return index_by(data.get("customers", []), "customer_id").get(customer_id)


def get_policy(data: dict, policy_id: str) -> dict | None:
    return index_by(data.get("policies", []), "policy_id").get(policy_id)


def get_plan(data: dict, plan_name: str) -> dict | None:
    plans = data.get("plans", {}).get("plans", [])
    return index_by(plans, "plan").get(plan_name)


def get_claim_context(data: dict, claim_id: str) -> dict[str, Any]:
    """Join one claim with its customer, policy, and plan details.

    Returns {"claim", "customer", "policy", "plan"}; missing links are None.
    Raises KeyError if the claim_id does not exist.
    """
    claim = get_claim(data, claim_id)
    if claim is None:
        raise KeyError(f"Unknown claim_id: {claim_id}")
    policy = get_policy(data, claim.get("policy_id", ""))
    customer = get_customer(data, claim.get("customer_id", ""))
    plan = get_plan(data, policy["plan"]) if policy else None
    return {"claim": claim, "customer": customer, "policy": policy, "plan": plan}


def summary(data: dict) -> dict[str, int]:
    """Quick counts per dataset, handy for a first notebook cell."""
    out: dict[str, int] = {}
    for key, value in data.items():
        if isinstance(value, list):
            out[key] = len(value)
        elif isinstance(value, dict) and "plans" in value and isinstance(value["plans"], list):
            out[key] = len(value["plans"])
        else:
            out[key] = 1
    return out


if __name__ == "__main__":
    loaded = load_all()
    print(summary(loaded))
    if loaded.get("claims"):
        first_id = loaded["claims"][0]["claim_id"]
        ctx = get_claim_context(loaded, first_id)
        print(f"Example: {first_id} -> {ctx['claim']['summary']}")
