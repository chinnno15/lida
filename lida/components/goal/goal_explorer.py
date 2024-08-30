import json
import logging

import alog

from lida.components.goal.instructions import SYSTEM_INSTRUCTIONS, FORMAT_INSTRUCTIONS
from lida.utils import clean_code_snippet
from llmx import TextGenerator
from lida.datamodel.__init__ import TextGenerationConfig
from lida.datamodel.persona import Persona
from lida.components.goal.goal import Goal

logger = logging.getLogger("lida")


class GoalExplorer(object):
    """Generate goals given a summary of data"""

    def __init__(self) -> None:
        pass

    def generate(self, summary: dict, textgen_config: TextGenerationConfig,
                 text_gen: TextGenerator, n=5, persona: Persona = None) -> list[Goal]:
        """Generate goals given a summary of data"""

        user_prompt = f"""The number of GOALS to generate is {n}. The goals should be based on the data summary below, \n\n .
        {summary} \n\n"""

        if not persona:
            persona = Persona(
                persona="A highly skilled data analyst who can come up with complex, insightful goals about data",
                rationale="")

        user_prompt += f"""\n The generated goals SHOULD BE FOCUSED ON THE INTERESTS AND PERSPECTIVE of a '{persona.persona} persona, who is insterested in complex, insightful goals about the data. \n"""

        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "assistant",
             "content":
             f"{user_prompt}\n\n {FORMAT_INSTRUCTIONS} \n\n. The generated {n} goals are: \n "}]

        result: list[Goal] = text_gen.generate(messages=messages, config=textgen_config)

        try:
            json_string = clean_code_snippet(result.text[0]["content"])
            result = json.loads(json_string)
            # cast each item in the list to a Goal object
            if isinstance(result, dict):
                result = [result]
            result = [Goal(**x) for x in result]
        except json.decoder.JSONDecodeError:
            logger.info(f"Error decoding JSON: {result.text[0]['content']}")
            alog.info(f"Error decoding JSON: {result.text[0]['content']}")
            raise ValueError(
                "The model did not return a valid JSON object while attempting generate goals. Consider using a larger model or a model with higher max token length.")
        return result
