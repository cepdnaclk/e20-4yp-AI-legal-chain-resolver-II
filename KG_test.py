from neo4j import GraphDatabase

URI      = "neo4j+s://2f6943ad.databases.neo4j.io"
USERNAME = "2f6943ad"
PASSWORD = "YOUR_PASSWORD_HERE"
DATABASE = "2f6943ad"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def run(query):
    with driver.session(database=DATABASE) as session:
        return session.run(query).data()

# ---------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------
passed = 0
failed = 0

def check(label, condition, detail=""):
    global passed, failed
    if condition:
        print(f"   PASS | {label}")
        passed += 1
    else:
        print(f"   FAIL | {label} {detail}")
        failed += 1

# ---------------------------------------------------------------
# Test 1: Node counts
# ---------------------------------------------------------------
def test_node_counts():
    print("\n TEST 1: Node Counts")
    results = run("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count")
    counts  = {r['label']: r['count'] for r in results}

    check("පනත node exists",    counts.get('පනත', 0)    >= 1)
    check("ආයතනය >= 6",         counts.get('ආයතනය', 0)  >= 6)
    check("නිලධාරි >= 6",        counts.get('නිලධාරි', 0) >= 6)
    check("අරමුණ == 4",          counts.get('අරමුණ', 0)   == 4)
    check("කාර්යය >= 6",         counts.get('කාර්යය', 0)  >= 6)
    check("වගන්ති >= 10",         counts.get('වගන්ති', 0)  >= 10)
    check("වරද >= 7",             counts.get('වරද', 0)     >= 7)
    check("දඩුවම >= 5",           counts.get('දඩුවම', 0)   >= 5)
    check("යෙදුම >= 5",           counts.get('යෙදුම', 0)   >= 5)
    check("අරමුදල == 1",          counts.get('අරමුදල', 0)  == 1)

# ---------------------------------------------------------------
# Test 2: Relationship counts
# ---------------------------------------------------------------
def test_relationships():
    print("\n TEST 2: Relationships")
    results = run("MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count")
    counts  = {r['type']: r['count'] for r in results}
    total   = sum(counts.values())

    check("Total relationships >= 30",    total >= 30,   f"(got {total})")
    check("ESTABLISHES exists",           counts.get('ESTABLISHES', 0) >= 2)
    check("HAS_OBJECTIVE exists",         counts.get('HAS_OBJECTIVE', 0) >= 4)
    check("HAS_FUNCTION exists",          counts.get('HAS_FUNCTION', 0) >= 6)
    check("GOVERNS exists",               counts.get('GOVERNS', 0) >= 6)
    check("RESULTS_IN exists",            counts.get('RESULTS_IN', 0) >= 5)
    check("HEARD_IN exists",              counts.get('HEARD_IN', 0) >= 7)
    check("APPOINTS exists",              counts.get('APPOINTS', 0) >= 3)
    check("REFERS_TO exists",             counts.get('REFERS_TO', 0) >= 1)
    check("RECOMMENDS exists",            counts.get('RECOMMENDS', 0) >= 1)

# ---------------------------------------------------------------
# Test 3: Key node properties
# ---------------------------------------------------------------
def test_properties():
    print("\n TEST 3: Key Node Properties")
    r = run("MATCH (p:පනත {id:'act_9_2003'}) RETURN p.year AS y, p.number AS n")
    check("Act year == 2003",   r and r[0]['y'] == 2003)
    check("Act number == 9",    r and r[0]['n'] == 9)

    r = run("MATCH (a:ආයතනය {id:'adhikariya'}) RETURN a.short_name AS sn")
    check("CAA short_name == 'CAA'", r and r[0]['sn'] == 'CAA')

    r = run("MATCH (d:නිලධාරි {id:'director_general'}) RETURN d.section AS s")
    check("DG section == '52'", r and r[0]['s'] == '52')

    r = run("MATCH (f:අරමුදල {id:'caa_fund'}) RETURN f.name AS n")
    check("Fund node has name", r and r[0]['n'] is not None)

# ---------------------------------------------------------------
# Test 4: Graph connectivity
# ---------------------------------------------------------------
def test_connectivity():
    print("\n TEST 4: Graph Connectivity")

    r = run("""MATCH (p:පනත {id:'act_9_2003'})-[:ESTABLISHES]->(a:ආයතනය {id:'adhikariya'})
               RETURN count(a) AS c""")
    check("Act ESTABLISHES CAA",  r and r[0]['c'] == 1)

    r = run("""MATCH (a:ආයතනය {id:'adhikariya'})-[:HAS_OBJECTIVE]->(o:අරමුණ)
               RETURN count(o) AS c""")
    check("CAA has 4 objectives", r and r[0]['c'] == 4)

    r = run("""MATCH (v:වරද)-[:RESULTS_IN]->(d:දඩුවම)
               RETURN count(d) AS c""")
    check("Offences linked to penalties", r and r[0]['c'] >= 5)

    r = run("""MATCH (d:නිලධාරි {id:'director_general'})-[:REFERS_TO]->(s:ආයතනය {id:'sabha'})
               RETURN count(s) AS c""")
    check("DG refers to CAC",     r and r[0]['c'] == 1)

    r = run("""MATCH (s:ආයතනය {id:'sabha'})-[:RECOMMENDS]->(a:ආයතනය {id:'adhikariya'})
               RETURN count(a) AS c""")
    check("CAC recommends to CAA", r and r[0]['c'] == 1)

# ---------------------------------------------------------------
# Test 5: Orphan check
# ---------------------------------------------------------------
def test_no_orphans():
    print("\n TEST 5: Orphan Node Check")
    r = run("""MATCH (n) WHERE NOT (n)--() AND NOT n:පනත
               RETURN count(n) AS c""")
    orphans = r[0]['c'] if r else 0
    check(f"No orphan nodes (found {orphans})", orphans == 0)

# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
if __name__ == "__main__":
    print(" Running Knowledge Graph Tests...\n")
    print("=" * 50)

    test_node_counts()
    test_relationships()
    test_properties()
    test_connectivity()
    test_no_orphans()

    print("\n" + "=" * 50)
    print(f" Results: {passed} passed | {failed} failed")
    if failed == 0:
        print(" All tests passed!")
    else:
        print("  Some tests failed. Check graph data.")

    driver.close()