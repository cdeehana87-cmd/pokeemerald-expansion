# Run from the repo root:  python3 reachability_report.py
# READ-ONLY. Lists Hoenn Dex species that nothing in the game data seems to give the player.
import re, os, sys, json, glob

def read(p): return open(p, encoding='utf-8', errors='replace').read()
if not os.path.isdir('src') or not os.path.isdir('data'): sys.exit("STOP: run from the repo root")
out = []
def say(s=""): print(s); out.append(s)

# ---------- 1. Hoenn Dex membership (validated against real species names) ----------
all_species = set()
for p in glob.glob('src/data/pokemon/species_info/*.h'):
    all_species.update(re.findall(r'\[SPECIES_([A-Z0-9_]+)\]\s*=', read(p)))
def valid(names):
    seen = []
    for n in names:
        if n in all_species and n not in seen: seen.append(n)
    return seen
cand1, samples = [], []
for p in glob.glob('include/**/*.h', recursive=True) + glob.glob('src/**/*.[ch]', recursive=True):
    for i, line in enumerate(read(p).split('\n'), 1):
        if 'HOENN_DEX' in line and len(samples) < 12: samples.append(f"{p}:{i}: {line.strip()[:110]}")
        cand1 += re.findall(r'\bHOENN_DEX_([A-Z0-9_]+)\b', line)
cand2 = []
for p in glob.glob('src/**/*.[ch]', recursive=True) + glob.glob('include/**/*.h', recursive=True):
    cand2 += re.findall(r'\bHOENN_TO_NATIONAL\(([A-Z0-9_]+)\)', read(p))
hoenn, method, conditional_off = [], "", []
# Method 0: the X-macro FOREACH_SPECIES_IN_HOENN_DEX_ORDER(F) in include/constants/pokedex.h
def cfg_value(name):
    for p in glob.glob('include/config/*.h'):
        m = re.search(r'^\s*#\s*define\s+' + re.escape(name) + r'\s+(\S+)', read(p), re.M)
        if m: return m.group(1)
    return None
xp = 'include/constants/pokedex.h'
if os.path.exists(xp):
    lines = read(xp).split('\n'); i0 = next((i for i, l in enumerate(lines) if 'define FOREACH_SPECIES_IN_HOENN_DEX_ORDER' in l), None)
    if i0 is not None:
        names = []; i = i0
        while i < len(lines):
            l = lines[i]
            m = re.search(r'HOENN_DEX_IF\((\w+),\s*F\(([A-Z0-9_]+)\)\)', l)
            if m:
                v = cfg_value(m.group(1))
                (names if v in ('TRUE', '1') else conditional_off).append(m.group(2) if v in ('TRUE', '1') else f"{m.group(2)}[{m.group(1)}={v}]")
            else:
                m = re.search(r'\bF\(([A-Z0-9_]+)\)', l)
                if m: names.append(m.group(1))
            if not l.rstrip().endswith('\\') and i > i0: break
            i += 1
        v = valid(names)
        if len(v) >= 100: hoenn, method = v, "FOREACH_SPECIES_IN_HOENN_DEX_ORDER macro"
if not hoenn:
    for name, cand in (("HOENN_DEX_* constants", cand1), ("HOENN_TO_NATIONAL(...) table", cand2)):
        v = valid(cand)
        if len(v) >= 100: hoenn, method = v, name; break
if not hoenn:
    say(f"STOP: could not find a believable Hoenn Dex list (known species: {len(all_species)}, "
        f"valid HOENN_DEX_* names: {len(valid(cand1))}, valid HOENN_TO_NATIONAL names: {len(valid(cand2))}).")
    say("Lines mentioning HOENN_DEX, for Claude to read:")
    for l in samples: say("  " + l)
    open('reachability_report.txt', 'w').write("\n".join(out) + "\n"); sys.exit(1)
say(f"Hoenn Dex species found: {len(hoenn)}   (via {method})")
if conditional_off: say(f"Not counted (their config switch is off or unknown): {', '.join(conditional_off)}")

# ---------- 2. Evolution families ----------
parent = {}
def find(a):
    parent.setdefault(a, a)
    while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b): parent[find(a)] = find(b)
trade_left = []      # (species, target) still evolving by trade
item_evos = []       # (species, item, target)
for p in glob.glob('src/data/pokemon/species_info/*.h'):
    cur = None
    for line in read(p).split('\n'):
        h = re.match(r'\s*\[SPECIES_([A-Z0-9_]+)\]\s*=', line)
        if h: cur = h.group(1); find(cur)
        for m in re.finditer(r'\{(EVO_[A-Z_]+),\s*([^,{}]+),\s*SPECIES_([A-Z0-9_]+)', line):
            if cur is None: continue
            union(cur, m.group(3))
            if m.group(1) in ('EVO_TRADE', 'EVO_TRADE_ITEM'): trade_left.append((cur, m.group(3)))
            if m.group(1) == 'EVO_ITEM': item_evos.append((cur, m.group(2).strip(), m.group(3)))

# ---------- 3. Sources of Pokemon ----------
wild, wild_frlg, script_src, script_frlg = set(), set(), set(), set()
def collect(obj, mapname=None):
    if isinstance(obj, dict):
        if isinstance(obj.get('map'), str): mapname = obj['map']
        sp = obj.get('species')
        if isinstance(sp, str) and sp.startswith('SPECIES_'):
            (wild_frlg if mapname and 'FRLG' in mapname.upper() else wild).add(sp[8:])
        for v in obj.values(): collect(v, mapname)
    elif isinstance(obj, list):
        for v in obj: collect(v, mapname)
wp = 'src/data/wild_encounters.json'
if os.path.exists(wp): collect(json.load(open(wp, encoding='utf-8')))
else: say(f"note: {wp} not found")
cmd = re.compile(r'\b(?:givemon|setwildbattle|seteventmon|giveegg)\s+SPECIES_([A-Z0-9_]+)')
for p in glob.glob('data/**/*.inc', recursive=True):
    for m in cmd.finditer(read(p)):
        (script_frlg if 'frlg' in p.lower() else script_src).add(m.group(1))
trade_p = 'src/data/trade.h'
if os.path.exists(trade_p):
    for m in re.finditer(r'\.species\s*=\s*SPECIES_([A-Z0-9_]+)', read(trade_p)): script_src.add(m.group(1))
known_c = {'TREECKO', 'TORCHIC', 'MUDKIP', 'LILEEP', 'ANORITH'}   # starters and fossils are coded in C: only ONE of each group is really given (see section E)

direct = wild | script_src | known_c
direct_frlg = wild_frlg | script_frlg
fam_ok, fam_frlg = set(), set()
for s in direct: fam_ok.add(find(s))
for s in direct_frlg: fam_frlg.add(find(s))

none, only_frlg, via_family = [], [], 0
for n in hoenn:
    if n in direct: continue
    f = find(n)
    if f in fam_ok: via_family += 1; continue
    (only_frlg if f in fam_frlg else none).append(n)

def wrap(names):
    for i in range(0, len(names), 5): say("   " + ", ".join(names[i:i+5]))
say(f"\nHoenn Dex species with a direct source (wild/gift/static/trade): {sum(1 for n in hoenn if n in direct)}")
say(f"Reached only by evolving/breeding from something obtainable: {via_family}")
say(f"\nA) NOTHING GIVES THESE (family not found in wild data, gifts or trades): {len(none)}")
wrap(none) if none else say("   (none)")
say(f"\nB) ONLY IN FireRed/LeafGreen map data (probably unreachable in Emerald): {len(only_frlg)}")
wrap(only_frlg) if only_frlg else say("   (none)")
tl = [f"{a}->{b}" for a, b in trade_left if a in hoenn or b in hoenn]
say(f"\nC) Hoenn Dex species still evolving by TRADE: {len(tl)}")
wrap(tl) if tl else say("   (none)")
ie = sorted({f"{a}+{i.replace('ITEM_','')}" for a, i, b in item_evos if a in hoenn or b in hoenn})
say(f"\nD) Hoenn Dex evolutions that need an ITEM (check you can get the item): {len(ie)}")
wrap(ie) if ie else say("   (none)")
STARTERS = ['TREECKO', 'TORCHIC', 'MUDKIP']
FOSSILS = ['LILEEP', 'ANORITH']
say("\nE) CHOOSE-ONE GROUPS (the totals above count these as reachable, but a normal game only gives ONE per group):")
for label, grp in (("Starters", STARTERS), ("Fossils", FOSSILS)):
    given = [n for n in grp if n in (wild | script_src)]
    say(f"   {label}: {', '.join(grp)}   | found in wild/script data: {', '.join(given) if given else 'none (coded in C, so one choice only)'}")
say("\nNotes: legendaries, event Pokemon and anything coded in C (roamers, some gifts) can show up in A falsely. Review the list, don't trust it blindly.")
open('reachability_report.txt', 'w').write("\n".join(out) + "\n")
print("\n(saved as reachability_report.txt)")
