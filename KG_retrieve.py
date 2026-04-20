from neo4j import GraphDatabase
import json

URI      = "neo4j+s://2f6943ad.databases.neo4j.io"
USERNAME = "2f6943ad"
PASSWORD = "YOUR_PASSWORD_HERE"
DATABASE = "2f6943ad"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def run(query, **params):
    with driver.session(database=DATABASE) as session:
        return session.run(query, **params).data()

def print_section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

# ---------------------------------------------------------------
# 1. Graph Summary
# ---------------------------------------------------------------
def get_graph_summary():
    print_section(" GRAPH SUMMARY")
    results = run("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC")
    print(f"  {'Node Type':<20} {'Count':>6}")
    print(f"  {'-'*28}")
    total = 0
    for r in results:
        print(f"  {str(r['label']):<20} {r['count']:>6}")
        total += r['count']
    print(f"  {'-'*28}")
    print(f"  {'TOTAL':<20} {total:>6}")

    rel = run("MATCH ()-[r]->() RETURN count(r) AS c")
    print(f"\n  Total Relationships: {rel[0]['c']}")

# ---------------------------------------------------------------
# 2. Get all institutions
# ---------------------------------------------------------------
def get_institutions():
    print_section("  ALL INSTITUTIONS (ආයතන)")
    results = run("MATCH (a:ආයතනය) RETURN a.name AS name, a.type AS type, a.short_name AS short ORDER BY a.id")
    for r in results:
        short = f"[{r['short']}]" if r['short'] else ""
        print(f"  • {r['name']} {short}")
        print(f"    Type: {r['type']}")

# ---------------------------------------------------------------
# 3. Get CAA objectives
# ---------------------------------------------------------------
def get_objectives():
    print_section(" CAA OBJECTIVES (අරමුණු - Section 7)")
    results = run("""
        MATCH (a:ආයතනය {id:'adhikariya'})-[:HAS_OBJECTIVE]->(o:අරමුණ)
        RETURN o.code AS code, o.category AS cat, o.description AS desc
        ORDER BY o.id
    """)
    for r in results:
        print(f"  [{r['code']}] {r['cat']}")
        print(f"      {r['desc']}\n")

# ---------------------------------------------------------------
# 4. Get all offences and their penalties
# ---------------------------------------------------------------
def get_offences_and_penalties():
    print_section("  OFFENCES → PENALTIES")
    results = run("""
        MATCH (v:වරද)-[:RESULTS_IN]->(d:දඩුවම)
        RETURN v.name AS offence, v.section AS sec,
               d.fine AS fine, d.prison AS prison, d.type AS pen_type
        ORDER BY v.id
    """)
    for r in results:
        print(f"  Offence : {r['offence']} (Section {r['sec']})")
        print(f"  Penalty : Fine: {r['fine']}  Prison: {r.get('prison','N/A')}")
        print(f"  Type    : {r['pen_type']}")
        print()

# ---------------------------------------------------------------
# 5. Get all officials and their roles
# ---------------------------------------------------------------
def get_officials():
    print_section(" OFFICIALS (නිලධාරි)")
    results = run("MATCH (n:නිලධාරි) RETURN n.name AS name, n.role AS role, n.appointment AS app ORDER BY n.id")
    for r in results:
        print(f"  • {r['name']}")
        if r['role']:        print(f"    Role       : {r['role']}")
        if r['app']:         print(f"    Appointed  : {r['app']}")
        print()

# ---------------------------------------------------------------
# 6. Get key definitions
# ---------------------------------------------------------------
def get_definitions():
    print_section(" KEY DEFINITIONS (Section 75)")
    results = run("MATCH (y:යෙදුම) RETURN y.term AS term, y.meaning AS meaning ORDER BY y.id")
    for r in results:
        print(f"  {r['term']}")
        print(f"    → {r['meaning']}\n")

# ---------------------------------------------------------------
# 7. Find path: Act → Offence → Penalty
# ---------------------------------------------------------------
def get_legal_chain():
    print_section(" LEGAL CHAIN: Act → Section → Offence → Penalty")
    results = run("""
        MATCH (p:පනත)-[:CONTAINS]->(s:වගන්ති)-[:GOVERNS]->(v:වරද)-[:RESULTS_IN]->(d:දඩුවම)
        RETURN s.title AS section, v.name AS offence, d.fine AS fine
        ORDER BY s.number
    """)
    for r in results:
        print(f"  Section : {r['section']}")
        print(f"  Offence : {r['offence']}")
        print(f"  Fine    : {r['fine']}\n")

# ---------------------------------------------------------------
# 8. Neighbourhood of CAA
# ---------------------------------------------------------------
def get_caa_neighbourhood():
    print_section(" CAA DIRECT CONNECTIONS")
    results = run("""
        MATCH (a:ආයතනය {id:'adhikariya'})-[r]-(b)
        RETURN type(r) AS rel, labels(b)[0] AS node_type, 
               CASE WHEN b.name IS NOT NULL THEN b.name ELSE b.id END AS node_name
        ORDER BY type(r)
    """)
    for r in results:
        print(f"  [{r['rel']}] → ({r['node_type']}) {r['node_name']}")

# ---------------------------------------------------------------
# 9. Export graph as JSON snapshot
# ---------------------------------------------------------------
def export_snapshot():
    print_section(" EXPORTING GRAPH SNAPSHOT")
    nodes = run("MATCH (n) RETURN labels(n)[0] AS label, n.id AS id, n.name AS name")
    rels  = run("MATCH (a)-[r]->(b) RETURN a.id AS from, type(r) AS rel, b.id AS to")

    snapshot = {
        "graph": "CAA Knowledge Graph - 2003 Act No.9",
        "nodes": nodes,
        "relationships": rels
    }
    with open("kg_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"   Saved to kg_snapshot.json ({len(nodes)} nodes, {len(rels)} rels)")

# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
if __name__ == "__main__":
    print(" CAA Knowledge Graph - Query Engine\n")

    get_graph_summary()
    get_institutions()
    get_objectives()
    get_offences_and_penalties()
    get_officials()
    get_definitions()
    get_legal_chain()
    get_caa_neighbourhood()
    export_snapshot()

    print("\n All queries completed.")
    driver.close()