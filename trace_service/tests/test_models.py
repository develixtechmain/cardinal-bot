from models import compute_summary_from_events, parse_search_query


def test_parse_empty():
    assert parse_search_query("  ") == ("empty", None)


def test_parse_uuid():
    u = "550e8400-e29b-41d4-a716-446655440000"
    k, v = parse_search_query(u)
    assert k == "correlation"
    assert v == u


def test_parse_source():
    k, v = parse_search_query("-100123:456")
    assert k == "source"
    assert v == ("-100123", 456)


def test_parse_like():
    k, v = parse_search_query("embedding")
    assert k == "like"
    assert v == "embedding"


def test_summary_errors():
    events = [
        {"service": "a", "stage": "x", "status": "ok"},
        {"service": "b", "stage": "y", "status": "error"},
    ]
    s = compute_summary_from_events(events)
    assert "Error" in s
    assert "b/y" in s


def test_summary_tail():
    events = [{"service": "s", "stage": "p", "status": "ok"} for _ in range(5)]
    s = compute_summary_from_events(events)
    assert "s/p" in s
