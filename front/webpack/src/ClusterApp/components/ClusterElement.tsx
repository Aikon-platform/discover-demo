import React, { useEffect, useState } from "react";
import { ClusterEditorContext } from "../actions";
import { Icon } from "@iconify/react";
import { ClusterInfo, ClusterProps } from "../types";
import { BasicImageList, SelectableImageList } from "./ImageLists";
import { IconBtn } from "../../utils/IconBtn";

const N_SHOWN = {"grid": 8, "rows": 18};

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

  const scrollIntoView = () => {
    setTimeout(() => elRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
  }

  const onRenameSubmit = (e: React.SyntheticEvent) => {
    e.preventDefault();
    const val = nameInput.current!.value;
    if (val) {
      editorContext?.dispatch({ type: "cluster_rename", cluster_id: cluster.id, name: val});
    }
    setRenaming(false);
  };

  const toggleEdition = (val?: boolean) => {
    editorContext?.dispatch({ type: "viewer_focus", cluster_id: val ? cluster.id : null});
    if (!val) scrollIntoView();
    setRenaming(false);
  };

  const askForMerge = () => {
    editorContext?.dispatch({ type: "cluster_ask", cluster_id: cluster.id, for_action: "cluster_merge"})
  };

  const n_shown = N_SHOWN[editorContext!.state.viewer_display];

  // if juste expanded or editing, scroll to the element
  useEffect(() => {
    if (expanded || props.editing) scrollIntoView();
  }, [expanded, props.editing]);

  const btnMore = (cluster.images.length > n_shown && 
    <a className="cl-more" href="javascript:void(0)" onClick={() => {setExpanded(!expanded); scrollIntoView();}}>
      {expanded ? "–" : "+"}{cluster.images.length - n_shown}
    </a>
  );

  const btnExpand = (cluster.images.length > n_shown && 
    (expanded ?
      <p><IconBtn icon="mdi:chevron-up" label="Collapse" onClick={() => {setExpanded(false); scrollIntoView();}} /></p> :
      <p><IconBtn icon="mdi:chevron-down" label="Expand" onClick={() => {setExpanded(true)}} /></p>)
  );

  return (
    <div className={"cl-cluster" + (expanded || props.editing ? " cl-expanded" : "")}>
      <div className="cl-anchor" ref={elRef}></div>
      <div className="cl-props">
        <div className="cl-propcontent">
          <div className="cl-propinfo">
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


            {editable ? 
            <p>
              {props.editing ?
              <React.Fragment>
                <IconBtn icon="mdi:merge" label="Merge with..." onClick={askForMerge}/>
                <IconBtn icon="mdi:check-bold" label="End edition" onClick={() => toggleEdition(false)} /> 
              </React.Fragment>:
                <IconBtn icon="mdi:edit" label="Edit cluster" onClick={() => toggleEdition(true)} />}
            </p> : btnExpand}
          </div>
          {cluster.proto_url && 
          <div className="cl-protoinfo">
          <p>{transformed ?
              <IconBtn icon="mdi:image" label="Show images" onClick={() => {setTransformed(false)}} /> :
              <IconBtn icon="mdi:panorama-variant" label="Show protos" onClick={() => {setTransformed(true)}} />}
          </p>
            <div className="cl-proto">
              <img src={editorContext?.state.base_url + cluster.proto_url} alt="cl-proto" className="prototype" />
              {cluster.mask_url && false && <img src={editorContext!.state.base_url + cluster.mask_url} alt="mask" className="mask" />}
            </div>
          </div>}

        </div>
      </div>
      <div className="cl-samples">
          {props.editing ?
          <SelectableImageList images={cluster.images} transformed={transformed} /> :
          <BasicImageList images={cluster.images} transformed={transformed} limit={expanded ? undefined : n_shown} expander={btnMore}/>
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

