"""Contrôles de qualité lus dans sql/quality_checks.sql."""
import re

from src.db import SQL_DIR

CHECK_LINE = re.compile(r"^--\s*check:\s*(.+?)\s*\|\s*(error|warning)\s*$")


def parse_checks(text):
    """Découpe le fichier en (nom, gravité, requête)."""
    checks, current = [], None
    for line in text.splitlines():
        match = CHECK_LINE.match(line.strip())
        if match:
            if current:
                checks.append(current)
            current = [match.group(1), match.group(2), []]
        elif current is not None and not line.strip().startswith("--"):
            current[2].append(line)
    if current:
        checks.append(current)
    return [(name, severity, "\n".join(body).strip()) for name, severity, body in checks]


def run_checks(conn):
    """Exécute les contrôles. Retourne la liste des erreurs (les avertissements sont seulement affichés)."""
    text = (SQL_DIR / "quality_checks.sql").read_text(encoding="utf-8")
    errors = []
    for name, severity, query in parse_checks(text):
        with conn.cursor() as cur:
            cur.execute(query)
            n = cur.fetchone()[0]
        if n == 0:
            print(f"  OK       {name}")
        elif severity == "warning":
            print(f"  ATTENTION {name} : {n}")
        else:
            print(f"  ERREUR   {name} : {n}")
            errors.append((name, n))
    return errors
