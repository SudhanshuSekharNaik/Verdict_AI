from typing import Any, Dict, List, Optional

# Official Indian Legal Knowledge Base
# Sources: Official Ministry of Home Affairs (MHA) & India Code (indiacode.nic.in)
INDIAN_LAW_DATABASE: List[Dict[str, Any]] = [
    # --- Bharatiya Nyaya Sanhita, 2023 (BNS) ---
    {
        "id": "BNS_303",
        "act": "Bharatiya Nyaya Sanhita, 2023",
        "act_code": "BNS",
        "section_or_article": "Section 303",
        "type": "Section",
        "title": "Theft",
        "official_text": (
            "(1) Whoever, intending to take dishonestly any movable property out of the possession of any person "
            "without that person's consent, moves that property in order to such taking, is said to commit theft.\n\n"
            "(2) Whoever commits theft shall be punished with imprisonment of either description for a term which may extend "
            "to three years, or with fine, or with both; and in case of second or subsequent conviction, with rigorous imprisonment "
            "for a term which shall not be less than one year but which may extend to five years and with fine."
        ),
        "plain_explanation": (
            "Theft occurs when someone dishonestly moves or takes any movable item belonging to another person without "
            "their permission, intending to permanently deprive them of it."
        ),
        "case_relevance": (
            "Directly applicable to allegations concerning the unauthorized removal and dishonest taking of movable property "
            "(such as electronics, office equipment, or personal belongings) without consent."
        ),
        "elements_to_establish": [
            "1. Property must be movable (e.g. laptop, equipment, documents)",
            "2. Property was in possession of another person",
            "3. Taking was without the possessor's consent",
            "4. Property was physically moved or removed",
            "5. Dishonest intention (mens rea) existed at the time of moving"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy IPC Section 379",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22477",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Potentially applicable primary offence"
    },
    {
        "id": "BNS_305",
        "act": "Bharatiya Nyaya Sanhita, 2023",
        "act_code": "BNS",
        "section_or_article": "Section 305",
        "type": "Section",
        "title": "Theft in dwelling house, or place used for custody of property",
        "official_text": (
            "Whoever commits theft in any building, tent or vessel, which building, tent or vessel is used as a human "
            "dwelling, or used for the custody of property, shall be punished with imprisonment of either description for a "
            "term which may extend to seven years, and shall also be liable to fine."
        ),
        "plain_explanation": (
            "Aggravated theft committed inside a building, office, or secured premise used for custody of property."
        ),
        "case_relevance": (
            "Relevant when an alleged theft occurs within locked commercial premises, office rooms, or secure corporate offices."
        ),
        "elements_to_establish": [
            "1. Commission of theft as defined under Section 303",
            "2. Offence occurred inside a building, office, or custody room"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy IPC Section 380",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22477",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Potentially relevant aggravated provision"
    },
    {
        "id": "BNS_316",
        "act": "Bharatiya Nyaya Sanhita, 2023",
        "act_code": "BNS",
        "section_or_article": "Section 316",
        "type": "Section",
        "title": "Criminal breach of trust",
        "official_text": (
            "(1) Whoever, being in any manner entrusted with property, or with any dominion over property, dishonestly "
            "misappropriates or converts to his own use that property... commits criminal breach of trust."
        ),
        "plain_explanation": (
            "Occurs when an employee or trustee entrusted with property dishonestly converts or misuses it for personal gain."
        ),
        "case_relevance": "Applicable where the accused had lawful custody or fiduciary access to the property before alleged misappropriation.",
        "elements_to_establish": [
            "1. Entrustment of property to the accused",
            "2. Dishonest misappropriation or conversion to own use"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy IPC Section 405/406",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22477",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Alternative offence consideration"
    },
    {
        "id": "BNS_318",
        "act": "Bharatiya Nyaya Sanhita, 2023",
        "act_code": "BNS",
        "section_or_article": "Section 318",
        "type": "Section",
        "title": "Cheating",
        "official_text": (
            "(1) Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any "
            "property to any person... is said to cheat."
        ),
        "plain_explanation": "Deceiving someone dishonestly to obtain property or financial gain.",
        "case_relevance": "Applicable where misrepresentation or deception was used to acquire property or sell stolen goods.",
        "elements_to_establish": [
            "1. Deception of a person",
            "2. Fraudulent or dishonest inducement to deliver property"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy IPC Section 415/420",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22477",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Supplementary commercial consideration"
    },

    # --- Bharatiya Sakshya Adhiniyam, 2023 (BSA - Evidence Law) ---
    {
        "id": "BSA_104",
        "act": "Bharatiya Sakshya Adhiniyam, 2023",
        "act_code": "BSA",
        "section_or_article": "Section 104",
        "type": "Section",
        "title": "Burden of proof",
        "official_text": (
            "Whoever desires any Court to give judgment as to any legal right or liability dependent on the existence of "
            "facts which he asserts, must prove that those facts exist. When a person is bound to prove the existence of any "
            "fact, it is said that the burden of proof lies on that person."
        ),
        "plain_explanation": (
            "In criminal matters, the burden of proving all elements of the offence rests entirely on the prosecution, "
            "which must establish guilt beyond a reasonable doubt."
        ),
        "case_relevance": "Fundamental evidentiary rule governing the allocation of proof and the standard of reasonable doubt.",
        "elements_to_establish": [
            "1. Prosecution bears the affirmative burden of proving guilt",
            "2. Burden does not shift to defense merely on suspicion",
            "3. Evidentiary gaps or inconclusive identification favor the accused"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy Indian Evidence Act, 1872 Section 101",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22479",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Crucial evidentiary standard"
    },
    {
        "id": "BSA_61",
        "act": "Bharatiya Sakshya Adhiniyam, 2023",
        "act_code": "BSA",
        "section_or_article": "Section 61",
        "type": "Section",
        "title": "Admissibility of electronic records",
        "official_text": (
            "Nothing in this Adhiniyam shall apply to electronic records... any information contained in an electronic record "
            "which is printed on a paper, stored, recorded or copied in optical or magnetic media produced by a computer shall "
            "be deemed to be also a document... and shall be admissible in any proceedings."
        ),
        "plain_explanation": "Regulates the admissibility, certificate requirements, and evidentiary weight of CCTV footage, digital logs, and computer records.",
        "case_relevance": "Applicable to CCTV footage from Orion Technologies corridors and time-stamped entry records.",
        "elements_to_establish": [
            "1. Integrity of the digital security footage",
            "2. Verification that video captures entry/exit without internal room surveillance"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy Indian Evidence Act, 1872 Section 65B",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22479",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Relevant to security video proof"
    },
    {
        "id": "BSA_117",
        "act": "Bharatiya Sakshya Adhiniyam, 2023",
        "act_code": "BSA",
        "section_or_article": "Section 117",
        "type": "Section",
        "title": "Burden of proving fact especially within knowledge",
        "official_text": (
            "When any fact is especially within the knowledge of any person, the burden of proving that fact is upon him."
        ),
        "plain_explanation": "Explaining why someone was in a specific locked room or what was in their backpack when such facts are within their personal knowledge.",
        "case_relevance": "Relates to defendant's statement explaining his reason for entering the office to collect personal documents.",
        "elements_to_establish": [
            "1. Special knowledge of personal items in backpack",
            "2. Innocent explanation for presence in authorized room"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy Indian Evidence Act, 1872 Section 106",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22479",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Relevant to explanation of presence"
    },

    # --- Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS - Procedural Law) ---
    {
        "id": "BNSS_35",
        "act": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "act_code": "BNSS",
        "section_or_article": "Section 35",
        "type": "Section",
        "title": "When police may arrest without warrant",
        "official_text": (
            "Any police officer may without an order from a Magistrate and without a warrant, arrest any person who commits, "
            "in the presence of a police officer, a cognizable offence, or against whom a reasonable complaint has been made, "
            "or credible information has been received, or a reasonable suspicion exists of having been so concerned."
        ),
        "plain_explanation": "Sets statutory conditions and procedural safeguards required for police arrest in cognizable property offences.",
        "case_relevance": "Procedural context for investigation and suspect detention.",
        "elements_to_establish": [
            "1. Cognizable offence alleged",
            "2. Reasonable suspicion based on credible inquiry"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy CrPC Section 41",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22478",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Procedural reference"
    },
    {
        "id": "BNSS_173",
        "act": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "act_code": "BNSS",
        "section_or_article": "Section 173",
        "type": "Section",
        "title": "Information in cognizable cases (First Information Report)",
        "official_text": (
            "Every information relating to the commission of a cognizable offence, if given orally to an officer in charge of "
            "a police station, shall be reduced to writing by him or under his direction..."
        ),
        "plain_explanation": "Procedure for filing FIR and initiating criminal investigation into reported thefts.",
        "case_relevance": "Procedural basis for theft complaint filed by Neha Sharma at 9:30 PM.",
        "elements_to_establish": [
            "1. Formal recording of the initial complaint",
            "2. Prompt reporting of property loss"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy CrPC Section 154",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22478",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Procedural reference"
    },

    # --- Constitution of India ---
    {
        "id": "CONST_20_3",
        "act": "Constitution of India",
        "act_code": "Constitution",
        "section_or_article": "Article 20(3)",
        "type": "Article",
        "title": "Protection against self-incrimination",
        "official_text": (
            "No person accused of any offence shall be compelled to be a witness against himself."
        ),
        "plain_explanation": (
            "An accused person has an absolute constitutional right to remain silent and cannot be compelled to give testimony "
            "or confession against themselves."
        ),
        "case_relevance": "Protects the defendant's right to deny the allegation without drawing an adverse presumption of guilt from silence.",
        "elements_to_establish": [
            "1. Accused status",
            "2. Immunity from compelled self-incrimination"
        ],
        "is_legacy": False,
        "legacy_mapping": None,
        "source_url": "https://www.indiacode.nic.in/handle/123456789/1522",
        "effective_date": "26 January 1950",
        "verified_date": "August 2026",
        "applicability_status": "Constitutional protection"
    },
    {
        "id": "CONST_21",
        "act": "Constitution of India",
        "act_code": "Constitution",
        "section_or_article": "Article 21",
        "type": "Article",
        "title": "Protection of life and personal liberty (Right to Fair Trial)",
        "official_text": (
            "No person shall be deprived of his life or personal liberty except according to procedure established by law."
        ),
        "plain_explanation": (
            "Guarantees that no individual can be convicted or deprived of liberty without a fair, impartial trial conducted "
            "under strict procedures established by law."
        ),
        "case_relevance": "Guarantees fair trial rights and standard of proof before deprivation of personal liberty.",
        "elements_to_establish": [
            "1. Fair procedure established by law",
            "2. Impartial adjudication and presumption of innocence"
        ],
        "is_legacy": False,
        "legacy_mapping": None,
        "source_url": "https://www.indiacode.nic.in/handle/123456789/1522",
        "effective_date": "26 January 1950",
        "verified_date": "August 2026",
        "applicability_status": "Fundamental fair trial guarantee"
    },

    # --- Homicide, Murder & Affirmative Defenses (BNS / IPC / Evidence Law) ---
    {
        "id": "BNS_103",
        "act": "Bharatiya Nyaya Sanhita, 2023",
        "act_code": "BNS",
        "section_or_article": "Section 103",
        "type": "Section",
        "title": "Punishment for murder",
        "official_text": (
            "(1) Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine.\n\n"
            "Except in cases hereinafter excepted, culpable homicide is murder if the act by which the death is caused is done with the "
            "intention of causing death, or with the intention of causing such bodily injury as the offender knows to be likely to cause death."
        ),
        "plain_explanation": (
            "Statutory offence of intentional killing or intentionally inflicting fatal bodily injuries without lawful justification."
        ),
        "case_relevance": "Directly applicable to charges of intentional homicide, shooting, stabbing, or fatal violence.",
        "elements_to_establish": [
            "1. Death of a human being caused by the accused",
            "2. Actus reus: Act causing death committed by the accused",
            "3. Mens rea: Intention to cause death or fatal bodily injury known to cause death",
            "4. Absence of general exceptions or statutory mitigations"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy IPC Section 300 / 302",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22477",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Primary homicide provision"
    },
    {
        "id": "IPC_302",
        "act": "Indian Penal Code, 1860 (Legacy)",
        "act_code": "IPC",
        "section_or_article": "Section 302",
        "type": "Section",
        "title": "Punishment for murder",
        "official_text": (
            "Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine."
        ),
        "plain_explanation": (
            "Historical and substantive Indian Penal Code provision defining capital punishment or life imprisonment for intentional murder."
        ),
        "case_relevance": "Applicable to historical landmark proceedings and criminal trials charged under IPC §302.",
        "elements_to_establish": [
            "1. Causing of death of the victim",
            "2. Intention of causing death or fatal injury",
            "3. Absence of applicable exceptions under Section 300"
        ],
        "is_legacy": True,
        "legacy_mapping": "Corresponds to BNS Section 103 (Current Law)",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/2263",
        "effective_date": "Historical / Pre-2024 Offenses",
        "verified_date": "August 2026",
        "applicability_status": "Primary historical murder statute"
    },
    {
        "id": "IPC_300_EX1",
        "act": "Indian Penal Code, 1860 (Legacy)",
        "act_code": "IPC",
        "section_or_article": "Section 300, Exception 1",
        "type": "Section",
        "title": "Grave and sudden provocation (Mitigating Exception to Murder)",
        "official_text": (
            "Exception 1.—When culpable homicide is not murder.—Culpable homicide is not murder if the offender, "
            "whilst deprived of the power of self-control by grave and sudden provocation, causes the death of the person who gave the provocation...\n\n"
            "Provided that the provocation is not sought or voluntarily provoked by the offender as an excuse for killing or doing harm to any person."
        ),
        "plain_explanation": (
            "Mitigates murder to culpable homicide not amounting to murder ONLY if the killing occurred under the immediate, "
            "unbroken loss of self-control caused by grave AND sudden provocation. If there was an intervening interval of time "
            "and intermediate deliberate actions (cooling-off period), the element of suddenness is defeated as a matter of law."
        ),
        "case_relevance": (
            "Governs affirmative provocation defenses. Under landmark Supreme Court jurisprudence (K.M. Nanavati v. State of Maharashtra AIR 1962 SC 605), "
            "infidelity confession is grave provocation, but the defense fails if intermediate deliberate actions demonstrate cooling off / deliberation."
        ),
        "elements_to_establish": [
            "1. Provocation must be grave (capable of causing a reasonable person to lose self-control)",
            "2. Provocation must be SUDDEN (immediate, without cooling-off period)",
            "3. Fatal act must occur whilst deprived of self-control before passion cools",
            "4. Intervening sequence of deliberate acts (travel, weapon retrieval under pretext) defeats suddenness"
        ],
        "is_legacy": True,
        "legacy_mapping": "Corresponds to Exception 1 to BNS Section 103(1)",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/2263",
        "effective_date": "Historical / Pre-2024 Offenses",
        "verified_date": "August 2026",
        "applicability_status": "Crucial affirmative defense exception"
    },
    {
        "id": "IPC_304",
        "act": "Indian Penal Code, 1860 (Legacy)",
        "act_code": "IPC",
        "section_or_article": "Section 304 (Part I)",
        "type": "Section",
        "title": "Punishment for culpable homicide not amounting to murder",
        "official_text": (
            "Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life, "
            "or imprisonment of either description for a term which may extend to ten years, and shall also be liable to fine, "
            "if the act by which the death is caused is done with the intention of causing death..."
        ),
        "plain_explanation": (
            "Punishment applicable when intentional killing falls within one of the statutory exceptions (such as grave and sudden provocation) to Section 300."
        ),
        "case_relevance": "Alternative lesser charge sought by defense when arguing mitigating exceptions under Section 300.",
        "elements_to_establish": [
            "1. Culpable homicide established",
            "2. Statutory exception to Section 300 proven on preponderance of probabilities"
        ],
        "is_legacy": True,
        "legacy_mapping": "Corresponds to BNS Section 105",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/2263",
        "effective_date": "Historical / Pre-2024 Offenses",
        "verified_date": "August 2026",
        "applicability_status": "Alternative mitigating charge"
    },
    {
        "id": "BSA_108",
        "act": "Bharatiya Sakshya Adhiniyam, 2023",
        "act_code": "BSA",
        "section_or_article": "Section 108",
        "type": "Section",
        "title": "Burden of proving that case of accused comes within exceptions",
        "official_text": (
            "When a person is accused of any offence, the burden of proving the existence of circumstances bringing the case "
            "within any of the General Exceptions in the Bharatiya Nyaya Sanhita, 2023, or within any special exception or proviso "
            "contained in any other part of the same Sanhita, or in any law defining the offence, is upon him, and the Court shall presume the absence of such circumstances."
        ),
        "plain_explanation": (
            "When the defense raises an affirmative defense or exception (such as provocation, private defense, or accident), "
            "the legal burden is on the accused to establish the exception on a preponderance of probabilities."
        ),
        "case_relevance": "Directly controls the evidentiary burden for affirmative defenses under Exception 1 to IPC §300 / BNS §103.",
        "elements_to_establish": [
            "1. Legal presumption of absence of mitigating exception",
            "2. Burden of proof rests upon the accused to establish all elements of the exception on preponderance of probabilities",
            "3. Accused must prove both gravity AND suddenness without intervening cooling-off"
        ],
        "is_legacy": False,
        "legacy_mapping": "Corresponds to legacy Indian Evidence Act, 1872 Section 105",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/22479",
        "effective_date": "1 July 2024",
        "verified_date": "August 2026",
        "applicability_status": "Evidentiary rule on defense exceptions"
    },
    # --- Historical / Legacy Indian Penal Code (IPC, 1860) ---
    {
        "id": "IPC_379",
        "act": "Indian Penal Code, 1860 (Legacy)",
        "act_code": "IPC",
        "section_or_article": "Section 379",
        "type": "Section",
        "title": "Punishment for theft (Historical provision)",
        "official_text": (
            "Whoever commits theft shall be punished with imprisonment of either description for a term which may extend to "
            "three years, or with fine, or with both."
        ),
        "plain_explanation": "Historical penalty provision for theft prior to 1 July 2024.",
        "case_relevance": "Historical statutory comparison. Superseded by Section 303 of Bharatiya Nyaya Sanhita, 2023 for new offences.",
        "elements_to_establish": [
            "1. Historical theft definition under Section 378 IPC",
            "2. Note: For offences committed on or after 1 July 2024, BNS Section 303 applies."
        ],
        "is_legacy": True,
        "legacy_mapping": "Superseded by BNS Section 303 (Current Law)",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/2263",
        "effective_date": "Historical (Superseded on 1 July 2024)",
        "verified_date": "August 2026",
        "applicability_status": "Legacy / historical provision"
    }
]


def search_laws(
    query: str = "",
    source_filter: Optional[str] = None,
    type_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Searches the Indian Law Database with query and source filtering."""
    q = query.strip().lower()
    results = []

    for item in INDIAN_LAW_DATABASE:
        if source_filter and source_filter.lower() != "all":
            if item["act_code"].lower() != source_filter.lower() and source_filter.lower() not in item["act"].lower():
                continue

        if type_filter and type_filter.lower() != "all":
            if item["type"].lower() != type_filter.lower():
                continue

        if q:
            searchable = (
                f"{item['act']} {item['section_or_article']} {item['title']} "
                f"{item['plain_explanation']} {item['official_text']} {item.get('legacy_mapping','')}"
            ).lower()
            if q not in searchable:
                continue

        results.append(item)

    return results


def get_provision_by_id(provision_id: str) -> Optional[Dict[str, Any]]:
    for item in INDIAN_LAW_DATABASE:
        if item["id"] == provision_id:
            return item
    return None


def match_applicable_laws(facts: str, charge: str) -> List[Dict[str, Any]]:
    """
    Identifies potentially applicable statutory and constitutional provisions
    based on case facts and charge, prioritizing current Bharatiya laws.
    """
    matched: List[Dict[str, Any]] = []
    charge_lower = charge.lower()
    facts_lower = facts.lower()

    # 1. Primary Offence Matching
    if any(k in charge_lower or k in facts_lower for k in ["murder", "homicide", "302", "304", "provocation", "nanavati", "shot", "shooting", "stab"]):
        if "ipc" in charge_lower or "1860" in charge_lower or "nanavati" in charge_lower or "302" in charge_lower:
            ipc_302 = get_provision_by_id("IPC_302")
            if ipc_302:
                matched.append(ipc_302)
            ipc_300 = get_provision_by_id("IPC_300_EX1")
            if ipc_300:
                matched.append(ipc_300)
            ipc_304 = get_provision_by_id("IPC_304")
            if ipc_304:
                matched.append(ipc_304)
        else:
            bns_103 = get_provision_by_id("BNS_103")
            if bns_103:
                matched.append(bns_103)
            ipc_300 = get_provision_by_id("IPC_300_EX1")
            if ipc_300:
                matched.append(ipc_300)

        bsa_108 = get_provision_by_id("BSA_108")
        if bsa_108:
            matched.append(bsa_108)

    if "theft" in charge_lower or "stolen" in facts_lower or "stole" in facts_lower:
        bns_303 = get_provision_by_id("BNS_303")
        if bns_303:
            matched.append(bns_303)
        bns_305 = get_provision_by_id("BNS_305")
        if bns_305 and ("office" in facts_lower or "building" in facts_lower or "room" in facts_lower):
            matched.append(bns_305)

    if "trust" in charge_lower or "misappropriation" in charge_lower:
        bns_316 = get_provision_by_id("BNS_316")
        if bns_316:
            matched.append(bns_316)

    if "cheat" in charge_lower or "fraud" in charge_lower:
        bns_318 = get_provision_by_id("BNS_318")
        if bns_318:
            matched.append(bns_318)

    # 2. Evidentiary Rules (BSA)
    bsa_104 = get_provision_by_id("BSA_104")
    if bsa_104 and bsa_104 not in matched:
        matched.append(bsa_104)

    if "footage" in facts_lower or "cctv" in facts_lower or "security" in facts_lower or "electronic" in facts_lower:
        bsa_61 = get_provision_by_id("BSA_61")
        if bsa_61:
            matched.append(bsa_61)

    # 3. Procedural Law (BNSS)
    if "arrest" in facts_lower or "police" in facts_lower or "fir" in facts_lower:
        bnss_173 = get_provision_by_id("BNSS_173")
        if bnss_173:
            matched.append(bnss_173)

    # 4. Constitutional Considerations
    const_21 = get_provision_by_id("CONST_21")
    if const_21 and const_21 not in matched:
        matched.append(const_21)

    # Fallback to general provisions if empty
    if not matched:
        matched = [get_provision_by_id("BNS_303"), get_provision_by_id("BSA_104"), get_provision_by_id("CONST_21")]

    return [m for m in matched if m]


def generate_case_issues(facts: str, charge: str) -> List[Dict[str, Any]]:
    """
    Extracts structured issues before the court based on the charge and canonical facts.
    """
    charge_lower = charge.lower()
    facts_lower = facts.lower()
    
    if any(k in charge_lower or k in facts_lower for k in ["murder", "homicide", "provocation", "nanavati", "302", "304", "exception 1", "ahuja"]):
        return [
            {
                "issue_id": "ISSUE_01",
                "question": "Whether the accused committed the physical acts causing the death of the deceased (actus reus).",
                "prosecution_position": "Supports — The accused discharged the firearm striking the deceased three times, causing fatal injuries.",
                "defense_position": "Concedes the physical discharge during struggle, but contends the fatal shots occurred in sudden scuffle without premeditation.",
                "judge_finding": "Pending deliberation",
                "finding_rationale": ""
            },
            {
                "issue_id": "ISSUE_02",
                "question": "Whether the interval of time and deliberate sequence of actions between the triggering provocation and the shooting (cooling-off period) negates the element of suddenness under Exception 1 to Section 300 IPC / BNS §103.",
                "prosecution_position": "Supports — Intervening interval (dropping family at cinema, boarding naval ship, procuring revolver under false pretext, traveling across Bombay) provided ample time to cool down and reflect, negating suddenness as a matter of law.",
                "defense_position": "Disputes — Accused remained in continuous emotional shock and continuous agitation from wife's confession through the bedroom confrontation.",
                "judge_finding": "Pending deliberation",
                "finding_rationale": ""
            },
            {
                "issue_id": "ISSUE_03",
                "question": "Whether the evidence establishes murder beyond reasonable doubt under Section 302 IPC / BNS §103, or whether the defense has discharged its burden of proving mitigating circumstances under BSA §108 / IEA §105.",
                "prosecution_position": "Supports — All statutory elements of murder are proved beyond reasonable doubt; affirmative defense fails due to deliberate intermediate preparation.",
                "defense_position": "Challenges — Asserts entitlement to Exception 1 mitigation or acquittal under provocation doctrine.",
                "judge_finding": "Pending deliberation",
                "finding_rationale": ""
            }
        ]
    elif "theft" in charge_lower:
        return [
            {
                "issue_id": "ISSUE_01",
                "question": "Whether the defendant (Arjun Mehta) moved or took the laptop from Neha Sharma's desk.",
                "prosecution_position": "Supports — Exclusive presence and departure with backpack establishes removal.",
                "defense_position": "Disputes — No footage or eyewitness shows the laptop being touched or placed in bag.",
                "judge_finding": "Pending deliberation",
                "finding_rationale": ""
            },
            {
                "issue_id": "ISSUE_02",
                "question": "Whether any taking of the laptop was without the consent of the owner (Neha Sharma).",
                "prosecution_position": "Supports — Laptop was kept in locked office and reported stolen immediately.",
                "defense_position": "Disputes — Concedes lack of owner consent generally, but disputes defendant's involvement.",
                "judge_finding": "Pending deliberation",
                "finding_rationale": ""
            },
            {
                "issue_id": "ISSUE_03",
                "question": "Whether the defendant possessed the requisite dishonest intention (mens rea) to permanently deprive.",
                "prosecution_position": "Supports — Subsequent appearance of laptop at second-hand shop indicates intent to dispose.",
                "defense_position": "Challenges — Defendant entered solely to collect documents; no proof connecting him to resale.",
                "judge_finding": "Pending deliberation",
                "finding_rationale": ""
            },
            {
                "issue_id": "ISSUE_04",
                "question": "Whether the circumstantial evidence is sufficient to establish guilt beyond reasonable doubt under BSA §104.",
                "prosecution_position": "Supports — Totality of opportunity, container, and shopkeeper description satisfies burden.",
                "defense_position": "Challenges — Lack of fingerprints, DNA, positive ID, and 12-minute window leaves reasonable doubt.",
                "judge_finding": "Pending deliberation",
                "finding_rationale": ""
            }
        ]
    else:
        return [
            {
                "issue_id": "ISSUE_01",
                "question": "Whether the acts alleged in the charge were committed by the defendant.",
                "prosecution_position": "Supports",
                "defense_position": "Disputes",
                "judge_finding": "Pending deliberation",
                "finding_rationale": ""
            },
            {
                "issue_id": "ISSUE_02",
                "question": "Whether the required mental state (mens rea) is established by the factual record.",
                "prosecution_position": "Supports",
                "defense_position": "Challenges",
                "judge_finding": "Pending deliberation",
                "finding_rationale": ""
            },
            {
                "issue_id": "ISSUE_03",
                "question": "Whether the evidence meets the legal standard of proof required by law.",
                "prosecution_position": "Supports",
                "defense_position": "Challenges",
                "judge_finding": "Pending deliberation",
                "finding_rationale": ""
            }
        ]
