
from pathlib import Path

from psycopg2 import sql

from src.db import connect

TABLES = [
    "dim_date", "dim_customer", "dim_product", "dim_seller",
    "fact_order_items", "fact_payments", "fact_reviews",
]


def select_list(conn, table):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'dwh' AND table_name = %s ORDER BY ordinal_position",
            (table,),
        )
        columns = cur.fetchall()
    parts = []
    for name, data_type in columns:
        ident = sql.Identifier(name)
        if data_type == "boolean":
            parts.append(sql.SQL("{}::int AS {}").format(ident, ident))
        else:
            parts.append(ident)
    return sql.SQL(", ").join(parts)


def export_all(conn, out_dir="exports"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for table in TABLES:
        path = out / f"{table}.csv"
        query = sql.SQL("COPY (SELECT {} FROM dwh.{}) TO STDOUT WITH (FORMAT csv, HEADER true)").format(
            select_list(conn, table), sql.Identifier(table)
        )
        with conn.cursor() as cur, open(path, "w", encoding="utf-8", newline="") as f:
            cur.copy_expert(query.as_string(conn), f)
        print(f"  {path}")


if __name__ == "__main__":
    with connect() as connection:
        export_all(connection)
