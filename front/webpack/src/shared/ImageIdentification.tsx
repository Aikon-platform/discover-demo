import {getImageName, getSourceName, NameProviderContext} from "./naming";
import React from "react";
import { ImageInfo } from "./types";

interface ImageIdentificationProps {
    image: ImageInfo;
    isTitle?: boolean;
    prefix?: string;
}

export function ImageIdentification({ image, isTitle = false, prefix="" }: ImageIdentificationProps): React.JSX.Element {
    const nameProvider = React.useContext(NameProviderContext);
    const fallbackName = isTitle ? image.document?.name || image.id : image.name;
    const Tag = isTitle ? 'h4' : 'span';
    const classes = isTitle ? "mt-2" : "";

    return (
        <span>
            <Tag className={classes} title={getImageName(nameProvider, image) || fallbackName}>
                <span className="tag is-light is-bold mb-3">
                    {prefix ? `${prefix} ` : ""}
                    Image #{image.num}
                </span><br/>
                <span>{getImageName(nameProvider, image, !isTitle) || fallbackName}</span>
            </Tag>
            {isTitle && <p>{getSourceName(nameProvider, image.document) || image.document?.name || image.subtitle || ""}</p>}
        </span>
    );
}
