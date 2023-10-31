import { createRoot } from 'react-dom/client';
import ClusterApp from "./ClusterApp";

function initClusterViewer(
  target_root: HTMLElement, 
  result_data: any, 
  editable?: boolean, 
  editing?: boolean,
  formfield?: HTMLInputElement) {
    createRoot(target_root).render(
      <ClusterApp result_data={result_data} editable={editable} editing={editing} formfield={formfield} />
    );
  }

export { initClusterViewer };