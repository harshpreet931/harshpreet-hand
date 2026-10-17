import { AbsoluteFill, Img, Interactive, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Paper } from "../components/Paper";
import { MONO } from "../fonts";
import { C, HAND, clamp } from "../theme";

const TYPED = [
  "A conceptual model that describes how data is communicated",
  "over a network. It is a 7 layer model. First introduced in",
  "1970s. Made by ISO.",
];

export const Compare: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 110, paddingTop: 96 }}>
        <Interactive.Div name="Title" style={{ fontFamily: HAND, fontSize: 104, lineHeight: 1.25, color: C.ink, opacity: interpolate(frame, [0, 16], [0, 1], clamp) }}>
          Same sentence: notebook vs. font
        </Interactive.Div>
        <div style={{ marginTop: 26, opacity: interpolate(frame, [12, 26], [0, 1], clamp) }}>
          <div style={{ fontFamily: MONO, fontSize: 24, letterSpacing: "0.12em", color: C.margin, marginBottom: 10 }}>MY NOTEBOOK · PAGE 5</div>
          <Img src={staticFile("notes-sample.jpg")} style={{ width: 1590, borderRadius: 12, boxShadow: "0 10px 30px rgba(20,26,46,0.14)" }} />
        </div>
        <div style={{ marginTop: 34, opacity: interpolate(frame, [34, 44], [0, 1], clamp) }}>
          <div style={{ fontFamily: MONO, fontSize: 24, letterSpacing: "0.12em", color: C.margin, marginBottom: 6 }}>TYPED IN HARSHPREET HAND</div>
          {TYPED.map((line, i) => (
            <div
              key={i}
              style={{
                fontFamily: HAND,
                fontSize: 60,
                lineHeight: 1.45,
                color: C.ink,
                whiteSpace: "nowrap",
                clipPath: `inset(-30% ${interpolate(frame, [44 + i * 24, 68 + i * 24], [100, 0], clamp)}% -60% 0)`,
              }}
            >
              {line}
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
