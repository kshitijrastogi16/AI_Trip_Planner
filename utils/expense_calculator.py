class Calculator:
    @staticmethod
    def multiply(a: float, b: float) -> float:
        """Multiply two numeric values."""
        return float(a) * float(b)

    @staticmethod
    def calculate_total(*x: float) -> float:
        """
        Calculate the sum of the given numbers.

        Args:
            x: A sequence of numeric values.

        Returns:
            The sum of the numbers.
        """
        return sum(x)

    @staticmethod
    def calculate_daily_budget(total: float, days: int) -> float:
        """
        Calculate the daily expense budget.

        Args:
            total: Total cost.
            days: Total number of days.

        Returns:
            Expense for a single day, or 0 if days is not positive.
        """
        return total / days if days > 0 else 0