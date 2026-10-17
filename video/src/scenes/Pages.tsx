import { AbsoluteFill, Easing, Img, Interactive, interpolate, random, staticFile, useCurrentFrame } from "remotion";
import { Count } from "../components/Count";
import { Paper } from "../components/Paper";
import { SANS } from "../fonts";
import { C, HAND, clamp } from "../theme";

const PAGES = Array.from({ length: 120 }, (_, i) => i);

export const Pages: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 110, paddingTop: 96 }}>
        <Interactive.Div name="Title" style={{ fontFamily: HAND, fontSize: 104, lineHeight: 1.25, color: C.ink }}>
          <Count to={120} from={6} duration={80} /> pages of notes
        </Interactive.Div>
        <Interactive.Div
          name="Subtitle"
          style={{
            fontFamily: SANS,
            fontSize: 36,
            color: C.muted,
            opacity: interpolate(frame, [10, 28], [0, 1], clamp),
          }}
        >
          Computer Networks, the full syllabus. Photographed on a phone, straight from the notebook.
        </Interactive.Div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(20, 1fr)",
            gap: 8,
            marginTop: 40,
            scale: interpolate(frame, [0, 150], [1, 1.035], clamp),
            transformOrigin: "50% 0%",
          }}
        >
          {PAGES.map((i) => {
            const delay = 6 + random(`page-${i}`) * 70;
            return (
              <Img
                key={i}
                src={staticFile(`pages/p${String(i).padStart(3, "0")}.jpg`)}
                style={{
                  width: "100%",
                  aspectRatio: "3 / 4",
                  objectFit: "cover",
                  borderRadius: 4,
                  boxShadow: "0 2px 6px rgba(20,26,46,0.18)",
                  opacity: interpolate(frame, [delay, delay + 10], [0, 1], clamp),
                  scale: interpolate(frame, [delay, delay + 14], [0.82, 1], {
                    ...clamp,
                    easing: Easing.bezier(0.16, 1, 0.3, 1),
                  }),
                  rotate: `${(random(`rot-${i}`) - 0.5) * 3}deg`,
                }}
              />
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
