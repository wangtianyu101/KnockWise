/**
 * V3 学习计划模块类型定义（PR 1 · V3.0）
 * 与 backend/services/study_plan_service.py schema 对齐
 */

export interface StudyPlan {
  id: string;
  name: string;
  description?: string;
  goal?: string;
  start_date: string;        // ISO date 'YYYY-MM-DD'
  end_date: string;
  status: 'active' | 'paused' | 'completed' | 'expired';
  weekly_target: Array<{
    week_idx: number;
    target_count: number;
    target_topics: string[];
  }>;
  progress?: StudyPlanProgress;
  created_at: string;
  updated_at: string;
}

export interface StudyPlanProgress {
  total_target: number;       // 累计 weekly_target 总和
  mastered: number;            // 已掌握题数
  learning: number;
  new_count: number;
  completion_rate: number;      // 0-1
  weak_topics_remaining: string[];
}

export interface StudyPlanCreateInput {
  name: string;
  description?: string;
  goal?: string;
  start_date: string;
  end_date: string;
  weekly_target: StudyPlan['weekly_target'];
}

export interface StudyPlanListResponse {
  items: StudyPlan[];
}
