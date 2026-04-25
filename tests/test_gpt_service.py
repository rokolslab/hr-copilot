from gpt_service import build_responses_request


def test_build_responses_request_uses_documented_fields() -> None:
    result = build_responses_request("system", "user")

    assert result == {"instructions": "system", "input": "user"}
