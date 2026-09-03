"""
Internal Graph Database Engine for RED CROSS WEST GODAVARI.
Implements Neo4j Graph Cypher traversal semantics locally:
(:Person)-[:HAS_BLOOD_GROUP]->(:BloodGroup)-[:CAN_DONATE_TO]->(:BloodGroup)
"""

import logging
from typing import Dict, List, Set

BLOOD_DONATION_MAP = {
    'O-': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'],
    'O+': ['O+', 'A+', 'B+', 'AB+'],
    'A-': ['A-', 'A+', 'AB-', 'AB+'],
    'A+': ['A+', 'AB+'],
    'B-': ['B-', 'B+', 'AB-', 'AB+'],
    'B+': ['B+', 'AB+'],
    'AB-': ['AB-', 'AB+'],
    'AB+': ['AB+']
}

# Reverse mapping: Recipient BG -> Compatible Donor BGs
COMPATIBLE_DONORS_FOR_RECIPIENT = {
    'O-': ['O-'],
    'O+': ['O-', 'O+'],
    'A-': ['O-', 'A-'],
    'A+': ['O-', 'O+', 'A-', 'A+'],
    'B-': ['O-', 'B-'],
    'B+': ['O-', 'O+', 'B-', 'B+'],
    'AB-': ['O-', 'A-', 'B-', 'AB-'],
    'AB+': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+']
}

class InMemGraphEngine:
    def __init__(self):
        self.person_nodes: Dict[str, Dict] = {}  # phone -> donor dict
        self.blood_groups: Set[str] = set(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'])
        self.can_donate_edges: Dict[str, List[str]] = BLOOD_DONATION_MAP

    def upsert_person(self, person_dict: Dict):
        phone = str(person_dict.get('phone', '')).strip()
        if not phone:
            return
        bg = str(person_dict.get('blood_group', 'O+')).strip().upper()
        person_dict['blood_group'] = bg
        self.person_nodes[phone] = person_dict

    def delete_person(self, phone: str):
        phone = str(phone).strip()
        if phone in self.person_nodes:
            del self.person_nodes[phone]

    def clear(self):
        self.person_nodes.clear()

    def query_compatible_donors(self, recipient_bg: str) -> List[Dict]:
        """
        Cypher Traversal Equivalent:
        MATCH (target:BloodGroup {type: $recipient_bg})<-[:CAN_DONATE_TO]-(donor_bg:BloodGroup)<-[:HAS_BLOOD_GROUP]-(p:Person)
        RETURN p
        """
        target_bg = str(recipient_bg).strip().upper()
        compatible_bgs = COMPATIBLE_DONORS_FOR_RECIPIENT.get(target_bg, [target_bg])

        matched_donors = []
        for phone, p in self.person_nodes.items():
            donor_bg = p.get('blood_group', '').strip().upper()
            if donor_bg in compatible_bgs:
                matched_donors.append(p)

        return matched_donors

    def generate_neo4j_cypher_seed_script(self, file_path: str = "redcross_neo4j_seed.cypher") -> str:
        """Generate ready-to-run Cypher script for Neo4j Desktop or AuraDB."""
        lines = [
            "// ===========================================================",
            "// RED CROSS WEST GODAVARI — Neo4j Graph Database Seed Script",
            "// ===========================================================",
            "",
            "// 1. Create Constraints",
            "CREATE CONSTRAINT person_phone_uniq IF NOT EXISTS FOR (p:Person) REQUIRE p.phone IS UNIQUE;",
            "CREATE CONSTRAINT bg_type_uniq IF NOT EXISTS FOR (b:BloodGroup) REQUIRE b.type IS UNIQUE;",
            "",
            "// 2. Create BloodGroup Nodes & CAN_DONATE_TO Edges"
        ]

        all_bgs = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
        for bg in all_bgs:
            lines.append(f"MERGE (:BloodGroup {{type: '{bg}'}});")

        lines.append("")
        for donor_bg, rec_list in BLOOD_DONATION_MAP.items():
            for rec_bg in rec_list:
                lines.append(
                    f"MATCH (d:BloodGroup {{type: '{donor_bg}'}}), (r:BloodGroup {{type: '{rec_bg}'}}) MERGE (d)-[:CAN_DONATE_TO]->(r);"
                )

        lines.append("")
        lines.append("// 3. Create Person Nodes & HAS_BLOOD_GROUP Edges")

        for phone, p in self.person_nodes.items():
            name = p.get('name', '').replace("'", "\\'")
            bg = p.get('blood_group', 'O+')
            dob = p.get('dob', '')
            last_don = p.get('last_donation', '')
            loc = p.get('location', '').replace("'", "\\'")

            lines.append(f"""MERGE (p:Person {{phone: '{phone}'}})
SET p.name = '{name}', p.dob = '{dob}', p.last_donation = '{last_don}', p.location = '{loc}'
WITH p
MATCH (bg:BloodGroup {{type: '{bg}'}})
MERGE (p)-[:HAS_BLOOD_GROUP]->(bg);""")

        cypher_content = "\n".join(lines)
        with open(file_path, "w") as f:
            f.write(cypher_content)

        return file_path
