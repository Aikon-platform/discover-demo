import React, { useState } from "react";

export interface ImageProps {
  origpath: string;
  raw_url: string;
  tsf_url?: string;
  distance: number;
}

export interface ClusterProps {
  id: number;
  proto_url?: string;
  mask_url?: string;
  images: ImageProps[];
}

const N_SHOWN = 10;

export function ClusterElement(props: ClusterProps) {
  const [expanded, setExpanded] = useState(false);
  const [transformed, setTransformed] = useState(false);

  return (
    <div className={"cluster" + (expanded ? " expanded" : "")}>
      <div className="props">
        <div className="propcontent">
          <h3>Cluster {props.id}</h3>
          <p>{props.images.length} images</p>
          {props.proto_url && <React.Fragment><p><a href="javascript:void(0);" onClick={() => {setTransformed(!transformed)}}>
            {transformed ? "Show original images" : "Show transformed prototypes" }</a>
          </p>
          <div className="proto">
            <img src={props.proto_url} alt="proto" className="prototype" />
            {props.mask_url && false && <img src={props.mask_url} alt="mask" className="mask" />}
          </div></React.Fragment>}
        </div>
      </div>
      <div className="samples">
        <div className="samplecontent">
          {props.images.slice(0, expanded ? undefined : N_SHOWN).map((image) => (
            <img src={transformed ? image.tsf_url : image.raw_url} alt={image.origpath} title={image.distance.toFixed(4)} />
          ))}
          {props.images.length === 0 && <p>(No image)</p>}
          {props.images.length > N_SHOWN && <a className="more" href="javascript:void(0)" onClick={() => {setExpanded(!expanded)}}>{expanded ? "–" : "+"}{props.images.length - N_SHOWN}</a>}
        </div>
      </div>
      <a className="overlay hidden" href="javascript:void(0)"></a>
    </div>
  );
}
