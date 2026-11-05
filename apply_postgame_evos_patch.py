# Run from the repo root:  python3 apply_postgame_evos_patch.py
# Linoone -> Obstagoon (Lv 45) and Corsola -> Cursola (Lv 40), but only once the National Dex is enabled (postgame).
import re, os, sys
def die(m): print("STOP:", m); sys.exit(1)
G3 = 'src/data/pokemon/species_info/gen_3_families.h'
G2 = 'src/data/pokemon/species_info/gen_2_families.h'
PK = 'src/pokemon.c'
for p in (G3, G2, PK):
    if not os.path.exists(p): die(f"{p} not found - run from the repo root")
files = {p: open(p, encoding='utf-8').read() for p in (G3, G2, PK)}
if 'GetEvolutionTargetSpeciesRaw' in files[PK]: die("already applied")

def add_evo(p, species, form_line, evo_line):
    t = files[p]
    s = t.find(f'[SPECIES_{species}] =')
    if s < 0: die(f"[SPECIES_{species}] not found")
    m = re.compile(r'^([ \t]*)' + re.escape(form_line) + r'[ \t]*$', re.M).search(t, s)
    if not m: die(f"{species}: could not find '{form_line}' - nothing was changed")
    if '.evolutions' in t[s:m.start()]: die(f"{species} already has an .evolutions line - tell Claude")
    files[p] = t[:m.start()] + f"{m.group(1)}{evo_line}\n" + t[m.start():]
    print(f"ok: {species} evolution added")

add_evo(G3, 'LINOONE', '.formSpeciesIdTable = sLinooneFormSpeciesIdTable,', '.evolutions = EVOLUTION({EVO_LEVEL, 45, SPECIES_OBSTAGOON}),')
add_evo(G2, 'CORSOLA', '.formSpeciesIdTable = sCorsolaFormSpeciesIdTable,', '.evolutions = EVOLUTION({EVO_LEVEL, 40, SPECIES_CURSOLA}),')

sig = r'enum Species GetEvolutionTargetSpecies\(struct Pokemon \*mon, enum EvolutionMode mode, u16 evolutionItem, struct Pokemon \*tradePartner, bool32 \*canStopEvo, enum EvoState evoState\)'
params = 'struct Pokemon *mon, enum EvolutionMode mode, u16 evolutionItem, struct Pokemon *tradePartner, bool32 *canStopEvo, enum EvoState evoState'
new, n = re.subn(sig, lambda m: f'''static enum Species GetEvolutionTargetSpeciesRaw({params});

// Obstagoon and Cursola only evolve once the National Dex is enabled (postgame).
enum Species GetEvolutionTargetSpecies({params})
{{
    enum Species target = GetEvolutionTargetSpeciesRaw(mon, mode, evolutionItem, tradePartner, canStopEvo, evoState);
    if ((target == SPECIES_OBSTAGOON || target == SPECIES_CURSOLA) && !IsNationalPokedexEnabled())
        return SPECIES_NONE;
    return target;
}}

static enum Species GetEvolutionTargetSpeciesRaw({params})''', files[PK])
if n != 1: die(f"GetEvolutionTargetSpecies definition matched {n} places (expected 1) - nothing was changed")
files[PK] = new
if not re.search(r'#include "event_data\.h"', files[PK]):
    files[PK], k = re.subn(r'(#include "global\.h"\n)', lambda m: m.group(1) + '#include "event_data.h"\n', files[PK], count=1)
    if k != 1: die("could not add the event_data.h include - nothing was changed")
    print("ok: event_data.h include added")
print("ok: postgame gate added to the evolution check")
for p, t in files.items(): open(p, 'w', encoding='utf-8').write(t)
print("DONE. Now run:  make -j$(nproc)")
