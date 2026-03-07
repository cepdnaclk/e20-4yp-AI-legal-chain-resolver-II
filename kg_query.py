from neo4j import GraphDatabase

# ── Neo4j connection ────────────────────────────────────────────────────────────
URI      = "neo4j+s://f92fdc9e.databases.neo4j.io"
USER     = "neo4j"
PASSWORD = "EQlO46eqAiS8UhKs5GDQ5c4qYVQwvG6kJLZWpFg30Jg"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ── Query function ──────────────────────────────────────────────────────────────
def search_kg(query: str):
    cypher = """
    MATCH (n:Node)
    WHERE n.name CONTAINS $term
    OPTIONAL MATCH (n)-[r_out:CONNECTED_TO]->(target:Node)
    OPTIONAL MATCH (source:Node)-[r_in:CONNECTED_TO]->(n)
    RETURN
        n.name     AS node,
        n.category AS category,
        COLLECT(DISTINCT {
            type              : 'out',
            relation          : r_out.relationship_type,
            related_node      : target.name,
            related_category  : target.category
        }) AS outgoing,
        COLLECT(DISTINCT {
            type              : 'in',
            relation          : r_in.relationship_type,
            related_node      : source.name,
            related_category  : source.category
        }) AS incoming
    LIMIT 5
    """
    with driver.session() as session:
        return session.run(cypher, term=query).data()

# ── Display results ─────────────────────────────────────────────────────────────
def display(results, query):
    if not results:
        print(f"\n  No nodes found for: '{query}'")
        print("  Try a different keyword from your query.\n")
        return

    print(f"\n{'═' * 60}")
    print(f"  Results for: '{query}'")
    print(f"{'═' * 60}")

    for record in results:
        print(f"\n  NODE     : {record['node']}")
        print(f"  CATEGORY : [{record['category']}]")

        out = [r for r in record['outgoing'] if r.get('related_node')]
        inc = [r for r in record['incoming'] if r.get('related_node')]

        if out:
            print("  OUTGOING :")
            for r in out:
                print(f"    → [{r['relation']}] {r['related_node']} ({r['related_category']})")

        if inc:
            print("  INCOMING :")
            for r in inc:
                print(f"    ← [{r['relation']}] {r['related_node']} ({r['related_category']})")

    print(f"\n{'─' * 60}\n")

# ── Main loop ───────────────────────────────────────────────────────────────────
def main():
    print("\n  Sinhala Legal Knowledge Graph — Node Search")
    print("  Type a Sinhala keyword to search. Type 'exit' to quit.\n")

    while True:
        query = input("  Enter query: ").strip()

        if query.lower() in ("exit", "quit"):
            print("\n  Goodbye!\n")
            driver.close()
            break

        if not query:
            continue

        results = search_kg(query)
        display(results, query)

if __name__ == "__main__":
    main()
