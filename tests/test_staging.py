import pytest

from src.staging import FILES, check_identifier, read_header


def test_read_header_removes_bom(tmp_path):
    path = tmp_path / "translation.csv"
    path.write_text("\ufeffproduct_category_name,product_category_name_english\nbeleza,beauty\n", encoding="utf-8")
    assert read_header(path) == ["product_category_name", "product_category_name_english"]


def test_read_header_plain_file(tmp_path):
    path = tmp_path / "sellers.csv"
    path.write_text("seller_id,seller_city\ns1,sao paulo\n", encoding="utf-8")
    assert read_header(path) == ["seller_id", "seller_city"]


def test_check_identifier_accepts_normal_names():
    assert check_identifier("order_purchase_timestamp") == "order_purchase_timestamp"


@pytest.mark.parametrize("bad", ["Order Id", "id; DROP TABLE x", "1abc", ""])
def test_check_identifier_rejects_unsafe_names(bad):
    with pytest.raises(ValueError):
        check_identifier(bad)


def test_every_expected_file_maps_to_a_table():
    assert len(set(FILES.values())) == len(FILES) == 8
