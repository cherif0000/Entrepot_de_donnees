
import argparse
import sys

from src.db import connect, run_sql_file
from src.export_csv import export_all
from src.quality import run_checks
from src.staging import load_all


def run(data_dir="data/olist", export=False):
    with connect() as conn:
        print("1. Réinitialisation de l'entrepôt")
        run_sql_file(conn, "00_reset.sql")

        print("2. Chargement des fichiers bruts (staging)")
        load_all(conn, data_dir)

        print("3. Construction des dimensions")
        run_sql_file(conn, "10_dimensions.sql")

        print("4. Construction des tables de faits")
        run_sql_file(conn, "20_facts.sql")

        print("5. Contrôles de qualité")
        errors = run_checks(conn)
        if errors:
            print("Pipeline arrêté : des contrôles bloquants ont échoué.")
            return False

        if export:
            print("6. Export CSV")
            export_all(conn)
    print("Pipeline terminé.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Pipeline de l'entrepôt Olist")
    parser.add_argument("--data-dir", default="data/olist")
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    sys.exit(0 if run(args.data_dir, args.export) else 1)


if __name__ == "__main__":
    main()
