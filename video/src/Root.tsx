import React from "react";
import {Composition} from "remotion";
import {PromisesVideo} from "./PromisesVideo";

export const Root: React.FC = () => (
  <Composition id="PromisesVideo" component={PromisesVideo} durationInFrames={1800} fps={30} width={1920} height={1080} />
);
