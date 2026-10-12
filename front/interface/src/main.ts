import { mount } from "svelte";
import ClusterApp from "./ClusterApp/components/ClusterApp.svelte";
import { unserializeClusterFile } from "./ClusterApp/converters";
import ProgressTracker from "./shared/components/ProgressTracker.svelte";
import SimilarityApp from "./SimilarityApp/components/SimilarityApp.svelte";
import ImageGenericList from "./shared/components/ImageGenericList.svelte";
import type { TImageInfo } from "./shared/types";
import DatasetImageBrowser from "./DatasetApp/components/DatasetImageBrowser.svelte";
import type { TDatasetFormatType, TDjangoDatasetInterface } from "./DatasetApp/types";

import "../sass/main.scss";
import SearchResults from "./SimilarityApp/components/SearchResults.svelte";
import { initWatermarksForm } from "./WatermarksApp/form";
import AlignmentApp from "./AlignmentApp/components/AlignmentApp.svelte";

/**
 * Mount the cluster viewer in the given target root.
 * @param target_root the root element to mount the cluster viewer in
 * @param clustering_data the clustering data to display
 * @param base_media_url the base url for media files
 * @param editable whether the cluster viewer should be editable
 * @param editing whether the cluster viewer should be in editing mode
 * @param formfield the form field to update with the current clustering data
 */
function initClusterViewer(
    target_root: HTMLElement,
    clustering_data: any,
    base_media_url: string,
    editable?: boolean,
    editing?: boolean,
    formfield?: HTMLInputElement
) {
    mount(ClusterApp, {
        target: target_root,
        props: {
            clustering_data: unserializeClusterFile(clustering_data),
            base_url: base_media_url,
            editable,
            editing,
            formfield,
        },
    });
}

/**
 * Mount the progress tracker in the given target root.
 * @param target_root the root element to mount the progress tracker in
 * @param tracking_url the url to track
 */
function initProgressTracker(target_root: HTMLElement, tracking_url: string) {
    mount(ProgressTracker, {
        target: target_root,
        props: {
            tracking_url,
        },
    });
}

/**
 * Mount the similarity app in the given target root.
 * @param target_root the root element to mount the similarity app in
 * @param source_index_url the url to the source index
 * @param sim_matrix_url the url to the similarity matrix
 * @param mode the mode to display the similarity app in
 */
function initSimilarityApp(
    target_root: HTMLElement,
    source_index_url: string,
    sim_matrix_url: string,
    mode?: "cluster" | "browse",
    metadata_url?: string,
) {
    mount(SimilarityApp, {
        target: target_root,
        props: {
            source_index_url,
            sim_matrix_url,
            mode,
            metadata_url,
        },
    });
}

/**
 * Mount the similarity app in the given target root.
 * @param target_root the root element to mount the similarity app in
 * @param source_index_url the url to the source index
 * @param query_result_url the url to the query result
 */
function initSearchResults(
    target_root: HTMLElement,
    source_index_url: string,
    query_result_url: string,
    metadata_url?: string,
) {
    mount(SearchResults, {
        target: target_root,
        props: {
            source_index_url,
            query_result_url,
            metadata_url,
        },
    });
}

/**
 * Mount the image generic list in the given target root.
 * @param target_root the root element to mount the image generic list in
 * @param image_array the array of images to display
 */
function initImageGenericList(target_root: HTMLElement, image_array: TImageInfo[]) {
    mount(ImageGenericList, {
        target: target_root,
        props: {
            image_array,
        },
    });
}

/**
 * Mount the dataset image browser in the given target root.
 * @param target_root the root element to mount the dataset image browser in
 * @param dataset the dataset to display
 * @param datasetFormat the format of the dataset
 */
function initDatasetImageBrowser(
    target_root: HTMLElement,
    dataset: TDjangoDatasetInterface,
    datasetFormat: TDatasetFormatType,
    metadataURL: string
) {
    mount(DatasetImageBrowser, {
        target: target_root,
        props: {
            dataset,
            datasetFormat,
            metadataURL,
        },
    });
}

/**
 * Mount the alignment app in the given target root.
 * @param target_root the root element to mount the alignment app in
 * @param alignment_url the url to alignment task results to load, if any
 */
function initAlignmentApp(
    target_root: HTMLElement,
    alignment_url?: string,
) {
    mount(AlignmentApp, {
        target: target_root,
        props: {
            alignment_url,
        },
    })
}

(window as any).DemoTools = {
    initClusterViewer,
    initProgressTracker,
    initSimilarityApp,
    initImageGenericList,
    initDatasetImageBrowser,
    initSearchResults,
    initWatermarksForm,
    initAlignmentApp
};
