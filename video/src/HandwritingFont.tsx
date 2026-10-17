import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
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

export type HandwritingFontProps = { portfolioUrl: string };

export const HandwritingFont: React.FC<HandwritingFontProps> = ({ portfolioUrl }) => {
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={150} name="Hook">
        <Hook />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence durationInFrames={150} name="Pages">
        <Pages />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence durationInFrames={180} name="Ink">
        <Ink />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence durationInFrames={210} name="Letters">
        <Letters />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence durationInFrames={180} name="Picks">
        <Picks />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence durationInFrames={210} name="Redraw">
        <Redraw />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence durationInFrames={210} name="Quirks">
        <Quirks />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence durationInFrames={180} name="FontBuilt">
        <FontBuilt />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence durationInFrames={165} name="Compare">
        <Compare />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence durationInFrames={270} name="Cost">
        <Cost />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence durationInFrames={165} name="Outro">
        <Outro portfolioUrl={portfolioUrl} />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
