from lida.datamodel.__init__ import ChartExecutorResponse, Summary
from typing import Any, List

import alog
import ast
import base64
import importlib
import io
import matplotlib.pyplot as plt
import plotly.io as pio
import polars as pl
import re
import sys
import traceback


def preprocess_code(code: str) -> str:
    """Preprocess code to remove any preamble and explanation text"""

    code = code.replace("<imports>", "")
    code = code.replace("<stub>", "")
    code = code.replace("<transforms>", "")

    # remove all text after chart = plot(data)
    if "chart = plot(data)" in code:
        # alog.info(code)
        index = code.find("chart = plot(data)")
        if index != -1:
            code = code[: index + len("chart = plot(data)")]

    if "```" in code:
        pattern = r"```(?:\w+\n)?([\s\S]+?)```"
        matches = re.findall(pattern, code)
        if matches:
            code = matches[0]
        # code = code.replace("```", "")
        # return code

    if "import" in code:
        # return only text after the first import statement
        index = code.find("import")
        if index != -1:
            code = code[index:]

    code = code.replace("```", "")
    if "chart = plot(data)" not in code:
        code = code + "\nchart = plot(data)"

    # if "seaborn" in code:
    #     if "data.to_pandas()" in code:
    #         code = code.replace("data.to_pandas()", "data")

    if "polars" in code:
        if "groupby" in code:
            code = code.replace("groupby", "group_by")

        if ".with_column(" in code:
            code = code.replace(".with_column(", ".with_columns(")
        if "reverse=True" in code:
            code = code.replace("reverse=True", "descending=True")

    return code


def get_globals_dict(code_string, data):
    # Parse the code string into an AST
    tree = ast.parse(code_string)
    # Extract the names of the imported modules and their aliases
    imported_modules = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = importlib.import_module(alias.name)
                imported_modules.append((alias.name, alias.asname, module))
        elif isinstance(node, ast.ImportFrom):
            module = importlib.import_module(node.module)
            for alias in node.names:
                obj = getattr(module, alias.name)
                imported_modules.append(
                    (f"{node.module}.{alias.name}", alias.asname, obj)
                )

    # Import the required modules into a dictionary
    globals_dict = {}
    for module_name, alias, obj in imported_modules:
        if alias:
            globals_dict[alias] = obj
        else:
            globals_dict[module_name.split(".")[-1]] = obj

    ex_dicts = {"pl": pl, "data": data, "plt": plt}
    globals_dict.update(ex_dicts)
    return globals_dict


class ChartExecutor:
    """Execute code and return chart object"""

    def __init__(self) -> None:
        pass

    def execute(
        self,
        code_specs: List[str],
        data: Any,
        summary: Summary,
        library="altair",
        return_error: bool = False,
    ) -> Any:
        """Validate and convert code"""

        # # check if user has given permission to execute code. if env variable
        # # LIDA_ALLOW_CODE_EVAL is set to '1'. Else raise exception
        # if os.environ.get("LIDA_ALLOW_CODE_EVAL") != '1':
        #     raise Exception(
        #         "Permission to execute code not granted. Please set the environment variable LIDA_ALLOW_CODE_EVAL to '1' to allow code execution.")

        if isinstance(summary, dict):
            summary = Summary(**summary)

        charts = []
        code_spec_copy = code_specs.copy()
        code_specs = [preprocess_code(code) for code in code_specs]

        alog.info('### print code_specs ###')
        alog.info(''.join(code_specs))

        if library == "altair":
            for code in code_specs:
                try:
                    ex_locals = get_globals_dict(code, data)
                    exec(code, ex_locals)
                    chart = ex_locals["chart"]
                    vega_spec = chart.to_dict()
                    del vega_spec["data"]
                    if "datasets" in vega_spec:
                        del vega_spec["datasets"]

                    vega_spec["data"] = {"url": f"/files/data/{summary.file_name}"}
                    charts.append(
                        ChartExecutorResponse(
                            spec=vega_spec,
                            status=True,
                            raster=None,
                            code=code,
                            library=library,
                        )
                    )
                except Exception as exception_error:
                    alog.info(code_spec_copy, "\n===========\n")
                    alog.info(exception_error)
                    alog.info(traceback.format_exc())
                    if return_error:
                        charts.append(
                            ChartExecutorResponse(
                                spec=None,
                                status=False,
                                raster=None,
                                code=code,
                                library=library,
                                error={
                                    "message": str(exception_error),
                                    "traceback": traceback.format_exc(),
                                },
                            )
                        )
            return charts
        elif library == "matplotlib" or library == "seaborn":
            # print colum dtypes
            for code in code_specs:
                # import alog
                # alog.info(code)

                try:
                    ex_locals = get_globals_dict(code, data)
                    exec(code, ex_locals)

                    chart, df, cols = ex_locals["chart"]

                    if plt:
                        buf = io.BytesIO()
                        plt.box(False)
                        plt.grid(color="lightgray", linestyle="dashed", zorder=-10)
                        # try:
                        #     plt.draw()
                        #     # plt.tight_layout()
                        # except AttributeError:
                        #     alog.info("Warning: tight_layout encountered an error. The layout may not be optimal.")
                        #     pass

                        plt.savefig(buf, format="png", dpi=100, pad_inches=0.2)
                        buf.seek(0)
                        plot_data = base64.b64encode(buf.read()).decode("ascii")
                        plt.close()
                    charts.append(
                        ChartExecutorResponse(
                            df=df,
                            cols=cols,
                            spec=None,
                            status=True,
                            raster=plot_data,
                            code=code,
                            library=library,
                        )
                    )
                except Exception as exception_error:
                    # alog.info(exception_error)

                    traceback.print_exception(Exception,
                                              exception_error,
                                              tb=None,
                                              limit=None,
                                              file=sys.stderr)

                    alog.info(code_specs[0])

                    alog.info(("****\n", str(exception_error)))

                    # alog.info(traceback.format_exc())
                    if return_error:
                        charts.append(
                            ChartExecutorResponse(
                                spec=None,
                                status=False,
                                raster=None,
                                code=code,
                                library=library,
                                error={
                                    "message": str(exception_error),
                                    "traceback": traceback.format_exc(),
                                },
                            )
                        )
            return charts
        elif library == "ggplot":
            # print colum dtypes
            for code in code_specs:
                try:
                    ex_locals = get_globals_dict(code, data)
                    exec(code, ex_locals)
                    chart = ex_locals["chart"]
                    if plt:
                        buf = io.BytesIO()
                        chart.save(buf, format="png")
                        plot_data = base64.b64encode(buf.getvalue()).decode("utf-8")
                    charts.append(
                        ChartExecutorResponse(
                            spec=None,
                            status=True,
                            raster=plot_data,
                            code=code,
                            library=library,
                        )
                    )
                except Exception as exception_error:
                    alog.info(code)
                    alog.info(traceback.format_exc())
                    if return_error:
                        charts.append(
                            ChartExecutorResponse(
                                spec=None,
                                status=False,
                                raster=None,
                                code=code,
                                library=library,
                                error={
                                    "message": str(exception_error),
                                    "traceback": traceback.format_exc(),
                                },
                            )
                        )
            return charts

        elif library == "plotly":
            for code in code_specs:
                try:
                    ex_locals = get_globals_dict(code, data)
                    exec(code, ex_locals)
                    chart = ex_locals["chart"]

                    if pio:
                        chart_bytes = pio.to_image(chart, 'png')
                        plot_data = base64.b64encode(chart_bytes).decode('utf-8')

                        charts.append(
                            ChartExecutorResponse(
                                spec=None,
                                status=True,
                                raster=plot_data,
                                code=code,
                                library=library,
                            )
                        )
                except Exception as exception_error:
                    alog.info(code)
                    alog.info(traceback.format_exc())
                    if return_error:
                        charts.append(
                            ChartExecutorResponse(
                                spec=None,
                                status=False,
                                raster=None,
                                code=code,
                                library=library,
                                error={
                                    "message": str(exception_error),
                                    "traceback": traceback.format_exc(),
                                },
                            )
                        )
            return charts

        else:
            raise Exception(
                f"Unsupported library. Supported libraries are altair, matplotlib, seaborn, ggplot, plotly. You provided {library}"
            )
