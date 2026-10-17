import "./index.css";
import { Composition, Folder } from "remotion";
import { HandwritingFont } from "./HandwritingFont";
import "./fonts";
import { Compare } from "./scenes/Compare";
import { Cost } from "./scenes/Cost";
import { FontBuilt } from "./scenes/FontBuilt";
import { Hook } from "./scenes/Hook";
import { Ink } from "./scenes/Ink";
import { Letters } from "./scenes/Letters";
import { Outro } from "./scenes/Outro";
import { Pages } from "./scenes/Pages";
import { Picks } from "./scenes/Picks";
import { Quirks } from "./scenes/Quirks";
import { Redraw } from "./scenes/Redraw";

// 150+150+180+210+180+210+210+180+165+270+165 = 2070 frames, minus 10 fades x 12 = 1950 (65 s)
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="HandwritingFont"
        component={HandwritingFont}
        durationInFrames={1950}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ portfolioUrl: "" }}
      />
      <Folder name="Scenes">
        <Composition id="Hook" component={Hook} durationInFrames={150} fps={30} width={1920} height={1080} />
        <Composition id="Pages" component={Pages} durationInFrames={150} fps={30} width={1920} height={1080} />
        <Composition id="Ink" component={Ink} durationInFrames={180} fps={30} width={1920} height={1080} />
        <Composition id="Letters" component={Letters} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="Picks" component={Picks} durationInFrames={180} fps={30} width={1920} height={1080} />
        <Composition id="Redraw" component={Redraw} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="Quirks" component={Quirks} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="FontBuilt" component={FontBuilt} durationInFrames={180} fps={30} width={1920} height={1080} />
        <Composition id="Compare" component={Compare} durationInFrames={165} fps={30} width={1920} height={1080} />
        <Composition id="Cost" component={Cost} durationInFrames={270} fps={30} width={1920} height={1080} />
        <Composition id="Outro" component={Outro} durationInFrames={165} fps={30} width={1920} height={1080} defaultProps={{ portfolioUrl: "" }} />
      </Folder>
    </>
  );
};
