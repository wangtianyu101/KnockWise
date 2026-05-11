"""Answer Evaluation Agent.

Evaluates user answers and extracts blind spots.
"""

import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.config import settings


class EvaluateAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=0,
        )

    async def evaluate_answer(
        self,
        question_text: str,
        answer_key_points: list,
        user_answer: str,
        topic: str,
        sub_topic: str,
    ) -> dict:
        """Evaluate the user's answer and extract blind spots.

        Returns:
            {
                "score": int (1-5),
                "blind_spots": [str],
                "feedback": str (short evaluation),
                "is_correct": bool (pass threshold)
            }
        """
        key_points_str = "\n".join(f"- {p}" for p in answer_key_points) if answer_key_points else "无预设要点"

        prompt = f"""评估以下面试回答：

技术方向：{topic} > {sub_topic}
面试题：{question_text}

参考答案要点：
{key_points_str}

用户回答：
{user_answer}

请返回 JSON：
{{
  "score": 3,
  "covered_points": ["命中的要点1", "命中的要点2"],
  "missed_points": ["遗漏的要点1"],
  "blind_spots": ["用户暴露的知识盲区"],
  "feedback": "简短的评估和建议（1-2句话）"
}}

score: 1=完全不会, 2=严重不足, 3=基本覆盖, 4=准确完整, 5=深入且有见解
blind_spots: 回答明显薄弱则指具体盲区方向，回答不错则返回空数组。
你的回答将被程序解析，必须严格输出 JSON。直接输出 JSON，不加代码块标记。

{{"score":3,"covered_points":[],"missed_points":[],"blind_spots":[],"feedback":""}}"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="你是技术面试评估专家。你的回答将被程序解析，严格 JSON 格式，禁止输出任何非 JSON 文字。"),
                HumanMessage(content=prompt),
            ])
            text = response.content.strip()
            # Robust extraction
            clean = text.removeprefix("```json").removesuffix("```").removesuffix("```").strip()
            m = re.search(r'\{[^{}]*"score"\s*:\s*\d+[^{}]*\}', clean)
            result = json.loads(m.group()) if m else json.loads(clean)
        except Exception:
            result = {"score": 3, "covered_points": [], "missed_points": [], "blind_spots": [], "feedback": ""}

        return {
            "score": max(1, min(5, result.get("score", 3))),
            "blind_spots": result.get("blind_spots", []),
            "feedback": result.get("feedback", ""),
            "covered_points": result.get("covered_points", []),
            "missed_points": result.get("missed_points", []),
            "is_correct": result.get("score", 3) >= 3,
        }


evaluate_agent = EvaluateAgent()
