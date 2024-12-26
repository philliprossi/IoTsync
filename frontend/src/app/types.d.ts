declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

interface TemperatureData {
  time: string;
  temperature: number;
  temperature_f: number;
}

interface Alert {
  id: number;
  timestamp: string;
  type: string;
  temperature: number;
  threshold: number;
  message: string;
}

interface TemperatureChartProps {
  data: TemperatureData[];
  currentTemperature: number | null;
  lastUpdateTime: string;
  minThreshold: number;
  minTemperature: number | null;
  maxTemperature: number | null;
  onTimeRangeChange: (range: string) => void;
}

interface RecentAlertsProps {
  alerts: Alert[];
} 