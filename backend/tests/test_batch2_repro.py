import json, os, pytest
from app.services.engine_service import run_engine
from tests.conftest import make_event, make_category, make_unit, make_participant, make_mark, assign_mark
def marks_of(n): return [] if not n.startswith("MARK:") else [m.strip() for m in n.split("|")[0].replace("MARK:","").split("+") if m.strip()]
@pytest.mark.asyncio
async def test_b2(db):
    # v1.0.2: these repro fixtures are generated in dev sessions and are
    # not shipped in the repo — skip cleanly when absent so a fresh
    # clone's pytest run stays green.
    if not os.path.exists("/tmp/people2.json"):
        pytest.skip("stress fixture /tmp/people2.json not present (generated in dev sessions)")
    people=json.load(open("/tmp/people2.json"))
    ev=await make_event(db)
    gl=await make_mark(db,ev.id,name="Gruppenleiter",cluster_behaviour="split")
    fl=await make_mark(db,ev.id,name="Fleischesser",cluster_behaviour="none")
    mu=await make_mark(db,ev.id,name="Musiker",cluster_behaviour="together")
    mkid={"Gruppenleiter":gl.id,"Fleischesser":fl.id,"Musiker":mu.id}
    cat=await make_category(db,ev.id,has_capacity=True,settings={"engine":{"use_group_codes":True,"group_remaining_by_gender":True,"split_oversized_groups":True,"include_pending":True,"equalise_after_allocation":True,"mark_priorities":[{"id":str(fl.id),"behaviour":"none"},{"id":str(mu.id),"behaviour":"together"},{"id":str(gl.id),"behaviour":"split"}]}})
    Z=[await make_unit(db,cat.id,f"Zimmer {i}",capacity=8) for i in range(1,8)]
    men=await make_unit(db,cat.id,"Men",capacity=12); men.gender_restriction="male"
    fra=await make_unit(db,cat.id,"Frauen",capacity=20); fra.gender_restriction="female"
    flr=await make_unit(db,cat.id,"Fleischesser",capacity=8); flr.mark_restriction=fl.id
    mur=await make_unit(db,cat.id,"Musiker",capacity=8)
    await db.flush()
    rooms=Z+[men,fra,flr,mur]; name_of={str(u.id):u.name for u in rooms}; genrooms={str(u.id) for u in Z}
    pmap={}
    for pr in people:
        p=await make_participant(db,ev.id,first_name=pr["first_name"],last_name=pr["last_name"],gender=(pr["gender"] or None),group_code=(pr["group_code"] or None))
        pmap[str(p.id)]=pr
        for m in marks_of(pr["Notes"]): await assign_mark(db,ev.id,mkid[m],p.id)
    await db.flush()
    res=await run_engine(db,ev.id,cat.id,mode="replace")
    where={pid:name_of[uid] for uid,pids in res["proposed"].items() for pid in pids}
    print(f"\n  ASSIGNED {sum(len(v) for v in res['proposed'].values())}/100  UNASSIGNED {len(res['unplaced'])}")
    print("  room fill:", {u.name: f"{len(res['proposed'].get(str(u.id),[]))}/{u.capacity}" for u in rooms})
    # single-gender clusters sitting in GENERAL rooms while their gender room has slack
    print(f"\n  Men free seats: {men.capacity-len(res['proposed'].get(str(men.id),[]))}")
    fams={}
    for pid,pr in pmap.items():
        if pr["group_code"]: fams.setdefault(pr["group_code"],[]).append((pr,where.get(pid,"UNASSIGNED")))
    print("  ALL-MALE clusters and where they are:")
    for c,mem in fams.items():
        if all(p["gender"]=="male" for p,_ in mem):
            rs=sorted(set(r for _,r in mem))
            in_general = any(r.startswith("Zimmer") for _,r in mem)
            print(f"    {c:20} ({len(mem)} male): {', '.join(rs)}{'   <-- MALE CLUSTER IN A GENERAL ROOM' if in_general else ''}")
    # unassigned
    for pid in res["unplaced"]:
        pr=pmap[pid]; print(f"\n  UNASSIGNED: {pr['first_name']} {pr['last_name']} gender={pr['gender'] or 'UNKNOWN'} marks={marks_of(pr['Notes']) or '-'}")
