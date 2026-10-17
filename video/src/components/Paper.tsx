import { AbsoluteFill } from "remotion";
import { C } from "../theme";

// Notebook paper: ruled lines every 72px and a double red margin, like the notes.
export const Paper: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: C.paper,
        backgroundImage: `repeating-linear-gradient(to bottom, transparent 0px, transparent 71px, ${C.rule} 71px, ${C.rule} 72px)`,
        backgroundPosition: "0px 30px",
      }}
    >
      <div style={{ position: "absolute", left: 150, top: 0, bottom: 0, width: 3, backgroundColor: C.margin, opacity: 0.55 }} />
      <div style={{ position: "absolute", left: 158, top: 0, bottom: 0, width: 1.5, backgroundColor: C.margin, opacity: 0.35 }} />
      <AbsoluteFill
        style={{
          background: "radial-gradient(ellipse at 50% 42%, rgba(255,255,255,0) 58%, rgba(31,47,140,0.07) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};
