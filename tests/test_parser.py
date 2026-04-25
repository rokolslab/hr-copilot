from parser import clean_text, prepare_resume_text


def test_clean_text_removes_extra_spaces_and_blank_lines() -> None:
    raw_text = "  Python   developer  \n\n  Built   APIs   \n  Team player  "

    result = clean_text(raw_text)

    assert result == "Python developer\nBuilt APIs\nTeam player"


def test_clean_text_respects_max_char_limit() -> None:
    result = clean_text("abcdef", max_chars=4)

    assert result == "abcd"


def test_prepare_resume_text_falls_back_to_manual_text() -> None:
    result = prepare_resume_text(None, "  Backend engineer with Python and SQL.  ", max_chars=100)

    assert result == "Backend engineer with Python and SQL."
