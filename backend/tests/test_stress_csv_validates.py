import os
import pytest
from app.services.batch_register_service import parse_csv
from tests.conftest import make_event

@pytest.mark.asyncio
async def test_stress_csv_imports_clean(db):
    ev = await make_event(db)
    # v1.0.2: these repro fixtures are generated in dev sessions and are
    # not shipped in the repo — skip cleanly when absent so a fresh
    # clone's pytest run stays green.
    if not os.path.exists("/mnt/user-data/outputs/20260710_moimio_stress_test_batch2_participants.csv"):
        pytest.skip("stress fixture /mnt/user-data/outputs/20260710_moimio_stress_test_batch2_participants.csv not present (generated in dev sessions)")
    content = open("/mnt/user-data/outputs/20260710_moimio_stress_test_batch2_participants.csv","rb").read()
    res = await parse_csv(content, ev.id, db, dob_format="eu")
    s = res["summary"]
    print("\n  SUMMARY:", s)
    # show any invalid rows with reasons
    bad = [(r["row"], r.get("errors")) for r in res["rows"] if not r["valid"]]
    if bad:
        print("  INVALID ROWS:", bad[:20])
    # unknown headers become auto-created custom fields on import
    unk = res.get("new_custom_field_candidates") or res.get("unknown_headers") or "see keys:" 
    print("  new-custom-field candidate keys present:", [k for k in res.keys() if "custom" in k or "unknown" in k])
    assert s["total"] == 100, s
    assert s["invalid"] == 0, f"{s['invalid']} invalid rows: {bad[:10]}"
    print("  ALL 100 ROWS VALID — imports clean")
