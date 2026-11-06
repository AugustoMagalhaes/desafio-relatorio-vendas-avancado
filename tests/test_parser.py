from __future__ import annotations

from pathlib import Path

import pytest

from sales_cli.parser import detect_delimiter, read_text

SAMPLE_TEXT: str = "produto;preço unitário;ação"


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "cp1252", "latin-1"])
def test_read_text_decodes_supported_encodings(tmp_path: Path, encoding: str) -> None:
    path: Path = tmp_path / "sales.csv"
    _ = path.write_bytes(SAMPLE_TEXT.encode(encoding))
    assert read_text(path) == SAMPLE_TEXT


def test_read_text_removes_utf8_bom(tmp_path: Path) -> None:
    path: Path = tmp_path / "sales.csv"
    _ = path.write_bytes(SAMPLE_TEXT.encode("utf-8-sig"))
    assert not read_text(path).startswith("\ufeff")


def test_read_text_falls_back_to_latin1_for_undefined_cp1252_bytes(
    tmp_path: Path,
) -> None:
    path: Path = tmp_path / "sales.csv"
    _ = path.write_bytes(b"abc\x81")
    assert read_text(path) == "abc\x81"


def test_read_text_raises_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        _ = read_text(tmp_path / "missing.csv")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a;b;c", ";"),
        ("a,b,c", ","),
        ("a\tb\tc", "\t"),
        ("abc", ","),
        ("", ","),
        ("\n\nproduto;quantidade", ";"),
        ("a;b,c;d", ";"),
        ("a,b;c,d", ","),
    ],
)
def test_detect_delimiter(text: str, expected: str) -> None:
    assert detect_delimiter(text) == expected
