"""
Data Access Managers Module.

DAOs are responsible for scraping, parsing, storing and delivering a specific type of
data. i.e. Pubmed Publications, Clinical Trials, Gene-Disease Relationships.
"""
from typing import Generator
from abc import ABC, abstractmethod
from pandas import DataFrame
from geniepy.errors import SchemaError
from geniepy.datamgmt.parsers import BaseParser, CtdParser
import geniepy.datamgmt.repository as dr


class BaseDao(ABC):
    """Data Access Object Abstract Base Class."""

    __slots__ = ["_repository", "_parser"]

    @abstractmethod
    def download(self):
        """Download new data from online sources if available."""

    @abstractmethod
    def purge_records(self):
        """Purge all dao's database records."""

    # pylint: disable=bad-continuation
    def query(
        self, query: str = None, chunksize: int = dr.CHUNKSIZE
    ) -> Generator[DataFrame, None, None]:
        """
        Query DAO repo and returns a generator of DataFrames with query results.

        Keyword Arguments:
            query {str} -- Query string. (default: {None} returns all values)
            chunksize {int} -- Number of rows of dataframe per chunk (default: {10e3})

        Returns:
            Generator[DataFrame] -- Generator to iterate over DataFrame results.
        """
        # pylint: disable=no-member
        return self._repository.query(query=query, chunksize=chunksize)

    def save(self, payload: DataFrame):
        """
        Save payload to database given data is valid.

        Arguments:
            payload {DataFrame} -- payload to be saved to table

        Raises:
            SchemaError: dataframe does not conform to table schema.
        """
        # pylint: disable=no-member
        if not self._parser.is_valid(payload):
            raise SchemaError
        self._repository.save(payload)

    @property
    def tablename(self):
        """Return the dao repo tablename."""
        # pylint: disable=no-member
        return self._repository.tablename


class CtdDao(BaseDao):
    """Implementation of CTD Data Access Object."""

    __slots__ = ["_repository", "_parser"]

    def __init__(self, repository: dr.BaseRepository):
        """Initialize DAO state."""
        self._repository = repository
        self._parser = CtdParser()

    def purge_records(self):
        """Purge all dao's database records."""
        self._repository.delete_all()

    def download(self):
        """Download new data from online sources if available."""
        # TODO implement scraping inside parser in parser
        # new_data: pd.DataFrame = self._parser.fetch_new_data()
        # if not new_data.empty:
        #     self._repository.save(new_data)
