from pydantic import BaseModel
from typing import Optional, Dict
from uuid import UUID

# 6.1. /users/me/tests/stats
class UserTestsStatsResponse(BaseModel):
    total_tests_completed: int
    average_time_seconds: Optional[float]
    max_time_seconds: Optional[int]
    min_time_seconds: Optional[int]
    total_correct_answers: int
    total_wrong_answers: int

# 6.2. /users/me/questions/stats
# пример группировки: { "Algorithms": {"correct": 5, "wrong": 3}, "Swift Basics": {...} }
class TopicStats(BaseModel):
    correct: int
    wrong: int

class UserQuestionsStatsResponse(BaseModel):
    total_correct_answers: int
    total_wrong_answers: int
    by_topic: Dict[str, TopicStats]  # словарь topic -> {correct, wrong}
