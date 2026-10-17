import assets from "./data/assets.json";
import stats from "./data/session_stats.json";

export const C = {
  paper: "#F4F5FB",
  sheet: "#FBFCFF",
  rule: "#D5DBEE",
  margin: "#D0605E",
  ink: "#1F2F8C",
  inkSoft: "#4D5A93",
  text: "#141A2E",
  muted: "#5A6380",
  highlight: "#FFE45C",
  line: "#DDE2F1",
};

export const HAND = '"Harshpreet Hand", cursive';

export type Stroke = { d: string; len: number };
export type Phrase = {
  text: string;
  width: number;
  glyphs: { ch: string; paths: Stroke[] }[];
};

export const WRITING = assets.writing as Record<string, Phrase>;
export const ASSETS = assets;
export const STATS = stats;

export const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;
