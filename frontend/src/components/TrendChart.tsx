import BaseChart from './BaseChart'

interface TrendChartProps {
  data: Array<{ date: string; [key: string]: number | string }>
  dimensions?: string[]
}

const dimLabels: Record<string, string> = {
  spicy: '辣', sweet: '甜', sour: '酸', salty: '咸', umami: '鲜', bitter: '苦'
}
const colors = ['#D9A35F', '#244657', '#9A6338', '#48BB78', '#E53E3E', '#718096']

export default function TrendChart({ data, dimensions = ['spicy', 'sweet', 'salty', 'umami'] }: TrendChartProps) {
  const dates = data.map(d => d.date)

  const series = dimensions.map((dim, i) => ({
    name: dimLabels[dim] || dim,
    type: 'line',
    smooth: true,
    data: data.map(d => d[dim] as number),
    itemStyle: { color: colors[i % colors.length] },
    lineStyle: { width: 2 },
  }))

  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: dimensions.map(d => dimLabels[d] || d), bottom: 0 },
    grid: { top: 20, right: 20, bottom: 40, left: 40 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', min: 0, max: 1 },
    series,
    animationDuration: 800,
  }

  return <BaseChart option={option} style={{ height: 220 }} />
}
