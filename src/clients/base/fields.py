import re
from typing import Any, Self

from pydantic_core import core_schema


class PathTemplate(str):
    """
    Custom Pydantic type for validating URL paths that may contain template parameters
    with type modifiers (e.g., /users/{user_id:int}).
    """

    # Captures: {variable_name:type_hint} or just {variable_name}
    # Group 1: variable_name, Group 2: optional type_hint
    TEMPLATE_PARAM_REGEX = re.compile(r"\{([a-zA-Z0-9_]+)(?::(str|int|uuid))?\}")
    ALLOWED_TYPES = {"str", "int", "uuid"}

    @classmethod
    def validate_template(cls, v: str) -> Self:
        if not v.startswith("/"):
            raise ValueError("Path must start with a leading slash '/'.")

        # Basic syntax check
        if v.count("{") != v.count("}"):
            raise ValueError("Mismatched or unclosed template braces in path.")

        # Check all template parameters for valid names and allowed type modifiers
        for match in cls.TEMPLATE_PARAM_REGEX.finditer(v):
            param_name = match.group(1)
            type_hint = match.group(2)

            if not param_name:
                raise ValueError(
                    f"Path contains empty template parameter '{match.group(0)}'"
                )

            if type_hint and type_hint not in cls.ALLOWED_TYPES:
                raise ValueError(
                    f"Unsupported type modifier '{type_hint}'"
                    f"for parameter '{param_name}'"
                    f"Allowed types are: {', '.join(cls.ALLOWED_TYPES)}"
                )

        # If validation passes, create and return the PathTemplate instance
        return cls(v)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type[Any], handler: Any
    ) -> core_schema.CoreSchema:
        # Chain validation logic: string validation -> custom template check
        return core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate_template),
            ]
        )
