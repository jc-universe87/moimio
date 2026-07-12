import json, os, pytest
from app.services.engine_service import run_engine
from tests.conftest import make_event, make_category, make_unit, make_participant, make_mark, assign_mark

def marks_of(note):
    return [] if not note.startswith("MARK:") else [m.strip() for m in note.split("|")[0].replace("MARK:","").split("+") if m.strip()]

@pytest.mark.asyncio
async def test_full_run(db):
    # v1.0.2: these repro fixtures are generated in dev sessions and are
    # not shipped in the repo — skip cleanly when absent so a fresh
    # clone's pytest run stays green.
    if not os.path.exists("/tmp/people.json"):
        pytest.skip("stress fixture /tmp/people.json not present (generated in dev sessions)")
    people = json.load(open("/tmp/people.json"))
    ev = await make_event(db)
    # marks
    gl = await make_mark(db, ev.id, name="Gruppenleiter", cluster_behaviour="split", colour="#22c55e")
    fl = await make_mark(db, ev.id, name="Fleischesser", cluster_behaviour="none", colour="#a855f7")
    mu = await make_mark(db, ev.id, name="Musiker", cluster_behaviour="together", colour="#3b82f6")
    mkid = {"Gruppenleiter":gl.id,"Fleischesser":fl.id,"Musiker":mu.id}
    cat = await make_category(db, ev.id, has_capacity=True, settings={"engine":{
        "use_group_codes":True,"group_remaining_by_gender":True,"split_oversized_groups":True,
        "include_pending":True,"equalise_after_allocation":True,
        "mark_priorities":[{"id":str(fl.id),"behaviour":"none"},{"id":str(mu.id),"behaviour":"together"},{"id":str(gl.id),"behaviour":"split"}],
    }})
    # rooms matching the screenshot
    Z = [await make_unit(db, cat.id, f"Zimmer {i}", capacity=8) for i in range(1,7)]
    maen = await make_unit(db, cat.id, "Maenner", capacity=14); maen.gender_restriction="male"
    frau = await make_unit(db, cat.id, "Frauen", capacity=14); frau.gender_restriction="female"
    flr  = await make_unit(db, cat.id, "Fleischesser", capacity=8); flr.mark_restriction=fl.id
    mur  = await make_unit(db, cat.id, "Musiker", capacity=8)
    await db.flush()
    rooms = Z + [maen, frau, flr, mur]
    name_of = {str(u.id): u.name for u in rooms}

    # participants + marks
    pmap = {}
    for pr in people:
        p = await make_participant(db, ev.id, first_name=pr["first_name"], last_name=pr["last_name"],
                                   gender=(pr["gender"] or None), group_code=(pr["group_code"] or None))
        pmap[str(p.id)] = (pr, p)
        for m in marks_of(pr["Notes"]):
            await assign_mark(db, ev.id, mkid[m], p.id)
    await db.flush()

    res = await run_engine(db, ev.id, cat.id, mode="replace")
    placed_room = {}
    for uid, pids in res["proposed"].items():
        for pid in pids: placed_room[pid] = name_of[uid]

    tot = sum(len(v) for v in res["proposed"].values())
    print(f"\n  ASSIGNED {tot} / 100   UNASSIGNED {len(res['unplaced'])}   (your run: 91 / 9)")
    print("  room fill:", {u.name: len(res["proposed"].get(str(u.id),[])) for u in rooms})

    # family cohesion
    fams = {}
    for pid,(pr,p) in pmap.items():
        c = pr["group_code"]
        if c: fams.setdefault(c, []).append((pr["first_name"]+" "+pr["last_name"], placed_room.get(pid,"UNASSIGNED")))
    print("\n  FAMILY COHESION (rooms each family landed in):")
    for c in sorted(fams, key=lambda k:-len(fams[k])):
        rs = sorted(set(r for _,r in fams[c]))
        split = "  <-- SPLIT" if len(rs)>1 else ""
        print(f"    {c:12} ({len(fams[c])}): {', '.join(rs)}{split}")

    # CHOI detail
    print("\n  CHOI-2024 detail (the mixed-group family):")
    for pid,(pr,p) in pmap.items():
        if pr["group_code"]=="CHOI-2024":
            mk = "+".join(marks_of(pr["Notes"])) or "-"
            print(f"    {pr['first_name']} {pr['last_name']:8} marks={mk:20} -> {placed_room.get(pid,'UNASSIGNED')}  reason={res['proposed'] and (res.get('reasons',{}) or {}).get(pid,'')}")

    # unassigned
    print("\n  UNASSIGNED — each with gender (all should be unplaceable):")
    for pid in res["unplaced"]:
        pr,_ = pmap[pid]
        print(f"    {pr['first_name']} {pr['last_name']:8} gender={pr['gender'] or 'UNKNOWN':8} marks={'+'.join(marks_of(pr['Notes'])) or '-'}")
