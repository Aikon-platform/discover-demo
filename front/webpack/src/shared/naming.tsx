import React from "react";
import { NameProvider } from "./types";
import { Document, ImageInfo } from "./types";


export const NameProviderContext = React.createContext<NameProvider>({});

export function getImageName(context: NameProvider, image: ImageInfo, ellipsis=false): string {
    let name = (image.document && context[image.document.uid]?.images[image.src || image.id]) || image.id;
    if (ellipsis) {
        name = name.split('.').slice(0, -1).join('.');
        if (name.length >= 16){
            name = name.slice(0, 5) + "..." + name.slice(-10);
        }
    }
    return name;
}

export function getSourceName(context: NameProvider, source?: Document): string | undefined {
    if (source === undefined)
        return undefined;
    return context[source.uid]?.name || source.name || source.uid;
}

export function fetchIIIFNames(sources: Document[], callback: (context: NameProvider) => void) {
    return new Promise(async (resolve, reject) => {
        const all_sources: NameProvider = {};
        for (const source of sources) {
            fetch(source.src)
            .then(response => response.json())
            .then(manifest => {
                // extract title and other metadata
                if (manifest.metadata === undefined)
                    return source;
                const metadata = Object.fromEntries(manifest.metadata.map(({label, value}:{ label: string, value: string }) => [label.toLowerCase(), value]));
                if (metadata.title === undefined)
                    metadata.title = source.name;

                // extract image names?
                const canvases = manifest.sequences && manifest.sequences[0]?.canvases;
                const image_labels = canvases && Object.fromEntries(canvases.map((canvas: any) => {
                    const label: string = canvas.label || canvas.title || (canvas.images && canvas.images[0].label) || canvas["@id"] || canvas.id;
                    const id: string = (canvas.images && canvas.images[0].resource && canvas.images[0].resource["@id"]) || canvas["@id"] || canvas.id;
                    return [id, label];
                }));

                all_sources[source.uid] = { name: metadata.title, metadata, images: image_labels };

                callback(all_sources);
            });
            // slow down the requests
            await new Promise(resolve => setTimeout(resolve, 300));
        }
    });
}
