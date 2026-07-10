import { nearestIndex, normaliseRow, rowAt, transformX, transformXValue } from "./live-math";
import type { Domain, LivePayload, Normalisation, PlotRect } from "./live-types";

const COLORS = {
  background: "#121821",
  current: "#22c7d6",
  baseline: "#8a96a6",
  difference: "#f2b84b",
  grid: "#26313e",
  text: "#d9e0e8",
  muted: "#91a0b2",
} as const;

function projectX(value: number, plot: PlotRect, domain: Domain, reversed: boolean): number {
  const ratio = (value - domain.xMin) / (domain.xMax - domain.xMin);
  return plot.left + (reversed ? 1 - ratio : ratio) * plot.width;
}

function projectY(value: number, plot: PlotRect, domain: Domain): number {
  const ratio = (value - domain.yMin) / (domain.yMax - domain.yMin);
  return plot.top + (1 - ratio) * plot.height;
}

function drawTrace(
  context: CanvasRenderingContext2D,
  x: Float32Array,
  y: Float32Array,
  color: string,
  width: number,
  plot: PlotRect,
  domain: Domain,
  reversed: boolean,
): void {
  if (domain.xMax <= domain.xMin || domain.yMax <= domain.yMin) {
    return;
  }
  context.beginPath();
  context.strokeStyle = color;
  context.lineWidth = width;
  let started = false;
  for (let index = 0; index < x.length; index += 1) {
    const xValue = x[index] ?? Number.NaN;
    const yValue = y[index] ?? Number.NaN;
    if (!Number.isFinite(xValue) || !Number.isFinite(yValue)) {
      continue;
    }
    const px = projectX(xValue, plot, domain, reversed);
    const py = projectY(yValue, plot, domain);
    started ? context.lineTo(px, py) : context.moveTo(px, py);
    started = true;
  }
  context.stroke();
}

function drawGrid(
  context: CanvasRenderingContext2D,
  plot: PlotRect,
  domain: Domain,
  axisTitle: string,
  reversed: boolean,
): void {
  context.strokeStyle = COLORS.grid;
  context.fillStyle = COLORS.muted;
  context.font = "12px Cascadia Mono, Consolas, monospace";
  context.textAlign = "center";
  for (let index = 0; index <= 5; index += 1) {
    const ratio = index / 5;
    const x = plot.left + ratio * plot.width;
    const y = plot.top + ratio * plot.height;
    context.beginPath();
    context.moveTo(x, plot.top);
    context.lineTo(x, plot.top + plot.height);
    context.moveTo(plot.left, y);
    context.lineTo(plot.left + plot.width, y);
    context.stroke();
    const axisRatio = reversed ? 1 - ratio : ratio;
    const xValue = domain.xMin + axisRatio * (domain.xMax - domain.xMin);
    context.fillText(xValue.toPrecision(4), x, plot.top + plot.height + 20);
  }
  context.fillStyle = COLORS.text;
  context.fillText(axisTitle, plot.left + plot.width / 2, plot.top + plot.height + 42);
}

function drawMarkers(
  context: CanvasRenderingContext2D,
  data: LivePayload,
  frameIndex: number,
  wavelength: number,
  twoTheta: Float32Array,
  current: Float32Array,
  plot: PlotRect,
  domain: Domain,
  reversed: boolean,
): void {
  const candidates = [...(data.markers[frameIndex] ?? [])]
    .sort((left, right) => right.intensity - left.intensity)
    .slice(0, 12);
  const occupied: number[] = [];
  context.font = "11px Cascadia Mono, Consolas, monospace";
  context.textAlign = "center";
  for (const marker of candidates) {
    const xValue = transformXValue(marker.twoTheta, wavelength, data.xAxis);
    if (!Number.isFinite(xValue) || xValue < domain.xMin || xValue > domain.xMax) {
      continue;
    }
    const px = projectX(xValue, plot, domain, reversed);
    if (occupied.some((value) => Math.abs(value - px) < 42)) {
      continue;
    }
    const peakIndex = nearestIndex(twoTheta, marker.twoTheta);
    const peakValue = current[peakIndex] ?? 0;
    const peakY = Math.min(plot.top + plot.height, projectY(peakValue, plot, domain));
    const labelY = Math.max(plot.top + 14, peakY - 8);
    context.strokeStyle = COLORS.current;
    context.beginPath();
    context.moveTo(px, labelY + 3);
    context.lineTo(px, peakY);
    context.stroke();
    context.fillStyle = COLORS.text;
    context.fillText(marker.hkl, px, labelY);
    occupied.push(px);
    if (occupied.length >= 8) {
      break;
    }
  }
}

export function canvasCssHeight(cssWidth: number, showDifference: boolean): number {
  const baseHeight = cssWidth <= 520 ? 340 : 420;
  return showDifference ? baseHeight + 50 : baseHeight;
}
export function renderFrame(
  canvas: HTMLCanvasElement,
  data: LivePayload,
  matrix: Float32Array,
  twoTheta: Float32Array,
  frameIndex: number,
  mode: Normalisation,
  showDifference: boolean,
): void {
  const context = canvas.getContext("2d");
  if (context === null) {
    return;
  }
  const pixelRatio = window.devicePixelRatio || 1;
  const cssWidth = Math.max(320, canvas.clientWidth);
  const cssHeight = canvasCssHeight(cssWidth, showDifference);
  canvas.style.height = `${cssHeight}px`;
  canvas.width = Math.round(cssWidth * pixelRatio);
  canvas.height = Math.round(cssHeight * pixelRatio);
  context.scale(pixelRatio, pixelRatio);
  context.fillStyle = COLORS.background;
  context.fillRect(0, 0, cssWidth, cssHeight);
  const plot = { left: 64, top: 22, width: cssWidth - 84, height: cssHeight - 84 };
  const current = normaliseRow(
    rowAt(matrix, frameIndex, data.columns),
    mode,
    data.globalMaximum,
    data.localMaxima[frameIndex] ?? 0,
  );
  const baseline = normaliseRow(
    rowAt(matrix, data.baselineIndex, data.columns),
    mode,
    data.globalMaximum,
    data.localMaxima[data.baselineIndex] ?? 0,
  );
  const difference = new Float32Array(current.length);
  let observedMin = 0;
  let observedMax = 0;
  for (let index = 0; index < current.length; index += 1) {
    difference[index] = (current[index] ?? 0) - (baseline[index] ?? 0);
    observedMin = Math.min(observedMin, difference[index] ?? 0);
    observedMax = Math.max(observedMax, current[index] ?? 0, baseline[index] ?? 0);
  }
  const yMin = data.yAuto && showDifference ? observedMin * 1.08 : data.yAuto ? 0 : data.yMinimum;
  const yMax = data.yAuto ? Math.max(observedMax * 1.08, 1) : data.yMaximum;
  const domain = { xMin: data.xMinimum, xMax: data.xMaximum, yMin, yMax };
  const axisTitle =
    data.xAxis === "2theta"
      ? "2theta (deg)"
      : data.xAxis === "q_primary"
        ? "q_primary (A^-1)"
        : "d_primary (A)";
  const reversed = data.xAxis === "d_primary";
  drawGrid(context, plot, domain, axisTitle, reversed);
  const wavelength = data.wavelengths[frameIndex] ?? 1;
  const currentX = transformX(twoTheta, wavelength, data.xAxis);
  const baselineX = transformX(
    twoTheta,
    data.wavelengths[data.baselineIndex] ?? wavelength,
    data.xAxis,
  );
  drawTrace(context, baselineX, baseline, COLORS.baseline, 1.4, plot, domain, reversed);
  drawTrace(context, currentX, current, COLORS.current, 2, plot, domain, reversed);
  if (showDifference) {
    drawTrace(context, currentX, difference, COLORS.difference, 1.2, plot, domain, reversed);
  }
  drawMarkers(context, data, frameIndex, wavelength, twoTheta, current, plot, domain, reversed);
}
