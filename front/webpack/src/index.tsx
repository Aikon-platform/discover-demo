import { createRoot } from 'react-dom/client';
import { ClusterApp } from "./ClusterApp/components/ClusterApp";
import { TaskProgressTracker } from './ProgressTracker';
import "./sass/style.scss";
import { MatchViewer, WatermarkSimBrowser } from './WatermarkMatches';
import { unserializeSingleWatermarkMatches, unserializeWatermarkSimilarity } from './WatermarkMatches/types';

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
  query_image: the image url used as a query
  matches: the matches to render
  source_url: the url of the folder of the index files (index.json, images)
  */
  fetch(source_url + "index.json").then(response => response.json()).then(index => {
    const all_matches = unserializeSingleWatermarkMatches(query_image, matches, index, source_url);
    createRoot(target_root).render(
      <MatchViewer all_matches={all_matches} />
    );
  });
}

function initWatermarkSimBrowser(target_root: HTMLElement, source_url: string) {
  /*
  Main entry point for the watermark similarity browser app.

  target_root: the root element to render the app in
  source_url: the url to fetch the images and index from
  */
  fetch(source_url + "similarity.json").then(response => response.json()).then(matches => {
    fetch(source_url + "index.json").then(response => response.json()).then(index => {
      const all_matches = unserializeWatermarkSimilarity(matches, index, source_url);
      createRoot(target_root).render(
        <WatermarkSimBrowser matches={all_matches} index={index} />
      );
    });
  });
}

export {
  initClusterViewer,
  initProgressTracker,
  initWatermarkMatches,
  initWatermarkSimBrowser
};
