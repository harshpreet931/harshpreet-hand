import { loadFont } from "@remotion/fonts";
import { loadFont as loadSans } from "@remotion/google-fonts/IBMPlexSans";
import { loadFont as loadMono } from "@remotion/google-fonts/IBMPlexMono";
import { staticFile } from "remotion";

export const { fontFamily: SANS } = loadSans("normal", {
  weights: ["400", "500", "600"],
  subsets: ["latin"],
});
export const { fontFamily: MONO } = loadMono("normal", {
  weights: ["400", "500"],
  subsets: ["latin"],
});

loadFont({
  family: "Harshpreet Hand",
  url: staticFile("fonts/HarshpreetHand-Regular.woff2"),
  weight: "400",
});
loadFont({
  family: "Harshpreet Hand",
  url: staticFile("fonts/HarshpreetHand-Bold.woff2"),
  weight: "700",
});
