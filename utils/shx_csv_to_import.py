import csv
import json
from pathlib import Path

SRC_CSV = Path("SHX_TestData_MemberHousehold_Krokek_4 more.csv")
OUT_JSON = Path("batches_to_retry/batch_from_shx.json")


def clean(s: str) -> str:
    if s is None:
        return ""
    # Normalize spaces, remove NBSP and trim
    return s.replace("\u00A0", " ").strip()


def main() -> None:
    if not SRC_CSV.exists():
        raise SystemExit(f"Source CSV not found: {SRC_CSV}")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    data = []
    with SRC_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            mmid = clean(row.get("MMID", ""))
            first = clean(row.get("FirstName", ""))
            last = clean(row.get("LastName", ""))
            ssn = clean(row.get("SSN", ""))

            if not mmid:
                # Per assumption, MMID should exist; skip if absent
                continue

            person = {
                "customerId": mmid,
                "statisticalUseAllowed": True,
                "declarationAvailable": True,
                "status": "ACTIVE",
                "firstName": first,
                "lastName": last,
                # birthday intentionally omitted per requirements
                "customerCards": [
                    {"number": mmid, "type": "MAIN_CARD", "scope": "GLOBAL"},
                    {"number": ssn, "type": "PARTNER_CARD", "scope": "GLOBAL"},
                ],
            }

            data.append({
                "changeType": "CREATE",
                "type": "PERSON",
                "person": person,
            })

    payload = {"data": data}
    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(data)} records to {OUT_JSON}")


if __name__ == "__main__":
    main()

