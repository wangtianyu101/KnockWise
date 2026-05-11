"""Report Generation Agent.

Generates interview reports with radar charts, blind spot analysis, and improvement plans.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.config import settings

# Skill categories for radar chart (matching the knowledge graph)
SKILL_CATEGORIES = [
    "agent_architecture",
    "tool_use",
    "memory",
    "mcp",
    "retrieval",
    "chunking",
    "advanced_rag",
    "rag_evaluation",
    "langchain",
    "langgraph",
    "java",
]


class ReportAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=0.3,
        )

    async def generate_report(
        self,
        profile: dict,
        questions_asked: list[dict],
        blind_spots: list[str],
        total_score: float,
        round: str,
    ) -> dict:
        """Generate a comprehensive interview report.

        Returns:
            {
                "overall_score": float (1-5),
                "radar_data": {category: score},
                "top_blind_spots": [{topic, severity, suggestion}],
                "improvement_plan": [{action, resources, priority}],
                "summary": str,
            }
        """
        questions_summary = self._summarize_questions(questions_asked)
        blind_spots_summary = ", ".join(blind_spots) if blind_spots else "无特别盲区"

        prompt = f"""根据以下面试数据生成一份面试评估报告：

面试轮次：{round}
用户技术栈：{profile.get("tech_stack", [])}
工作年限：{profile.get("years_of_exp", 0)} 年

答题情况：
{questions_summary}

暴露的知识盲区：
{blind_spots_summary}

请返回 JSON：
{{
  "overall_score": 3.5,
  "summary": "整体评价（2-3句话）",
  "radar_data": {{
    "agent_architecture": 3,
    "tool_use": 3,
    "memory": 3,
    "mcp": 3,
    "retrieval": 3,
    "chunking": 3,
    "advanced_rag": 3,
    "rag_evaluation": 3,
    "langchain": 3,
    "langgraph": 3,
    "java": 3
  }},
  "top_blind_spots": [
    {{"topic": "方向名称", "severity": "high/medium/low", "suggestion": "具体建议"}}
  ],
  "improvement_plan": [
    {{"action": "做什么", "resources": "学习资源", "priority": "high/medium/low"}}
  ]
}}

overall_score 是 1-5 的浮点数。radar_data 每个维度的分数根据答题情况推算，没涉及到的维度给 3（默认值）。
只返回 JSON。"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="你是技术面试评估报告专家。只返回 JSON。"),
                HumanMessage(content=prompt),
            ])
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            import json
            result = json.loads(text)
        except Exception:
            result = self._fallback_report(total_score, blind_spots, round)

        # Ensure radar_data has all categories
        for cat in SKILL_CATEGORIES:
            if cat not in result.get("radar_data", {}):
                result.setdefault("radar_data", {})[cat] = 3

        return result

    def _summarize_questions(self, questions: list[dict]) -> str:
        lines = []
        for q in questions[-10:]:  # latest 10
            lines.append(
                f"- [{q.get('topic', '')}] {q.get('question_text', '')[:60]}... "
                f"评分: {q.get('score', 'N/A')}"
            )
        return "\n".join(lines) if lines else "无答题记录"

    def _fallback_report(self, total_score: float, blind_spots: list[str], round: str) -> dict:
        avg_score = max(1.0, min(5.0, total_score / max(1, len(blind_spots) if blind_spots else 3)))
        return {
            "overall_score": round(avg_score, 1),
            "summary": f"{round} 面试完成。",
            "radar_data": {cat: 3 for cat in SKILL_CATEGORIES},
            "top_blind_spots": [
                {"topic": bs, "severity": "medium", "suggestion": "建议系统学习该方向"}
                for bs in blind_spots[:3]
            ],
            "improvement_plan": [],
        }


report_agent = ReportAgent()
