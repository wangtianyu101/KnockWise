/**
 * V3 PlanCreateModal（PR 1 · T4 · 创建学习计划 Modal）
 * 422 错误展示（V2 L4 错误格式）+ 409 同名冲突 toast
 */
import { useState } from 'react';
import { Modal, Form, Input, DatePicker, message, Button } from 'antd';
import { getToken } from '@/lib/api';
import type { StudyPlanCreateInput } from '@/types/v3-plan';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function PlanCreateModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const payload: StudyPlanCreateInput = {
        name: values.name.trim(),
        description: values.description?.trim() || undefined,
        goal: values.goal?.trim() || undefined,
        start_date: values.start_date.format('YYYY-MM-DD'),
        end_date: values.end_date.format('YYYY-MM-DD'),
        weekly_target: parseWeeklyTarget(values.weekly_target || ''),
      };

      const res = await fetch(`${API_BASE}/api/learn/plans`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify(payload),
      });

      if (res.status === 422) {
        const err = await res.json();
        const detail = err?.error?.details;
        message.error(`字段错误：${detail?.field || '未知'} · ${err?.error?.message || '校验失败'}`);
        return;
      }
      if (res.status === 409) {
        message.error('同名计划已存在，请换一个名字');
        return;
      }
      if (!res.ok) {
        message.error(`创建失败 (HTTP ${res.status})`);
        return;
      }

      onCreated();
      form.resetFields();
    } catch (err) {
      if (err?.errorFields) {
        message.warning('请填写所有必填字段');
      } else {
        message.error('提交失败');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal
      title="创建学习计划"
      open={open}
      onCancel={onClose}
      width={600}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          创建
        </Button>,
      ]}
    >
      <Form form={form} layout="vertical" preserve={false}>
        <Form.Item
          label="计划名称"
          name="name"
          rules={[
            { required: true, message: '请输入计划名称' },
            { max: 50, message: '最多 50 字符' },
          ]}
        >
          <Input placeholder="如：2 周算法冲刺" maxLength={50} showCount />
        </Form.Item>
        <Form.Item label="日期范围" required>
          <div className="flex gap-2">
            <Form.Item
              name="start_date"
              rules={[{ required: true, message: '请选择开始日期' }]}
              noStyle
            >
              <DatePicker placeholder="开始日期" />
            </Form.Item>
            <span className="self-center text-gray-500">~</span>
            <Form.Item
              name="end_date"
              dependencies={['start_date']}
              rules={[
                { required: true, message: '请选择结束日期' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    const start = getFieldValue('start_date');
                    if (!value || !start) return Promise.resolve();
                    return value.isAfter(start)
                      ? Promise.resolve()
                      : Promise.reject(new Error('结束日期必须晚于开始日期'));
                  },
                }),
              ]}
              noStyle
            >
              <DatePicker placeholder="结束日期" />
            </Form.Item>
          </div>
        </Form.Item>
        <Form.Item label="目标" name="goal">
          <Input.TextArea rows={2} maxLength={200} showCount placeholder="如：掌握 algorithms 50%" />
        </Form.Item>
        <Form.Item label="周目标（JSON）" name="weekly_target" tooltip='如 [{"week_idx":1,"target_count":10,"target_topics":["algorithms"]}]'>
          <Input.TextArea
            rows={3}
            placeholder='[{"week_idx":1,"target_count":10,"target_topics":["algorithms"]}]'
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}

function parseWeeklyTarget(raw: string): StudyPlanCreateInput['weekly_target'] {
  if (!raw || !raw.trim()) return [];
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((w) => typeof w?.week_idx === 'number' && typeof w?.target_count === 'number')
      .map((w) => ({
        week_idx: w.week_idx,
        target_count: w.target_count,
        target_topics: Array.isArray(w.target_topics) ? w.target_topics : [],
      }));
  } catch {
    return [];
  }
}
