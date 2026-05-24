from __future__ import annotations

from typing import TypeAlias
"""Common code for permissions."""

from collections.abc import Mapping

# MyPy doesn't support recursion yet. So writing it out as far as we need.

ValueType: TypeAlias = (
    # Example: entities.all = { read: true, control: true }
    Mapping[str, bool] | bool | None
)

# Example: entities.domains = { light: … }
SubCategoryDict: TypeAlias = Mapping[str, ValueType]

SubCategoryType: TypeAlias = SubCategoryDict | bool | None

CategoryType: TypeAlias = (
    # Example: entities.domains
    Mapping[str, SubCategoryType]
    # Example: entities.all
    | Mapping[str, ValueType]
    | bool
    | None
)

# Example: { entities: … }
PolicyType: TypeAlias = Mapping[str, CategoryType]
