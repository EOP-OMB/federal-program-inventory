import csv
import os
import sqlite3
import zipfile
from pathlib import Path

BIG_UNIFIED_TABLE_FIRST_YEAR = "2015"

def _strip_newlines(value):
    if isinstance(value, str):
        return value.replace("\r", "").replace("\n", "")
    return value

def generate_csv_from_query(query, filename, params = (), zip = False) -> None:
    db_path = Path(os.environ.get("SQLITE_DB_PATH", "/app/transformed_data.db"))
    if not db_path.exists():
        raise FileNotFoundError(
            f"SQLite database not found at {db_path}. "
            "Set SQLITE_DB_PATH to the correct location."
        )

    output_dir = Path("/app/_dynamic")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / filename
    csv_file = output_file.with_suffix(".csv")
    zip_file = output_file.with_suffix(".zip")

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        headers = [description[0] for description in cursor.description]

    with csv_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        sanitized_rows = [[_strip_newlines(cell) for cell in row] for row in rows]
        writer.writerows(sanitized_rows)

    print(f"Wrote {len(rows)} rows to {csv_file}")

    if zip:
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(csv_file, arcname=filename + ".csv")
        csv_file.unlink(missing_ok=True)

def main() -> None:
    generate_csv_from_query("""
        SELECT
            gwo.id,
            gwo.gwo,
            gwo.gwo_definition,
            focus_area as subcategory,
			taxonomy_focus_area.id as subcategory_code,
			category,
			taxonomy_focus_area.id as category_code
        FROM gwo
        JOIN taxonomy_focus_area on gwo.focus_area_id = taxonomy_focus_area.id
        JOIN taxonomy_category ON taxonomy_focus_area.category_id = taxonomy_category.id
    """, "gwo")

    generate_csv_from_query("""
        SELECT
            pon.id,
            pon.pon2 as pon,
            pon.pon_definition,
            focus_area as subcategory,
			taxonomy_focus_area.id as subcategory_code,
			category,
			taxonomy_focus_area.id as category_code
        FROM pon
        JOIN taxonomy_focus_area on pon.focus_area_id = taxonomy_focus_area.id
        JOIN taxonomy_category ON taxonomy_focus_area.category_id = taxonomy_category.id
    """, "pon")

    generate_csv_from_query("""
        SELECT *
        FROM program_to_pon
    """, "program_to_pon")

    generate_csv_from_query("""
        SELECT
            program.id as program_id,
            program.name as program_name,
            program.popular_name,
            program.program_type,
			program.objective as program_description,
            (SELECT a2.agency_name
        FROM agency a2
        WHERE a2.id = a1.tier_1_agency_id) as top_agency_name,
        (SELECT a2.agency_name
            FROM agency a2
            WHERE a2.id = a1.tier_2_agency_id) as sub_agency_name,
        program_amounts_lookup.fiscal_year,
        program_amounts_lookup.outlay,
        program_amounts_lookup.obligation,
        program_amounts_lookup.expenditure,
        program_amounts_lookup.forgone_revenue,
        program_amounts_lookup.sam_estimated_obligation,
        program_amounts_lookup.sam_actual_obligation,
        program_amounts_lookup.usaspending_obligation_by_action_date,
		gwo.id as gwo_id,
		gwo.gwo
        FROM program
        LEFT JOIN agency a1 ON program.agency_id = a1.id
        LEFT JOIN program_amounts_lookup
        ON program.id = program_amounts_lookup.id
		LEFT JOIN program_to_gwo
		ON program.id = program_to_gwo.program_id
		LEFT JOIN gwo
		ON program_to_gwo.gwo_id = gwo.id
        WHERE program_amounts_lookup.fiscal_year >= ?
    """, "fpi_unified_table", (BIG_UNIFIED_TABLE_FIRST_YEAR, ), True)

if __name__ == "__main__":
    main()
