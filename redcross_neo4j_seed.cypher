// ===========================================================
// RED CROSS WEST GODAVARI — Neo4j Graph Database Seed Script
// ===========================================================

// 1. Create Constraints
CREATE CONSTRAINT person_phone_uniq IF NOT EXISTS FOR (p:Person) REQUIRE p.phone IS UNIQUE;
CREATE CONSTRAINT bg_type_uniq IF NOT EXISTS FOR (b:BloodGroup) REQUIRE b.type IS UNIQUE;

// 2. Create BloodGroup Nodes & CAN_DONATE_TO Edges
MERGE (:BloodGroup {type: 'A+'});
MERGE (:BloodGroup {type: 'A-'});
MERGE (:BloodGroup {type: 'B+'});
MERGE (:BloodGroup {type: 'B-'});
MERGE (:BloodGroup {type: 'O+'});
MERGE (:BloodGroup {type: 'O-'});
MERGE (:BloodGroup {type: 'AB+'});
MERGE (:BloodGroup {type: 'AB-'});

MATCH (d:BloodGroup {type: 'O-'}), (r:BloodGroup {type: 'O-'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O-'}), (r:BloodGroup {type: 'O+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O-'}), (r:BloodGroup {type: 'A-'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O-'}), (r:BloodGroup {type: 'A+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O-'}), (r:BloodGroup {type: 'B-'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O-'}), (r:BloodGroup {type: 'B+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O-'}), (r:BloodGroup {type: 'AB-'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O-'}), (r:BloodGroup {type: 'AB+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O+'}), (r:BloodGroup {type: 'O+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O+'}), (r:BloodGroup {type: 'A+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O+'}), (r:BloodGroup {type: 'B+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'O+'}), (r:BloodGroup {type: 'AB+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'A-'}), (r:BloodGroup {type: 'A-'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'A-'}), (r:BloodGroup {type: 'A+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'A-'}), (r:BloodGroup {type: 'AB-'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'A-'}), (r:BloodGroup {type: 'AB+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'A+'}), (r:BloodGroup {type: 'A+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'A+'}), (r:BloodGroup {type: 'AB+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'B-'}), (r:BloodGroup {type: 'B-'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'B-'}), (r:BloodGroup {type: 'B+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'B-'}), (r:BloodGroup {type: 'AB-'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'B-'}), (r:BloodGroup {type: 'AB+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'B+'}), (r:BloodGroup {type: 'B+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'B+'}), (r:BloodGroup {type: 'AB+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'AB-'}), (r:BloodGroup {type: 'AB-'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'AB-'}), (r:BloodGroup {type: 'AB+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);
MATCH (d:BloodGroup {type: 'AB+'}), (r:BloodGroup {type: 'AB+'}) MERGE (d)-[:CAN_DONATE_TO]->(r);

// 3. Create Person Nodes & HAS_BLOOD_GROUP Edges
MERGE (p:Person {phone: '+919848433131'})
SET p.name = 'Siva', p.dob = '', p.last_donation = '', p.location = 'Eluru, West Godavari'
WITH p
MATCH (bg:BloodGroup {type: 'O+'})
MERGE (p)-[:HAS_BLOOD_GROUP]->(bg);
MERGE (p:Person {phone: '+919247796949'})
SET p.name = 'usha', p.dob = '1998-05-15', p.last_donation = '2026-01-10', p.location = 'Eluru, West Godavari'
WITH p
MATCH (bg:BloodGroup {type: 'O+'})
MERGE (p)-[:HAS_BLOOD_GROUP]->(bg);