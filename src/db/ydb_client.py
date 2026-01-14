"""
YDB Client for Yandex Database (Serverless)
"""

import os
import json
import re
from typing import Optional, List, Dict, Any, Tuple

# YDB SDK is optional - works without it for basic operations
try:
    import ydb
    HAS_YDB = True
except ImportError:
    HAS_YDB = False


class YDBClient:
    """Yandex Database client for serverless YDB"""
    
    def __init__(self):
        self.endpoint = os.getenv('YDB_ENDPOINT', '')
        self.database = os.getenv('YDB_DATABASE', '')
        self.driver = None
        self.pool = None
    
    def _get_credentials(self):
        """Get YDB credentials"""
        if not HAS_YDB:
            return None
            
        # Try service account key file
        sa_key_file = os.getenv('YC_SA_KEY_FILE')
        if sa_key_file and os.path.exists(sa_key_file):
            return ydb.iam.ServiceAccountCredentials.from_file(sa_key_file)
        
        # Try metadata service (when running in YC)
        try:
            return ydb.iam.MetadataUrlCredentials()
        except:
            pass
        
        # Try OAuth token
        token = os.getenv('YC_TOKEN')
        if token:
            return ydb.credentials.AccessTokenCredentials(token)
        
        return None
    
    def connect(self):
        """Establish connection to YDB"""
        if not HAS_YDB:
            raise RuntimeError("YDB SDK not installed. Run: pip install ydb")
        
        if self.driver:
            return
        
        driver_config = ydb.DriverConfig(
            endpoint=self.endpoint,
            database=self.database,
            credentials=self._get_credentials()
        )
        
        self.driver = ydb.Driver(driver_config)
        self.driver.wait(timeout=10)
        self.pool = ydb.SessionPool(self.driver)
    
    def execute(self, query: str, parameters: dict = None) -> List[Dict]:
        """Execute YQL query"""
        self.connect()
        
        def callee(session):
            if parameters:
                prepared = session.prepare(query)
                result_sets = session.transaction().execute(
                    prepared,
                    parameters,
                    commit_tx=True
                )
            else:
                result_sets = session.transaction().execute(
                    query,
                    commit_tx=True
                )
            
            results = []
            for result_set in result_sets:
                for row in result_set.rows:
                    results.append(dict(row))
            return results
        
        return self.pool.retry_operation_sync(callee)

    def _validate_table_name(self, table: str) -> str:
        """Validate table name to prevent injection.

        Only allows alphanumeric characters and underscores.
        """
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table):
            raise ValueError(f"Invalid table name: {table}")
        return table

    def _build_select_query(self, table: str, where: dict = None, limit: int = 100) -> Tuple[str, Optional[dict]]:
        """Build a parameterized SELECT query.

        Returns tuple of (query_string, parameters_dict).
        """
        table = self._validate_table_name(table)

        if where:
            # Build parameterized query
            declares = []
            conditions = []
            params = {}

            for k, v in where.items():
                param_name = f'p_{k}'
                declares.append(f'DECLARE ${param_name} AS Utf8;')
                conditions.append(f'{k} = ${param_name}')
                params[f'${param_name}'] = str(v) if v is not None else ''

            # nosec B608 - table is validated, values use parameterized placeholders ($p_field)
            query = f"{' '.join(declares)} SELECT * FROM {table} WHERE {' AND '.join(conditions)} LIMIT {limit}"
            return query, params
        else:
            return f"SELECT * FROM {table} LIMIT {limit}", None

    def _build_delete_query(self, table: str, where: dict) -> Tuple[str, dict]:
        """Build a parameterized DELETE query.

        Returns tuple of (query_string, parameters_dict).
        """
        table = self._validate_table_name(table)

        # Build parameterized query
        declares = []
        conditions = []
        params = {}

        for k, v in where.items():
            param_name = f'p_{k}'
            declares.append(f'DECLARE ${param_name} AS Utf8;')
            conditions.append(f'{k} = ${param_name}')
            params[f'${param_name}'] = str(v) if v is not None else ''

        # nosec B608 - table is validated, values use parameterized placeholders ($p_field)
        query = f"{' '.join(declares)} DELETE FROM {table} WHERE {' AND '.join(conditions)}"
        return query, params

    def insert(self, table: str, data: dict) -> bool:
        """Insert record into table"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(f'${k}' for k in data.keys())
        
        query = f"""
            DECLARE ${' DECLARE $'.join(f'{k} AS Utf8;' for k in data.keys())}
            
            UPSERT INTO {table} ({columns})
            VALUES ({placeholders});
        """
        
        # Convert values to proper types
        params = {}
        for k, v in data.items():
            if isinstance(v, dict):
                params[f'${k}'] = json.dumps(v)
            else:
                params[f'${k}'] = str(v) if v is not None else None
        
        self.execute(query, params)
        return True
    
    def select(self, table: str, where: dict = None, limit: int = 100) -> List[Dict]:
        """Select records from table using parameterized queries."""
        query, params = self._build_select_query(table, where, limit)
        return self.execute(query, params)

    def delete(self, table: str, where: dict) -> bool:
        """Delete records from table using parameterized queries."""
        query, params = self._build_delete_query(table, where)
        self.execute(query, params)
        return True


# Simple in-memory fallback when YDB is not available
class MemoryDB:
    """In-memory database for development/testing"""
    
    def __init__(self):
        self.tables: Dict[str, List[Dict]] = {}
    
    def execute(self, query: str, parameters: dict = None) -> List[Dict]:
        # Very basic query parsing for simple cases
        return []
    
    def insert(self, table: str, data: dict) -> bool:
        if table not in self.tables:
            self.tables[table] = []
        self.tables[table].append(data)
        return True
    
    def select(self, table: str, where: dict = None, limit: int = 100) -> List[Dict]:
        if table not in self.tables:
            return []
        
        results = self.tables[table]
        
        if where:
            results = [
                r for r in results
                if all(r.get(k) == v for k, v in where.items())
            ]
        
        return results[:limit]
    
    def delete(self, table: str, where: dict) -> bool:
        if table not in self.tables:
            return True
        
        self.tables[table] = [
            r for r in self.tables[table]
            if not all(r.get(k) == v for k, v in where.items())
        ]
        return True


def get_db():
    """Get database client (YDB or fallback)"""
    if os.getenv('YDB_ENDPOINT') and HAS_YDB:
        return YDBClient()
    else:
        return MemoryDB()


# CLI
if __name__ == "__main__":
    import sys
    
    db = get_db()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ydb_client.py select <table> [where_json]")
        print("  python ydb_client.py insert <table> <data_json>")
        print("  python ydb_client.py query '<yql>'")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "select":
        table = sys.argv[2]
        where = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
        results = db.select(table, where)
        print(json.dumps(results, indent=2, default=str))
    
    elif cmd == "insert":
        table = sys.argv[2]
        data = json.loads(sys.argv[3])
        db.insert(table, data)
        print("OK")
    
    elif cmd == "query":
        query = sys.argv[2]
        results = db.execute(query)
        print(json.dumps(results, indent=2, default=str))
