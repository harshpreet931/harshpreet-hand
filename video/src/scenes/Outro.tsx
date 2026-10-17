import { AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame } from "remotion";
import { Handwrite } from "../components/Handwrite";
import { Paper } from "../components/Paper";
import { MONO, SANS } from "../fonts";
import { C, HAND, WRITING, clamp } from "../theme";

export const Outro: React.FC<{ portfolioUrl: string }> = ({ portfolioUrl }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 110, justifyContent: "center" }}>
        <div
          style={{
            fontFamily: HAND,
            fontWeight: 700,
            fontSize: 132,
            lineHeight: 1.25,
            color: C.ink,
            clipPath: `inset(-30% ${interpolate(frame, [8, 58], [100, 0], { ...clamp, easing: Easing.bezier(0.45, 0, 0.55, 1) })}% -40% 0)`,
          }}
        >
          Now it's a theme
          <br />
          on my portfolio.
        </div>
        <Interactive.Div
          name="Built with"
          style={{
            fontFamily: SANS,
            fontSize: 44,
            color: C.text,
            marginTop: 26,
            opacity: interpolate(frame, [62, 80], [0, 1], clamp),
          }}
        >
          Built from one prompt with Claude Opus 5.5 in Claude Code.
        </Interactive.Div>
        {portfolioUrl ? (
          <div style={{ fontFamily: MONO, fontSize: 40, color: C.margin, marginTop: 18, opacity: interpolate(frame, [74, 90], [0, 1], clamp) }}>
            {portfolioUrl}
          </div>
        ) : null}
        <div style={{ position: "absolute", right: 120, bottom: 70 }}>
          <Handwrite phrase={WRITING["Harshpreet Hand"]} xh={30} from={84} duration={50} color={C.inkSoft} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
