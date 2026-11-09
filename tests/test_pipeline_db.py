"""Test d'intégration : exécute tout le pipeline sur les données synthétiques de tests/fixtures.

Il réinitialise les schémas staging et dwh de la base utilisée : n'utilise JAMAIS ta vraie base.
Il ne s'exécute que si la variable TEST_POSTGRES_DB est définie (une base de test dédiée).
"""
import os
from pathlib import Path

import pytest

from src import pipeline
from src.db import connect

FIXTURES = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_POSTGRES_DB"),
    reason="TEST_POSTGRES_DB non défini : base de test requise",
)


@pytest.fixture(scope="module")
def built(request):
    mp = pytest.MonkeyPatch()
    mp.setenv("POSTGRES_DB", os.environ["TEST_POSTGRES_DB"])
    request.addfinalizer(mp.undo)
    assert pipeline.run(str(FIXTURES)) is True
    return True


def scalar(query):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchone()[0]


def test_no_order_item_is_lost(built):
    assert scalar("SELECT COUNT(*) FROM dwh.fact_order_items") == scalar("SELECT COUNT(*) FROM staging.order_items")


def test_reviews_are_deduplicated_on_exact_duplicates(built):
    assert scalar("SELECT COUNT(*) FROM dwh.fact_reviews") == scalar("SELECT COUNT(*) FROM staging.order_reviews")
    assert scalar("SELECT COUNT(DISTINCT review_id) FROM dwh.fact_reviews") < scalar("SELECT COUNT(*) FROM dwh.fact_reviews")


def test_customer_dimension_uses_unique_id(built):
    assert scalar("SELECT COUNT(*) FROM dwh.dim_customer") < scalar("SELECT COUNT(*) FROM staging.customers")


def test_missing_and_untranslated_categories(built):
    assert scalar("SELECT category_en FROM dwh.dim_product WHERE product_id = 'prod_nocat'") == "unknown"
    assert scalar("SELECT category_en FROM dwh.dim_product WHERE product_id = 'prod_notrad'") == "pc_gamer"


def test_lateness_is_consistent_with_dates(built):
    assert scalar("SELECT COUNT(*) FROM dwh.fact_order_items WHERE is_late AND delay_days <= 0") == 0
