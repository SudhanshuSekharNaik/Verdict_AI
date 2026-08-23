import asyncio
import os
import sys
from pathlib import Path

# Enable UTF-8 encoding for Windows terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add root and backend directories to sys.path
root_dir = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, root_dir)
sys.path.insert(0, str(Path(root_dir) / "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal, engine
from app.models.base import Base
from app.models.case import Case, CaseStatusEnum, CaseTypeEnum
from app.models.claim import Claim, ClaimPartyEnum, GroundingStatusEnum
from app.models.event import Event
from app.models.evidence import Evidence, EvidencePartyEnum, EvidenceStatusEnum
from app.models.evidence_chunk import EvidenceChunk
from app.models.legal_source import LegalChunk, LegalSource
from app.models.party import Party, PartyRoleEnum
from app.models.user import User, UserRoleEnum
from app.security.passwords import get_password_hash
from rag.chunking import LegalStructureChunker
from rag.embeddings import EmbeddingService


async def seed_database():
    print("🌱 Starting Aadalat AI Database Seeding...")

    # 1. Initialize Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 2. Seed Users
        users_to_seed = [
            ("judge@aadalat.ai", "Hon'ble Justice P.K. Roy", "judge123", UserRoleEnum.JUDGE),
            ("admin@aadalat.ai", "System Administrator", "admin123", UserRoleEnum.ADMIN),
            ("user@aadalat.ai", "Advocate Rahul Verma", "user123", UserRoleEnum.USER),
        ]

        for email, name, pwd, role in users_to_seed:
            res = await db.execute(select(User).where(User.email == email))
            if not res.scalars().first():
                user = User(
                    email=email,
                    full_name=name,
                    hashed_password=get_password_hash(pwd),
                    role=role,
                    is_active=True,
                )
                db.add(user)
        await db.commit()
        print("✅ Users seeded.")

        # 3. Seed Legal Sources (Precedents & Statutory Provisions)
        legal_sources_data = [
            {
                "citation": "(2021) 8 SCC 342",
                "title": "M/s Greenfield Infrastructure v. Union of India",
                "court": "Supreme Court of India",
                "year": 2021,
                "jurisdiction": "India",
                "source_type": "PRECEDENT",
                "full_text": (
                    "FACTS: The respondent withheld contractor security deposit without contemporaneous inspection.\n\n"
                    "ISSUES: Whether unilateral damages deduction without joint verification is permissible in law.\n\n"
                    "RATIO DECIDENDI: The standard of proof in civil and tenancy matters is preponderance of probabilities. "
                    "Where a party claims quantifiable damages or set-off against an admitted deposit, the burden of establishing "
                    "actual loss through contemporaneous itemized accounts and timely joint inspection records rests strictly on the claimant. "
                    "Unilateral assertions formulated post-vacancy cannot substantiate lawful deduction.\n\n"
                    "FINAL ORDER: Appeal allowed. Full deposit refund decreed with 6% interest."
                ),
                "summary": "Unilateral damage deductions without contemporaneous joint inspection records cannot be sustained in law.",
                "provenance_url": "https://judgments.ecourts.gov.in/sample/4491",
            },
            {
                "citation": "2019 SCC OnLine Del 7891",
                "title": "Anil Verma v. Sunita Rathi",
                "court": "Delhi High Court",
                "year": 2019,
                "jurisdiction": "India",
                "source_type": "PRECEDENT",
                "full_text": (
                    "FACTS: Tenancy dispute regarding deduction of ₹45,000 for repainting and general wear and tear.\n\n"
                    "ISSUES: Scope of permissible tenancy deposit deductions.\n\n"
                    "RATIO DECIDENDI: Normal wear and tear resulting from ordinary habitation cannot be deducted from a tenant's security deposit. "
                    "A landlord seeking deductions must demonstrate damage attributable to wilful default or extraordinary misuse, supported by genuine invoices.\n\n"
                    "FINAL ORDER: Respondent directed to refund the entire deducted sum."
                ),
                "summary": "Normal wear and tear cannot be deducted from tenant security deposits.",
                "provenance_url": "https://delhihighcourt.nic.in/judgments/7891",
            },
            {
                "citation": "2022 NCDRC 450",
                "title": "Karan Malhotra v. AutoTech Motors Pvt Ltd",
                "court": "National Consumer Disputes Redressal Commission",
                "year": 2022,
                "jurisdiction": "India",
                "source_type": "PRECEDENT",
                "full_text": (
                    "FACTS: Complainant purchased a certified pre-owned car represented as 100% accident free, but later discovered prior structural chassis repairs.\n\n"
                    "ISSUES: Whether non-disclosure of prior collision history constitutes unfair trade practice.\n\n"
                    "RATIO DECIDENDI: Concealment of material vehicular collision history in pre-owned commercial sales constitutes an unfair trade practice under Section 2(47) of the Consumer Protection Act, 2019. "
                    "The seller cannot evade liability by asserting lack of personal knowledge when affirmative declarations were made to induce purchase.\n\n"
                    "FINAL ORDER: Full refund ordered along with compensation of ₹50,000."
                ),
                "summary": "Affirmative misrepresentation of vehicle accident history constitutes actionable unfair trade practice.",
                "provenance_url": "https://cms.nic.in/ncdrc/orders/450",
            },
            {
                "citation": "Section 73 of Indian Contract Act, 1872",
                "title": "Compensation for loss or damage caused by breach of contract",
                "court": "Codified Legislation",
                "year": 1872,
                "jurisdiction": "India",
                "source_type": "STATUTE",
                "statute_section": "Section 73",
                "full_text": (
                    "When a contract has been broken, the party who suffers by such breach is entitled to receive, "
                    "from the party who has broken the contract, compensation for any loss or damage caused to him thereby, "
                    "which naturally arose in the usual course of things from such breach, or which the parties knew, when they made the contract, to be likely to result from the breach of it."
                ),
                "summary": "Statutory basis for liquidated and unliquidated damages for contractual breach.",
                "provenance_url": "https://indiacode.nic.in/handle/123456789/2187",
            },
        ]

        for src_data in legal_sources_data:
            res = await db.execute(select(LegalSource).where(LegalSource.citation == src_data["citation"]))
            if not res.scalars().first():
                source = LegalSource(**src_data)
                db.add(source)
                await db.flush()

                # Chunk & embed
                chunks = LegalStructureChunker.chunk_legal_document(
                    text=src_data["full_text"], source_metadata=src_data
                )
                for c in chunks:
                    emb = EmbeddingService.embed_text(c["chunk_text"])
                    lc = LegalChunk(
                        source_id=source.id,
                        chunk_index=c["chunk_index"],
                        section_type=c["section_type"],
                        chunk_text=c["chunk_text"],
                        embedding=emb,
                        metadata_json=c,
                    )
                    db.add(lc)
        await db.commit()
        print("✅ Legal Sources & RAG Precedents seeded.")

        # 4. Seed the 5 Complete Benchmark Demo Cases
        demo_cases_spec = [
            {
                "case_number": "AAD-2026-001",
                "title": "Security Deposit Dispute: Rahul Kumar vs. Suresh Sharma",
                "case_type": "PROPERTY",
                "jurisdiction": "Delhi State Consumer Disputes Redressal Commission",
                "description": "Tenant Rahul Kumar vacated premises on 30 June 2025 seeking refund of ₹50,000 security deposit. Landlord Suresh Sharma deducted ₹35,000 citing wall repainting and deep damages.",
                "plaintiff_name": "Rahul Kumar",
                "defendant_name": "Suresh Sharma",
                "disputed_amount": 50000.0,
                "claims": [
                    {"party": ClaimPartyEnum.PLAINTIFF, "statement": "Tenant vacated flat in pristine condition on 30 June 2025 and is entitled to full ₹50,000 refund.", "amount": 50000.0, "status": GroundingStatusEnum.SUPPORTED},
                    {"party": ClaimPartyEnum.DEFENDANT, "statement": "Landlord incurred ₹35,000 for urgent wall repairs and fixture replacements.", "amount": 35000.0, "status": GroundingStatusEnum.CONFLICTING},
                ],
                "events": [
                    {"date_raw_str": "01 July 2024", "title": "Tenancy Agreement Executed", "description": "11-month lease executed with ₹50,000 security deposit.", "party": "UNDISPUTED"},
                    {"date_raw_str": "30 June 2025", "title": "Tenant Vacation & Handover", "description": "Tenant moved out and took timestamped photos showing clean walls.", "party": "PLAINTIFF"},
                    {"date_raw_str": "12 July 2025", "title": "Landlord Unilateral Inspection", "description": "Landlord generated inspection report 12 days later without tenant notice.", "party": "DEFENDANT", "conflict_flag": True, "conflict_notes": "⚠️ TIMELINE CONFLICT: Inspection conducted 12 days after keys surrendered with unverified intervening access."},
                ],
                "evidence": [
                    {"title": "Tenancy Agreement dated 01 July 2024", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "CONTRACT", "text": "Clause 8: Full ₹50,000 security deposit refundable within 7 days of key handover, subject only to actual wilful damage."},
                    {"title": "Move-Out Photos with Timestamps (30 June 2025)", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "IMAGE", "text": "Timestamped metadata: 30 June 2025 14:22 PM. Walls and fixtures intact, freshly swept, no water damage."},
                    {"title": "Bank Transfer Receipt of Deposit (₹50,000)", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "BANK_RECORD", "text": "NEFT Ref: HDFC202407018899 ₹50,000 credited to Suresh Sharma."},
                    {"title": "Repair Invoice dated 14 July 2025 (₹35,000)", "party": EvidencePartyEnum.DEFENDANT, "doc_type": "INVOICE", "text": "Invoice #881: Wall plastering and repainting ₹35,000. Generated 14 days after tenancy termination."},
                ],
            },
            {
                "case_number": "AAD-2026-002",
                "title": "Used Car Misrepresentation: Priya Sharma vs. Rajesh Auto Dealership",
                "case_type": "CONSUMER",
                "jurisdiction": "District Consumer Commission, Mumbai",
                "description": "Buyer purchased used car advertised as 100% accident free for ₹6,50,000. Subsequent service revealed major prior chassis rebuild in 2023.",
                "plaintiff_name": "Priya Sharma",
                "defendant_name": "Rajesh Auto Dealership",
                "disputed_amount": 650000.0,
                "claims": [
                    {"party": ClaimPartyEnum.PLAINTIFF, "statement": "Dealership fraudulently advertised vehicle as 100% accident free.", "amount": 650000.0, "status": GroundingStatusEnum.SUPPORTED},
                    {"party": ClaimPartyEnum.DEFENDANT, "statement": "Dealership had no personal knowledge of prior accident history.", "amount": 0.0, "status": GroundingStatusEnum.CONFLICTING},
                ],
                "events": [
                    {"date_raw_str": "15 March 2024", "title": "Vehicle Advertisement Published", "description": "Online ad stating '2021 Sedan - Single Owner - 100% Accident Free Guarantee'.", "party": "DEFENDANT"},
                    {"date_raw_str": "20 March 2024", "title": "Purchase & Delivery", "description": "Buyer paid ₹6,50,000 upon verbal confirmation of clean record.", "party": "PLAINTIFF"},
                    {"date_raw_str": "10 May 2024", "title": "Authorized Workshop Inspection", "description": "OEM workshop logs show chassis alignment & welding done in Nov 2023.", "party": "PLAINTIFF"},
                ],
                "evidence": [
                    {"title": "Advertisement Printout (100% Accident Free)", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "NOTICE", "text": "Marketing brochure: 'Inspected 120 Points. Zero Accident Record Guaranteed.'"},
                    {"title": "WhatsApp Chat with Sales Representative", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "MESSAGE", "text": "Sales rep text: 'Don't worry madam, completely genuine car, never touched.'"},
                    {"title": "OEM Workshop Service History Record (Nov 2023)", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "INVOICE", "text": "Service Log #7721: Major front collision structural chassis repair, air bag replacement."},
                ],
            },
            {
                "case_number": "AAD-2026-003",
                "title": "Employment Termination Dispute: Vikram Mehta vs. TechCorp Solutions",
                "case_type": "EMPLOYMENT",
                "jurisdiction": "Labour Court / Civil Court, Bengaluru",
                "description": "Senior engineer terminated without 2 months notice pay (₹1,80,000). Employer claims termination was for performance misconduct.",
                "plaintiff_name": "Vikram Mehta",
                "defendant_name": "TechCorp Solutions",
                "disputed_amount": 180000.0,
                "claims": [
                    {"party": ClaimPartyEnum.PLAINTIFF, "statement": "Wrongful termination in breach of employment agreement requiring 60 days severance.", "amount": 180000.0, "status": GroundingStatusEnum.SUPPORTED},
                    {"party": ClaimPartyEnum.DEFENDANT, "statement": "Termination was for cause following performance warning.", "amount": 0.0, "status": GroundingStatusEnum.CONFLICTING},
                ],
                "events": [
                    {"date_raw_str": "02 April 2024", "title": "Internal HR Termination Email", "description": "Internal email confirms termination decision was finalised on 02 April.", "party": "DEFENDANT"},
                    {"date_raw_str": "10 April 2024", "title": "Performance Warning Issued", "description": "Management sent first performance improvement notice.", "party": "DEFENDANT", "conflict_flag": True, "conflict_notes": "⚠️ TIMELINE CONFLICT: Termination decision predates the performance warning by 8 days."},
                    {"date_raw_str": "15 April 2024", "title": "Immediate Termination Notice", "description": "Employee relieved without notice pay.", "party": "PLAINTIFF"},
                ],
                "evidence": [
                    {"title": "Employment Contract Clause 12", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "CONTRACT", "text": "Clause 12: Either party may terminate with 60 days written notice or salary in lieu thereof, except for proved gross misconduct."},
                    {"title": "Internal Email Audit Log (02 April 2024)", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "MESSAGE", "text": "HR Director: 'Process Vikram's exit by 15 April.'"},
                ],
            },
            {
                "case_number": "AAD-2026-004",
                "title": "Online Laptop Dispute: Neha Gupta vs. GadgetStore Online",
                "case_type": "CONSUMER",
                "jurisdiction": "District Consumer Disputes Redressal Forum, Pune",
                "description": "Buyer paid ₹85,000 for brand new sealed laptop. Serial number check revealed warranty had been activated 6 months earlier by previous user.",
                "plaintiff_name": "Neha Gupta",
                "defendant_name": "GadgetStore Online",
                "disputed_amount": 85000.0,
                "claims": [
                    {"party": ClaimPartyEnum.PLAINTIFF, "statement": "Refurbished unit sold deceitfully as new sealed product.", "amount": 85000.0, "status": GroundingStatusEnum.SUPPORTED},
                    {"party": ClaimPartyEnum.DEFENDANT, "statement": "Product was received sealed from distributor.", "amount": 0.0, "status": GroundingStatusEnum.UNSUPPORTED},
                ],
                "events": [
                    {"date_raw_str": "10 October 2023", "title": "OEM Warranty Activation", "description": "Manufacturer database records initial warranty registration.", "party": "PLAINTIFF"},
                    {"date_raw_str": "25 April 2024", "title": "Purchase by Neha Gupta", "description": "Invoiced as 'Brand New Sealed Retail Unit'.", "party": "DEFENDANT", "conflict_flag": True, "conflict_notes": "⚠️ TIMELINE CONFLICT: Warranty active 6 months before customer purchase date."},
                ],
                "evidence": [
                    {"title": "Tax Invoice #GS-2024-881", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "INVOICE", "text": "Sold: ProBook Laptop Serial #SN-998822 ₹85,000 Brand New Sealed."},
                    {"title": "OEM Warranty Verification Certificate", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "NOTICE", "text": "Official Portal: Serial #SN-998822 initial activation date: 10-Oct-2023. Warranty remaining: 6 months."},
                ],
            },
            {
                "case_number": "AAD-2026-005",
                "title": "Digital Payment & Service Dispute: Amit Patel vs. DesignStudio LLP",
                "case_type": "CONTRACT",
                "jurisdiction": "Commercial Court, Ahmedabad",
                "description": "Client paid ₹1,20,000 for custom software and web application. Studio failed to deliver working code and refused refund claiming it was non-refundable advance.",
                "plaintiff_name": "Amit Patel",
                "defendant_name": "DesignStudio LLP",
                "disputed_amount": 120000.0,
                "claims": [
                    {"party": ClaimPartyEnum.PLAINTIFF, "statement": "Complete failure of consideration and failure to deliver agreed milestones.", "amount": 120000.0, "status": GroundingStatusEnum.SUPPORTED},
                    {"party": ClaimPartyEnum.DEFENDANT, "statement": "Payment was non-refundable retainer for creative research.", "amount": 120000.0, "status": GroundingStatusEnum.CONFLICTING},
                ],
                "events": [
                    {"date_raw_str": "05 January 2024", "title": "Scope of Work Agreed", "description": "Scope email detailing 4 milestones with milestone-based payout.", "party": "PLAINTIFF"},
                    {"date_raw_str": "10 January 2024", "title": "UPI & Bank Transfer ₹1,20,000", "description": "Payment credited for Milestone 1 & 2 deliverables.", "party": "PLAINTIFF"},
                    {"date_raw_str": "28 February 2024", "title": "Project Abandoned", "description": "Agency ceased communication without deploying source code.", "party": "PLAINTIFF"},
                ],
                "evidence": [
                    {"title": "Scope of Work Document (Email)", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "CONTRACT", "text": "Payment schedule: 50% on wireframe approval, 50% on live deployment."},
                    {"title": "Payment Receipts (₹1,20,000)", "party": EvidencePartyEnum.PLAINTIFF, "doc_type": "BANK_RECORD", "text": "Transaction Ref: ICICI00192834 ₹1,20,000 credited to DesignStudio LLP."},
                ],
            },
        ]

        for c_spec in demo_cases_spec:
            res = await db.execute(select(Case).where(Case.case_number == c_spec["case_number"]))
            existing_case = res.scalars().first()
            if not existing_case:
                case = Case(
                    case_number=c_spec["case_number"],
                    title=c_spec["title"],
                    case_type=c_spec["case_type"],
                    jurisdiction=c_spec["jurisdiction"],
                    description=c_spec["description"],
                    status=CaseStatusEnum.READY_FOR_HEARING,
                    metadata_json={
                        "plaintiff_name": c_spec["plaintiff_name"],
                        "defendant_name": c_spec["defendant_name"],
                        "disputed_amount": c_spec["disputed_amount"],
                    },
                )
                db.add(case)
                await db.flush()

                # Add Parties
                db.add(Party(case_id=case.id, name=c_spec["plaintiff_name"], role=PartyRoleEnum.PLAINTIFF))
                db.add(Party(case_id=case.id, name=c_spec["defendant_name"], role=PartyRoleEnum.DEFENDANT))

                # Add Claims
                for cl in c_spec["claims"]:
                    db.add(Claim(
                        case_id=case.id,
                        party=cl["party"],
                        claim_type="SUBSTANTIVE",
                        statement=cl["statement"],
                        amount=cl["amount"],
                        grounding_status=cl["status"],
                        grounding_confidence=0.92,
                    ))

                # Add Evidence
                for ev in c_spec["evidence"]:
                    ev_hash = f"hash_{case.case_number}_{ev['title'][:10]}".replace(" ", "_")
                    db_ev = Evidence(
                        case_id=case.id,
                        party=ev["party"],
                        title=ev["title"],
                        document_type=ev["doc_type"],
                        source="DEMO_BUNDLE",
                        verification_status=EvidenceStatusEnum.VERIFIED,
                        file_hash=ev_hash,
                        extracted_text=ev["text"],
                        extraction_metadata={"source": "Fictional Demo Case Bundle", "disclaimer": "NOT A REAL COURT RECORD"},
                    )
                    db.add(db_ev)
                    await db.flush()

                    db.add(EvidenceChunk(
                        evidence_id=db_ev.id,
                        chunk_index=0,
                        chunk_text=ev["text"],
                        embedding=EmbeddingService.embed_text(ev["text"]),
                        metadata_json={"page": 1},
                    ))

                # Add Events
                for evnt in c_spec["events"]:
                    db.add(Event(
                        case_id=case.id,
                        date_raw_str=evnt["date_raw_str"],
                        title=evnt["title"],
                        description=evnt["description"],
                        party=evnt["party"],
                        conflict_flag=evnt.get("conflict_flag", False),
                        conflict_notes=evnt.get("conflict_notes"),
                    ))

        await db.commit()
        print("✅ 5 Benchmark Demo Cases seeded with evidence, claims, and timeline.")

    print("🎉 Database Seeding Complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
