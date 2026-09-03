import logging
from typing import Dict, List, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)

# Blood Compatibility Mapping: Who can donate to whom
BLOOD_DONATION_MAP = {
    'O-': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'], # Universal Donor
    'O+': ['O+', 'A+', 'B+', 'AB+'],
    'A-': ['A-', 'A+', 'AB-', 'AB+'],
    'A+': ['A+', 'AB+'],
    'B-': ['B-', 'B+', 'AB-', 'AB+'],
    'B+': ['B+', 'AB+'],
    'AB-': ['AB-', 'AB+'],
    'AB+': ['AB+'] # Universal Recipient
}

class Neo4jManager:
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.connected = False
        self.error_message = ""
        
    def connect(self) -> bool:
        """Attempt connection to Neo4j database."""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            self.connected = True
            self.error_message = ""
            self.initialize_schema()
            return True
        except Exception as e:
            self.connected = False
            self.error_message = str(e)
            logging.warning(f"Neo4j Connection Failed: {e}")
            return False

    def close(self):
        if self.driver:
            self.driver.close()

    def initialize_schema(self):
        """Create constraints, BloodGroup nodes, and CAN_DONATE_TO compatibility edges."""
        if not self.connected or not self.driver:
            return
            
        with self.driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT person_phone_uniq IF NOT EXISTS FOR (p:Person) REQUIRE p.phone IS UNIQUE")
                session.run("CREATE CONSTRAINT bg_type_uniq IF NOT EXISTS FOR (b:BloodGroup) REQUIRE b.type IS UNIQUE")
            except Exception as e:
                logging.info(f"Schema constraint init info: {e}")
                
            for donor_bg, recipients in BLOOD_DONATION_MAP.items():
                session.run("MERGE (b:BloodGroup {type: $bg})", bg=donor_bg)
                for recipient_bg in recipients:
                    session.run("MERGE (r:BloodGroup {type: $rec_bg})", rec_bg=recipient_bg)
                    session.run("""
                        MATCH (donor:BloodGroup {type: $donor_bg})
                        MATCH (rec:BloodGroup {type: $rec_bg})
                        MERGE (donor)-[:CAN_DONATE_TO]->(rec)
                    """, donor_bg=donor_bg, rec_bg=recipient_bg)

    def upsert_donor(self, donor_dict: Dict) -> bool:
        """Upsert a single donor node and relationships in Neo4j."""
        if not self.connected or not self.driver:
            return False
            
        phone = str(donor_dict.get('phone', '')).strip()
        if not phone:
            return False
            
        query = """
        MERGE (p:Person {phone: $phone})
        SET p.name = $name,
            p.blood_group = $blood_group,
            p.dob = $dob,
            p.last_donation = $last_donation,
            p.location = $location,
            p.is_eligible = $is_eligible,
            p.updated_at = timestamp()
            
        MERGE (bg:BloodGroup {type: $blood_group})
        MERGE (p)-[:HAS_BLOOD_GROUP]->(bg)
        
        FOREACH (_ IN CASE WHEN $location IS NOT NULL AND $location <> '' THEN [1] ELSE [] END |
            MERGE (loc:Location {name: $location})
            MERGE (p)-[:LIVES_IN]->(loc)
        )
        """
        
        with self.driver.session() as session:
            session.run(query, 
                phone=phone,
                name=donor_dict.get('name', ''),
                blood_group=donor_dict.get('blood_group', 'Unknown'),
                dob=str(donor_dict.get('dob', '')),
                last_donation=str(donor_dict.get('last_donation', '')),
                location=donor_dict.get('location', ''),
                is_eligible=bool(donor_dict.get('is_eligible', True))
            )
        return True

    def delete_donor(self, phone: str) -> bool:
        """Delete a donor node and its relationships from Neo4j."""
        if not self.connected or not self.driver:
            return False
        clean_p = str(phone).strip()
        query = "MATCH (p:Person {phone: $phone}) DETACH DELETE p"
        with self.driver.session() as session:
            session.run(query, phone=clean_p)
        return True

    def sync_dataframe(self, df: pd.DataFrame) -> int:
        """Sync entire dataframe to Neo4j."""
        if not self.connected or df is None or df.empty:
            return 0
        count = 0
        for idx, row in df.iterrows():
            if self.upsert_donor(row.to_dict()):
                count += 1
        return count

    def get_compatible_donors_graph(self, target_blood_group: str) -> List[Dict]:
        """Cypher Traversal: Find donors whose blood group CAN_DONATE_TO target blood group."""
        if not self.connected or not self.driver:
            return []
            
        query = """
        MATCH (target:BloodGroup {type: $target_bg})<-[:CAN_DONATE_TO]-(donor_bg:BloodGroup)<-[:HAS_BLOOD_GROUP]-(p:Person)
        RETURN p.name AS name, p.phone AS phone, donor_bg.type AS blood_group, p.dob AS dob, p.last_donation AS last_donation, p.location AS location, p.is_eligible AS is_eligible
        """
        with self.driver.session() as session:
            result = session.run(query, target_bg=target_blood_group)
            return [record.data() for record in result]

    def get_neo4j_stats(self) -> Dict:
        """Return counts of Person nodes, BloodGroup nodes, and relationships."""
        if not self.connected or not self.driver:
            return {"status": "Disconnected", "person_count": 0, "rel_count": 0}
            
        with self.driver.session() as session:
            persons = session.run("MATCH (p:Person) RETURN count(p) AS cnt").single()["cnt"]
            rels = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]
            return {"status": "Connected", "person_count": persons, "rel_count": rels}
