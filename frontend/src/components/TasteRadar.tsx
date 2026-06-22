import BaseChart from './BaseChart'

interface TasteRadarProps {
  data: Record<string, number>
  compareData?: Record<string, number>
  title?: string
}

const dimLabels: Record<string, string> = {
  spicy: '辣', sweet: '甜', sour: '酸', salty: '咸', umami: '鲜', bitter: '苦'
}

export default function TasteRadar({ data, compareData, title }: TasteRadarProps) {
  const dims = Object.keys(data)
  const indicators = dims.map(d => ({ name: dimLabels[d] || d, max: 1 }))

  const series: any[] = [{
    name: '我的口味',
    type: 'radar',
    data: [{ value: dims.map(d => data[d]), name: '我的口味', areaStyle: { opacity: 0.3 } }],
    itemStyle: { color: '#D9A35F' },
    lineStyle: { color: '#D9A35F' },
  }]

  if (compareData) {
    series.push({
      name: '对方口味',
      type: 'radar',
      data: [{ value: dims.map(d => compareData[d] || 0), name: '对方口味', areaStyle: { opacity: 0.2 } }],
      itemStyle: { color: '#244657' },
      lineStyle: { color: '#244657' },
    })
  }

  const option = {
    title: title ? { text: title, left: 'center', textStyle: { fontSize: 14, color: '#2C2118' } } : undefined,
    radar: { indicator: indicators, radius: '65%' },
    series,
    animationDuration: 1000,
    animationEasing: 'elasticOut',
  }

  return <BaseChart option={option} style={{ height: 260 }} />
}
