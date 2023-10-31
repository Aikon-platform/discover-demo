import React, { useState } from "react";

export interface ImageProps {
  origpath: string;
  raw_url: string;
  tsf_url?: string;
  distance: number;
}

export interface ClusterProps {
  id: number;
  name: string;
  proto_url?: string;
  mask_url?: string;
  images: ImageProps[];
  editable: boolean;
  editing: boolean;
  onEdit: (cluster: ClusterProps, editing: boolean) => void;
  onChangeName?: (cluster: ClusterProps, name: string) => void;
}

const N_SHOWN = 10;

export function ClusterElement(props: ClusterProps) {
  const [expanded, setExpanded] = useState(false);
  const [transformed, setTransformed] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const nameInput = React.createRef<HTMLInputElement>();

  const onRenameSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const val = nameInput.current!.value;
    setRenaming(false);
    if (!props.onChangeName) {
      return;
    }
    props.onChangeName(props, val);
  }

  return (
    <div className={"cl-cluster" + (expanded ? " cl-expanded" : "")}>
      <div className="cl-props">
        <div className="cl-propcontent">
          {!(renaming && props.editing) ? 
          <h3>{props.name} <a href="javascript:void(0)" onClick={() => {props.onEdit(props, true); setRenaming(true)}}>Rename</a></h3> : 
          <form onSubmit={onRenameSubmit}><input type="text" ref={nameInput} value={props.name}></input> <input type="submit" value="Save"></input></form>
          }
          
          <p>Cluster #{props.id}, {props.images.length} images</p>

          {props.editable && 
          <p>
            <a href="javascript:void(0);" onClick={() => {props.onEdit(props, !props.editing)}}>
            {props.editing ? "End edit" : "Edit" }</a>
          </p>}
          
          {props.proto_url && 
          <React.Fragment>
            <p><a href="javascript:void(0);" onClick={() => {setTransformed(!transformed)}}>
              {transformed ? "Show original images" : "Show transformed prototypes" }</a>
            </p>
            <div className="cl-proto">
              <img src={props.proto_url} alt="cl-proto" className="prototype" />
              {props.mask_url && false && <img src={props.mask_url} alt="mask" className="mask" />}
            </div>
          </React.Fragment>}

        </div>
      </div>
      <div className="cl-samples">
        <div className="cl-samplecontent">
          {props.images.slice(0, expanded ? undefined : N_SHOWN).map((image) => (
            <img src={transformed ? image.tsf_url : image.raw_url} alt={image.origpath} title={image.distance.toFixed(4)} />
          ))}
          {props.images.length === 0 && <p>(No image)</p>}
          {props.images.length > N_SHOWN && <a className="cl-more" href="javascript:void(0)" onClick={() => {setExpanded(!expanded)}}>{expanded ? "–" : "+"}{props.images.length - N_SHOWN}</a>}
        </div>
      </div>
      <a className="cl-overlay cl-hidden" href="javascript:void(0)"></a>
    </div>
  );
}
