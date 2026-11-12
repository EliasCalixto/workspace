import { loadFont } from "@remotion/google-fonts/Fredoka";
import {
  AbsoluteFill,
  Easing,
  Interactive,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Plant } from "./Plant";

const { fontFamily } = loadFont("normal", { weights: ["600"], subsets: ["latin"] });

const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const Sun = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <Interactive.Div
      name="Sol"
      style={{
        position: "absolute",
        right: 140,
        top: 330,
        width: 220,
        height: 220,
        translate: interpolate(frame, [0, 1.5 * fps], ["0px 300px", "0px 0px"], {
          ...clamp,
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
      }}
    >
      <svg viewBox="-110 -110 220 220" width={220} height={220} style={{ overflow: "visible" }}>
        <g transform={`rotate(${(frame / fps) * 20})`}>
          {Array.from({ length: 12 }).map((_, i) => (
            <rect
              key={i}
              x={-6}
              y={-108}
              width={12}
              height={30}
              rx={6}
              fill="#FFC93C"
              transform={`rotate(${i * 30})`}
            />
          ))}
        </g>
        <circle r={68} fill="#FFD95A" />
      </svg>
    </Interactive.Div>
  );
};

const Cloud = ({ top, speed, offset }: { readonly top: number; readonly speed: number; readonly offset: number }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const x = ((offset + (frame / fps) * speed) % (width + 400)) - 300;

  return (
    <svg
      viewBox="0 0 260 110"
      width={260}
      height={110}
      style={{ position: "absolute", top, left: 0, translate: `${x}px 0px`, opacity: 0.9 }}
    >
      <circle cx={70} cy={70} r={40} fill="#fff" />
      <circle cx={130} cy={50} r={50} fill="#fff" />
      <circle cx={190} cy={70} r={38} fill="#fff" />
      <rect x={70} y={70} width={120} height={40} fill="#fff" />
    </svg>
  );
};

const Hearts = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const start = 4 * fps;
  const period = 2.5 * fps;
  if (frame < start) {
    return null;
  }

  return (
    <>
      {[-220, 190, -140, 250, -260, 150].map((dx, i) => {
        const t = ((frame - start + i * (period / 6)) % period) / period;
        return (
          <svg
            key={i}
            viewBox="0 0 24 22"
            width={56}
            height={52}
            style={{
              position: "absolute",
              left: 960 + dx - 28,
              top: 560,
              translate: `${Math.sin(t * 6 + i) * 25}px ${-t * 300}px`,
              opacity: interpolate(t, [0, 0.15, 0.75, 1], [0, 1, 1, 0]),
              scale: interpolate(t, [0, 0.2], [0.4, 1], clamp),
            }}
          >
            <path
              d="M12 21 C 5 15, 0 11, 0 6 A 6 6 0 0 1 12 4 A 6 6 0 0 1 24 6 C 24 11, 19 15, 12 21 Z"
              fill="#FF6F91"
            />
          </svg>
        );
      })}
    </>
  );
};

const Title = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <Interactive.Div
      name="Título"
      style={{
        position: "absolute",
        top: 110,
        left: 0,
        right: 0,
        textAlign: "center",
        fontFamily,
        fontWeight: 600,
        fontSize: 112,
        color: "#2E6B34",
        textShadow: "0 6px 0 rgba(255,255,255,0.7)",
        opacity: interpolate(frame, [4 * fps, 4.6 * fps], [0, 1], clamp),
        scale: interpolate(frame, [4 * fps, 4.8 * fps], [0.6, 1], {
          ...clamp,
          easing: Easing.spring({ damping: 10 }),
          output: "perceptual-scale",
        }),
      }}
    >
      ¡Hola! Soy una plantita feliz
    </Interactive.Div>
  );
};

export const PlantitaFeliz = () => {
  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, #8FD3FF 0%, #CDEFFF 65%, #FFF6D8 100%)",
      }}
    >
      <Sun />
      <Cloud top={330} speed={60} offset={100} />
      <Cloud top={500} speed={40} offset={1200} />
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: -100,
          right: -100,
          height: 230,
          background: "#9BD770",
          borderRadius: "50% 50% 0 0",
        }}
      />
      <Hearts />
      <Interactive.Div
        name="Plantita"
        style={{
          position: "absolute",
          left: 660,
          top: 200,
          width: 600,
          height: 840,
        }}
      >
        <Plant />
      </Interactive.Div>
      <Title />
    </AbsoluteFill>
  );
};
