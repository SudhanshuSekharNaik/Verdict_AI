import pytest


@pytest.mark.asyncio
async def test_case_creation_and_retrieval(async_client):
    case_payload = {
        "title": "Commercial Tenancy Dispute - Alpha Corp vs Beta Ltd",
        "case_type": "CIVIL",
        "jurisdiction": "High Court of Delhi",
        "description": "Lessee seeking refund of commercial security deposit after lease surrender.",
        "plaintiff_name": "Alpha Corp",
        "defendant_name": "Beta Ltd",
        "disputed_amount": 150000.0,
    }
    # Create Case
    create_res = await async_client.post("/api/v1/cases/", json=case_payload)
    assert create_res.status_code == 201
    created_case = create_res.json()["data"]
    case_id = created_case["id"]
    assert "AAD-" in created_case["case_number"]

    # Retrieve Case
    get_res = await async_client.get(f"/api/v1/cases/{case_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["title"] == case_payload["title"]

    # List Cases
    list_res = await async_client.get("/api/v1/cases/")
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_case_intake_agent_endpoint(async_client):
    intake_payload = {
        "narrative": "I rented a shop from Mr. Ramesh in Delhi for ₹40,000 monthly rent. I deposited ₹80,000 security deposit on 01 January 2024. I vacated on 31 December 2024. He refused to refund my deposit.",
        "jurisdiction_hint": "Delhi",
    }
    intake_res = await async_client.post("/api/v1/cases/intake", json=intake_payload)
    assert intake_res.status_code == 200
    data = intake_res.json()["data"]
    assert "Dispute" in data["title"]
    assert data["disputed_amount"] == 80000.0
    assert len(data["claims"]) >= 1
