import re

from src.db import SQL_DIR, connect

QUERY_LINE = re.compile(r"^--\s*query:\s*(.+?)\s*$")


def parse_queries(text):
    queries, current = [], None
    for line in text.splitlines():
        match = QUERY_LINE.match(line.strip())
        if match:
            if current:
                queries.append(current)
            current = [match.group(1), []]
        elif current is not None and not line.strip().startswith("--"):
            current[1].append(line)
    if current:
        queries.append(current)
    return [(title, "\n".join(body).strip()) for title, body in queries]


def main():
    text = (SQL_DIR / "analytics.sql").read_text(encoding="utf-8")
    with connect() as conn:
        for title, query in parse_queries(text):
            with conn.cursor() as cur:
                cur.execute(query)
                columns = [d[0] for d in cur.description]
                rows = cur.fetchall()
            print(f"\n{title}")
            print(" | ".join(columns))
            for row in rows:
                print(" | ".join(str(v) for v in row))


if __name__ == "__main__":
    main()
