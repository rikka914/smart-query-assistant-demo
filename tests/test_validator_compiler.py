import unittest
from datetime import datetime,timedelta,timezone

from api.app.compiler import compile_query
from api.app.models import QueryFilters,QueryPlan
from api.app.validator import QueryPlanValidatorError, validate_and_normalize

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)

class ValidatorCompilerTest(unittest.TestCase):
    def test_user_value_is_parameterized(self) -> None:
        malicious = "龙湖区' OR '1'='1"
        plan = QueryPlan(
            intent="detail_search",
            filters=QueryFilters(
                start_time=NOW - timedelta(days=7),
                end_time = NOW,
                district = malicious
            ),

        )

        compiled = compile_query(plan)

        self.assertNotIn(malicious,compiled.sql)
        self.assertEqual(compiled.params['district'], malicious)
        self.assertIn("district = :district",compiled.sql)


    def test_only_whitelisted_view_is_used(self) -> None:
        plan = QueryPlan(
            intent="similar_case_search",
            filters=QueryFilters(
                start_time= NOW - timedelta(days=30),
                end_time= NOW
            ),
            semantic_query="胸闷出汗",
            limit=10,
        )

        compiled = compile_query(plan)
        self.assertIn("dispatch.v_dispatch_case_search",compiled.sql)
        self.assertIn(":semantic_query", compiled.sql)
        self.assertEqual(compiled.params["semantic_query"],"胸闷出汗")

    def test_time_span_over_one_year_is_rejected(self) -> None:
        plan = QueryPlan(
            intent="detail_search",
            filters=QueryFilters(
                start_time= NOW - timedelta(days=400),
                end_time= NOW
            )
        ) 
        with self.assertRaises(QueryPlanValidatorError):
            validate_and_normalize(plan,"Asia/Shanghai")

    def test_missing_time_is_filled(self) -> None:
        plan = QueryPlan(intent="detail_search")
        result = validate_and_normalize(plan,"Asia/Shanghai")
        self.assertIsNotNone(result.filters.start_time)
        self.assertIsNotNone(result.filters.end_time)

if __name__ == "__main__":
    unittest.main()