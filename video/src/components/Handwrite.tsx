import { Easing, interpolate, useCurrentFrame } from "remotion";
import { C, Phrase, clamp } from "../theme";

// Draws a phrase stroke by stroke using the font's own pen centrelines
// (x-height units, baseline at y=0). Strokes are written in order with a
// short pen-lift between them.
const TOP = 2.05;
const BOTTOM = 1.45;
const LIFT = 0.28;

export const Handwrite: React.FC<{
  phrase: Phrase;
  xh: number;
  from: number;
  duration: number;
  color?: string;
  nib?: number;
}> = ({ phrase, xh, from, duration, color = C.ink, nib = 0.13 }) => {
  const frame = useCurrentFrame();
  const strokes = phrase.glyphs.flatMap((g) => g.paths);
  const total = strokes.reduce((s, p) => s + p.len + LIFT, 0);
  const progress = interpolate(frame, [from, from + duration], [0, total], {
    ...clamp,
    easing: Easing.bezier(0.33, 0.1, 0.4, 1),
  });
  let acc = 0;
  const w = phrase.width + 0.3;
  return (
    <svg
      width={w * xh}
      height={(TOP + BOTTOM) * xh}
      viewBox={`-0.15 ${-TOP} ${w} ${TOP + BOTTOM}`}
      style={{ overflow: "visible", display: "block" }}
    >
      {strokes.map((p, i) => {
        const start = acc;
        acc += p.len + LIFT;
        const shown = Math.min(Math.max(progress - start, 0), p.len);
        return (
          <path
            key={i}
            d={p.d}
            fill="none"
            stroke={color}
            strokeWidth={nib}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray={`${p.len} ${p.len + 1}`}
            strokeDashoffset={p.len - shown}
            opacity={shown > 0 ? 1 : 0}
          />
        );
      })}
    </svg>
  );
};
