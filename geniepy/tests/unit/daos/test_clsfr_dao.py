"""Module to test Data Access Objects."""
import pytest
from geniepy.datamgmt.daos import BaseDao, ClassifierDao
from geniepy.errors import SchemaError
import tests.testdata as td
import geniepy.datamgmt.repositories as dr
from geniepy.errors import DaoError

VALID_DF = td.CLSFR_VALID_DF
INVALID_DF = td.CLSFR_INVALID_DF


class TestClassifierDao:
    """PyTest data access object test class."""

    test_repo = dr.SqlRepository("sqlite://", dr.CLSFR_TABLE_NAME, dr.CLSFR_DAO_TABLE)
    test_dao: BaseDao = ClassifierDao(test_repo)

    def read_record(self, digest):
        """Read record(s) from database (tests helper method)."""
        query_str = f"SELECT * FROM {self.test_dao.tablename} WHERE digest='{digest}';"
        generator = self.test_dao.query(query=query_str)
        return generator

    def test_constructor(self):
        """Ensure obj constructed successfully."""
        assert self.test_dao is not None

    @pytest.mark.parametrize("payload", INVALID_DF)
    def test_save_invalid_df(self, payload):
        """Test save invalid dataframe to dao's repository."""
        with pytest.raises(SchemaError):
            self.test_dao.save(payload)

    @pytest.mark.parametrize("payload", VALID_DF)
    def test_save_valid_df(self, payload):
        """Test save valid dataframe to dao's repo doesn't raise error."""
        self.test_dao.save(payload)

    @pytest.mark.parametrize("payload", VALID_DF)
    def test_query(self, payload):
        """Query valid record."""
        # Start with empty table
        self.test_dao.purge()
        # Try to create records in db for test if don't exist
        try:
            self.test_dao.save(payload)
        except DaoError:
            pass
        # Attempt to retrieve record
        digest = payload.digest[0]
        generator = self.read_record(digest)
        chunk = next(generator)
        assert chunk.equals(payload)

    def test_query_non_existent(self):
        """Query non-existent record should return empty."""
        # Attempt to retrieve record
        digest = "INVALID digest"
        generator = self.read_record(digest)
        # Make sure generator doesn't return anything since no records in database
        with pytest.raises(StopIteration):
            next(generator)

    def test_purge(self):
        """Test delete all records from repository."""
        # Try to fill database, in case is empty
        for record in VALID_DF:
            try:
                self.test_dao.save(record)
            except DaoError:
                pass
        # Delete all records
        self.test_dao.purge()
        # Make sure no records left
        generator = self.test_dao.query()
        # generator shouldn't return anything since no records in database
        with pytest.raises(StopIteration):
            next(generator)
        # Test building and reading from table again, make sure still functional
        self.test_query(VALID_DF[0])

    @pytest.mark.parametrize("chunksize", [*range(1, len(VALID_DF) + 1)])
    def test_query_chunksize(self, chunksize):
        """Query all by chunk."""
        # Try to fill database, in case is empty
        for record in VALID_DF:
            try:
                self.test_dao.save(record)
            except DaoError:
                pass
        # Get all records in database
        generator = self.test_dao.query(chunksize=chunksize)
        # Make sure number generator provides df of chunksize each iteration
        result_df = next(generator)
        assert result_df.digest.count() == chunksize

    def test_download_not_impl(self):
        """Download method not impl in classifier dao."""
        with pytest.raises(NotImplementedError):
            self.test_dao.download()