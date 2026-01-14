"""Tests for YDB Client - SQL injection prevention."""
import pytest
from src.db.ydb_client import YDBClient, MemoryDB


class TestYDBClientParameterizedQueries:
    """Test parameterized queries to prevent SQL injection."""

    def test_select_with_where_uses_parameters(self):
        """Scenario: select() should use parameterized queries for WHERE clause.

        Given a YDBClient instance
        When I call select with a where clause containing malicious input
        Then the query should be safely parameterized
        And no SQL injection should be possible
        """
        client = YDBClient()

        # Malicious input in a string field (not user_id/amount which are Int64)
        malicious_input = {'category': '"; DROP TABLE users; --'}

        # The method should build a parameterized query, not string concat
        query, params = client._build_select_query('expenses', malicious_input, 100)

        # Query should use parameter placeholders, not direct string values
        assert '"; DROP TABLE' not in query
        assert '$p_category' in query
        assert 'DECLARE' in query

    def test_int64_fields_reject_string_injection(self):
        """Scenario: Int64 fields should reject string injection attempts.

        Given a YDBClient instance
        When I try to pass a malicious string to an Int64 field (user_id)
        Then it should raise ValueError (type safety prevents injection)
        """
        client = YDBClient()

        # Malicious input that would break string concatenation
        malicious_input = {'user_id': '"; DROP TABLE users; --'}

        # Int64 fields reject non-numeric input - this IS the security
        with pytest.raises(ValueError):
            client._build_select_query('expenses', malicious_input, 100)

    def test_select_without_where_is_safe(self):
        """Scenario: select() without WHERE should be safe."""
        client = YDBClient()

        query, params = client._build_select_query('expenses', None, 50)

        assert 'SELECT * FROM expenses' in query
        assert 'LIMIT 50' in query
        assert params is None or params == {}

    def test_delete_uses_parameters(self):
        """Scenario: delete() should use parameterized queries.

        Given a YDBClient instance
        When I call delete with a where clause containing malicious input
        Then the query should be safely parameterized
        """
        client = YDBClient()

        malicious_input = {'id': '1; DROP TABLE expenses; --'}

        query, params = client._build_delete_query('expenses', malicious_input)

        # Query should use parameter placeholders
        assert '; DROP TABLE' not in query
        assert '$id' in query or '$p_id' in query
        assert 'DECLARE' in query

    def test_select_escapes_table_name(self):
        """Scenario: Table names should be validated."""
        client = YDBClient()

        # Table names should only allow alphanumeric and underscore
        with pytest.raises(ValueError):
            client._build_select_query('expenses; DROP TABLE users', None, 100)

    def test_delete_escapes_table_name(self):
        """Scenario: Table names in delete should be validated."""
        client = YDBClient()

        with pytest.raises(ValueError):
            client._build_delete_query('expenses; DROP TABLE users', {'id': '1'})


class TestMemoryDBSafety:
    """Test MemoryDB is also safe (even though it's in-memory)."""

    def test_memory_select_filters_correctly(self):
        """MemoryDB select should filter by exact match."""
        db = MemoryDB()
        db.insert('users', {'id': '1', 'name': 'Alice'})
        db.insert('users', {'id': '2', 'name': 'Bob'})

        # Should only return exact matches
        results = db.select('users', {'id': '1'})
        assert len(results) == 1
        assert results[0]['name'] == 'Alice'

    def test_memory_delete_removes_correct_records(self):
        """MemoryDB delete should only remove matching records."""
        db = MemoryDB()
        db.insert('users', {'id': '1', 'name': 'Alice'})
        db.insert('users', {'id': '2', 'name': 'Bob'})

        db.delete('users', {'id': '1'})

        results = db.select('users')
        assert len(results) == 1
        assert results[0]['name'] == 'Bob'
