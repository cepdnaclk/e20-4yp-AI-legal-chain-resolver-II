from neo4j import GraphDatabase

URI      = "neo4j+s://2f6943ad.databases.neo4j.io"
USERNAME = "2f6943ad"
PASSWORD = "YOUR_PASSWORD_HERE"
DATABASE = "2f6943ad"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def run(query, **params):
    with driver.session(database=DATABASE) as session:
        return session.run(query, **params).data()

# ================================================================
# BASE AGENT
# ================================================================
class BaseAgent:
    def __init__(self, name, description):
        self.name        = name
        self.description = description

    def can_handle(self, question: str) -> bool:
        raise NotImplementedError

    def answer(self, question: str) -> str:
        raise NotImplementedError

    def __repr__(self):
        return f"Agent({self.name})"

# ================================================================
# AGENT 1 — Legal Agent
# Handles: sections, acts, definitions, objectives, functions
# ================================================================
class LegalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Legal Agent",
            description="Answers questions about Act sections, objectives, functions and definitions"
        )
        self.keywords = [
            'section', 'act', 'law', 'objective', 'function', 'definition',
            'වගන්ති', 'අරමුණ', 'කාර්යය', 'යෙදුම', 'නීතිය', 'පනත'
        ]

    def can_handle(self, question: str) -> bool:
        q = question.lower()
        return any(k in q for k in self.keywords)

    def answer(self, question: str) -> str:
        q = question.lower()
        lines = []

        # Objectives query
        if any(w in q for w in ['objective', 'අරමුණ', 'goal', 'purpose']):
            results = run("""
                MATCH (a:ආයතනය {id:'adhikariya'})-[:HAS_OBJECTIVE]->(o:අරමුණ)
                RETURN o.code AS code, o.category AS cat, o.description AS desc
                ORDER BY o.id
            """)
            lines.append(f" CAA has {len(results)} objectives (Section 7):\n")
            for r in results:
                lines.append(f"  [{r['code']}] {r['cat']}: {r['desc']}")

        # Functions query
        elif any(w in q for w in ['function', 'duty', 'කාර්යය', 'duties']):
            results = run("""
                MATCH (a:ආයතනය {id:'adhikariya'})-[:HAS_FUNCTION]->(f:කාර්යය)
                RETURN f.code AS code, f.category AS cat, f.description AS desc
                ORDER BY f.id
            """)
            lines.append(f" CAA has {len(results)} functions (Section 8):\n")
            for r in results:
                lines.append(f"  [{r['code']}] {r['cat']}: {r['desc']}")

        # Definition query
        elif any(w in q for w in ['definition', 'meaning', 'define', 'යෙදුම', 'mean']):
            results = run("MATCH (y:යෙදුම) RETURN y.term AS term, y.meaning AS meaning ORDER BY y.id")
            lines.append(" Key definitions (Section 75):\n")
            for r in results:
                lines.append(f"  {r['term']} → {r['meaning']}")

        # Section lookup
        elif any(w in q for w in ['section', 'වගන්ති']):
            results = run("MATCH (v:වගන්ති) RETURN v.number AS num, v.title AS title ORDER BY v.number")
            lines.append(f" Act contains {len(results)} key sections:\n")
            for r in results:
                lines.append(f"  Section {r['num']}: {r['title']}")

        else:
            lines.append("  Legal Agent: Please ask about sections, objectives, functions, or definitions.")

        return "\n".join(lines)

# ================================================================
# AGENT 2 — Penalty Agent
# Handles: offences, fines, prison, penalties
# ================================================================
class PenaltyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Penalty Agent",
            description="Answers questions about offences, fines and imprisonment"
        )
        self.keywords = [
            'penalty', 'fine', 'prison', 'offence', 'offense', 'punish',
            'දඩුවම', 'වරද', 'දඩ', 'බන්ධනාගාර', 'illegal', 'violation'
        ]

    def can_handle(self, question: str) -> bool:
        q = question.lower()
        return any(k in q for k in self.keywords)

    def answer(self, question: str) -> str:
        q = question.lower()
        lines = []

        # All offences + penalties
        if any(w in q for w in ['all', 'list', 'show', 'සියලු']):
            results = run("""
                MATCH (v:වරද)-[:RESULTS_IN]->(d:දඩුවම)
                RETURN v.name AS offence, v.section AS sec,
                       d.fine AS fine, d.prison AS prison
                ORDER BY v.id
            """)
            lines.append(f"  {len(results)} offence-penalty pairs found:\n")
            for r in results:
                prison = f" | Prison: {r['prison']}" if r.get('prison') else ""
                lines.append(f"  [{r['sec']}] {r['offence']}")
                lines.append(f"       Fine: {r['fine']}{prison}\n")

        # Hoarding specific
        elif any(w in q for w in ['hoard', 'storage', 'ගබඩා']):
            results = run("""
                MATCH (v:වරද {id:'off_hoard'})-[:RESULTS_IN]->(d:දඩුවම)
                RETURN v.name AS offence, d.fine AS fine, d.prison AS prison
            """)
            lines.append("  Hoarding Offence (Section 17):\n")
            for r in results:
                lines.append(f"  Offence : {r['offence']}")
                lines.append(f"  Fine    : {r['fine']}")
                lines.append(f"  Prison  : {r.get('prison', 'N/A')}")

        # Price violation
        elif any(w in q for w in ['price', 'මිල', 'overpricing']):
            results = run("""
                MATCH (v:වරද)-[:RESULTS_IN]->(d:දඩුවම)
                WHERE v.id IN ['off_price','off_overprice']
                RETURN v.name AS offence, d.fine AS fine, d.prison AS prison
            """)
            lines.append("  Price-related Offences:\n")
            for r in results:
                lines.append(f"  Offence : {r['offence']}")
                lines.append(f"  Fine    : {r['fine']}")
                lines.append(f"  Prison  : {r.get('prison','N/A')}\n")

        # Corporate vs individual
        elif any(w in q for w in ['company', 'corporate', 'corporation', 'සංස්ථාව']):
            results = run("""
                MATCH (d:දඩුවම)
                WHERE d.type CONTAINS 'සංස්ථාව'
                RETURN d.type AS type, d.fine AS fine, d.section AS sec
            """)
            lines.append(" Corporate Penalties:\n")
            for r in results:
                lines.append(f"  [{r['sec']}] {r['type']}: Fine {r['fine']}")

        else:
            results = run("""
                MATCH (v:වරද)-[:RESULTS_IN]->(d:දඩුවම)
                RETURN v.name AS offence, d.fine AS fine
                ORDER BY v.id LIMIT 5
            """)
            lines.append("  Sample offences and fines:\n")
            for r in results:
                lines.append(f"  {r['offence']} → {r['fine']}")

        return "\n".join(lines)

# ================================================================
# AGENT 3 — Institution Agent
# Handles: organisations, officials, appointments, roles
# ================================================================
class InstitutionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Institution Agent",
            description="Answers questions about institutions, officials and their relationships"
        )
        self.keywords = [
            'institution', 'organisation', 'official', 'minister', 'appoint',
            'director', 'chairman', 'court', 'caa', 'cac', 'slsi', 'parliament',
            'ආයතනය', 'නිලධාරි', 'අමාත්‍ය', 'සභාව', 'නිලය'
        ]

    def can_handle(self, question: str) -> bool:
        q = question.lower()
        return any(k in q for k in self.keywords)

    def answer(self, question: str) -> str:
        q = question.lower()
        lines = []

        # Who appoints whom
        if any(w in q for w in ['appoint', 'who appoints', 'appointed by']):
            results = run("""
                MATCH (a)-[:APPOINTS]->(b)
                RETURN a.name AS appointer, b.name AS appointed
            """)
            lines.append(" Appointment relationships:\n")
            for r in results:
                lines.append(f"  {r['appointer']} → appoints → {r['appointed']}")

        # CAA connections
        elif any(w in q for w in ['caa', 'adhikariya', 'authority', 'connection']):
            results = run("""
                MATCH (a:ආයතනය {id:'adhikariya'})-[r]-(b)
                RETURN type(r) AS rel, labels(b)[0] AS type,
                       CASE WHEN b.name IS NOT NULL THEN b.name ELSE b.id END AS name
                ORDER BY type(r)
            """)
            lines.append("  CAA connections:\n")
            for r in results:
                lines.append(f"  [{r['rel']}] ({r['type']}) {r['name']}")

        # All institutions
        elif any(w in q for w in ['institution', 'all', 'list', 'ආයතනය']):
            results = run("MATCH (a:ආයතනය) RETURN a.name AS name, a.type AS type ORDER BY a.id")
            lines.append(f"  {len(results)} institutions:\n")
            for r in results:
                lines.append(f"  • {r['name']} — {r['type']}")

        # Director General
        elif any(w in q for w in ['director', 'dg', 'general', 'secretary']):
            results = run("""
                MATCH (d:නිලධාරි {id:'director_general'})
                RETURN d.name AS name, d.role AS role,
                       d.secretary AS sec, d.section AS section
            """)
            lines.append(" Director General:\n")
            for r in results:
                lines.append(f"  Name      : {r['name']}")
                lines.append(f"  Role      : {r['role']}")
                lines.append(f"  Secretary : {r['sec']}")
                lines.append(f"  Section   : {r['section']}")

        # CAC / Sabha
        elif any(w in q for w in ['cac', 'sabha', 'council', 'සභාව']):
            results = run("""
                MATCH (s:ආයතනය {id:'sabha'})-[r]-(b)
                RETURN type(r) AS rel,
                       CASE WHEN b.name IS NOT NULL THEN b.name ELSE b.id END AS name
            """)
            lines.append("  CAC (සභාව) connections:\n")
            for r in results:
                lines.append(f"  [{r['rel']}] {r['name']}")

        else:
            results = run("MATCH (n:නිලධාරි) RETURN n.name AS name, n.role AS role ORDER BY n.id")
            lines.append(" All officials:\n")
            for r in results:
                lines.append(f"  • {r['name']}" + (f" — {r['role']}" if r['role'] else ""))

        return "\n".join(lines)

# ================================================================
# ORCHESTRATOR — routes questions to the right agent
# ================================================================
class Orchestrator:
    def __init__(self, agents):
        self.agents = agents

    def ask(self, question: str) -> str:
        print(f"\n{'─'*55}")
        print(f" Question: {question}")
        print(f"{'─'*55}")

        for agent in self.agents:
            if agent.can_handle(question):
                print(f" Routed to: {agent.name}")
                print(f"{'─'*55}")
                return agent.answer(question)

        # Fallback — general graph stats
        print(" Routed to: General Agent (fallback)")
        print(f"{'─'*55}")
        total_nodes = run("MATCH (n) RETURN count(n) AS c")[0]['c']
        total_rels  = run("MATCH ()-[r]->() RETURN count(r) AS c")[0]['c']
        return (
            f"  I couldn't find a specialised agent for that question.\n"
            f"   The CAA Knowledge Graph has {total_nodes} nodes and {total_rels} relationships.\n"
            f"   Try asking about: objectives, functions, sections, offences, penalties, officials."
        )

# ================================================================
# MAIN — Demo Q&A session
# ================================================================
if __name__ == "__main__":
    print(" CAA Knowledge Graph — Multi-Agent Q&A System")
    print("=" * 55)

    agents       = [LegalAgent(), PenaltyAgent(), InstitutionAgent()]
    orchestrator = Orchestrator(agents)

    questions = [
        "What are the objectives of CAA?",
        "What are the functions and duties of the authority?",
        "What is the penalty for hoarding goods?",
        "Show all offences and fines",
        "Who appoints the Director General?",
        "What institutions are connected to CAA?",
        "What are the key definitions in the Act?",
        "What are corporate penalties for agreement violations?",
        "Show all key sections of the act",
        "What is the role of the CAC sabha?",
    ]

    for q in questions:
        answer = orchestrator.ask(q)
        print(answer)

    print(f"\n{'='*55}")
    print(" Multi-Agent Q&A session complete.")
    driver.close()