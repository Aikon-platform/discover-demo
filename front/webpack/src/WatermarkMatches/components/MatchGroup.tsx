import { WatermarkMatch } from "../types";
import { Match } from "./Match";

export function MatchGroup({ matches }: { matches: WatermarkMatch[] }) {
    /*
    Component to render a group of watermark matches.
    */
    return (
        <div>
            {matches.map((match, idx) => (
                <Match key={idx} {...match} />
            ))}
        </div>
    );
}
