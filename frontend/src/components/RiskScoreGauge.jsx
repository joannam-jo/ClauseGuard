import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const RISK_COLORS = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
};

export function RiskScoreGauge({ score = 0, size = 200 }) {
  // Clamp score between 0 and 10
  const normalizedScore = Math.max(0, Math.min(10, score));
  
  // Calculate gauge data
  const gaugeData = useMemo(() => {
    const filled = normalizedScore * 10; // Convert to percentage of 100
    const empty = 100 - filled;
    return [
      { name: 'filled', value: filled },
      { name: 'empty', value: empty },
    ];
  }, [normalizedScore]);

  // Determine color based on score
  const getScoreColor = (score) => {
    if (score <= 3) return RISK_COLORS.low;
    if (score <= 6) return RISK_COLORS.medium;
    return RISK_COLORS.high;
  };

  const scoreColor = getScoreColor(normalizedScore);

  // Get risk level text
  const getRiskLevel = (score) => {
    if (score <= 3) return 'Low Risk';
    if (score <= 6) return 'Medium Risk';
    return 'High Risk';
  };

  const COLORS = [scoreColor, 'hsl(var(--muted))'];

  return (
    <div className="flex flex-col items-center" data-testid="risk-score-gauge">
      <div className="relative" style={{ width: size, height: size / 2 + 20 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={gaugeData}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={size * 0.35}
              outerRadius={size * 0.45}
              paddingAngle={0}
              dataKey="value"
              stroke="none"
            >
              {gaugeData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        
        {/* Score display in center */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-end pb-2"
          style={{ top: '20%' }}
        >
          <span
            className="text-4xl font-bold tabular-nums"
            style={{ color: scoreColor }}
          >
            {normalizedScore.toFixed(1)}
          </span>
          <span className="text-sm text-muted-foreground font-mono">/10</span>
        </div>
      </div>
      
      <div className="text-center mt-2">
        <p className="text-lg font-semibold" style={{ color: scoreColor }}>
          {getRiskLevel(normalizedScore)}
        </p>
        <p className="text-xs text-muted-foreground">
          {normalizedScore <= 3
            ? 'Generally safe to proceed'
            : normalizedScore <= 6
            ? 'Review and negotiate terms'
            : 'Consider alternatives'}
        </p>
      </div>
    </div>
  );
}
