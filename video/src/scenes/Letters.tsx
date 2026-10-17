import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Count } from "../components/Count";
import { Paper } from "../components/Paper";
import { StepTitle } from "../components/StepTitle";
import { MONO, SANS } from "../fonts";
import { ASSETS, C, HAND, clamp } from "../theme";

const PICK = [0, 1, 3, 4, 5, 7]; // Interconnection, Handshake, request, Jitter, Queue, reject
const H = 78;

export const Letters: React.FC = () => {
  const frame = useCurrentFrame();
  const words = PICK.map((i) => ASSETS.words[i]);
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 110, paddingTop: 96 }}>
        <StepTitle
          step="STEP 2 OF 6"
          title="Read my handwriting"
          sub="Claude read the words in the photos, then matched every pen stroke to a letter."
        />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", columnGap: 60, rowGap: 26, marginTop: 40 }}>
          {words.map((w, k) => {
            const t0 = 26 + k * 12;
            const segAt = t0 + 34;
            const typeAt = t0 + 44;
            const shown = Math.round(interpolate(frame, [typeAt, typeAt + 14], [0, w.label.length], clamp));
            const dw = (w.w * H) / w.h;
            return (
              <div key={k} style={{ display: "flex", alignItems: "center", gap: 22, opacity: interpolate(frame, [t0, t0 + 10], [0, 1], clamp) }}>
                <div style={{ position: "relative", width: Math.min(dw, 400), height: H, borderRadius: 8, overflow: "hidden", flexShrink: 0, boxShadow: "0 4px 14px rgba(20,26,46,0.12)" }}>
                  <Img src={staticFile(w.img)} style={{ position: "absolute", height: H, width: dw, maxWidth: "none" }} />
                  <div style={{ position: "absolute", inset: 0, backgroundColor: C.sheet, opacity: interpolate(frame, [segAt, segAt + 8], [0, 1], clamp) }}>
                    <Img src={staticFile(w.seg)} style={{ height: H, width: dw, maxWidth: "none" }} />
                  </div>
                </div>
                <div style={{ fontFamily: SANS, fontSize: 34, color: C.margin, opacity: interpolate(frame, [typeAt - 4, typeAt], [0, 1], clamp) }}>→</div>
                <div style={{ fontFamily: MONO, fontSize: 38, color: C.ink, whiteSpace: "nowrap" }}>
                  {w.label.slice(0, shown)}
                  <span style={{ opacity: shown < w.label.length && frame >= typeAt ? 1 : 0 }}>▍</span>
                </div>
              </div>
            );
          })}
        </div>
        <div style={{ display: "flex", gap: 90, marginTop: 42, alignItems: "baseline" }}>
          {[
            { n: 704, label: "words read", at: 60 },
            { n: 2479, label: "letters found", at: 72 },
          ].map((s) => (
            <div key={s.label} style={{ display: "flex", alignItems: "baseline", gap: 18, opacity: interpolate(frame, [s.at, s.at + 12], [0, 1], clamp) }}>
              <span style={{ fontFamily: HAND, fontSize: 110, color: C.ink, lineHeight: 1 }}>
                <Count to={s.n} from={s.at} duration={80} />
              </span>
              <span style={{ fontFamily: SANS, fontSize: 36, color: C.muted }}>{s.label}</span>
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
