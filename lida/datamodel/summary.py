from typing import List, Any, Optional

from pydantic.dataclasses import dataclass


@dataclass
class Summary:
    """A summary of a dataset"""

    name: str
    file_name: str
    dataset_description: str
    field_names: List[Any]
    fields: Optional[List[Any]] = None

    def _repr_markdown_(self):
        field_lines = "\n".join([f"- **{name}:** {field}" for name,
        field in zip(self.field_names, self.fields)])
        return f"""
## Dataset Summary

---

**Name:** {self.name}

**File Name:** {self.file_name}

**Dataset Description:**

{self.dataset_description}

**Fields:**

{field_lines}
"""
