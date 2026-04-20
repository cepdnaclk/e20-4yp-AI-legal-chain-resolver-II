from neo4j import GraphDatabase

# --- Credentials ---
URI      = "neo4j+s://2f6943ad.databases.neo4j.io"
USERNAME = "2f6943ad"
PASSWORD = "YOUR_PASSWORD_HERE"   # replace after reset
DATABASE = "2f6943ad"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# ---------------------------------------------------------------
# Helper
# ---------------------------------------------------------------
def run_query(tx, query, **params):
    tx.run(query, **params)

def execute(query):
    with driver.session(database=DATABASE) as session:
        session.execute_write(run_query, query)

# ---------------------------------------------------------------
# 1. Clear existing data
# ---------------------------------------------------------------
def clear_graph():
    execute("MATCH (n) DETACH DELETE n")
    print("🗑️  Graph cleared.")

# ---------------------------------------------------------------
# 2. Create constraints
# ---------------------------------------------------------------
CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:පනත)    REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ආයතනය)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:නිලධාරි) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:අරමුණ)   REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:කාර්යය)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:වගන්ති)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:වරද)     REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:දඩුවම)   REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:අරමුදල)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:යෙදුම)   REQUIRE n.id IS UNIQUE",
]

def create_constraints():
    for c in CONSTRAINTS:
        execute(c)
    print("Constraints created.")

# ---------------------------------------------------------------
# 3. Create Nodes
# ---------------------------------------------------------------
NODES = [
    # Act
    """CREATE (:පනත {id:'act_9_2003', name:'2003 අංක 9 - පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනත',
        year:2003, number:9,
        description:'පාරිභෝගිකයන් ආරක්ෂා කිරීම හා සාධාරණ වෙළෙඳ ක්‍රියාකාරකම් ප්‍රවර්ධනය'})""",

    # Institutions
    """CREATE (:ආයතනය {id:'adhikariya', name:'පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය',
        short_name:'CAA', type:'සංස්ථා ආයතනය', section:'2'})""",
    """CREATE (:ආයතනය {id:'sabha', name:'පාරිභෝගික කටයුතු පිළිබඳ සභාව',
        short_name:'CAC', type:'විමර්ශන සභාව', section:'30'})""",
    """CREATE (:ආයතනය {id:'slsi', name:'ශ්‍රී ලංකා ප්‍රමිති ආයතනය',
        short_name:'SLSI', type:'ප්‍රමිති ආයතනය'})""",
    """CREATE (:ආයතනය {id:'parliament', name:'පාර්ලිමේන්තුව',
        type:'ව්‍යවස්ථාදායක ආයතනය'})""",
    """CREATE (:ආයතනය {id:'appeal_court', name:'අභියාචනාධිකරණය',
        type:'අධිකරණ ආයතනය'})""",
    """CREATE (:ආයතනය {id:'magistrate', name:'මහේස්ත්‍රාත් අධිකරණය',
        type:'අධිකරණ ආයතනය'})""",

    # Officials
    """CREATE (:නිලධාරි {id:'sabhapathi', name:'සභාපතිවරයා',
        appointment:'අමාත්‍යවරයා විසින්', term:'අවුරුදු 3', service_type:'පූර්ණ කාලීන'})""",
    """CREATE (:නිලධාරි {id:'director_general', name:'අධ්‍යක්ෂ ජනරාල්',
        role:'ප්‍රධාන විධායක නිලධරයා', secretary:'ලේකම් ලෙස', section:'52'})""",
    """CREATE (:නිලධාරි {id:'amathya', name:'අමාත්‍යවරයා',
        role:'CAA සාමාජිකයන් පත් කිරීම'})""",
    """CREATE (:නිලධාරි {id:'purna_samasika', name:'පූර්ණ කාලීන සාමාජිකයන්',
        count:'3 දෙනා', term:'අවුරුදු 3'})""",
    """CREATE (:නිලධාරි {id:'anya_samasika', name:'අනෙකුත් සාමාජිකයන්',
        count:'දහ දෙනකට නොඅඩු'})""",
    """CREATE (:නිලධාරි {id:'bala_nildhary', name:'බලය ලත් නිලධාරිය',
        powers:'පරිශ්‍ර ඇතුළු වීම, භාණ්ඩ රඳවා ගැනීම', section:'58'})""",

    # Objectives
    """CREATE (:අරමුණ {id:'obj_1', code:'අ',
        description:'ජීවිතයට හා දේපලට උපද්‍රවකාරී භාණ්ඩවලට එරෙහිව ආරක්ෂාව',
        category:'ආරක්ෂාව', section:'7'})""",
    """CREATE (:අරමුණ {id:'obj_2', code:'ආ',
        description:'අසාධාරණ වෙළෙඳ පිළිවෙත් - ආරක්ෂාව',
        category:'වෙළෙඳ ආරක්ෂාව', section:'7'})""",
    """CREATE (:අරමුණ {id:'obj_3', code:'ඇ',
        description:'තරගකාරී මිලකට ප්‍රමාණවත් භාණ්ඩ ප්‍රවේශය',
        category:'ලබාගැනීමේ හැකියාව', section:'7'})""",
    """CREATE (:අරමුණ {id:'obj_4', code:'ඈ',
        description:'සීමාකාරී වෙළෙඳ, සූරාකෑම් - සහනය',
        category:'පාරිභෝගික ගිලිරීම', section:'7'})""",

    # Functions
    """CREATE (:කාර්යය {id:'func_1', code:'අ', category:'ගිවිසුම් සීමා',
        description:'සීමාකාරී ගිවිසුම්, මිල ගිවිසුම්, ආධිපත්‍ය', section:'8'})""",
    """CREATE (:කාර්යය {id:'func_2', code:'ආ', category:'විමර්ශන',
        description:'තරග විරෝධී ක්‍රියා - විමර්ශන', section:'8'})""",
    """CREATE (:කාර්යය {id:'func_3', code:'ඇ', category:'තරගකාරිත්වය',
        description:'ඵලදායී තරගකාරිත්වය ප්‍රවර්ධනය', section:'8'})""",
    """CREATE (:කාර්යය {id:'func_4', code:'ඈ', category:'අයිතිවාසිකම්',
        description:'මිල, ලබාගැනීම, ගුණය - ආරක්ෂාව', section:'8'})""",
    """CREATE (:කාර්යය {id:'func_5', code:'ඉ', category:'දැනුවත් කිරීම',
        description:'ගුණය, ප්‍රමිති, මිල ගැන දැනුවත් කිරීම', section:'8'})""",
    """CREATE (:කාර්යය {id:'func_6', code:'ඒ', category:'අධ්‍යාපනය',
        description:'සෞඛ්‍යය, ආරක්ෂාව - පාරිභෝගික අධ්‍යාපනය', section:'8'})""",

    # Key Sections
    """CREATE (:වගන්ති {id:'sec_2',  number:2,  title:'අධිකාරිය පිහිටුවීම',
        summary:'CAA සංස්ථාවක් ලෙස, නඩු හැකියාව'})""",
    """CREATE (:වගන්ති {id:'sec_7',  number:7,  title:'අරමුණු',
        summary:'CAA ප්‍රධාන අරමුණු 4'})""",
    """CREATE (:වගන්ති {id:'sec_8',  number:8,  title:'කාර්යයන්',
        summary:'ගිවිසුම්, විමර්ශන, ප්‍රමිති'})""",
    """CREATE (:වගන්ති {id:'sec_10', number:10, title:'ලේබල් හා විධාන',
        summary:'ලේබල් කිරීම, මිල ලකුණු'})""",
    """CREATE (:වගන්ති {id:'sec_12', number:12, title:'ප්‍රමිති',
        summary:'නිෂ්පාදනය, ගබඩා, විකිණීම ප්‍රමිති'})""",
    """CREATE (:වගන්ති {id:'sec_14', number:14, title:'ලිඛිත ගිවිසුම්',
        summary:'උපරිම මිල, ප්‍රමිති ගිවිසුම්'})""",
    """CREATE (:වගන්ති {id:'sec_15', number:15, title:'විකිණීම ප්‍රතික්ෂේප නොකළ යුතුය',
        summary:'භාණ්ඩ විකිණීම ප්‍රතික්ෂේප කළ නොහැකිය'})""",
    """CREATE (:වගන්ති {id:'sec_17', number:17, title:'ගබඩා සීමා',
        summary:'අධික ගබඩා නොකළ යුතුය'})""",
    """CREATE (:වගන්ති {id:'sec_18', number:18, title:'නිශ්චිත භාණ්ඩ',
        summary:'CAA අනුමතය නොමැතිව මිල ඉහළ නොදැමිය යුතුය'})""",
    """CREATE (:වගන්ති {id:'sec_49', number:49, title:'CAA අරමුදල',
        summary:'ආදායම් ප්‍රභව, වියදම්'})""",
    """CREATE (:වගන්ති {id:'sec_52', number:52, title:'DG පත් කිරීම',
        summary:'DG - ප්‍රධාන විධායක, ලේකම්'})""",
    """CREATE (:වගන්ති {id:'sec_55', number:55, title:'ලිඛිත අවවාද',
        summary:'පළමු උල්ලංඝනය - ලිඛිත අවවාදය'})""",
    """CREATE (:වගන්ති {id:'sec_58', number:58, title:'ඇතුළු වීමේ බලය',
        summary:'පරිශ්‍ර ඇතුළු වීම, ලේඛන පරීක්ෂා'})""",
    """CREATE (:වගන්ති {id:'sec_60', number:60, title:'දඩුවම්',
        summary:'දඩ හා බන්ධනාගාර'})""",
    """CREATE (:වගන්ති {id:'sec_75', number:75, title:'අර්ථ දැක්වීම්',
        summary:'භාණ්ඩ, සේවාව, සාදන්නා, වෙළෙන්දා'})""",

    # Offences
    """CREATE (:වරද {id:'off_label',     name:'ලේබල් / මිල ලකුණු උල්ලංඝනය', section:'10'})""",
    """CREATE (:වරද {id:'off_overprice', name:'ලකුණු කළ මිලට වැඩිකර විකිණීම', section:'11'})""",
    """CREATE (:වරද {id:'off_refuse',    name:'විකිණීම ප්‍රතික්ෂේප', section:'15'})""",
    """CREATE (:වරද {id:'off_hoard',     name:'අධික ගබඩා', section:'17'})""",
    """CREATE (:වරද {id:'off_price',     name:'CAA අනුමතය නොමැතිව මිල ඉහළ', section:'18'})""",
    """CREATE (:වරද {id:'off_records',   name:'ලේඛන / ව්‍යාජ ප්‍රකාශ / බාධා', section:'60'})""",
    """CREATE (:වරද {id:'off_agreement', name:'CAA ගිවිසුම් කඩ කිරීම', section:'14'})""",

    # Penalties
    """CREATE (:දඩුවම {id:'pen_rec_p1',   type:'ලේඛන - පළමු - පුද්ගල',
        fine:'රු. 1,000 - 5,000', prison:'මාස 3', section:'60(1)(i)'})""",
    """CREATE (:දඩුවම {id:'pen_rec_c1',   type:'ලේඛන - පළමු - සංස්ථාව',
        fine:'රු. 5,000 - 10,000', section:'60(1)(ii)'})""",
    """CREATE (:දඩුවම {id:'pen_agree_p1', type:'ගිවිසුම් - පළමු - පුද්ගල',
        fine:'රු. 5,000 - 50,000', prison:'අවුරුද්ද', section:'60(2)(i)'})""",
    """CREATE (:දඩුවම {id:'pen_agree_c1', type:'ගිවිසුම් - පළමු - සංස්ථාව',
        fine:'රු. 50,000 - 1,000,000', section:'60(2)(ii)'})""",
    """CREATE (:දඩුවම {id:'pen_hoard_p1', type:'ගබඩා - පළමු - පුද්ගල',
        fine:'රු. 1,000 - 10,000', prison:'මාස 6', section:'60(3)(i)'})""",
    """CREATE (:දඩුවම {id:'pen_price_p1', type:'නිශ්චිත භාණ්ඩ - පළමු - පුද්ගල',
        fine:'රු. 5,000 - 50,000', prison:'අවුරුද්ද', section:'60(4)(i)'})""",

    # Fund
    """CREATE (:අරමුදල {id:'caa_fund', name:'CAA අරමුදල',
        income:'පාර්ලිමේන්තු, ගාස්තු, දඩ 1/3, ප්‍රදාන',
        expenditure:'ගෙවීම්, සංවිධාන, අධ්‍යාපනය', section:'49'})""",

    # Definitions
    """CREATE (:යෙදුම {id:'def_consumer',     term:'පාරිභෝගිකයා',
        meaning:'භාණ්ඩ හෝ සේවා භාවිත කරන තැනැත්තා', section:'75'})""",
    """CREATE (:යෙදුම {id:'def_goods',        term:'භාණ්ඩ',
        meaning:'ආහාර, පානය, බෙහෙත්, ඉන්ධන', section:'75'})""",
    """CREATE (:යෙදුම {id:'def_services',     term:'සේවාව',
        meaning:'බැංකු, රක්ෂණ, ප්‍රවාහනය, IT', section:'75'})""",
    """CREATE (:යෙදුම {id:'def_trader',       term:'වෙළෙන්දා',
        meaning:'තොග හා සිල්ලර විකිණීම, ආනයනය', section:'75'})""",
    """CREATE (:යෙදුම {id:'def_manufacturer', term:'සාදන්නා',
        meaning:'සාදන, එකලස් කරන, සකස් කරන', section:'75'})""",
]

RELATIONSHIPS = [
    "MATCH (p:පනත {id:'act_9_2003'}),(a:ආයතනය {id:'adhikariya'})  CREATE (p)-[:ESTABLISHES {section:'2'}]->(a)",
    "MATCH (p:පනත {id:'act_9_2003'}),(s:ආයතනය {id:'sabha'})       CREATE (p)-[:ESTABLISHES {section:'30'}]->(s)",
    "MATCH (p:පනත {id:'act_9_2003'}),(v:වගන්ති)                    CREATE (p)-[:CONTAINS]->(v)",
    "MATCH (p:පනත {id:'act_9_2003'}),(y:යෙදුම)                     CREATE (p)-[:DEFINES]->(y)",
    "MATCH (a:ආයතනය {id:'adhikariya'}),(o:අරමුණ)                   CREATE (a)-[:HAS_OBJECTIVE]->(o)",
    "MATCH (a:ආයතනය {id:'adhikariya'}),(f:කාර්යය)                  CREATE (a)-[:HAS_FUNCTION]->(f)",
    "MATCH (a:ආයතනය {id:'adhikariya'}),(f:අරමුදල {id:'caa_fund'})  CREATE (a)-[:HAS_FUND]->(f)",
    "MATCH (p:ආයතනය {id:'parliament'}),(f:අරමුදල {id:'caa_fund'})  CREATE (p)-[:APPROPRIATES]->(f)",
    "MATCH (a:ආයතනය {id:'adhikariya'}),(d:නිලධාරි {id:'director_general'}) CREATE (a)-[:APPOINTS {section:'52'}]->(d)",
    "MATCH (m:නිලධාරි {id:'amathya'}),(s:නිලධාරි {id:'sabhapathi'})        CREATE (m)-[:APPOINTS]->(s)",
    "MATCH (m:නිලධාරි {id:'amathya'}),(p:නිලධාරි {id:'purna_samasika'})    CREATE (m)-[:APPOINTS]->(p)",
    "MATCH (m:නිලධාරි {id:'amathya'}),(a:නිලධාරි {id:'anya_samasika'})     CREATE (m)-[:APPOINTS]->(a)",
    "MATCH (m:නිලධාරි {id:'amathya'}),(d:නිලධාරි {id:'director_general'})  CREATE (m)-[:APPROVES]->(d)",
    "MATCH (d:නිලධාරි {id:'director_general'}),(a:ආයතනය {id:'adhikariya'}) CREATE (d)-[:SERVES_AS_SECRETARY]->(a)",
    "MATCH (s:නිලධාරි {id:'sabhapathi'}),(a:ආයතනය {id:'adhikariya'})       CREATE (s)-[:LEADS]->(a)",
    "MATCH (d:නිලධාරි {id:'director_general'}),(s:ආයතනය {id:'sabha'})      CREATE (d)-[:REFERS_TO {section:'19'}]->(s)",
    "MATCH (s:ආයතනය {id:'sabha'}),(d:නිලධාරි {id:'director_general'})      CREATE (s)-[:REPORTS_TO {section:'19'}]->(d)",
    "MATCH (s:ආයතනය {id:'sabha'}),(a:ආයතනය {id:'adhikariya'})              CREATE (s)-[:RECOMMENDS {section:'20'}]->(a)",
    "MATCH (a:ආයතනය {id:'adhikariya'}),(s:ආයතනය {id:'slsi'})               CREATE (a)-[:ADOPTS_STANDARDS {section:'12'}]->(s)",
    "MATCH (a:ආයතනය {id:'adhikariya'}),(c:ආයතනය {id:'appeal_court'})       CREATE (a)-[:APPEAL_LIES_TO {section:'20'}]->(c)",
    "MATCH (n:නිලධාරි {id:'bala_nildhary'}),(s:වගන්ති {id:'sec_58'})        CREATE (n)-[:EMPOWERED_BY]->(s)",
    "MATCH (s:වගන්ති {id:'sec_10'}),(v:වරද {id:'off_label'})     CREATE (s)-[:GOVERNS]->(v)",
    "MATCH (s:වගන්ති {id:'sec_15'}),(v:වරද {id:'off_refuse'})    CREATE (s)-[:GOVERNS]->(v)",
    "MATCH (s:වගන්ති {id:'sec_17'}),(v:වරද {id:'off_hoard'})     CREATE (s)-[:GOVERNS]->(v)",
    "MATCH (s:වගන්ති {id:'sec_18'}),(v:වරද {id:'off_price'})     CREATE (s)-[:GOVERNS]->(v)",
    "MATCH (s:වගන්ති {id:'sec_60'}),(v:වරද {id:'off_records'})   CREATE (s)-[:GOVERNS]->(v)",
    "MATCH (s:වගන්ති {id:'sec_14'}),(v:වරද {id:'off_agreement'}) CREATE (s)-[:GOVERNS]->(v)",
    "MATCH (v:වරද),(m:ආයතනය {id:'magistrate'})                   CREATE (v)-[:HEARD_IN]->(m)",
    "MATCH (v:වරද {id:'off_records'}),  (d:දඩුවම {id:'pen_rec_p1'})   CREATE (v)-[:RESULTS_IN]->(d)",
    "MATCH (v:වරද {id:'off_records'}),  (d:දඩුවම {id:'pen_rec_c1'})   CREATE (v)-[:RESULTS_IN]->(d)",
    "MATCH (v:වරද {id:'off_agreement'}),(d:දඩුවම {id:'pen_agree_p1'}) CREATE (v)-[:RESULTS_IN]->(d)",
    "MATCH (v:වරද {id:'off_agreement'}),(d:දඩුවම {id:'pen_agree_c1'}) CREATE (v)-[:RESULTS_IN]->(d)",
    "MATCH (v:වරද {id:'off_refuse'}),   (d:දඩුවම {id:'pen_hoard_p1'}) CREATE (v)-[:RESULTS_IN]->(d)",
    "MATCH (v:වරද {id:'off_hoard'}),    (d:දඩුවම {id:'pen_hoard_p1'}) CREATE (v)-[:RESULTS_IN]->(d)",
    "MATCH (v:වරද {id:'off_price'}),    (d:දඩුවම {id:'pen_price_p1'}) CREATE (v)-[:RESULTS_IN]->(d)",
    "MATCH (y:යෙදුම),(s:වගන්ති {id:'sec_75'}) CREATE (y)-[:DEFINED_IN]->(s)",
]

def create_nodes():
    for q in NODES:
        execute(q)
    print(f" {len(NODES)} nodes created.")

def create_relationships():
    for q in RELATIONSHIPS:
        execute(q)
    print(f" {len(RELATIONSHIPS)} relationships created.")

# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
if __name__ == "__main__":
    print(" Building Consumer Affairs Authority Knowledge Graph...\n")
    clear_graph()
    create_constraints()
    create_nodes()
    create_relationships()
    print("\n Knowledge Graph successfully created in Neo4j Aura!")
    driver.close()