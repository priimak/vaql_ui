from typing import override

import polars
from polars import DataFrame

from vaql import VAQLFilter
from vaql.vaql_filter import FilterApplicator, Op


class PolarsFilterApplicator(FilterApplicator[DataFrame]):
    def __init__(self, source_data_frame: DataFrame):
        self.source_data_frame = source_data_frame

    @override
    def apply_filter(self, all_filters: list[VAQLFilter]) -> DataFrame:
        filter_text = all_filters[0].text
        exp = None

        def get_exp_acc():
            if filter_text == "":
                return None
            else:
                return polars.col("vaql_fts_column").str.contains_any(
                    [filter_text], ascii_case_insensitive = (filter_text.lower() == filter_text)
                )

        exp_acc = get_exp_acc()
        exp_head_negating = all_filters[0].negating

        for f in all_filters[1:]:
            filter_text = f.text
            next_exp = polars.col("vaql_fts_column").str.contains_any(
                [filter_text], ascii_case_insensitive = (filter_text.lower() == filter_text)
            )
            if filter_text == "":
                next_exp = None
            if f.op == Op.AND:
                if exp_acc is not None:
                    if exp_head_negating:
                        exp_acc = exp_acc.not_()
                    if exp is None:
                        exp = exp_acc
                    else:
                        exp = exp & exp_acc

                exp_acc = next_exp
                exp_head_negating = f.negating
                # exp = exp & next_exp
            else:
                if next_exp is not None:
                    if exp_acc is None:
                        if exp_head_negating:
                            exp_acc = next_exp.not_()
                        else:
                            exp_acc = next_exp
                    else:
                        exp_acc = exp_acc | next_exp

        if exp_acc is not None:
            if exp is None:
                if exp_head_negating:
                    exp_acc = exp_acc.not_()
                exp = exp_acc
            else:
                if exp_head_negating:
                    exp_acc = exp_acc.not_()
                exp = exp & exp_acc

        if exp is None:
            return self.source_data_frame.clone()
        else:
            return self.source_data_frame.filter(exp)
