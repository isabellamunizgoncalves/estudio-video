import React from "react";
import { Composition } from "remotion";
import { Video } from "./Video";
import type { Timeline } from "./tipos";
import { TEMAS_EXEMPLO, timelineExemplo } from "./exemplo";

const metadados = ({ props }: { props: { timeline: Timeline } }) => ({
  durationInFrames: props.timeline.duracaoQuadros,
  fps: props.timeline.fps,
  width: props.timeline.largura,
  height: props.timeline.altura,
});

// "Video" recebe o timeline.json do projeto via --props (ferramentas/edicao/render.py).
// "Exemplo-<canal>" mostra o design de cada canal sem mídia nem voz.
export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Video"
      component={Video}
      defaultProps={{ timeline: timelineExemplo(TEMAS_EXEMPLO.retrovisage, "retrovisage") }}
      calculateMetadata={metadados}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
    />
    {Object.entries(TEMAS_EXEMPLO).map(([canal, tema]) => (
      <Composition
        key={canal}
        id={`Exemplo-${canal}`}
        component={Video}
        defaultProps={{ timeline: timelineExemplo(tema, canal) }}
        calculateMetadata={metadados}
        durationInFrames={450}
        fps={30}
        width={1920}
        height={1080}
      />
    ))}
  </>
);
