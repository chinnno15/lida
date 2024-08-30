from pydantic.dataclasses import dataclass


@dataclass
class Persona:
    """A persona"""
    persona: str
    rationale: str

    def _repr_markdown_(self):
        return f"""
### Persona
---

**Persona:** {self.persona}

**Rationale:** {self.rationale}
"""
