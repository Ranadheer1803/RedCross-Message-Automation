import logging
from typing import Dict, List, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)

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

def clean_value(val, default=""):
    if pd.isna(val) or val is None:
        return default
    return str(val).strip()

class Neo4jManager:
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.connected = False
        self.error_message = ""
        
    def connect(self) -> bool:
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

    def clear_all_database(self) -> bool:
        """Purge all Person nodes from Neo4j while retaining BloodGroup schema."""
        if not self.connected or not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run("MATCH (p:Person) DETACH DELETE p")
            return True
        except Exception as e:
            logging.error(f"Error purging Neo4j database: {e}")
            return False

    def upsert_donor(self, donor_dict: Dict) -> bool:
        if not self.connected or not self.driver:
            return False
            
        phone = clean_value(donor_dict.get('phone'))
        if not phone:
            return False
            
        name = clean_value(donor_dict.get('name'), "Unknown Donor")
        blood_group = clean_value(donor_dict.get('blood_group'), "O+")
        dob = clean_value(donor_dict.get('dob'))
        last_donation = clean_value(donor_dict.get('last_donation'))
        location = clean_value(donor_dict.get('location'), "General")
        is_eligible = bool(donor_dict.get('is_eligible', True))
        
        query = """
        MERGE (p:Person {phone: $phone})
        SET p.name = $name,
            p.blood_group = $blood_group,
            p.dob = $dob,
            p.last_donation = $last_donation,
            p.location = $location,
            p.is_eligible = $is_eligible
            
        MERGE (bg:BloodGroup {type: $blood_group})
        MERGE (p)-[:HAS_BLOOD_GROUP]->(bg)
        
        FOREACH (_ IN CASE WHEN $location IS NOT NULL AND $location <> '' THEN [1] ELSE [] END |
            MERGE (loc:Location {name: $location})
            MERGE (p)-[:LIVES_IN]->(loc)
        )
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, 
                    phone=phone,
                    name=name,
                    blood_group=blood_group,
                    dob=dob,
                    last_donation=last_donation,
                    location=location,
                    is_eligible=is_eligible
                )
            return True
        except Exception as e:
            logging.error(f"Error upserting donor to Neo4j: {e}")
            return False

    def delete_donor(self, phone: str) -> bool:
        if not self.connected or not self.driver:
            return False
        clean_p = clean_value(phone)
        if not clean_p:
            return False
        query = "MATCH (p:Person {phone: $phone}) DETACH DELETE p"
        try:
            with self.driver.session() as session:
                session.run(query, phone=clean_p)
            return True
        except Exception as e:
            logging.error(f"Error deleting donor from Neo4j: {e}")
            return False

    def sync_dataframe(self, df: pd.DataFrame) -> int:
        if not self.connected or df is None or df.empty:
            return 0
        count = 0
        for idx, row in df.iterrows():
            if self.upsert_donor(row.to_dict()):
                count += 1
        return count

    def get_compatible_donors_graph(self, target_blood_group: str) -> List[Dict]:
        if not self.connected or not self.driver:
            return []
            
        query = """
        MATCH (target:BloodGroup {type: $target_bg})<-[:CAN_DONATE_TO]-(donor_bg:BloodGroup)<-[:HAS_BLOOD_GROUP]-(p:Person)
        RETURN p.name AS name, p.phone AS phone, donor_bg.type AS blood_group, p.dob AS dob, p.last_donation AS last_donation, p.location AS location, p.is_eligible AS is_eligible
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, target_bg=target_blood_group)
                return [record.data() for record in result]
        except Exception as e:
            logging.error(f"Error querying Neo4j graph: {e}")
            return []

    def get_neo4j_stats(self) -> Dict:
        if not self.connected or not self.driver:
            return {"status": "Disconnected", "person_count": 0, "rel_count": 0}
            
        try:
            with self.driver.session() as session:
                persons = session.run("MATCH (p:Person) RETURN count(p) AS cnt").single()["cnt"]
                rels = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]
                return {"status": "Connected", "person_count": persons, "rel_count": rels}
        except Exception:
            return {"status": "Connected (Error fetching stats)", "person_count": 0, "rel_count": 0}
