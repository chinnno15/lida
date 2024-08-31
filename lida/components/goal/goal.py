import dataclasses
import json
from typing import Optional, Union, Any, List
import alog
import pandas as pd
import polars as pl
from llmx import TextGenerationConfig, llm, TextGenerationResponse
from pydantic.dataclasses import dataclass
from lida.components.goal.instructions import SYSTEM_INSTRUCTIONS, FORMAT_INSTRUCTIONS
from lida.datamodel.summary import Summary
from lida.datamodel.text_generator import TextGenerator
from lida.datamodel.persona import Persona
from lida.utils import clean_code_snippet, logger


@dataclass
class Goal:
    """A visualization goal"""
    question: str
    index: Optional[int] = 0
    persona: Optional[Persona] = None
    rationale: Optional[str] = None
    summary: Optional[Summary] = None
    data: Optional[List[Any]] = None
    text_gen: Optional[TextGenerator] = None
    textgen_config: Optional[TextGenerationConfig] = None
    visualization: Optional[str] = None

    def dump(self):
        return dict(
            question=self.question,
            index=self.index,
            persona=dataclasses.asdict(self.persona),
            rationale=self.rationale,
            visualization=self.visualization
        )

    # class Config:
    #     arbitrary_types_allowed = True

    def __post_init__(self):
        if not self.text_gen:
            self.text_gen = llm()

        if not self.persona:
            self.persona = Persona(
                persona="A highly skilled data analyst who can come up with complex, insightful goals about data.",
                rationale="")

        alog.info(f'### Goal: {self.question}')

        if not self.rationale:
            self.improve_goal()

    def improve_goal(self) -> None:
        """Improve the goal based solely on the question and summary."""
        summary = self.summary

        if not summary:
            raise Exception('summary is required.')

        textgen_config = self.textgen_config
        summary_str = summary.__dict__
        # summary_str = alog.pformat(summary.__dict__)

        data_str = None

        if self.data is not None:
            data_str = ''
            for df in self.data:
                if df.shape[0] > 20:
                    raise Exception('Only up to 20 rows of data can be used for goal generation.')

                data_str += df.to_json(orient='records')

        if data_str:
            user_prompt = (f"Generate a new goal based on the question: '{self.question}'. "
                           f"Use any values in the following data frame to correct any "
                           f"typos in the user's 'question': {data_str} \n\n"
                           f"Also, use the contents of the dataframe summary below: \n\n"
                           f"\n\n . {summary_str} \n\n")
        else:
            user_prompt = (f"Generate a new goal based on the question: '{self.question}' "
                           f"as well as the summary below: \n\n"
                           f"\n\n . {summary_str} \n\n")

        user_prompt += \
            (
                f"The generated goal SHOULD BE FOCUSED ON THE INTERESTS AND PERSPECTIVE of a '{self.persona.persona} persona, "
                f"who is insterested in complex, insightful goals about the data. \n "
                f"The question should be derived from the question: '{self.question}'. If the question is simple, please try to elaborate the question as to the type of aggregation necessary. IF POSSIBLE AND THE QUERY IS NOT SPECIFIC TO A DIFFERENT "
                f"TYPE OF AGGREGATION, ALWAYS AGGREGATE BY GROSS REVENUE.\n"
                f"PLEASE ONLY GENERATE ONE GOAL. IN ADDITION TO THIS, TRY TO INCLUDE THE URL AND Image URL COLUMN IN YOUR ANSWER.")
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "assistant",
             "content":
                 f"{user_prompt}\n\n {FORMAT_INSTRUCTIONS} \n\n. The generated goal is: \n "}]

        result: TextGenerationResponse = self.text_gen.generate(messages=messages, config=textgen_config)

        try:
            json_string = clean_code_snippet(result.text[0]["content"])
            result = json.loads(json_string)[0]
            # cast each item in the list to a Goal object

            alog.info(alog.pformat(result))

            for key in result.keys():
                setattr(self, key, result[key])

        except json.decoder.JSONDecodeError:
            logger.info(f"Error decoding JSON: {result.text[0]['content']}")
            alog.info(f"Error decoding JSON: {result.text[0]['content']}")
            raise ValueError(
                "The model did not return a valid JSON object while attempting generate goals. Consider using a larger model or a model with higher max token length.")
        return result

    def _repr_markdown_(self):
        return f"""
### Goal {self.index}
---
**Question:** {self.question}

**Visualization:** `{self.visualization}`

**Rationale:** {self.rationale}
"""
