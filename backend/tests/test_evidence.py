import pytest
import io


@pytest.mark.asyncio
async def test_evidence_upload_and_timeline(async_client):
    # 1. Create a Case
    case_payload = {
        "title": "Evidence Test Case",
        "case_type": "PROPERTY",
        "jurisdiction": "Delhi",
        "description": "Test Case for evidence ingestion",
    }
    c_res = await async_client.post("/api/v1/cases/", json=case_payload)
    case_id = c_res.json()["data"]["id"]

    # 2. Upload text evidence
    doc_content = b"Lease Deed dated 01 July 2024. Deposit of Rs 50,000 paid via NEFT. Handover on 30 June 2025."
    file_payload = {
        "file": ("lease_deed.txt", io.BytesIO(doc_content), "text/plain"),
    }
    data_payload = {
        "title": "Lease Deed 2024",
        "party": "PLAINTIFF",
        "document_type": "CONTRACT",
        "source": "UPLOAD",
    }
    ev_res = await async_client.post(
        f"/api/v1/cases/{case_id}/evidence", files=file_payload, data=data_payload
    )
    assert ev_res.status_code == 201
    ev_data = ev_res.json()["data"]
    assert ev_data["title"] == "Lease Deed 2024"
    assert ev_data["file_hash"] is not None

    # 3. Check Timeline extraction
    time_res = await async_client.get(f"/api/v1/cases/{case_id}/timeline")
    assert time_res.status_code == 200
    events = time_res.json()["data"]
    assert len(events) >= 1

    # 4. Check Evidence Graph
    graph_res = await async_client.get(f"/api/v1/cases/{case_id}/evidence-graph")
    assert graph_res.status_code == 200
    g_data = graph_res.json()["data"]
    assert len(g_data["nodes"]) >= 2
