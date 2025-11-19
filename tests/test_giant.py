from price_comparator.utils.parsing import parse_giant_product_html


def test_parse_giant_product_html_ld_json():
    html = """
    <html><head>
    <script type="application/ld+json">
    {"@type":"Product","offers":{"price":"5.25"}}
    </script>
    </head><body></body></html>
    """
    assert parse_giant_product_html(html) == 5.25


def test_parse_giant_product_html_text():
    html = "<span class='pdp-price__value'>$4.10</span>"
    assert parse_giant_product_html(html) == 4.10
