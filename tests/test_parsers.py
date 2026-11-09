from src.quality import parse_checks
from src.report import parse_queries

CHECKS = """
-- commentaire d'introduction
-- check: premier contrôle | error
SELECT 1;

-- check: second contrôle | warning
SELECT COUNT(*)
FROM x;
"""


def test_parse_checks_reads_name_severity_and_query():
    checks = parse_checks(CHECKS)
    assert [c[0] for c in checks] == ["premier contrôle", "second contrôle"]
    assert [c[1] for c in checks] == ["error", "warning"]
    assert checks[1][2] == "SELECT COUNT(*)\nFROM x;"


def test_parse_queries_reads_titles():
    text = "-- query: Titre A\nSELECT 1;\n\n-- query: Titre B\nSELECT 2;\n"
    assert parse_queries(text) == [("Titre A", "SELECT 1;"), ("Titre B", "SELECT 2;")]
