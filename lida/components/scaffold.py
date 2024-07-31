from dataclasses import asdict

from lida.datamodel import Goal


# if len(plt.xticks()[0])) > 20 assuming plot is made with plt or
# len(ax.get_xticks()) > 20 assuming plot is made with ax, set a max of 20
# ticks on x axis, ticker.MaxNLocator(20)

class ChartScaffold(object):
    """Return code scaffold for charts in multiple visualization libraries"""

    def __init__(
        self,
    ) -> None:

        pass

    def get_template(self, goal: Goal, library: str):

        general_instructions = (f"If the solution requires a single value (e.g. max, min, median, first, last etc), ALWAYS add a line (axvline or axhline) to the chart, ALWAYS with a legend containing the single value (formatted with 0.2F). If using a <field> where semantic_type=date, YOU MUST APPLY the following transform before using that column "
        f"i) convert date fields to date types using data = data.with_column(pl.col(<field>).str.to_datetime(time_zone='UTC')) "
        f"ii) drop the rows with NaT values data = data.filter(pl.all_horizontal(cs.float().is_not_nan())) "
        f"iii) convert field to right time format for plotting.  ALWAYS make sure the x-axis labels are legible (e.g., rotate when needed). "
        f"iv) Always use `list` dtype for column dtype List(String). \n"
        f"v) Always use `list` dtype for column dtype List(String). \n"
        f"iv) Always assume strings are lowercase. \n"
        f"vi) Always remove columns which have a dtype of List(String) just before creating the chart. \n"
        f"vii) ALWAYS return the dataframe used to create the chart along with the variable chart, i.e. data, chart. \n"
        f"Solve the task  carefully by completing ONLY the <imports> AND <stub> section. Given the dataset summary, the plot(data) method should generate a {library} chart ({goal.visualization}) that addresses this goal: {goal.question}. DO NOT WRITE ANY CODE TO LOAD THE DATA. The data is already loaded and available in the variable data.")

        matplotlib_instructions = f" {general_instructions} DO NOT include plt.show(). The plot method must return a matplotlib object (plt). Think step by step. \n"

        if library == "matplotlib":
            instructions = {
                "role": "assistant",
                "content": f"  {matplotlib_instructions}. Use BaseMap for charts that require a map. "}
            template = \
                f"""
import matplotlib.pyplot as plt
import polars as pl
<imports>
# plan -
def plot(data: pl.DataFrame):
    <stub> # only modify this section
    plt.title('{goal.question}', wrap=True)
    
    return plt;

chart = plot(data) # data already contains the data to be plotted. Always include this line. No additional code beyond this line."""
        elif library == "seaborn":
            instructions = {
                "role": "assistant",
                "content": f"{matplotlib_instructions}. Use BaseMap for charts that require a map. "}

            template = \
                f"""
import seaborn as sns
import polars as pl
import matplotlib.pyplot as plt
<imports>
# solution plan
# i.  ..
def plot(data: pl.DataFrame):

    <stub> # only modify this section
    plt.title('{goal.question}', wrap=True)
    return plt, <stub>; # add any additional variables that need to be returned, with the intermediate dataframe as `df`

chart = plot(data) # data already contains the data to be plotted. Always include this line. No additional code beyond this line."""

        elif library == "ggplot":
            instructions = {
                "role": "assistant",
                "content": f"{general_instructions}. The plot method must return a ggplot object (chart)`. Think step by step.p. \n",
            }

            template = \
                f"""
import plotnine as p9
<imports>
def plot(data: pl.DataFrame):
    chart = <stub>

    return chart;

chart = plot(data) # data already contains the data to be plotted. Always include this line. No additional code beyond this line.. """

        elif library == "altair":
            instructions = {
                "role": "system",
                "content": f"{general_instructions}. Always add a type that is BASED on semantic_type to each field such as :Q, :O, :N, :T, :G. Use :T if semantic_type is year or date. The plot method must return an altair object (chart)`. Think step by step. \n",
            }
            template = \
                """
import altair as alt
<imports>
def plot(data: pl.DataFrame):
    <stub> # only modify this section
    return chart
chart = plot(data) # data already contains the data to be plotted.  Always include this line. No additional code beyond this line..
"""

        elif library == "plotly":
            instructions = {
                "role": "system",
                "content": f"{general_instructions} If calculating metrics such as mean, median, mode, etc. ALWAYS use the option 'numeric_only=True' when applicable and available, AVOID visualizations that require nbformat library. DO NOT inlcude fig.show(). The plot method must return an plotly figure object (fig)`. Think step by step. \n.",
            }
            template = \
                """
import plotly.express as px
<imports>
def plot(data: pl.DataFrame):
    fig = <stub> # only modify this section

    return chart
chart = plot(data) # variable data already contains the data to be plotted and should not be loaded again.  Always include this line. No additional code beyond this line..
"""

        else:
            raise ValueError(
                "Unsupported library. Choose from 'matplotlib', 'seaborn', 'plotly', 'bokeh', 'ggplot', 'altair'."
            )

        return template, instructions
