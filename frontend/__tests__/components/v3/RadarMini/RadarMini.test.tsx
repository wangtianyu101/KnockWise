/**
 * RadarMini 测试 — V3.8 P2 · 6 测试
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RadarMini } from '@/components/v3/RadarMini/RadarMini';

describe('<RadarMini />', () => {
  it('渲染 5 边形外框 + 数据多边形', () => {
    const { container } = render(
      <RadarMini
        data={{ algorithm: 78, system_design: 75, network: 65, frontend: 50, ai: 40 }}
        company="字节"
        score={78}
      />
    );
    const polygons = container.querySelectorAll('polygon');
    // 外框 + 数据多边形 = 2 个
    expect(polygons.length).toBe(2);
  });

  it('color=pink 使用 #f472b6 描边', () => {
    const { container } = render(
      <RadarMini
        data={{ algorithm: 78 }}
        color="pink"
      />
    );
    const dataPolygon = container.querySelectorAll('polygon')[1];
    expect(dataPolygon?.getAttribute('stroke')).toBe('#f472b6');
  });

  it('placeholder=true 显示虚线', () => {
    const { container } = render(
      <RadarMini data={{}} placeholder company="?" />
    );
    const polygon = container.querySelector('polygon');
    expect(polygon?.getAttribute('stroke-dasharray')).toBe('3 3');
  });

  it('data 为空时不渲染数据多边形（只有外框）', () => {
    const { container } = render(
      <RadarMini data={{}} company="空" />
    );
    const polygons = container.querySelectorAll('polygon');
    // 只有外框（1 个）
    expect(polygons.length).toBe(1);
  });

  it('company + score 显示文字', () => {
    render(
      <RadarMini
        data={{ algorithm: 80 }}
        company="字节"
        score={80}
      />
    );
    expect(screen.getByText('字节')).toBeInTheDocument();
    expect(screen.getByText('80')).toBeInTheDocument();
  });

  it('5 维顺序固定（algorithm → ai 按 RADAR_DIMENSIONS 顺序）', () => {
    const { container } = render(
      <RadarMini
        data={{
          algorithm: 100,    // 顶部
          system_design: 0,  // 右上 → 内
          network: 0,        // 右下 → 内
          frontend: 0,       // 左下 → 内
          ai: 0,             // 左上 → 内
        }}
      />
    );
    const dataPolygon = container.querySelectorAll('polygon')[1];
    const points = dataPolygon?.getAttribute('points') ?? '';
    // algorithm=100 → 顶点 (40, 8)
    // 其他 0 → 中心 (40, 40)
    expect(points).toContain('40,8');  // 顶部
    expect(points).toContain('40,40'); // 中心 (4 个 0)
  });
});