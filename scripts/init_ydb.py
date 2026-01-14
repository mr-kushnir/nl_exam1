#!/usr/bin/env python
"""
Initialize YDB tables for NLExam bot.
Run this script once before first deployment.

Usage:
    python scripts/init_ydb.py
"""
import os
import sys
import httpx

try:
    import ydb
except ImportError:
    print("Error: ydb package not installed. Run: pip install ydb")
    sys.exit(1)


def get_iam_token():
    """Get IAM token from OAuth token"""
    oauth = os.getenv('YC_TOKEN')
    if not oauth:
        print("Error: YC_TOKEN not set")
        sys.exit(1)

    resp = httpx.post(
        'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        json={'yandexPassportOauthToken': oauth}
    )
    if resp.status_code != 200:
        print(f"Error getting IAM token: {resp.text}")
        sys.exit(1)

    return resp.json().get('iamToken')


def create_expenses_table(pool, database):
    """Create expenses table"""
    table_path = f"{database}/expenses"

    def create_table(session):
        session.create_table(
            table_path,
            ydb.TableDescription()
                .with_column(ydb.Column('user_id', ydb.OptionalType(ydb.PrimitiveType.Int64)))
                .with_column(ydb.Column('item', ydb.OptionalType(ydb.PrimitiveType.Utf8)))
                .with_column(ydb.Column('amount', ydb.OptionalType(ydb.PrimitiveType.Int64)))
                .with_column(ydb.Column('category', ydb.OptionalType(ydb.PrimitiveType.Utf8)))
                .with_column(ydb.Column('created_at', ydb.OptionalType(ydb.PrimitiveType.Utf8)))
                .with_primary_keys('user_id', 'created_at')
        )

    try:
        pool.retry_operation_sync(create_table)
        print(f"  Created table: {table_path}")
    except ydb.issues.SchemeError as e:
        if "already exists" in str(e):
            print(f"  Table already exists: {table_path}")
        else:
            raise


def main():
    print("YDB Initialization Script")
    print("=" * 40)

    # Get config from env
    endpoint = os.getenv('YDB_ENDPOINT', 'grpcs://ydb.serverless.yandexcloud.net:2135')
    database = os.getenv('YDB_DATABASE', '')

    if not database:
        print("Error: YDB_DATABASE not set")
        sys.exit(1)

    print(f"Endpoint: {endpoint}")
    print(f"Database: {database}")
    print()

    # Get IAM token
    print("Getting IAM token...")
    iam_token = get_iam_token()
    print("  OK")

    # Connect
    print("Connecting to YDB...")
    driver_config = ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
        credentials=ydb.credentials.AccessTokenCredentials(iam_token)
    )

    driver = ydb.Driver(driver_config)
    driver.wait(timeout=30)
    pool = ydb.SessionPool(driver)
    print("  OK")

    # Create tables
    print("Creating tables...")
    create_expenses_table(pool, database)

    # Done
    driver.stop()
    print()
    print("Initialization complete!")


if __name__ == "__main__":
    main()
