import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Paper } from "../components/Paper";
import { StepTitle } from "../components/StepTitle";
import { MONO, SANS } from "../fonts";
import { ASSETS, C, clamp } from "../theme";

const R = ASSETS.redraw;
const PH = 420;
const path = R.paths[0] as number[][];
const d = "M" + path.map(([x, y]) => `${x} ${y}`).join(" L");
const len = path.slice(1).reduce((s, p, i) => s + Math.hypot(p[0] - path[i][0], p[1] - path[i][1]), 0);
const bw = (R.bitmap.w * PH) / R.bitmap.h;

const Panel: React.FC<{ at: number; label: string; children: React.ReactNode }> = ({ at, label, children }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 18,
        opacity: interpolate(frame, [at, at + 12], [0, 1], clamp),
        translate: interpolate(frame, [at, at + 16], ["0px 20px", "0px 0px"], { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) }),
      }}
    >
      <div style={{ width: 300, height: 470, borderRadius: 16, backgroundColor: C.sheet, boxShadow: "0 8px 26px rgba(20,26,46,0.12)", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
        {children}
      </div>
      <div style={{ fontFamily: MONO, fontSize: 28, color: C.muted }}>{label}</div>
    </div>
  );
};

const Arrow: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ fontFamily: SANS, fontSize: 60, color: C.margin, marginBottom: 50, opacity: interpolate(frame, [at, at + 8], [0, 1], clamp) }}>→</div>
  );
};

export const Redraw: React.FC = () => {
  const frame = useCurrentFrame();
  const trace = interpolate(frame, [92, 128], [len, 0], { ...clamp, easing: Easing.bezier(0.45, 0, 0.55, 1) });
  const nib = interpolate(frame, [136, 172], [len, 0], { ...clamp, easing: Easing.bezier(0.45, 0, 0.55, 1) });
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 110, paddingTop: 96 }}>
        <StepTitle
          step="STEP 4 OF 6"
          title="Trace the pen, then redraw it"
          sub="Photos blur a ballpoint line, so each letter becomes the path the pen took."
        />
        <div style={{ display: "flex", alignItems: "center", gap: 26, marginTop: 40 }}>
          <Panel at={24} label={`photo · ${R.photo.src_h - 8} px tall`}>
            <Img src={staticFile("redraw/photo.png")} style={{ height: PH, imageRendering: "pixelated" }} />
          </Panel>
          <Arrow at={46} />
          <Panel at={50} label="ink shape">
            <Img src={staticFile("redraw/bitmap.png")} style={{ height: PH }} />
          </Panel>
          <Arrow at={80} />
          <Panel at={84} label="pen path">
            <div style={{ position: "relative", width: bw, height: PH }}>
              <Img src={staticFile("redraw/bitmap.png")} style={{ position: "absolute", height: PH, opacity: 0.18 }} />
              <svg viewBox={`0 0 ${R.bitmap.w} ${R.bitmap.h}`} width={bw} height={PH} style={{ position: "absolute", overflow: "visible" }}>
                <path d={d} fill="none" stroke={C.margin} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={`${len} ${len + 1}`} strokeDashoffset={trace} />
              </svg>
            </div>
          </Panel>
          <Arrow at={126} />
          <Panel at={130} label="one steady nib">
            <svg viewBox={`0 0 ${R.bitmap.w} ${R.bitmap.h}`} width={bw} height={PH} style={{ overflow: "visible" }}>
              <path d={d} fill="none" stroke={C.ink} strokeWidth={13} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={`${len} ${len + 1}`} strokeDashoffset={nib} opacity={nib < len ? 1 : 0} />
            </svg>
          </Panel>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
