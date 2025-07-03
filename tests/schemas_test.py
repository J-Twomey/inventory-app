import pytest

import src.schemas as schemas


@pytest.mark.parametrize(
    ('sub_nums', 'fees', 'expected'),
    (
        pytest.param(['1', '2'], ['10', '20'], {1: 10, 2: 20}, id='simple_case'),
        pytest.param(['1', '2', ''], ['10', '20', ''], {1: 10, 2: 20}, id='remove_empty_string'),
    ),
)
def test_build_grading_fee_dict(
        sub_nums: list[str],
        fees: list[str],
        expected: dict[int, int],
) -> None:
    result = schemas.build_grading_fee_dict(sub_nums=sub_nums, fees=fees)
    assert result == expected


def test_build_grading_fee_dict_uneven_length() -> None:
    sub_nums = ['1', '2', '3']
    fees = ['10', '20']
    with pytest.raises(ValueError):
        schemas.build_grading_fee_dict(sub_nums=sub_nums, fees=fees)
