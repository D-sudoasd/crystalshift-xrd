import { describe, expect, test } from "bun:test";

import { canvasCssHeight } from "./live-drawing";
import { clampFrame, normaliseRow, transformX } from "./live-math";

describe("live component calculations", () => {
  test("normalises model, global, and local intensity without mutating input", () => {
    const row = new Float32Array([0, 2, 4]);

    expect(Array.from(normaliseRow(row, "model", 8, 4))).toEqual([0, 2, 4]);
    expect(Array.from(normaliseRow(row, "global", 8, 4))).toEqual([0, 25, 50]);
    expect(Array.from(normaliseRow(row, "local", 8, 4))).toEqual([0, 50, 100]);
    expect(Array.from(row)).toEqual([0, 2, 4]);
  });

  test("transforms two-theta to q and d for the frame wavelength", () => {
    const twoTheta = new Float32Array([10, 20]);
    const wavelength = 0.5;

    const q = transformX(twoTheta, wavelength, "q_primary");
    const d = transformX(twoTheta, wavelength, "d_primary");

    expect(q[0]).toBeCloseTo((4 * Math.PI * Math.sin((5 * Math.PI) / 180)) / wavelength);
    expect(d[0]).toBeCloseTo(wavelength / (2 * Math.sin((5 * Math.PI) / 180)));
    expect(d[1]).toBeLessThan(d[0] ?? 0);
  });

  test("clamps frame indices to the prepared matrix", () => {
    expect(clampFrame(-1, 5)).toBe(0);
    expect(clampFrame(2, 5)).toBe(2);
    expect(clampFrame(7, 5)).toBe(4);
  });

  test("expands desktop and mobile Canvas height for the difference trace", () => {
    expect(canvasCssHeight(1280, false)).toBe(420);
    expect(canvasCssHeight(1280, true)).toBe(470);
    expect(canvasCssHeight(375, false)).toBe(340);
    expect(canvasCssHeight(375, true)).toBe(390);
  });
});
