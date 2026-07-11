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
  applyUiLabels(parentElement, data);

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

function applyUiLabels(
  root: HTMLElement | ShadowRoot,
  data: ComponentArgs["data"],
): void {
  const ui = data.ui;
  if (ui === undefined) {
    return;
  }
  const intensityLabel = requireElement<HTMLElement>(root, "[data-live-intensity-label]");
  if (intensityLabel !== null) {
    const select = intensityLabel.querySelector("select");
    intensityLabel.textContent = ui.intensity + " ";
    if (select !== null) {
      intensityLabel.appendChild(select);
    }
  }
  const optGlobal = requireElement<HTMLOptionElement>(root, "[data-live-opt-global]");
  const optLocal = requireElement<HTMLOptionElement>(root, "[data-live-opt-local]");
  const optModel = requireElement<HTMLOptionElement>(root, "[data-live-opt-model]");
  if (optGlobal !== null) {
    optGlobal.textContent = ui.globalRelative;
  }
  if (optLocal !== null) {
    optLocal.textContent = ui.localRelative;
  }
  if (optModel !== null) {
    optModel.textContent = ui.model;
  }
  const differenceText = requireElement<HTMLElement>(root, "[data-live-difference-text]");
  if (differenceText !== null) {
    differenceText.textContent = ui.difference;
  }
  const legendBaseline = requireElement<HTMLElement>(root, "[data-live-legend-baseline]");
  const legendCurrent = requireElement<HTMLElement>(root, "[data-live-legend-current]");
  const legendDifference = requireElement<HTMLElement>(
    root,
    "[data-live-legend-difference]",
  );
  if (legendBaseline !== null) {
    legendBaseline.textContent = ui.baseline;
  }
  if (legendCurrent !== null) {
    legendCurrent.textContent = ui.current;
  }
  if (legendDifference !== null) {
    legendDifference.textContent = ui.difference;
  }
  const canvas = requireElement<HTMLCanvasElement>(root, "[data-live-canvas]");
  const slider = requireElement<HTMLInputElement>(root, "[data-live-slider]");
  if (canvas !== null) {
    canvas.setAttribute("aria-label", ui.ariaCanvas);
  }
  if (slider !== null) {
    slider.setAttribute("aria-label", ui.ariaSlider);
  }
}

export { clampFrame, normaliseRow, transformX } from "./live-math";
