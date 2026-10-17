import { Easing, Interactive, interpolate, useCurrentFrame } from "remotion";
import { MONO, SANS } from "../fonts";
import { C, HAND, clamp } from "../theme";

export const StepTitle: React.FC<{ step?: string; title: string; sub?: string }> = ({ step, title, sub }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {step ? (
        <Interactive.Div
          name="Step"
          style={{
            fontFamily: MONO,
            fontSize: 26,
            letterSpacing: "0.14em",
            color: C.margin,
            opacity: interpolate(frame, [0, 14], [0, 1], clamp),
          }}
        >
          {step}
        </Interactive.Div>
      ) : null}
      <Interactive.Div
        name="Title"
        style={{
          fontFamily: HAND,
          fontSize: 104,
          lineHeight: 1.25,
          color: C.ink,
          opacity: interpolate(frame, [4, 20], [0, 1], clamp),
          translate: interpolate(frame, [4, 24], ["0px 18px", "0px 0px"], {
            ...clamp,
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        {title}
      </Interactive.Div>
      {sub ? (
        <Interactive.Div
          name="Subtitle"
          style={{
            fontFamily: SANS,
            fontSize: 36,
            lineHeight: 1.35,
            color: C.muted,
            maxWidth: 1450,
            opacity: interpolate(frame, [14, 30], [0, 1], clamp),
          }}
        >
          {sub}
        </Interactive.Div>
      ) : null}
    </div>
  );
};
