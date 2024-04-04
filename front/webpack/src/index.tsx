import { createRoot } from 'react-dom/client';
import { ClusterApp } from "./ClusterApp/components/ClusterApp";
import { TaskProgressTracker } from './ProgressTracker';
import "./sass/style.scss";
import { MatchList } from './WatermarkMatches';

function initClusterViewer(
  target_root: HTMLElement,
  clustering_data: any,
  base_media_url: string,
  editable?: boolean,
  editing?: boolean,
  formfield?: HTMLInputElement) {
  /*
  Main entry point for the clustering viewer app.

  target_root: the root element to render the app in
  clustering_data: the clustering data to render
  base_media_url: the base url for media files
  editable: whether the app should be editable
  editing: whether the app should be in editing mode
  formfield: the form field to update with the current clustering data
  */

  createRoot(target_root).render(
    <ClusterApp clustering_data={clustering_data} base_url={base_media_url}
                editable={editable} editing={editing} formfield={formfield} />
  );
}

function initProgressTracker(target_root: HTMLElement, tracking_url: string) {
  /*
  Main entry point for the progress tracker app.

  target_root: the root element to render the app in
  tracking_url: the url to track
  */

  createRoot(target_root).render(
    <TaskProgressTracker tracking_url={tracking_url} />
  );
}

function initWatermarkMatches(target_root: HTMLElement, query_image: string, matches: any, source_url: string) {
  /*
  Main entry point for the watermark matches app.

  target_root: the root element to render the app in
  matches: the matches to render
  */
  fetch(source_url + "index.json").then(response => response.json()).then(index => {
    createRoot(target_root).render(
      <MatchList query={query_image} matches={matches} source_index={index} source_url={source_url} />
    );
  });
}

export {
  initClusterViewer,
  initProgressTracker,
  initWatermarkMatches
};
