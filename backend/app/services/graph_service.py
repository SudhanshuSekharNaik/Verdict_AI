import uuid
from typing import Any, Dict, List
import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.claim import Claim
from app.models.event import Event
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceGraphResponse, GraphEdge, GraphNode


class GraphService:
    """Knowledge & Evidence Graph Engine powered by NetworkX."""

    @staticmethod
    async def build_case_graph(db: AsyncSession, case_id: uuid.UUID) -> EvidenceGraphResponse:
        case_res = await db.execute(
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.parties),
                selectinload(Case.evidence_list),
                selectinload(Case.events),
                selectinload(Case.claims),
            )
        )
        case = case_res.scalars().first()
        if not case:
            return EvidenceGraphResponse(case_id=case_id, nodes=[], edges=[])

        G = nx.DiGraph()

        # 1. Add Case Node
        case_node_id = f"case_{case.id}"
        G.add_node(
            case_node_id,
            label=f"Case: {case.case_number}",
            type="CASE",
            properties={"title": case.title, "case_type": case.case_type},
        )

        # 2. Add Parties
        for p in case.parties:
            p_id = f"party_{p.id}"
            G.add_node(p_id, label=p.name, type="PARTY", properties={"role": p.role.value})
            G.add_edge(case_node_id, p_id, relationship="PARTY_INVOLVED")

        # 3. Add Claims
        for c in case.claims:
            c_id = f"claim_{c.id}"
            G.add_node(
                c_id,
                label=f"Claim: {c.claim_type}",
                type="CLAIM",
                properties={
                    "statement": c.statement,
                    "party": c.party.value,
                    "grounding_status": c.grounding_status.value,
                },
            )
            # Link to case
            G.add_edge(case_node_id, c_id, relationship="DISPUTED_ISSUE")

        # 4. Add Evidence
        for ev in case.evidence_list:
            ev_id = f"evidence_{ev.id}"
            G.add_node(
                ev_id,
                label=ev.title,
                type="EVIDENCE",
                properties={
                    "document_type": ev.document_type,
                    "party": ev.party.value,
                    "status": ev.verification_status.value,
                },
            )
            G.add_edge(case_node_id, ev_id, relationship="ADMITTED_EXHIBIT")

            # Link evidence to claims based on party or text matching
            for c in case.claims:
                c_id = f"claim_{c.id}"
                if ev.party.value == c.party.value:
                    G.add_edge(ev_id, c_id, relationship="SUPPORTS")
                else:
                    G.add_edge(ev_id, c_id, relationship="CONTRADICTS")

        # 5. Add Timeline Events
        for evnt in case.events:
            evnt_id = f"event_{evnt.id}"
            G.add_node(
                evnt_id,
                label=f"{evnt.date_raw_str}: {evnt.title[:30]}",
                type="EVENT",
                properties={
                    "date": evnt.date_raw_str,
                    "conflict_flag": evnt.conflict_flag,
                },
            )
            G.add_edge(case_node_id, evnt_id, relationship="TIMELINE_MILESTONE")
            if evnt.source_evidence_id:
                G.add_edge(f"evidence_{evnt.source_evidence_id}", evnt_id, relationship="ESTABLISHES_DATE")

        # Convert NetworkX graph to API schema
        nodes_out = [
            GraphNode(id=n, label=data.get("label", n), type=data.get("type", "UNKNOWN"), properties=data.get("properties", {}))
            for n, data in G.nodes(data=True)
        ]
        edges_out = [
            GraphEdge(source=u, target=v, relationship=data.get("relationship", "RELATED_TO"), properties=data.get("properties", {}))
            for u, v, data in G.edges(data=True)
        ]

        return EvidenceGraphResponse(case_id=case_id, nodes=nodes_out, edges=edges_out)
