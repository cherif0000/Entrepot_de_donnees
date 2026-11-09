import csv
import re
from pathlib import Path

from psycopg2 import sql

FILES = {
    "olist_customers_dataset.csv": "customers",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}

IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


def read_header(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f))


def check_identifier(name):
    if not IDENTIFIER.match(name):
        raise ValueError(f"Nom de colonne inattendu : {name!r}")
    return name


def create_table(conn, table, columns):
    """Recrée staging.<table> avec une colonne texte par colonne du CSV."""
    cols = [check_identifier(c) for c in columns]
    with conn.cursor() as cur:
        cur.execute(sql.SQL("DROP TABLE IF EXISTS staging.{}").format(sql.Identifier(table)))
        cur.execute(
            sql.SQL("CREATE TABLE staging.{} ({})").format(
                sql.Identifier(table),
                sql.SQL(", ").join(sql.SQL("{} TEXT").format(sql.Identifier(c)) for c in cols),
            )
        )


def load_file(conn, path, table):
    """Charge un CSV avec COPY, la méthode la plus rapide de PostgreSQL. Retourne le nombre de lignes."""
    columns = read_header(path)
    create_table(conn, table, columns)
    copy_sql = sql.SQL(
        "COPY staging.{} ({}) FROM STDIN WITH (FORMAT csv, HEADER true)"
    ).format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(c) for c in columns),
    )
    with conn.cursor() as cur, open(path, "r", encoding="utf-8-sig", newline="") as f:
        cur.copy_expert(copy_sql, f)
        cur.execute(sql.SQL("SELECT COUNT(*) FROM staging.{}").format(sql.Identifier(table)))
        count = cur.fetchone()[0]
    conn.commit()
    return count


def load_all(conn, data_dir):
    data_dir = Path(data_dir)
    manquants = [name for name in FILES if not (data_dir / name).exists()]
    if manquants:
        raise FileNotFoundError(
            f"Fichiers manquants dans {data_dir} : {', '.join(manquants)}"
        )
    counts = {}
    for name, table in FILES.items():
        counts[table] = load_file(conn, data_dir / name, table)
        print(f"  staging.{table}: {counts[table]} lignes")
    return counts
