export type AxisKind = "2theta" | "q_primary" | "d_primary";
export type Normalisation = "model" | "global" | "local";

export type Marker = {
  readonly hkl: string;
  readonly twoTheta: number;
  readonly intensity: number;
};

export type LivePayload = {
  readonly axisLabel: string;
  readonly axisUnit: string;
  readonly axisValues: readonly number[];
  readonly baselineIndex: number;
  readonly currentIndex: number;
  readonly columns: number;
  readonly matrixF32: string;
  readonly twoThetaF32: string;
  readonly wavelengths: readonly number[];
  readonly localMaxima: readonly number[];
  readonly globalMaximum: number;
  readonly xAxis: AxisKind;
  readonly xMinimum: number;
  readonly xMaximum: number;
  readonly yAuto: boolean;
  readonly yMinimum: number;
  readonly yMaximum: number;
  readonly markers: readonly (readonly Marker[])[];
  readonly disabled: boolean;
};

export type ComponentArgs = {
  readonly data: LivePayload;
  readonly parentElement: HTMLElement | ShadowRoot;
  readonly setStateValue: (name: string, value: number) => void;
};

export type PlotRect = {
  readonly left: number;
  readonly top: number;
  readonly width: number;
  readonly height: number;
};

export type Domain = {
  readonly xMin: number;
  readonly xMax: number;
  readonly yMin: number;
  readonly yMax: number;
};
