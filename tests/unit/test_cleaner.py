from knowledge_poc.transformation.cleaner import clean_storage_html


def test_cleaner_preserves_headings_lists_and_tables():
    html = (
        "<h2>Rules</h2><ul><li>Offline 14 days</li></ul>"
        "<table><tr><td>A</td><td>B</td></tr></table>"
    )
    text = clean_storage_html(html, "Vessel NFRs")
    assert text.startswith("# Vessel NFRs")
    assert "## Rules" in text
    assert "- Offline 14 days" in text
    assert "| A | B |" in text
