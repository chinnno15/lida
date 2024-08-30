from typing import Optional
import alog
from llmx import TextGenerationConfig, llm
from pydantic.dataclasses import dataclass
from lida.components.goal.instructions import SYSTEM_INSTRUCTIONS, FORMAT_INSTRUCTIONS
from lida.datamodel.text_generator import TextGenerator
from lida.datamodel.persona import Persona


@dataclass
class Goal:
    """A visualization goal"""
    question: str
    index: Optional[int] = 0
    persona: Optional[Persona] = None
    rationale: Optional[str] = None
    summary: Optional[str] = None
    text_gen: Optional[TextGenerator] = None
    textgen_config: Optional[TextGenerationConfig] = None
    visualization: Optional[str] = None

    def __post_init__(self):
        if not self.text_gen:
            self.text_gen = llm()

        if not self.persona:
            self.persona = Persona(
                persona="A highly skilled data analyst who can come up with complex, insightful goals about data",
                rationale="")

        alog.info(f'### Goal: {self.question}')
        if not self.rationale:
            self.improve_goal()

    def improve_goal(self) -> None:
        """Improve the goal based solely on the question and summary."""
        summary = self.summary
        textgen_config = self.textgen_config

        user_prompt = f"""
        Generate a new goal based on the data summary below, \n\n .
        {summary} \n\n"""

        user_prompt += \
            (
                f"The generated goals SHOULD BE FOCUSED ON THE INTERESTS AND PERSPECTIVE of a '{self.persona.persona} persona, "
                f"who is insterested in complex, insightful goals about the data. \n "
                f"The question should be '{self.question}'.")

        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "assistant",
             "content":
                 f"{user_prompt}\n\n {FORMAT_INSTRUCTIONS} \n\n. The generated goal is: \n "}]

        # result: list[Goal] = text_gen.generate(messages=messages, config=textgen_config)
        #
        # try:
        #     json_string = clean_code_snippet(result.text[0]["content"])
        #     result = json.loads(json_string)
        #     # cast each item in the list to a Goal object
        #     if isinstance(result, dict):
        #         result = [result]
        #     result = [Goal(**x) for x in result]
        # except json.decoder.JSONDecodeError:
        #     logger.info(f"Error decoding JSON: {result.text[0]['content']}")
        #     alog.info(f"Error decoding JSON: {result.text[0]['content']}")
        #     raise ValueError(
        #         "The model did not return a valid JSON object while attempting generate goals. Consider using a larger model or a model with higher max token length.")
        # return result

    def _repr_markdown_(self):
        return f"""
### Goal {self.index}
---
**Question:** {self.question}

**Visualization:** `{self.visualization}`

**Rationale:** {self.rationale}
"""
