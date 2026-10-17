import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { Paper } from "../components/Paper";
import { StepTitle } from "../components/StepTitle";
import { MONO } from "../fonts";
import { C, HAND, clamp } from "../theme";

const LINES = ["ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz", "0123456789 & @ ? ! ( ) → ←"];
const CHIPS = ["394 glyphs", "2 weights", "up to 3 versions per letter", "4,010 kerning pairs", "TTF + WOFF2"];

export const FontBuilt: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 110, paddingTop: 96 }}>
        <StepTitle step="STEP 6 OF 6" title="Build a real font" />
        <div
          style={{
            fontFamily: HAND,
            fontWeight: 700,
            fontSize: 170,
            lineHeight: 1.2,
            color: C.ink,
            marginTop: -6,
            clipPath: `inset(-20% ${interpolate(frame, [16, 52], [100, 0], { ...clamp, easing: Easing.bezier(0.45, 0, 0.55, 1) })}% -40% 0)`,
          }}
        >
          Harshpreet Hand
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 0, marginTop: 6 }}>
          {LINES.map((line, li) => (
            <div key={li} style={{ fontFamily: HAND, fontSize: 66, lineHeight: 1.45, color: C.ink, letterSpacing: "0.02em" }}>
              {Array.from(line).map((ch, ci) => {
                const at = 44 + li * 10 + ci * 1.1;
                return (
                  <span key={ci} style={{ opacity: interpolate(frame, [at, at + 6], [0, 1], clamp) }}>
                    {ch}
                  </span>
                );
              })}
            </div>
          ))}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 14, marginTop: 22 }}>
          {CHIPS.map((c, i) => (
            <div
              key={c}
              style={{
                fontFamily: MONO,
                fontSize: 28,
                color: C.text,
                backgroundColor: "rgba(31,47,140,0.08)",
                padding: "10px 18px",
                borderRadius: 10,
                opacity: interpolate(frame, [100 + i * 6, 110 + i * 6], [0, 1], clamp),
              }}
            >
              {c}
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
