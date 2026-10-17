import { AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame } from "remotion";
import { Count } from "../components/Count";
import { Paper } from "../components/Paper";
import { MONO, SANS } from "../fonts";
import { C, HAND, STATS, clamp } from "../theme";

const minutes = Math.round(STATS.duration_seconds / 60);
const cacheShare = Math.round((STATS.tokens.cache_read / STATS.total_tokens) * 100);
const P = STATS.prices_per_mtok;

const ROWS: { value: number; fmt: (n: number) => string; label: string }[] = [
  { value: minutes, fmt: (n) => `${Math.floor(n / 60)}h ${String(Math.round(n) % 60).padStart(2, "0")}m`, label: "one prompt → finished font" },
  { value: STATS.api_calls, fmt: (n) => `${Math.round(n)}`, label: "model calls" },
  { value: STATS.tool_calls, fmt: (n) => `${Math.round(n)}`, label: "tool calls" },
  { value: STATS.total_tokens, fmt: (n) => `${(n / 1e6).toFixed(1)}M`, label: `tokens processed (${cacheShare}% cached)` },
  { value: STATS.tokens.output, fmt: (n) => `${Math.round(n / 1000)}K`, label: "tokens written by Claude" },
];

export const Cost: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ paddingLeft: 220, paddingRight: 110, paddingTop: 96 }}>
        <Interactive.Div name="Title" style={{ fontFamily: HAND, fontSize: 104, lineHeight: 1.25, color: C.ink, opacity: interpolate(frame, [0, 16], [0, 1], clamp) }}>
          So what did it cost?
        </Interactive.Div>
        <Interactive.Div name="Subtitle" style={{ fontFamily: SANS, fontSize: 34, color: C.muted, opacity: interpolate(frame, [10, 26], [0, 1], clamp) }}>
          Measured from the Claude Code session log for this build, not estimated.
        </Interactive.Div>
        <div style={{ display: "flex", gap: 70, marginTop: 34 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, width: 860 }}>
            {ROWS.map((r, i) => {
              const at = 22 + i * 14;
              return (
                <div key={i} style={{ display: "flex", alignItems: "baseline", gap: 26, opacity: interpolate(frame, [at, at + 10], [0, 1], clamp) }}>
                  <span style={{ fontFamily: HAND, fontSize: 84, lineHeight: 1.25, color: C.ink, width: 290, textAlign: "right", flexShrink: 0 }}>
                    <Count to={r.value} from={at} duration={50} format={r.fmt} />
                  </span>
                  <span style={{ fontFamily: SANS, fontSize: 31, lineHeight: 1.3, color: C.text }}>{r.label}</span>
                </div>
              );
            })}
          </div>
          <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: 8, opacity: interpolate(frame, [96, 110], [0, 1], clamp) }}>
            <div style={{ fontFamily: MONO, fontSize: 24, letterSpacing: "0.12em", color: C.margin }}>API COST · CLAUDE OPUS 5.5</div>
            <div style={{ position: "relative", display: "inline-block", alignSelf: "flex-start" }}>
              <div
                style={{
                  position: "absolute",
                  left: -14,
                  top: "42%",
                  height: "44%",
                  width: `${interpolate(frame, [150, 172], [0, 108], { ...clamp, easing: Easing.bezier(0.3, 0, 0.2, 1) })}%`,
                  backgroundColor: C.highlight,
                  borderRadius: 10,
                  rotate: "-1.5deg",
                  opacity: 0.9,
                }}
              />
              <span style={{ position: "relative", fontFamily: HAND, fontWeight: 700, fontSize: 210, lineHeight: 1.1, color: C.ink }}>
                <Count to={STATS.cost_total} from={104} duration={46} format={(n) => `$${n.toFixed(2)}`} />
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 18, opacity: interpolate(frame, [176, 190], [0, 1], clamp) }}>
              <span style={{ position: "relative", fontFamily: HAND, fontSize: 76, color: C.muted }}>
                ${STATS.cost_without_caching.toFixed(2)}
                <span
                  style={{
                    position: "absolute",
                    left: -6,
                    top: "52%",
                    height: 5,
                    borderRadius: 3,
                    backgroundColor: C.margin,
                    rotate: "-4deg",
                    width: `${interpolate(frame, [192, 206], [0, 106], clamp)}%`,
                  }}
                />
              </span>
              <span style={{ fontFamily: SANS, fontSize: 30, color: C.muted }}>without prompt caching</span>
            </div>
          </div>
        </div>
        <div style={{ fontFamily: MONO, fontSize: 22, color: C.muted, marginTop: 30, opacity: interpolate(frame, [200, 216], [0, 1], clamp) }}>
          Priced per 1M tokens: ${P.input} input · ${P.output} output · ${P.cache_read.toFixed(2)} cache read · ${P.cache_write_1h} cache write (1h)
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
