/**
 * RecentSedimentsCard — V2.3 知识库页"最近学习沉淀"卡
 * component-spec.md §2 完整定义（6 状态）
 */
import { useEffect, useState } from "react";
import { Card, List, Alert, Empty, Spin, Button } from "antd";
import { FileTextOutlined, AlertOutlined } from "@ant-design/icons";
import { getToken } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SedimentFile {
  rel_path: string;
  full_path: string | null;
  success: boolean;
  error: string | null;
}

interface Props {
  limit?: number;
}

export default function RecentSedimentsCard({ limit = 5 }: Props) {
  const [files, setFiles] = useState<SedimentFile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (process.env.NEXT_PUBLIC_V2_ENABLED === "false") {
      setLoading(false);
      return;
    }
    fetch(`${API}/api/v2/knowledge/recent-sediments?limit=${limit}`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then(async (r) => {
        const data = await r.json();
        setFiles(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [limit]);

  if (loading) {
    return (
      <Card className="mt-5" title="最近学习沉淀">
        <Spin />
      </Card>
    );
  }

  // 0 文件态
  if (files.length === 0) {
    return (
      <Card className="mt-5" title="最近学习沉淀">
        <Empty
          description="答完第一道题后，这里会生成你的第一份学习笔记"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  // 决策 7A：vault 不存在 → 所有 file.full_path === null → 渲染警告 + "vault 不可用"
  const vaultMissing = files.every((f) => !f.full_path);

  return (
    <Card className="mt-5" title="最近学习沉淀">
      {vaultMissing && (
        <Alert
          message="Obsidian 路径不存在"
          description="请在 ~/Obsidian/coding/ 创建目录以启用 Obsidian 写笔记功能"
          type="warning"
          showIcon
          icon={<AlertOutlined />}
          className="mb-4"
        />
      )}
      <List
        size="small"
        dataSource={files}
        renderItem={(file) => (
          <List.Item
            key={file.rel_path}
            actions={[
              <Button
                key="open"
                type="link"
                size="small"
                disabled={!file.full_path}
                onClick={() => {
                  if (file.full_path) {
                    window.open(`file://${file.full_path}`, "_blank");
                  }
                }}
              >
                打开
              </Button>,
            ]}
          >
            <List.Item.Meta
              avatar={<FileTextOutlined className="text-indigo-400" />}
              title={
                <span className="font-mono text-sm text-indigo-300">
                  {file.rel_path}
                </span>
              }
              description={
                vaultMissing ? (
                  <span className="text-amber-400 text-xs">vault 不可用</span>
                ) : (
                  <span className="text-gray-500 text-xs">Obsidian 文件</span>
                )
              }
            />
          </List.Item>
        )}
      />
    </Card>
  );
}
