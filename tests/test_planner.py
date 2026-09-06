from datetime import timedelta
import unittest
from api.app.planner import RuleBasedPlanner

class RuleBasePLannerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.planner = RuleBasedPlanner("Asia/Shanghai")

    def test_hospital_count(self) -> None:
        result = self.planner.plan("查询最近7天各医院的派车数量")
        self.assertEqual(result.plan.intent,"aggregate")
        self.assertEqual(result.plan.group_by,["hospital_name"])
        self.assertEqual(result.plan.metric,"count")
        span = result.plan.filters.end_time - result.plan.filters.start_time
        self.assertLess(abs(span - timedelta(days=7)),timedelta(seconds=2))

    def test_slow_dispatch_detail(self) -> None:
        result = self.planner.plan("查询最近30天龙湖区派车超过5分钟的记录")
        self.assertEqual(result.plan.intent,"detail_search")
        self.assertEqual(result.plan.filters.district,"龙湖区")
        self.assertEqual(result.plan.filters.min_dispatch_seconds,300)

    def test_similar_case_limit(self) -> None:
        result = self.planner.plan("查询10条与老人胸闷出汗意识模糊相似的警情")
        self.assertEqual(result.plan.intent,"similar_case_search")
        self.assertEqual(result.plan.limit,10)
        self.assertIn("老人胸闷",result.plan.semantic_query)

    def test_average_response(self) -> None:
        result = self.planner.plan("统计最近30天各区的平均响应时间")
        self.assertEqual(result.plan.intent,"aggregate")
        self.assertEqual(result.plan.group_by,["district"])
        self.assertEqual(result.plan.metric,"avg_response_seconds")




if __name__ == "__main__":
    unittest.main()