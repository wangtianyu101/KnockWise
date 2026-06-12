"""Followup Tree Engine — the core differentiator of CodeMock.

Loads a question's followup_tree JSON, evaluates the user's answer against
the tree's branches, and determines the next action:
  - followup: ask a deeper question
  - give_hint: provide a hint and ask again
  - probe: ask a clarifying question
  - degrade: drop to an easier related question
  - skip_and_record: skip this direction, record blind spot, move on
  - next_question: move to next question (max depth reached or answered well)
"""

import json
import re
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.config import settings

# Action types that the followup engine can return
ActionType = Literal["followup", "give_hint", "probe", "degrade", "skip_and_record", "next_question"]


class FollowupEngine:
    """Matches user answers to followup tree branches and generates next actions."""

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                temperature=0,
            )
        return self._llm

    async def determine_action(
        self,
        question: dict,
        user_answer: str,
        current_depth: int,
        followup_count: int,
        max_depth: int = 4,
    ) -> dict:
        """Evaluate the user's answer and determine the next action.

        Returns:
            {
                "action": ActionType,
                "followup_text": str,  # the next thing to say (if applicable)
                "blind_spot": str,     # blind spot to record (if skip_and_record)
                "next_question_id": str,  # if skip_and_record, which question to jump to
                "score": int,          # 1-5 evaluation score
            }
        """
        followup_tree = question.get("followup_tree", {})
        answer_key = question.get("answer_key_points", [])

        # No followup tree -> move on
        if not followup_tree or not followup_tree.get("branches"):
            return self._make_action("next_question", score=3)

        # Check if we've reached max depth or followup count
        if current_depth >= max_depth or followup_count >= 3:
            return self._make_action("next_question", score=self._quick_score(user_answer, answer_key))

        # Use LLM to match which branch the answer falls into
        matched = await self._match_branch(followup_tree, user_answer, question["question_text"], answer_key)

        action = matched.get("action", "followup")
        depth = matched.get("depth", current_depth + 1)
        blind_spot = matched.get("record_blind_spot", "")

        result = {
            "action": action,
            "score": self._calculate_score(matched, answer_key),
            "depth": depth,
        }

        if action == "skip_and_record":
            result["blind_spot"] = blind_spot or question.get("sub_topic", "")
            result["next_question_id"] = matched.get("next_question", "")
            result["followup_text"] = "好的，我们换个方向。"
        elif action == "give_hint":
            result["followup_text"] = matched.get("hint", "再想想看？")
        elif action == "degrade":
            result["followup_text"] = matched.get("followup", "没关系，换个角度聊聊。")
        elif action == "probe" or action == "followup":
            followup_q = await self._generate_followup_text(
                user_answer,
                matched.get("followup", ""),
                question.get("sub_topic", ""),
                action,
            )
            result["followup_text"] = followup_q
        else:
            result["followup_text"] = ""

        return result

    async def _match_branch(
        self,
        followup_tree: dict,
        user_answer: str,
        question_text: str,
        answer_key: list,
    ) -> dict:
        """Use LLM to match user's answer to the best-fitting branch."""
        branches = followup_tree.get("branches", [])
        if not branches:
            return {"action": "next_question"}

        branches_json = json.dumps(branches, ensure_ascii=False, indent=2)
        key_points_text = "\n".join(f"- {p}" for p in answer_key)

        prompt = f"""根据用户回答，判断匹配追问树哪个分支。

原题：{question_text}

参考答案要点：
{key_points_text}

用户回答："{user_answer}"

追问树分支：
{branches_json}

规则：
1. 回答很差（一两句话、无关、说不会）→ 选 action 为 skip_and_record 或 degrade 的分支
2. 触及部分要点但不完整 → 选 action 为 probe 的分支
3. 完整且正确 → 选 action 为 followup 且深度更大的分支
4. 完全答不上来 → skip_and_record 优先

只返回一行 JSON：
{{"matched_branch_index":0,"reason":"简短","score":3}}"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="技术面试评估。只输出一行JSON，格式{\"matched_branch_index\":0,\"reason\":\"...\",\"score\":3}。不输出任何其他文字。"),
                HumanMessage(content=prompt),
            ])
            text = response.content.strip()
            m = re.search(r'\{[^{}]*"matched_branch_index"\s*:\s*\d+[^{}]*\}', text)
            if m:
                result = json.loads(m.group())
            else:
                result = json.loads(text.removeprefix("```json").removesuffix("```").strip())
        except (json.JSONDecodeError, AttributeError):
            # Keyword fallback: try to match condition text
            return self._keyword_fallback(branches, user_answer)

        idx = result.get("matched_branch_index", 0)
        if 0 <= idx < len(branches):
            matched = dict(branches[idx])
            # Inject score from LLM evaluation
            if "score" not in matched:
                matched["score"] = result.get("score", 3)
            return matched

        return {"action": "next_question"}

    def _keyword_fallback(self, branches: list, user_answer: str) -> dict:
        """Fallback: match branch by keyword when JSON parsing fails."""
        user_lower = user_answer.lower()
        for i, branch in enumerate(branches):
            cond = branch.get("condition", "").lower()
            keywords = [w for w in cond.split() if len(w) >= 2]
            if any(kw in user_lower for kw in keywords[:5]):
                return dict(branch)
        # Prefer non-skip branches
        for b in branches:
            if b.get("action") != "skip_and_record":
                return dict(b)
        return dict(branches[0]) if branches else {"action": "next_question"}

    async def _generate_followup_text(
        self,
        user_answer: str,
        template_followup: str,
        topic: str,
        action: str,
    ) -> str:
        """Naturalize the followup question with an interviewer persona."""
        if not template_followup:
            return "能再详细说说吗？"

        prompt = f"""把下面的技术追问改写成口语面试追问。直接输出改写后的一句话，不加引号。

原始追问：{template_followup}
用户刚才的回答：{user_answer}
技术方向：{topic}

风格要求：
- 说话像跟同事聊技术，不要书面语
- 不要说"根据你的回答""让我换个方式问""你能详细解释"这类套话
- 可以直接追问，也可以先简短回应再追问（比如"嗯，那你觉得..."）
- 不要夸赞用户（不要说"很好""不错"）"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="你是字节资深面试官，面过500+人。追问直接、口语化、干脆。像跟同事聊技术，不书面不客套。"),
                HumanMessage(content=prompt),
            ])
            return response.content.strip().strip('"').strip()
        except Exception:
            return template_followup

    def _calculate_score(self, matched: dict, answer_key: list) -> int:
        """Calculate a 1-5 score based on match quality."""
        if "score" in matched:
            return max(1, min(5, int(matched["score"])))
        # Rough heuristic based on action type
        action = matched.get("action", "followup")
        if action == "skip_and_record":
            return 1
        elif action == "give_hint" or action == "degrade":
            return 2
        elif action == "probe":
            return 3
        elif action == "followup":
            depth = matched.get("depth", 1)
            return min(5, 3 + depth)
        return 3

    def _quick_score(self, user_answer: str, answer_key: list) -> int:
        """Quick score when max depth reached — used as fallback."""
        if not user_answer or len(user_answer) < 10:
            return 1
        if len(answer_key) == 0:
            return 3
        # Simple heuristic: longer answer with some keywords = better
        score = min(5, 2 + len(user_answer) // 200)
        return score

    def _make_action(self, action: ActionType, score: int = 3) -> dict:
        return {"action": action, "score": score, "followup_text": "", "depth": 0}


# Singleton
followup_engine = FollowupEngine()
