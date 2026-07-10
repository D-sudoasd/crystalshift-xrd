import type { AxisKind, Normalisation } from "./live-types";

export function clampFrame(index: number, count: number): number {
  return Math.max(0, Math.min(Math.round(index), Math.max(0, count - 1)));
}

export function normaliseRow(
  row: Float32Array,
  mode: Normalisation,
  globalMaximum: number,
  localMaximum: number,
): Float32Array {
  if (mode === "model") {
    return row.slice();
  }
  const maximum = mode === "global" ? globalMaximum : localMaximum;
  if (maximum <= 0) {
    return new Float32Array(row.length);
  }
  const output = new Float32Array(row.length);
  for (let index = 0; index < row.length; index += 1) {
    output[index] = ((row[index] ?? 0) / maximum) * 100;
  }
  return output;
}

export function transformXValue(
  twoTheta: number,
  wavelength: number,
  axis: AxisKind,
): number {
  if (axis === "2theta") {
    return twoTheta;
  }
  const theta = (twoTheta * Math.PI) / 360;
  const q = (4 * Math.PI * Math.sin(theta)) / wavelength;
  return axis === "q_primary" ? q : q > 0 ? (2 * Math.PI) / q : Number.NaN;
}

export function transformX(
  twoTheta: Float32Array,
  wavelength: number,
  axis: AxisKind,
): Float32Array {
  const output = new Float32Array(twoTheta.length);
  for (let index = 0; index < twoTheta.length; index += 1) {
    output[index] = transformXValue(twoTheta[index] ?? Number.NaN, wavelength, axis);
  }
  return output;
}

export function decodeFloat32(encoded: string): Float32Array {
  const binary = atob(encoded);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Float32Array(bytes.buffer);
}

export function rowAt(matrix: Float32Array, row: number, columns: number): Float32Array {
  const start = row * columns;
  return matrix.slice(start, start + columns);
}

export function nearestIndex(values: Float32Array, target: number): number {
  let low = 0;
  let high = values.length - 1;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if ((values[middle] ?? Number.POSITIVE_INFINITY) < target) {
      low = middle + 1;
    } else {
      high = middle;
    }
  }
  if (low === 0) {
    return 0;
  }
  const before = values[low - 1] ?? target;
  const after = values[low] ?? target;
  return Math.abs(before - target) <= Math.abs(after - target) ? low - 1 : low;
}
