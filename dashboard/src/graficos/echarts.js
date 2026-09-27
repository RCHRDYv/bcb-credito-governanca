/**
 * PT: O ECharts importado por partes (ADR 0017, decisão 2).
 *
 *     Entram só os tipos de gráfico e os componentes que o design system
 *     usa, e o renderizador SVG. O resto da biblioteca fica fora do build.
 *     Todo módulo de gráfico importa o ECharts daqui, e nunca do pacote
 *     inteiro, para o import por partes não se perder por acidente.
 *
 * EN: ECharts imported by parts: only the chart types and components the
 *     design system uses, plus the SVG renderer. Every chart module imports
 *     ECharts from here, never from the full package.
 */

import { BarChart, HeatmapChart, LineChart, MapChart, ScatterChart } from "echarts/charts";
import {
  AriaComponent,
  DatasetComponent,
  GeoComponent,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkLineComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";

echarts.use([
  BarChart,
  HeatmapChart,
  LineChart,
  MapChart,
  ScatterChart,
  AriaComponent,
  DatasetComponent,
  GeoComponent,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkLineComponent,
  TooltipComponent,
  VisualMapComponent,
  SVGRenderer,
]);

export { echarts };
