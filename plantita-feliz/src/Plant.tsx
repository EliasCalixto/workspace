import {
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

// Pivot of the sway: where the stem meets the soil.
const BASE_X = 250;
const BASE_Y = 425;

const Leaf = ({
  x,
  y,
  flip,
  appear,
}: {
  readonly x: number;
  readonly y: number;
  readonly flip: boolean;
  readonly appear: number;
}) => (
  <g transform={`translate(${x} ${y}) scale(${(flip ? -1 : 1) * appear} ${appear})`}>
    <path
      d="M0 0 C -40 -70, -140 -60, -160 -12 C -115 25, -45 30, 0 0 Z"
      fill="#5BBF5E"
    />
    <path
      d="M0 0 C -50 -20, -100 -22, -140 -14"
      stroke="#3E9443"
      strokeWidth={5}
      strokeLinecap="round"
      fill="none"
    />
  </g>
);

const Flower = ({ bloom }: { readonly bloom: number }) => (
  <g transform={`translate(${BASE_X} 165) scale(${bloom})`}>
    {[0, 60, 120, 180, 240, 300].map((angle) => (
      <circle
        key={angle}
        cx={Math.cos((angle * Math.PI) / 180) * 30}
        cy={Math.sin((angle * Math.PI) / 180) * 30}
        r={24}
        fill="#FF8FB1"
      />
    ))}
    <circle r={22} fill="#FFD23F" />
  </g>
);

export const Plant = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const stemGrowth = interpolate(frame, [0.5 * fps, 2.5 * fps], [0, 1], {
    ...clamp,
    easing: Easing.bezier(0.33, 1, 0.68, 1),
  });
  const leftLeaf = interpolate(frame, [1.6 * fps, 2.4 * fps], [0, 1], {
    ...clamp,
    easing: Easing.spring({ damping: 9 }),
  });
  const rightLeaf = interpolate(frame, [2 * fps, 2.8 * fps], [0, 1], {
    ...clamp,
    easing: Easing.spring({ damping: 9 }),
  });
  const bloom = interpolate(frame, [2.6 * fps, 3.6 * fps], [0, 1], {
    ...clamp,
    easing: Easing.spring({ damping: 8 }),
  });
  const smile = interpolate(frame, [3 * fps, 3.6 * fps], [572, 610], {
    ...clamp,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const cheeks = interpolate(frame, [3 * fps, 3.6 * fps], [0, 0.7], clamp);

  // Happy little hop when the flower opens.
  const hop = interpolate(
    frame,
    [3.4 * fps, 3.7 * fps, 4 * fps],
    [0, -40, 0],
    { ...clamp, easing: Easing.bezier(0.37, 0, 0.63, 1) },
  );

  // Gentle sway once fully grown, and two blinks.
  const swayIn = interpolate(frame, [2.5 * fps, 3.5 * fps], [0, 1], clamp);
  const sway = Math.sin((frame / fps) * 2) * 5 * swayIn;
  const blink = interpolate(
    frame,
    [5 * fps, 5.1 * fps, 5.2 * fps, 8 * fps, 8.1 * fps, 8.2 * fps],
    [1, 0.1, 1, 1, 0.1, 1],
    clamp,
  );

  return (
    <svg
      viewBox="0 0 500 700"
      width={600}
      height={840}
      style={{ overflow: "visible", translate: `0px ${hop}px` }}
    >
      <ellipse cx={BASE_X} cy={688} rx={150} ry={16} fill="#000" opacity={0.12} />

      <g transform={`rotate(${sway} ${BASE_X} ${BASE_Y})`}>
        <path
          d={`M${BASE_X} ${BASE_Y} C 238 340, 266 260, ${BASE_X} 170`}
          stroke="#4CAF50"
          strokeWidth={16}
          strokeLinecap="round"
          fill="none"
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1 - stemGrowth}
        />
        <Leaf x={247} y={330} flip={false} appear={leftLeaf} />
        <Leaf x={254} y={255} flip appear={rightLeaf} />
        <Flower bloom={bloom} />
      </g>

      <ellipse cx={BASE_X} cy={BASE_Y} rx={125} ry={16} fill="#6B4226" />
      <polygon points="130,450 370,450 340,685 160,685" fill="#E07A5F" />
      <rect x={110} y={418} width={280} height={52} rx={18} fill="#F2A07B" />

      <g>
        {[205, 295].map((cx) => (
          <ellipse
            key={cx}
            cx={cx}
            cy={535}
            rx={14}
            ry={19 * blink}
            fill="#3D2C2E"
          />
        ))}
        <circle cx={175} cy={572} r={18} fill="#FF6F91" opacity={cheeks} />
        <circle cx={325} cy={572} r={18} fill="#FF6F91" opacity={cheeks} />
        <path
          d={`M 218 572 Q 250 ${smile} 282 572`}
          stroke="#3D2C2E"
          strokeWidth={9}
          strokeLinecap="round"
          fill="none"
        />
      </g>
    </svg>
  );
};
