import React, { useState } from "react";
import { ClusterEditorContext } from "./ClusterApp";

export interface ImageInfo {
  path: string;
  raw_url: string;
  tsf_url?: string;
  distance: number;
  id: number;
}

export interface ClusterInfo {
  id: number;
  name: string;
  proto_url?: string;
  mask_url?: string;
  images: ImageInfo[];
}

export interface ClusterProps {
  info: ClusterInfo;
  editing: boolean;
}

const N_SHOWN = 10;

function ClusterImage(props: {image: ImageInfo, transformed: boolean, selected?: boolean, selectable: boolean, onClick?: () => void}) {
  const editorContext = React.useContext(ClusterEditorContext);
  const image = props.image;
  return (
    <div className={"cl-image" + (props.selected ? " cl-selected" : "")} onClick={props.onClick}>
      {props.selectable && <a href="javascript:void(0)" className="cl-selecter"></a>}
      <img src={editorContext!.state.base_url + ((props.transformed && image.tsf_url) ? image.tsf_url : image.raw_url)} 
      alt={image.id.toString()} title={image.path} />
    </div>
  );
}

function SelectableImageList(props: {images: ImageInfo[], limit?: number, transformed: boolean, expander?: React.ReactNode}) {
  const editorContext = React.useContext(ClusterEditorContext);
  const selection = editorContext!.state.image_selection;
  const toggleSelection = (image: ImageInfo) => {
    editorContext!.dispatch({type: "selection_change", images: [image], selected: !selection.has(image)});
  }

  return (
    <div className="cl-images cl-selectable">
        {props.images.slice(0, props.limit).map((image) => (
          <ClusterImage key={image.path} image={image} transformed={props.transformed} 
                        selectable={true} selected={selection.has(image)} onClick={() => toggleSelection(image)}/>
        ))}
        {props.images.length === 0 && <p>∅</p>}
        {props.expander}
    </div>
  );
}

function BasicImageList(props: {images: ImageInfo[], transformed: boolean, limit?: number, expander?: React.ReactNode}) {
  const editorContext = React.useContext(ClusterEditorContext);
  return (
    <div className="cl-images">
      {props.images.slice(0, props.limit).map((image) => (
        <ClusterImage key={image.path} image={image} transformed={props.transformed} selectable={false}/>
      ))}
      {props.images.length === 0 && <p>∅</p>}
      {props.expander}
    </div>
  );
}

export function MiniClusterElement(props: {info: ClusterInfo, selected: boolean, onClick?: () => void}) {
  const editorContext = React.useContext(ClusterEditorContext);
  const cluster = props.info;
  return (
    <div className={"cl-cluster" + (props.selected ? " cl-selected" : "")} onClick={props.onClick}>
      <div className="cl-props">
        <div className="cl-propcontent">
          <h3>{cluster.name}</h3>
          <p>{cluster.id > 0 && <React.Fragment>Cluster #{cluster.id}, {cluster.images.length} images</React.Fragment>} </p>
        </div>
      </div>
      <div className="cl-samples">
        <BasicImageList images={cluster.images} transformed={false} limit={5}/>
      </div>
      <a className="cl-overlay" href="javascript:void(0)"></a>
    </div>
  );
}
  

export function ClusterElement(props: ClusterProps) {
  const [expanded, setExpanded] = useState(false);
  const [transformed, setTransformed] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const nameInput = React.createRef<HTMLInputElement>();
  const selectionRef = React.createRef<typeof SelectableImageList>();
  const editorContext = React.useContext(ClusterEditorContext);

  const cluster = props.info;
  const editable = editorContext?.state.editing;

  const onRenameSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const val = nameInput.current!.value;
    if (val) {
      editorContext?.dispatch({ type: "cluster_rename", cluster_id: cluster.id, name: val});
    }
    setRenaming(false);
  }

  const toggleEdition = (val?: boolean) => {
    editorContext?.dispatch({ type: "edit_cluster", cluster_id: val ? cluster.id : null});
    setRenaming(false);
  }

  const expanderBtn = (cluster.images.length > N_SHOWN && 
    <a className="cl-more" href="javascript:void(0)" onClick={() => {setExpanded(!expanded)}}>
      {expanded ? "–" : "+"}{cluster.images.length - N_SHOWN}
    </a>
  );

  return (
    <div className={"cl-cluster" + (expanded ? " cl-expanded" : "")}>
      <div className="cl-props">
        <div className="cl-propcontent">
          {!(renaming && props.editing) ? 
          <h3>{cluster.name} {editable && <a href="javascript:void(0)" onClick={() => {toggleEdition(true); setRenaming(true)}}>Rename</a>}</h3> : 
          <form onSubmit={onRenameSubmit}><input type="text" ref={nameInput} defaultValue={cluster.name}></input> <input type="submit" value="Save"></input></form>
          }
          
          <p>{cluster.id > 0 && <React.Fragment>Cluster #{cluster.id}, {cluster.images.length} images</React.Fragment>}</p>

          {editable && 
          <p>
            <a href="javascript:void(0);" 
            onClick={() => {toggleEdition(!props.editing)}}>
            {props.editing ? "End edit" : "Edit" }</a>
          </p>}
          
          {cluster.proto_url && 
          <React.Fragment>
            <p><a href="javascript:void(0);" onClick={() => {setTransformed(!transformed)}}>
              {transformed ? "Show original images" : "Show transformed prototypes" }</a>
            </p>
            <div className="cl-proto">
              <img src={editorContext?.state.base_url + cluster.proto_url} alt="cl-proto" className="prototype" />
              {cluster.mask_url && false && <img src={editorContext!.state.base_url + cluster.mask_url} alt="mask" className="mask" />}
            </div>
          </React.Fragment>}

        </div>
      </div>
      <div className="cl-samples">
          {props.editing ?
          <SelectableImageList images={cluster.images} limit={expanded ? undefined : N_SHOWN} transformed={transformed} expander={expanderBtn}/> :
          <BasicImageList images={cluster.images} transformed={transformed} limit={expanded ? undefined : N_SHOWN} expander={expanderBtn}/>
          }
      </div>
      <a className="cl-overlay cl-hidden" href="javascript:void(0)"></a>
    </div>
  );
}
