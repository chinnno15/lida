from lida.components import Manager
from llmx import llm, TextGenerationConfig
import alog

from lida.components.goal.goal import Goal

lida = Manager(text_gen=llm("openai", model="gpt-4o"))


cars_data_url = "https://raw.githubusercontent.com/uwdata/draco/master/data/cars.csv"


def test_goals():
    textgen_config = TextGenerationConfig(
        n=1,
        temperature=0.1,
        use_cache=True,
        max_tokens=None
    )

    summary = lida.summarize(
        cars_data_url,
        textgen_config=textgen_config,
        summary_method="llm"
    )

    textgen_config.use_cache = False

    goals = lida.goals(summary, n=2, textgen_config=textgen_config)

    alog.info(alog.pformat(goals))

    assert len(goals) == 2
    assert len(goals[0].question) > 0

def test_goal_init():
    textgen_config = TextGenerationConfig(
        n=1,
        temperature=0.1,
        use_cache=True,
        max_tokens=None
    )

    summary = lida.summarize(
        cars_data_url,
        textgen_config=textgen_config,
        summary_method="llm"
    )

    textgen_config.use_cache = False

    goal = Goal(
        question='top selling items',
    )

    alog.info(alog.pformat(goal))

