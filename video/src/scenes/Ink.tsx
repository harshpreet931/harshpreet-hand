import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Paper } from "../components/Paper";
import { StepTitle } from "../components/StepTitle";
import { MONO } from "../fonts";
import { C, clamp } from "../theme";

const STAGES = ["phone photo", "blue-ink signal", "clean ink"];

export const Ink: React.FC = () => {
  const frame = useCurrentFrame();
  const w1 = interpolate(frame, [48, 84], [100, 0], clamp);
  const w2 = interpolate(frame, [108, 144], [100, 0], clamp);
  const active = frame < 66 ? 0 : frame < 126 ? 1 : 2;
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 110, paddingTop: 96 }}>
        <StepTitle
          step="STEP 1 OF 6"
          title="Separate the pen from the paper"
          sub="Ruled lines, the red margin and ink bleeding through from the back of the page: all removed."
        />
        <div
          style={{
            position: "relative",
            width: 1590,
            height: 288,
            marginTop: 44,
            borderRadius: 14,
            overflow: "hidden",
            boxShadow: "0 10px 30px rgba(20,26,46,0.14)",
            opacity: interpolate(frame, [16, 32], [0, 1], clamp),
          }}
        >
          <Img src={staticFile("ink/photo.jpg")} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} />
          <div style={{ position: "absolute", inset: 0, backgroundColor: "#FFFFFF", clipPath: `inset(0 ${w1}% 0 0)` }}>
            <Img src={staticFile("ink/signal.png")} style={{ width: "100%", height: "100%" }} />
          </div>
          <div style={{ position: "absolute", inset: 0, backgroundColor: C.sheet, clipPath: `inset(0 ${w2}% 0 0)` }}>
            <Img src={staticFile("ink/mask.png")} style={{ width: "100%", height: "100%" }} />
          </div>
          {[w1, w2].map((w, i) =>
            w > 0 && w < 100 ? (
              <div key={i} style={{ position: "absolute", top: 0, bottom: 0, left: `${100 - w}%`, width: 4, backgroundColor: C.margin }} />
            ) : null,
          )}
        </div>
        <div style={{ display: "flex", gap: 18, marginTop: 28 }}>
          {STAGES.map((s, i) => (
            <div
              key={s}
              style={{
                fontFamily: MONO,
                fontSize: 30,
                padding: "10px 20px",
                borderRadius: 999,
                color: i === active ? C.sheet : C.muted,
                backgroundColor: i === active ? C.ink : "rgba(31,47,140,0.07)",
              }}
            >
              {i + 1}. {s}
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
