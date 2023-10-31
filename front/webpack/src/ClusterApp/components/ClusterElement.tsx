import React, { useState } from "react";
import { ClusterEditorContext } from "../context";
import { Icon } from "@iconify/react";
import { ClusterInfo, ClusterProps } from "../types";
import { BasicImageList, SelectableImageList } from "./ImageLists";
import { IconBtn } from "../../utils/IconBtn";

const N_SHOWN = 10;

// Lightweight cluster element for the cluster list
export function MiniClusterElement(props: { info: ClusterInfo; selected: boolean; onClick?: () => void; }) {
  const editorContext = React.useContext(ClusterEditorContext);
  const cluster = props.info;
  return (
    <div className={"cl-cluster" + (props.selected ? " cl-selected" : "")} onClick={props.onClick}>
      <div className="cl-props">
        <div className="cl-propcontent">
          <h3>{cluster.name}</h3>
          <p>{cluster.id >= 0 && <React.Fragment>Cluster #{cluster.id}, {cluster.images.length} images</React.Fragment>} </p>
        </div>
      </div>
      <div className="cl-samples">
        <BasicImageList images={cluster.images} transformed={false} limit={5} />
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
  const editorContext = React.useContext(ClusterEditorContext);
  const elRef = React.useRef<HTMLDivElement>(null);

  const cluster = props.info;
  const editable = editorContext?.state.editing;

  const onRenameSubmit = (e: React.SyntheticEvent) => {
    e.preventDefault();
    const val = nameInput.current!.value;
    if (val) {
      editorContext?.dispatch({ type: "cluster_rename", cluster_id: cluster.id, name: val});
    }
    setRenaming(false);
  };

  const toggleEdition = (val?: boolean) => {
    editorContext?.dispatch({ type: "edit_cluster", cluster_id: val ? cluster.id : null});
    setTimeout(() => elRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    setRenaming(false);
  };

  const askForMerge = () => {
    editorContext?.dispatch({ type: "cluster_ask", cluster_id: cluster.id, for_action: "cluster_merge"})
  };

  const expanderBtn = (cluster.images.length > N_SHOWN && 
    <a className="cl-more" href="javascript:void(0)" onClick={() => {setExpanded(!expanded)}}>
      {expanded ? "–" : "+"}{cluster.images.length - N_SHOWN}
    </a>
  );

  return (
    <div ref={elRef} className={"cl-cluster" + (expanded ? " cl-expanded" : "")}>
      <div className="cl-props">
        <div className="cl-propcontent">
          <p className="cl-cluster-title">
          {(renaming && props.editing) ? 
              (<form onSubmit={onRenameSubmit}>
                <input type="text" ref={nameInput} defaultValue={cluster.name} autoFocus></input> 
                <a href="javascript:void(0)" onClick={onRenameSubmit} className="btn"><Icon icon="mdi:check-bold" /></a>
               </form>) :
              (<React.Fragment>
                <span>{cluster.name}</span> 
                {props.editing && <a href="javascript:void(0)" className="btn is-edit" onClick={() => {toggleEdition(true); setRenaming(true)}} title="Rename"><Icon icon="mdi:edit" /></a>}
              </React.Fragment>)
          }
          </p>
          
          <p>{cluster.id >= 0 && <React.Fragment>Cluster #{cluster.id}, {cluster.images.length} images</React.Fragment>}</p>

          {editable && 
          <p>
            {props.editing ?
            <React.Fragment>
              <IconBtn icon="mdi:merge" label="Merge with..." onClick={askForMerge}/>
              <IconBtn icon="mdi:check-bold" label="End edition" onClick={() => toggleEdition(false)} /> 
            </React.Fragment>:
              <IconBtn icon="mdi:edit" label="Edit cluster" onClick={() => toggleEdition(true)} />}
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
          <SelectableImageList images={cluster.images} transformed={transformed} expander={expanderBtn}/> :
          <BasicImageList images={cluster.images} transformed={transformed} limit={expanded ? undefined : N_SHOWN} expander={expanderBtn}/>
          }
      </div>
      {editable && !props.editing && 
      <a className="cl-overlay cl-hoveroptions" href="javascript:void(0)" onClick={() => toggleEdition(true)}>
        <IconBtn icon="mdi:edit" label="Edit cluster" />
        <IconBtn icon="mdi:merge" label="Merge with..." onClick={(e) => {e.stopPropagation(); askForMerge()}}/>
        </a>}
    </div>
  );
}

