"""Question Selection Engine.

Selects the next question based on:
  1. Interview round (round1=breadth, round2=depth)
  2. User's profile (tech stack, experience level)
  3. Questions already asked (avoid duplicates)
  4. Blind spots accumulated so far (target weak areas)
"""

import random
from typing import Optional

from services.seed_service import load_questions_from_files


class QuestionEngine:
    def __init__(self):
        self.all_questions: list[dict] = load_questions_from_files()

    def select_next_question(
        self,
        round: str,
        profile: dict,
        questions_asked: list[str],
        blind_spots: list[str],
        current_topic: Optional[str] = None,
    ) -> Optional[dict]:
        """Select the next question based on interview context.

        Strategy:
          1. Eliminate already-asked questions
          2. Filter by round (round1 or round2)
          3. If profile has tech_stack, prioritize those topics
          4. If blind_spots exist, prioritize them
          5. Pick based on difficulty matching experience level
          6. Fall back to random
        """
        available = [q for q in self.all_questions if q["id"] not in questions_asked]

        if not available:
            available = [q for q in self.all_questions if q["id"] not in questions_asked[-10:]]
        if not available:
            return random.choice(self.all_questions) if self.all_questions else None

        # Filter by round
        round_match = [q for q in available if q.get("round") == round]
        if round_match:
            available = round_match

        # Prioritize by tech stack
        tech_stack = [t.lower() for t in profile.get("tech_stack", [])]
        if tech_stack:
            tech_priorities = [
                q for q in available
                if any(t in q.get("topic", "").lower() or t in q.get("sub_topic", "").lower() for t in tech_stack)
            ]
            if tech_priorities:
                available = tech_priorities

        # Prioritize blind spots
        if blind_spots:
            blind_candidates = [
                q for q in available
                if any(bs.lower() in q.get("sub_topic", "").lower() for bs in blind_spots)
            ]
            if blind_candidates:
                available = blind_candidates

        # Match difficulty to experience
        years = profile.get("years_of_exp", 1)
        if years <= 1:
            target_difficulty = [1, 2, 3]
        elif years <= 3:
            target_difficulty = [2, 3, 4]
        else:
            target_difficulty = [3, 4, 5]

        diff_match = [q for q in available if q.get("difficulty", 3) in target_difficulty]
        if diff_match:
            available = diff_match

        # Random select from remaining
        return random.choice(available)

    def get_question_by_id(self, question_id: str) -> Optional[dict]:
        for q in self.all_questions:
            if q["id"] == question_id:
                return q
        return None

    def get_questions_by_topic(self, topic: str) -> list[dict]:
        return [q for q in self.all_questions if q.get("topic") == topic]


question_engine = QuestionEngine()
