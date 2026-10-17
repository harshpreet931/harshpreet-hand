import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Paper } from "../components/Paper";
import { StepTitle } from "../components/StepTitle";
import { MONO } from "../fonts";
import { ASSETS, C, HAND, clamp } from "../theme";

const TW = 102;
const TH = 137;

export const Picks: React.FC = () => {
  const frame = useCurrentFrame();
  const dim = interpolate(frame, [112, 128], [1, 0.16], clamp);
  const ring = interpolate(frame, [118, 146], [1, 0], clamp);
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 110, paddingTop: 96 }}>
        <StepTitle
          step="STEP 3 OF 6"
          title="Keep only the most typical ones"
          sub="Each sample is scored on how typical its shape is and how sharp the photo is."
        />
        <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 26 }}>
          {ASSETS.samples.map((row, r) => (
            <div key={row.ch} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 210, display: "flex", alignItems: "baseline", gap: 14, opacity: interpolate(frame, [22 + r * 6, 32 + r * 6], [0, 1], clamp) }}>
                <span style={{ fontFamily: HAND, fontSize: 76, color: C.ink, width: 50 }}>{row.ch}</span>
                <span style={{ fontFamily: MONO, fontSize: 24, color: C.muted }}>{row.count} found</span>
              </div>
              {row.tiles.map((t, i) => {
                const at = 26 + r * 6 + i * 3;
                return (
                  <div key={i} style={{ position: "relative", width: TW, height: TH, opacity: interpolate(frame, [at, at + 8], [0, 1], clamp) * (t.pick ? 1 : dim) }}>
                    <Img src={staticFile(t.src)} style={{ width: TW, height: TH }} />
                    {t.pick ? (
                      <svg width={TW + 16} height={TH - 20} style={{ position: "absolute", left: -8, top: 8, overflow: "visible" }}>
                        <ellipse
                          cx={(TW + 16) / 2}
                          cy={(TH - 20) / 2}
                          rx={(TW + 6) / 2}
                          ry={(TH - 28) / 2}
                          fill="none"
                          stroke={C.margin}
                          strokeWidth={4}
                          strokeLinecap="round"
                          pathLength={1}
                          strokeDasharray="1 1"
                          strokeDashoffset={ring}
                          transform={`rotate(-8 ${(TW + 16) / 2} ${(TH - 20) / 2})`}
                        />
                      </svg>
                    ) : null}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
