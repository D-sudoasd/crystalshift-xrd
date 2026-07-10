import { clampFrame, decodeFloat32 } from "./live-math";
import { renderFrame } from "./live-drawing";
import type { ComponentArgs, Normalisation } from "./live-types";

function requireElement<T extends Element>(
  root: HTMLElement | ShadowRoot,
  selector: string,
): T | null {
  return root.querySelector<T>(selector);
}

function selectedNormalisation(select: HTMLSelectElement): Normalisation {
  if (select.value === "model" || select.value === "local") {
    return select.value;
  }
  return "global";
}

export default function liveComponent(component: ComponentArgs): () => void {
  const { data, parentElement, setStateValue } = component;
  const canvas = requireElement<HTMLCanvasElement>(parentElement, "[data-live-canvas]");
  const slider = requireElement<HTMLInputElement>(parentElement, "[data-live-slider]");
  const valueLabel = requireElement<HTMLElement>(parentElement, "[data-live-value]");
  const modeSelect = requireElement<HTMLSelectElement>(
    parentElement,
    "[data-live-normalisation]",
  );
  const differenceToggle = requireElement<HTMLInputElement>(
    parentElement,
    "[data-live-difference]",
  );
  if (
    canvas === null ||
    slider === null ||
    valueLabel === null ||
    modeSelect === null ||
    differenceToggle === null
  ) {
    return () => undefined;
  }

  const matrix = decodeFloat32(data.matrixF32);
  const twoTheta = decodeFloat32(data.twoThetaF32);
  let frameIndex = clampFrame(data.currentIndex, data.axisValues.length);
  let animationFrame = 0;
  slider.min = "0";
  slider.max = String(Math.max(0, data.axisValues.length - 1));
  slider.step = "1";
  slider.value = String(frameIndex);
  slider.disabled = data.disabled;
  modeSelect.disabled = data.disabled;
  differenceToggle.disabled = data.disabled;

  const draw = (): void => {
    const value = data.axisValues[frameIndex] ?? 0;
    valueLabel.textContent =
      data.axisLabel + ": " + value.toPrecision(7) + " " + data.axisUnit;
    renderFrame(
      canvas,
      data,
      matrix,
      twoTheta,
      frameIndex,
      selectedNormalisation(modeSelect),
      differenceToggle.checked,
    );
  };
  const scheduleDraw = (): void => {
    cancelAnimationFrame(animationFrame);
    animationFrame = requestAnimationFrame(draw);
  };
  const onInput = (): void => {
    frameIndex = clampFrame(Number(slider.value), data.axisValues.length);
    scheduleDraw();
  };
  const onCommit = (): void => {
    setStateValue("selected_index", frameIndex);
  };

  slider.addEventListener("input", onInput);
  slider.addEventListener("change", onCommit);
  modeSelect.addEventListener("change", scheduleDraw);
  differenceToggle.addEventListener("change", scheduleDraw);
  const observer = new ResizeObserver(scheduleDraw);
  observer.observe(canvas);
  draw();

  return () => {
    cancelAnimationFrame(animationFrame);
    observer.disconnect();
    slider.removeEventListener("input", onInput);
    slider.removeEventListener("change", onCommit);
    modeSelect.removeEventListener("change", scheduleDraw);
    differenceToggle.removeEventListener("change", scheduleDraw);
  };
}

export { clampFrame, normaliseRow, transformX } from "./live-math";
