import React from "react";
import { Composition } from "remotion";
import { Video } from "./Video";
import type { Timeline } from "./tipos";
import { timelineExemplo } from "./exemplo";

// O vídeo inteiro vem do timeline.json passado em --props (veja ferramentas/edicao/render.py).
// Sem props, o Studio abre um exemplo só com motion graphics (sem mídia nem voz).
export const RemotionRoot: React.FC = () => (
  <Composition
    id="Video"
    component={Video}
    defaultProps={{ timeline: timelineExemplo as Timeline }}
    calculateMetadata={({ props }) => ({
      durationInFrames: props.timeline.duracaoQuadros,
      fps: props.timeline.fps,
      width: props.timeline.largura,
      height: props.timeline.altura,
    })}
    durationInFrames={300}
    fps={30}
    width={1920}
    height={1080}
  />
);
