"""End-to-end extract, transform, then load pipeline test."""
import json
import shutil
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from conftest import http_response
from data_processing import extract
from data_processing import load
from data_processing import transform

EXTRACT_FIXTURES = Path(__file__).parent / "fixtures" / "extract"
HAND_BUILT = Path(__file__).parent / "fixtures" / "transform"
HAND_BUILT_EXTRACTED = HAND_BUILT / "extracted"
HAND_BUILT_ASSISTANCE_ZIPS = HAND_BUILT / "usaspending" / "assistance"
HAND_BUILT_CONTRACT_ZIPS = HAND_BUILT / "usaspending" / "contracts"

TEMP_URI = "file:transform_e2e_temp?mode=memory&cache=shared"
MAIN_URI = "file:transform_e2e_main?mode=memory&cache=shared"

EXTRACT_PROGRAM_IDS = ["11.611", "12.002", "14.880", "93.127", "93.858"]
EXTRACT_HASHES = {
    "11.611": "3fae422b0b6eb1e105708601c3441d3c",
    "14.880": "24acf3f7334e3c64ce797fdc18014252",
    "12.002": "5cbdb4694d272cc01619c75d4ae9bda6",
    "93.127": "e60ac50c69716a8e2fb336a7cf018c6b",
    "93.858": "40305f91b32cd321078c9ad0393dd50a",
}


@pytest.fixture(autouse=True)
def patch_paths():
    """Override conftest autouse stub of exists/makedirs so real I/O works."""
    yield


@pytest.fixture
def real_sqlite():
    previous = {
        "temp_conn": transform.temp_conn,
        "temp_cur": transform.temp_cur,
        "conn": transform.conn,
        "cur": transform.cur,
    }
    # Keep a connection open so the shared in-memory DB survives main()'s
    # conn.close().
    keeper = sqlite3.connect(MAIN_URI, uri=True)
    transform.temp_conn = sqlite3.connect(TEMP_URI, uri=True)
    transform.temp_cur = transform.temp_conn.cursor()
    transform.conn = sqlite3.connect(MAIN_URI, uri=True)
    transform.cur = transform.conn.cursor()
    transform.cur.execute(f"ATTACH DATABASE '{TEMP_URI}' AS temp_db")
    transform.conn.commit()
    yield
    for conn in (transform.conn, transform.temp_conn, keeper):
        try:
            conn.close()
        except Exception:
            pass
    for name, value in previous.items():
        setattr(transform, name, value)


def _json_response(filename, status_code=200):
    body = (EXTRACT_FIXTURES / filename).read_text(encoding="utf-8")
    return http_response(json.loads(body), text=body, status_code=status_code)


def _json_item_response(filename, item_id, id_key="id", status_code=200):
    items = json.loads((EXTRACT_FIXTURES / filename).read_text(encoding="utf-8"))

    def item_identifier(item):
        if callable(id_key):
            return id_key(item)
        return item.get(id_key)

    match = next(
        (item for item in items if str(item_identifier(item)) == str(item_id)),
        None,
    )
    if match is None:
        raise AssertionError(f"No {filename} fixture item with {id_key}={item_id}")
    return http_response(match, status_code=status_code)


def _text_response(filename, status_code=200):
    body = (EXTRACT_FIXTURES / filename).read_text(encoding="utf-8")
    return http_response(text=body, status_code=status_code)


def _mock_get(url, headers=None, timeout=60, **kwargs):
    if "/sgs/v1/search/" in url:
        return _json_response("sam_cfda_search.json")
    if "/fac/v1/programs/dictionaries" in url:
        return _json_response("sam_dictionary.json")
    if "/fac/v1/programs/" in url:
        program_id = url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
        return _json_item_response("sam_program.json", program_id)
    if "/federalorganizations/v1/organizations/" in url:
        organization_id = url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
        return _json_item_response(
            "sam_organization.json",
            organization_id,
            id_key=lambda item: item["_embedded"][0]["org"]["orgKey"],
        )
    if "improper-payment-program-mapping.csv" in url:
        return _text_response("improper-payment-program-mapping.csv")
    raise AssertionError(f"Unexpected GET {url}")


def _mock_post(url, data=None, headers=None, timeout=60, **kwargs):
    if "autocomplete/cfda" in url:
        search_text = ""
        if isinstance(data, dict):
            search_text = str(data.get("search_text") or "")
        letter = search_text[:1]
        payload = json.loads(
            (EXTRACT_FIXTURES / "usaspending_autocomplete.json").read_text(
                encoding="utf-8"
            )
        )
        matches = []
        if letter:
            matches = [
                item for item in payload.get("results", [])
                if str(item.get("program_title") or "").lower().startswith(
                    letter.lower()
                )
            ]
        return http_response({"results": matches})
    if "references/filter" in url:
        body = data
        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8")
        if isinstance(body, str):
            body = json.loads(body)
        selected = (body or {}).get("filters", {}).get("selectedCFDA", {})
        program_number = next(iter(selected), None)
        return _json_item_response(
            "usaspending_filter.json",
            program_number,
            id_key="program_number",
        )
    raise AssertionError(f"Unexpected POST {url}")


def _run_extract(extracted_dir):
    disk = str(extracted_dir) + "/"
    with patch("data_processing.extract.DISK_DIRECTORY", disk), \
         patch("data_processing.extract.EXTRACTED_DIRECTORY", ""), \
         patch("data_processing.extract.check_extract_preconditions"), \
         patch("requests.get", side_effect=_mock_get), \
         patch("requests.post", side_effect=_mock_post):
        extract.main()


def _assert_extract_output(extracted_dir):
    listings_path = extracted_dir / "assistance-listings.json"
    dictionary_path = extracted_dir / "dictionary.json"
    ip_path = extracted_dir / "improper-payment-program-mapping.csv"
    orgs_path = extracted_dir / "organizations.json"
    hashes_path = extracted_dir / "usaspending-program-search-hashes.json"

    listings = json.loads(listings_path.read_text(encoding="utf-8"))
    assert isinstance(listings, list)
    assert len(listings) >= 1
    assert "programNumber" in listings[0]["data"]
    assert "lndian" not in listings_path.read_text(encoding="utf-8")
    assert "Indian" in listings_path.read_text(encoding="utf-8")
    program_numbers = {row["data"]["programNumber"] for row in listings}
    assert set(EXTRACT_PROGRAM_IDS) == program_numbers

    dictionary = json.loads(dictionary_path.read_text(encoding="utf-8"))
    assert "_embedded" in dictionary

    assert ip_path.read_text(encoding="utf-8") == (
        EXTRACT_FIXTURES / "improper-payment-program-mapping.csv"
    ).read_text(encoding="utf-8")

    organizations = json.loads(orgs_path.read_text(encoding="utf-8"))
    assert isinstance(organizations, list)
    assert "orgKey" in organizations[0]
    assert "_embedded" not in organizations[0]
    agency_names = {
        org.get("agencyName") or org.get("name") for org in organizations
    }
    assert "Department of the Treasury" in agency_names
    assert "Internal Revenue Service (IRS)" in agency_names

    hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
    assert isinstance(hashes, dict)
    for program_number in program_numbers:
        assert program_number in hashes
        assert isinstance(hashes[program_number], str)
        assert hashes[program_number]
        assert hashes[program_number] == EXTRACT_HASHES[program_number]


def _overlay_hand_built_extracted_files(extracted_dir):
    if not HAND_BUILT_EXTRACTED.exists():
        return
    for src in HAND_BUILT_EXTRACTED.iterdir():
        if src.is_file():
            shutil.copy(src, extracted_dir / src.name)


def _zip_directory(hand_built_dir, tmp_path, name):
    if hand_built_dir.exists():
        return str(hand_built_dir) + "/"
    empty = tmp_path / name
    empty.mkdir()
    return str(empty) + "/"


def _has_zip_files(directory):
    if not directory.exists():
        return False
    return any(
        path.is_file() and path.name[0] != "." and path.suffix.lower() == ".zip"
        for path in directory.iterdir()
    )


def _point_transform_at(extracted_dir, tmp_path):
    unzip = tmp_path / "unzip"
    unzip.mkdir()
    transform.REPO_DISK_DIRECTORY = ""
    transform.EXTRACTED_FILES_DIRECTORY = str(extracted_dir) + "/"
    transform.ADDITIONAL_PROGRAMS_DATA_PATH = str(
        extracted_dir / "additional-programs.csv"
    )
    transform.ASSISTANCE_ZIP_FILE_DIRECTORY = _zip_directory(
        HAND_BUILT_ASSISTANCE_ZIPS, tmp_path, "assistance_zips"
    )
    transform.CONTRACT_ZIP_FILE_DIRECTORY = _zip_directory(
        HAND_BUILT_CONTRACT_ZIPS, tmp_path, "contract_zips"
    )
    transform.UNZIP_TMP_DIRECTORY = str(unzip) + "/"
    transform.QA_DIRECTORY = tmp_path / "qa"
    transform.check_data_quality_before_transform.EXTRACTED_DIR = extracted_dir

def _assert_transform_output():
    conn = sqlite3.connect(MAIN_URI, uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    tables = {
        row[0]
        for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    expected_tables = {
        "agency",
        "category",
        "program",
        "program_authorization",
        "program_result",
        "program_sam_spending",
        "program_to_category",
        "usaspending_assistance_obligation_aggregation",
        "usaspending_assistance_outlay_aggregation",
        "other_program_spending",
        "improper_payment_mapping",
        "taxonomy_category",
        "taxonomy_focus_area",
        "gwo",
        "pon",
        "program_to_gwo",
        "program_to_pon",
    }
    assert expected_tables.issubset(tables)

    views = {
        row[0]
        for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='view'"
        )
    }
    assert "program_amounts_lookup" in views
    assert "program_taxonomy_lookup" in views

    program_ids = {
        row["id"]
        for row in cur.execute("SELECT id FROM program")
    }
    assert set(EXTRACT_PROGRAM_IDS).issubset(program_ids)

    listing = cur.execute(
        "SELECT * FROM program WHERE id = ?",
        ("11.611",),
    ).fetchone()
    assert listing["program_type"] == "assistance_listing"
    assert listing["name"] == "Manufacturing Extension Partnership"
    assert listing["is_subpart_f"] == 1
    assert listing["usaspending_awards_hash"] == EXTRACT_HASHES["11.611"]
    assert listing["sam_url"].endswith(
        "/fal/7f35e497c11544ad8900a967a1284d89/view"
    )

    popular = cur.execute(
        "SELECT popular_name FROM program WHERE id = ?",
        ("12.002",),
    ).fetchone()
    assert popular["popular_name"].startswith("APEX Accelerator Program")

    for program_id, expected_hash in EXTRACT_HASHES.items():
        row = cur.execute(
            "SELECT usaspending_awards_hash FROM program WHERE id = ?",
            (program_id,),
        ).fetchone()
        assert row["usaspending_awards_hash"] == expected_hash

    agencies = {
        row["agency_name"]
        for row in cur.execute("SELECT agency_name FROM agency")
    }
    assert "Department of Commerce" in agencies
    assert "Department of the Treasury" in agencies
    commerce = cur.execute(
        """
        SELECT is_cfo_act_agency FROM agency
        WHERE agency_name = ?
        """,
        ("Department of Commerce",),
    ).fetchone()
    assert commerce["is_cfo_act_agency"] == 1

    assert cur.execute("SELECT COUNT(*) FROM category").fetchone()[0] >= 1
    assert cur.execute(
        "SELECT COUNT(*) FROM program_sam_spending WHERE program_id = ?",
        ("11.611",),
    ).fetchone()[0] >= 1
    assert cur.execute(
        "SELECT COUNT(*) FROM program_to_category WHERE program_id = ?",
        ("11.611",),
    ).fetchone()[0] >= 1
    assert cur.execute(
        "SELECT COUNT(*) FROM program_authorization WHERE program_id = ?",
        ("11.611",),
    ).fetchone()[0] >= 1
    assert cur.execute(
        "SELECT COUNT(*) FROM improper_payment_mapping"
    ).fetchone()[0] >= 1

    amounts = cur.execute(
        """
        SELECT obligation, expenditure
        FROM program_amounts_lookup
        WHERE id = ? AND fiscal_year = ?
        """,
        ("11.611", "2025"),
    ).fetchone()
    assert amounts is not None

    orphaned = cur.execute(
        """
        SELECT COUNT(*) FROM program_to_category
        WHERE program_id NOT IN (SELECT id FROM program)
        """
    ).fetchone()[0]
    assert orphaned == 0

    if "IN.001" in program_ids:
        extra = cur.execute(
            "SELECT * FROM program WHERE id = ?",
            ("IN.001",),
        ).fetchone()
        assert extra["program_type"] == "interest"

    contracts = cur.execute(
        "SELECT * FROM program WHERE program_type = 'contracts'"
    ).fetchall()
    if contracts:
        assert contracts[0]["id"]

    temp = sqlite3.connect(TEMP_URI, uri=True)
    assistance_count = temp.execute(
        "SELECT COUNT(*) FROM usaspending_assistance"
    ).fetchone()[0]
    contract_count = temp.execute(
        "SELECT COUNT(*) FROM usaspending_contract"
    ).fetchone()[0]
    if _has_zip_files(HAND_BUILT_ASSISTANCE_ZIPS):
        assert assistance_count >= 1
    else:
        assert assistance_count == 0
    if _has_zip_files(HAND_BUILT_CONTRACT_ZIPS):
        assert contract_count >= 1
    else:
        assert contract_count == 0
    temp.close()
    conn.close()


def _write_transformed_db(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(MAIN_URI, uri=True)
    dst = sqlite3.connect(path)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def _load_front_matter(path):
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    body = content.split("---", 2)[1]
    return yaml.safe_load(body)


def _run_load(tmp_path, extracted_dir, monkeypatch):
    website = tmp_path / "website"
    indexer = tmp_path / "indexer"
    data_processing_dir = tmp_path / "data_processing"
    db_path = website / "transformed_data.db"
    _write_transformed_db(db_path)

    for relative in (
        "website/_data",
        "website/pages",
        "website/assets/files",
        "indexer",
        "data_processing",
    ):
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)

    load.obligations_data = {}
    load.outlays_data = {}
    monkeypatch.chdir(data_processing_dir)

    with patch.object(load, "full_path", str(db_path)), \
         patch.object(load, "QA_DIRECTORY", tmp_path / "qa"), \
         patch.object(load, "MARKDOWN_DIR", str(website / "_program")), \
         patch.object(
             load,
             "INFLATION_POPULATION_FILE_PATH",
             str(extracted_dir / "inflation_and_population_growth.csv"),
         ), \
         patch.object(
             load, "GLOBAL_DATA_YML_PATH", str(website / "_data" / "global_data.yml")
         ), \
         patch.object(
             load, "DATA_SOURCES_YML_PATH", str(website / "_data" / "data_sources.yml")
         ), \
         patch.object(
             load, "__file__", str(data_processing_dir / "load.py")
         ):
        load.main()

    return website, indexer


def _assert_load_output(website, indexer):
    program_dir = website / "_program"
    assert (program_dir / "11.611.md").is_file()
    assert (program_dir / "IN.001.md").is_file()
    assert (program_dir / "TC.001.md").is_file()
    assert list(program_dir.glob("G3.C.12.*.md"))

    listing = _load_front_matter(program_dir / "11.611.md")
    assert listing["layout"] == "program"
    assert listing["cfda"] == "11.611"
    assert listing["program_type"] == "assistance_listing"
    assert listing["obligations"]
    assert listing["outlays"]

    interest = _load_front_matter(program_dir / "IN.001.md")
    assert interest["program_type"] == "interest"
    assert interest["other_program_spending"]

    csv_path = website / "assets" / "files" / "all-program-data.csv"
    csv_text = csv_path.read_text(encoding="utf-8")
    assert csv_text.splitlines()[0].startswith("program_number,")
    assert "11.611" in csv_text
    assert "IN.001" in csv_text

    programs_json = json.loads(
        (indexer / "programs-table.json").read_text(encoding="utf-8")
    )
    assert isinstance(programs_json, list)
    assert {row["cfda"] for row in programs_json} >= set(EXTRACT_PROGRAM_IDS)

    global_data = yaml.safe_load(
        (website / "_data" / "global_data.yml").read_text(encoding="utf-8")
    )
    assert "InflationPopulation" in global_data

    dates = yaml.safe_load(
        (website / "_data" / "constants_global_dates.yml").read_text(encoding="utf-8")
    )
    assert dates["LAST_COMPLETED_FISCAL_YEAR"]

    sources = yaml.safe_load(
        (website / "_data" / "data_sources.yml").read_text(encoding="utf-8")
    )
    assert "data_sources" in sources

    for name in (
        "search.md", "taxonomy.md", "category.md", "home.md",
        "about-fpi.md", "about-terms.md",
    ):
        assert (website / "pages" / name).is_file()
        page = _load_front_matter(website / "pages" / name)
        assert "permalink" in page

    assert list((website / "_category").glob("*.md"))
    assert list((website / "_subcategory").glob("*.md"))
    assert list((website / "_gwo").glob("*.md"))
    assert list((website / "_pon").glob("*.md"))


def test_extract_then_transform(tmp_path, real_sqlite, monkeypatch):
    extracted_dir = tmp_path / "extracted"
    extracted_dir.mkdir()

    _run_extract(extracted_dir)
    _assert_extract_output(extracted_dir)

    _overlay_hand_built_extracted_files(extracted_dir)
    _point_transform_at(extracted_dir, tmp_path)
    transform.main()
    _assert_transform_output()
    website, indexer = _run_load(tmp_path, extracted_dir, monkeypatch)
    _assert_load_output(website, indexer)
