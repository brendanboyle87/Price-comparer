import pytest

from price_comparator.utils.parsing import parse_target_product_html, parse_target_product_json


def test_parse_target_product_json_extracts_price():
    payload = {
        "data": {
            "product": {
                "price": {
                    "current_retail": 3.49,
                }
            }
        }
    }
    assert parse_target_product_json(payload) == 3.49


def test_parse_target_product_html_from_ld_json():
    html = """
    <html><head>
    <script type="application/ld+json">
    {"@type":"Product","offers":{"price": "2.99"}}
    </script>
    </head><body></body></html>
    """
    assert parse_target_product_html(html) == 2.99
