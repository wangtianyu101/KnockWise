/**
 * Interview 相关 TS 类型 — V3.8 P3 前置
 * P2 也用到（HeroCard 数据类型），提前定义
 */

export interface InterviewRadarData {
  algorithm?: number;
  system_design?: number;
  network?: number;
  frontend?: number;
  ai?: number;
  [key: string]: number | undefined;
}

export interface InterviewRecentItem {
  id: string;
  round: string;
  style: string;
  status: 'completed' | 'in_progress' | 'aborted';
  total_questions: number;
  overall_score: number | null;
  radar_data: InterviewRadarData;
  started_at: string | null;
  ended_at: string | null;
}

export interface InterviewRecentResponse {
  items: InterviewRecentItem[];
  total: number;
}

export const RADAR_DIMENSIONS = [
  'algorithm',
  'system_design',
  'network',
  'frontend',
  'ai',
] as const;

export type RadarDimension = typeof RADAR_DIMENSIONS[number];