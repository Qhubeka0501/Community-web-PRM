"""
Lightweight integration/guard tests: they assert the Flask app stays syntactically
valid, that no SQLite runtime sneaks in, that product images stay in their own table
and that the multi-role selling rule remains documented in code.
"""

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "backend" / "app.py"


# Guard: the Flask app must always parse as valid Python.
def test_python_syntax():
    ast.parse(APP.read_text())


# Guard: the project must stay on MySQL - no SQLite artefacts anywhere.
def test_no_sqlite_runtime_usage():
    text = "\n".join(
        p.read_text(errors="ignore")
        for p in ROOT.rglob("*")
        if p.is_file()
        and "tests" not in p.parts
        and ".zip" not in p.suffix
    )

    forbidden = [
        "node:sqlite",
        "DatabaseSync",
        "residencehub.sqlite",
    ]

    for token in forbidden:
        assert token not in text


# Guard: product images live in their own table instead of numbered image columns.
def test_unlimited_product_images_schema():
    migration = (ROOT / "backend" / "migrate_database.py").read_text()

    assert "CREATE TABLE IF NOT EXISTS product_images" in migration
    assert "image1" not in migration
    assert "image15" not in migration


# Guard: any authenticated user may sell (multi-role rule must stay in code).
def test_multirole_seller_rule_documented():
    app = APP.read_text()

    assert "def can_sell(user): return user is not None" in app


def test_student_registration_labels_are_specific():
    register_template = (ROOT / "backend" / "templates" / "register.html").read_text()

    assert "Campus name" in register_template
    assert "Student number" in register_template