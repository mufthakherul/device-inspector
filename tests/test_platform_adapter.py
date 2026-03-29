from tools.platform_adapter import (
    build_release_matrix,
    get_platform_target,
    supported_platforms,
)


def test_supported_platforms_contains_harmonyos() -> None:
    platforms = supported_platforms()
    assert "harmonyos" in platforms


def test_harmonyos_target_is_scaffold() -> None:
    target = get_platform_target("harmonyos")
    assert target.support_level == "scaffold"
    assert ".hap" in target.outputs


def test_release_matrix_has_expected_columns() -> None:
    rows = build_release_matrix()
    assert rows
    first = rows[0]
    assert set(first.keys()) == {"platform", "outputs", "support_level", "notes"}
