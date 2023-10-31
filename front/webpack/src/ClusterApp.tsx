import { useEffect, useState } from "react";
import { ClusterElement, ClusterProps } from "./ClusterElement";

interface AppProps {
  result_data: {
    clusters: {
      id: number;
      name: string;
      proto_url: string;
      mask_url: string;
      images: {
        cluster_id: number;
        distance: number;
        path: string;
        raw_url: string;
        tsf_url: string;
      }[];
    }[];
    base_url: string;
  };
  editing?: boolean;
  editable?: boolean;
  formfield?: HTMLInputElement;
}

export default function ClusterApp({ result_data, editing=false, editable=false, formfield }: AppProps) {
  const clusters = result_data.clusters.map((cluster) => {
    const images = cluster.images.map((image) => {
      return {
        origpath: image.path,
        raw_url: result_data.base_url + image.raw_url,
        tsf_url: result_data.base_url + image.tsf_url,
        distance: image.distance,
      };
    });
    return {
      id: cluster.id,
      images: images,
      proto_url: result_data.base_url + cluster.proto_url,
      mask_url: cluster.mask_url ? result_data.base_url + cluster.mask_url : undefined,
      name: cluster.name
    };
  }).sort((a, b) => b.images.length - a.images.length);

  let [showEditor, setShowEditor] = useState(editable && editing);
  let [editingCluster, setEditingCluster] = useState<number | null>(null);

  useEffect(() => {
    if (formfield) {
      formfield.value = JSON.stringify(clusters);
    }
  }, [clusters]);

  const save = () => {
    if (formfield) {
      formfield.value = JSON.stringify(clusters);
      formfield.form!.submit();
    }
  }

  const setEditing = (target: ClusterProps, active: boolean) => {
    console.log("setEditing", target, active);
    if (!editable) {
      return;
    }
    if (!active) {
      return setEditingCluster(null);
    }
    setEditingCluster(target.id);
  }

  return (
    <div className={showEditor ? "cl-editor" : ""}>
      <div className="cl-editor-toolbar">
        <h1>Cluster {showEditor ? "Editor" : "Viewer"}</h1>
        {editable && 
          <div className="cl-editor-tools">
            {!showEditor && <button onClick={() => {setShowEditor(true)}}>Edit </button>}
            {showEditor && <button onClick={save}>Save changes</button>}
          </div>
      }
      </div>        
      <div className="cl-cluster-list">
      {clusters.map((cluster) => (
        <ClusterElement key={cluster.id} editable={showEditor} editing={editingCluster == cluster.id} onEdit={setEditing} {...cluster} />
      ))}
      </div>
    </div>
  );
}
