"""Search entries from GitHub."""
import datetime
import io
import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from .. import config
from ._base import BaseSearcher

log = logging.getLogger(__name__)

_MAX_RESULTS = 500


class Searcher(BaseSearcher):
    """Search previously published GitHub entries."""

    def __init__(self):
        super().__init__(name=Path(__file__).stem)
        self._repo = config.INSTANCE["publish"][self.name]

    @property
    def _syntax_help(self) -> str:
        return "https://j.mp/gh-search-syntax and https://j.mp/gh-search-code"

    def _search(self, query: str) -> Dict[str, Any]:  # pylint: disable=too-many-locals
        # Docs:
        # https://pygithub.readthedocs.io/en/latest/github.html#github.MainClass.Github.search_code
        # https://docs.github.com/en/rest/reference/search#search-code
        # https://docs.github.com/en/github/searching-for-information-on-github/understanding-the-search-syntax
        # https://docs.github.com/en/github/searching-for-information-on-github/searching-code#considerations-for-code-search
        dfs = []
        num_results = 0
        paginated_results = self._github.search_code(query, sort="indexed", highlight=True, repo=self._repo)  # highlight=True returns text_matches
        for result in paginated_results:
            content = result.decoded_content.decode()
            assert content.startswith("feed,title,long_url,short_url\n")
            path = Path(result.path)
            for text_match in result.text_matches:
                fragment = text_match["fragment"]
                fragment_index_in_content = content.find(fragment)
                assert fragment_index_in_content != -1
                for match in text_match["matches"]:
                    match_indices_in_fragment = match["indices"]
                    match_indices_in_content = [fragment_index_in_content + i for i in match_indices_in_fragment]  # Expected to always use only a single line.
                    line_indices_in_content = [content[: match_indices_in_content[0]].rfind("\n"), match_indices_in_content[1] + content[match_indices_in_content[1] :].find("\n")]
                    line_csv = content[: content.find("\n")] + content[slice(*line_indices_in_content)]
                    df = pd.read_csv(io.StringIO(line_csv), dtype="string")
                    df.insert(0, "channel", path.parts[0])
                    df.insert(0, "datetime", datetime.datetime.strptime(str(Path(*path.parts[1:])) + " +0000", "%Y/%m%d/%H%M%S.csv %z"))
                    dfs.append(df)
                    num_results += 1
                    if num_results == _MAX_RESULTS:
                        df = pd.concat(dfs)
                        self._process_results_df(df)
                        num_results = len(df)
                        if num_results == _MAX_RESULTS:
                            return {"results": df, "truncated": True}
                        dfs = [df]

        if dfs:
            df = pd.concat(dfs)
            self._process_results_df(df)
            return {"results": df, "truncated": False}
        return {"results": None}
