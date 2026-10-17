import { AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame } from "remotion";
import { Handwrite } from "../components/Handwrite";
import { Paper } from "../components/Paper";
import { MONO, SANS } from "../fonts";
import { C, WRITING, clamp } from "../theme";

export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 120, justifyContent: "center" }}>
        <Interactive.Div
          name="Eyebrow"
          style={{
            fontFamily: MONO,
            fontSize: 28,
            letterSpacing: "0.14em",
            color: C.muted,
            opacity: interpolate(frame, [0, 18], [0, 1], clamp),
          }}
        >
          CLAUDE OPUS 5.5 · CLAUDE CODE · ONE PROMPT
        </Interactive.Div>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 36, marginTop: 10, marginLeft: -12 }}>
          <Handwrite phrase={WRITING["my notes"]} xh={84} from={10} duration={46} />
          <Handwrite phrase={WRITING["→"]} xh={84} from={58} duration={14} color={C.margin} />
          <Handwrite phrase={WRITING["a font"]} xh={84} from={72} duration={34} />
        </div>
        <Interactive.Div
          name="Hook line"
          style={{
            fontFamily: SANS,
            fontSize: 46,
            lineHeight: 1.35,
            color: C.text,
            maxWidth: 1400,
            marginTop: 6,
            opacity: interpolate(frame, [104, 122], [0, 1], clamp),
            translate: interpolate(frame, [104, 126], ["0px 22px", "0px 0px"], {
              ...clamp,
              easing: Easing.bezier(0.16, 1, 0.3, 1),
            }),
          }}
        >
          I gave Claude my handwritten college notes.
          <br />
          It gave me back my handwriting, as a real font.
        </Interactive.Div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
