"""
Expense Storage Service.
Stores and retrieves expenses from YDB or in-memory storage.

BDD Reference: NLE-A-10
"""
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

from src.db.ydb_client import get_db, YDBClient, MemoryDB


@dataclass
class Expense:
    """Expense record"""
    user_id: int
    item: str
    amount: int
    category: str
    created_at: datetime = field(default_factory=datetime.now)


class ExpenseStorage:
    """Expense storage service with YDB or in-memory backend"""

    TABLE_NAME = "expenses"

    def __init__(self, use_memory: bool = False):
        if use_memory:
            self.db = MemoryDB()
        else:
            self.db = get_db()
        self._ensure_table()

    def _ensure_table(self):
        """Ensure expenses table exists"""
        if isinstance(self.db, YDBClient):
            try:
                self.db.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                        user_id Int64,
                        item Utf8,
                        amount Int64,
                        category Utf8,
                        created_at Timestamp,
                        PRIMARY KEY (user_id, created_at)
                    )
                """)
            except Exception:
                pass  # Table may already exist

    def save_expense(self, expense: Expense) -> bool:
        """Save expense to storage"""
        data = {
            "user_id": expense.user_id,
            "item": expense.item,
            "amount": expense.amount,
            "category": expense.category,
            "created_at": expense.created_at.isoformat() if expense.created_at else datetime.now().isoformat(),
        }
        return self.db.insert(self.TABLE_NAME, data)

    def get_expenses(self, user_id: int, limit: int = 100) -> List[Expense]:
        """Get all expenses for user"""
        rows = self.db.select(self.TABLE_NAME, {"user_id": user_id}, limit=limit)
        return [self._row_to_expense(row) for row in rows]

    def get_monthly_expenses(self, user_id: int) -> List[Expense]:
        """Get expenses for current month"""
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        expenses = self.get_expenses(user_id)
        return [
            e for e in expenses
            if e.created_at and e.created_at >= start_of_month
        ]

    def get_by_category(self, user_id: int, category: str) -> List[Expense]:
        """Get expenses by category"""
        expenses = self.get_monthly_expenses(user_id)
        return [e for e in expenses if e.category == category]

    def get_item_total(self, user_id: int, item: str) -> int:
        """Get total spent on specific item"""
        expenses = self.get_monthly_expenses(user_id)
        item_lower = item.lower()
        return sum(
            e.amount for e in expenses
            if item_lower in e.item.lower()
        )

    def get_category_totals(self, user_id: int) -> Dict[str, int]:
        """Get totals by category"""
        expenses = self.get_monthly_expenses(user_id)
        totals: Dict[str, int] = defaultdict(int)
        for e in expenses:
            totals[e.category] += e.amount
        return dict(totals)

    def get_total(self, user_id: int) -> int:
        """Get total expenses for current month"""
        expenses = self.get_monthly_expenses(user_id)
        return sum(e.amount for e in expenses)

    def get_top_categories(self, user_id: int, limit: int = 5) -> List[tuple]:
        """Get top spending categories"""
        totals = self.get_category_totals(user_id)
        sorted_totals = sorted(totals.items(), key=lambda x: -x[1])
        return sorted_totals[:limit]

    def _row_to_expense(self, row: dict) -> Expense:
        """Convert database row to Expense object"""
        created_at = row.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = datetime.now()
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()

        return Expense(
            user_id=int(row.get("user_id", 0)),
            item=str(row.get("item", "")),
            amount=int(row.get("amount", 0)),
            category=str(row.get("category", "Другое")),
            created_at=created_at,
        )

    def delete_expense(self, user_id: int, created_at: str) -> bool:
        """Delete expense by user_id and created_at timestamp"""
        return self.db.delete(self.TABLE_NAME, {
            "user_id": user_id,
            "created_at": created_at,
        })

    def update_expense_category(self, user_id: int, created_at: str, new_category: str) -> bool:
        """Update category for an expense"""
        return self.db.update(
            self.TABLE_NAME,
            {"user_id": user_id, "created_at": created_at},
            {"category": new_category}
        )

    def get_last_expense(self, user_id: int) -> Optional[Expense]:
        """Get the most recent expense for user"""
        expenses = self.get_expenses(user_id, limit=1)
        return expenses[0] if expenses else None

    def get_today_expenses(self, user_id: int) -> List[Expense]:
        """Get expenses for today only"""
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        expenses = self.get_expenses(user_id)
        return [
            e for e in expenses
            if e.created_at and e.created_at >= start_of_day
        ]

    def get_week_expenses(self, user_id: int, weeks_ago: int = 0) -> List[Expense]:
        """Get expenses for a specific week

        Args:
            user_id: User ID
            weeks_ago: 0 for current week, 1 for last week, etc.
        """
        now = datetime.now()

        # Calculate week boundaries (Monday to Sunday)
        days_since_monday = now.weekday()
        week_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
        week_start = week_start - timedelta(weeks=weeks_ago)
        week_end = week_start + timedelta(days=7)

        expenses = self.get_expenses(user_id)
        return [
            e for e in expenses
            if e.created_at and week_start <= e.created_at < week_end
        ]

    def get_today_total(self, user_id: int) -> int:
        """Get total expenses for today"""
        expenses = self.get_today_expenses(user_id)
        return sum(e.amount for e in expenses)

    def get_week_total(self, user_id: int, weeks_ago: int = 0) -> int:
        """Get total expenses for a specific week"""
        expenses = self.get_week_expenses(user_id, weeks_ago)
        return sum(e.amount for e in expenses)
