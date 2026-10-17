import { Easing, interpolate, useCurrentFrame } from "remotion";
import { clamp } from "../theme";

export const Count: React.FC<{
  to: number;
  from: number;
  duration: number;
  format?: (n: number) => string;
}> = ({ to, from, duration, format = (n) => Math.round(n).toLocaleString("en-US") }) => {
  const frame = useCurrentFrame();
  const n = interpolate(frame, [from, from + duration], [0, to], {
    ...clamp,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  return <span style={{ fontVariantNumeric: "tabular-nums" }}>{format(n)}</span>;
};
