import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Handwrite } from "../components/Handwrite";
import { Paper } from "../components/Paper";
import { StepTitle } from "../components/StepTitle";
import { SANS } from "../fonts";
import { C, WRITING, clamp } from "../theme";

const QUIRKS: { key: string; label: string }[] = [
  { key: "i", label: "ring-dotted i" },
  { key: "l", label: "looped l" },
  { key: "r", label: "looped r" },
  { key: "d", label: "curled d" },
  { key: "t", label: "half-crossed t" },
  { key: "2", label: "curled 2" },
  { key: "&", label: "crossed-leg &" },
  { key: "→", label: "the margin arrow" },
];

export const Quirks: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 110, paddingTop: 96 }}>
        <StepTitle step="STEP 5 OF 6" title="Keep the quirks" sub="The habits that make it my handwriting stay in the font." />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", rowGap: 10, columnGap: 30, marginTop: -30 }}>
          {QUIRKS.map((q, i) => {
            const at = 24 + i * 17;
            return (
              <div key={q.key} style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <Handwrite phrase={WRITING[q.key]} xh={92} from={at} duration={q.key === "→" ? 16 : 22} color={q.key === "→" ? C.margin : C.ink} />
                <div style={{ fontFamily: SANS, fontSize: 34, color: C.text, marginTop: -104, opacity: interpolate(frame, [at + 8, at + 20], [0, 1], clamp) }}>{q.label}</div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
