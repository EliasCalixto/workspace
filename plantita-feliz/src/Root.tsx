import { Composition } from "remotion";
import { PlantitaFeliz } from "./PlantitaFeliz";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="PlantitaFeliz"
        component={PlantitaFeliz}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
