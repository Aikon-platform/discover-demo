import { createRoot } from 'react-dom/client';
import { ClusterApp } from "./ClusterApp/components/ClusterApp";
import { TaskProgressTracker } from './ProgressTracker';
import "./sass/style.scss";

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

function initProgressTracker(target_root: HTMLElement, tracking_url: string) {
    createRoot(target_root).render(
      <TaskProgressTracker tracking_url={tracking_url} />
    );
}

export {
  initClusterViewer,
  initProgressTracker
};