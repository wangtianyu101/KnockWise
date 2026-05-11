import { Radar, RadarChart as ReRadar, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts";

interface RadarChartProps {
  data: Record<string, number>;
}

const LABEL_MAP: Record<string, string> = {
  agent_architecture: "Agent架构",
  tool_use: "工具调用",
  memory: "记忆管理",
  mcp: "MCP协议",
  retrieval: "检索策略",
  chunking: "文档分块",
  advanced_rag: "高级RAG",
  rag_evaluation: "RAG评估",
  langchain: "LangChain",
  langgraph: "LangGraph",
  java: "Java基础",
};

export default function RadarChart({ data }: RadarChartProps) {
  const chartData = Object.entries(data).map(([key, value]) => ({
    name: LABEL_MAP[key] || key,
    value: Math.max(0.5, value || 0),
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ReRadar data={chartData} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid stroke="#374151" strokeOpacity={0.5} />
        <PolarAngleAxis
          dataKey="name"
          tick={{ fill: "#a5b4fc", fontSize: 11 }}
        />
        <Radar
          name="能力评分"
          dataKey="value"
          stroke="#818cf8"
          fill="#6366f1"
          fillOpacity={0.25}
        />
      </ReRadar>
    </ResponsiveContainer>
  );
}
