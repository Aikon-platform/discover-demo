import { createRoot } from 'react-dom/client';
import ClusterApp from "./ClusterApp";

function initClusterViewer(
  target_root: HTMLElement, 
  clustering_data: any,
  base_media_url: string,
  editable?: boolean, 
  editing?: boolean,
  formfield?: HTMLInputElement) {
    createRoot(target_root).render(
      <ClusterApp clustering_data={clustering_data} base_url={base_media_url} 
                  editable={editable} editing={editing} formfield={formfield} />
    );
  }

export { initClusterViewer };