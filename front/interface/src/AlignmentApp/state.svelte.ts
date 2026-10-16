import {
    applyTransform,
    estimateTransform,
    invertMatrix,
    isProperWarp,
    multiplyMatrix,
    type TransformMatrix,
    type TransformModel,
} from "./transform";

export interface RawImage {
    file_name: string;
    width: number;
    height: number;
    data: any;
}

export type Point = { x: number; y: number; disabled?: boolean };

export type Tool = "transform" | "keypoints";

export interface AligningImage {
    image: RawImage;
    transform: TransformMatrix;
    visible: boolean;
    /** keypoints[k] matches across all images */
    keypoints: Point[];
    fitWarning?: string | null;
    opacity: number;
    invertColors: boolean;
    hFlip: boolean;
}

/** Temporary keypoint under the cursor, in the hovered image's pixels */
export interface HoverKeypoint {
    image: number;
    point: Point;
}

export class AlignmentState {
    images: AligningImage[] = $state([]);
    selected: number[] = $state([]);
    solo: number | null = $state(null);
    hover: HoverKeypoint | null = $state(null);
    /** Index of the keypoint currently hovered or dragged, in any image */
    activeKeypoint: number | null = $state(null);
    kpImageOverlay: number | null = $state(null);
    showKpImageOverlay = $state(true);
    /** Fit each image's transform onto the first image from keypoints */
    syncWithKeypoints = $state(true);
    transformModel: TransformModel = $state("scale");
    tool: Tool = $state("transform");

    /** Image `from` pixels -> image `to` pixels, through world space */
    warpMatrix(from: number, to: number): TransformMatrix | null {
        const invTo = invertMatrix(this.images[to].transform);
        return invTo && multiplyMatrix(invTo, this.images[from].transform);
    }

    warpPoint(from: number, to: number, p: Point): Point {
        if (from === to) return p;
        const m = this.warpMatrix(from, to);
        return m ? applyTransform(m, p.x, p.y) : p;
    }

    /** Add a keypoint set at `p` in image `from`, warped into all other images */
    addKeypoint(from: number, p: Point): number {
        for (let i = 0; i < this.images.length; i++) {
            this.images[i].keypoints.push({
                ...this.warpPoint(from, i, p),
                disabled: i !== from && i !== 0,
            });
        }
        this.keypointsChanged();
        return this.images[from].keypoints.length - 1;
    }

    moveKeypoint(image: number, k: number, p: Point) {
        this.images[image].keypoints[k] = p;
        this.keypointsChanged(image);
    }

    removeKeypoint(k: number) {
        for (const img of this.images) {
            img.keypoints.splice(k, 1);
        }
        this.activeKeypoint = null;
        this.keypointsChanged();
    }

    toggleKeypoint(image: number, k: number) {
        this.images[image].keypoints[k].disabled =
            !this.images[image].keypoints[k].disabled;
        this.keypointsChanged(image);
    }

    setSyncWithKeypoints(sync: boolean) {
        this.syncWithKeypoints = sync;
        if (sync) {
            this.resync();
        } else {
            for (const img of this.images) img.fitWarning = null;
        }
    }

    /** Refit all transforms, e.g. after the model or the first image changed */
    resync(force: boolean = false) {
        if (!this.syncWithKeypoints) return;
        if (this.images[0]) this.images[0].fitWarning = null;
        for (let i = 1; i < this.images.length; i++)
            this.fitToReference(i, force);
    }

    refit(index: number) {
        this.fitToReference(index);
    }

    /** Keypoints of `image` (or of every image) changed */
    private keypointsChanged(image?: number) {
        if (image === undefined || image === 0) {
            this.resync();
        } else if (this.syncWithKeypoints) {
            this.fitToReference(image);
        }
    }

    /**
     * Fit image `index` pixels -> first image pixels on their shared enabled
     * keypoints, then compose with the first image's transform. A degenerate
     * fit keeps the current (last correct) transform and sets a warning.
     * force: try to fit even if there are no keypoints (use corners)
     */
    private fitToReference(index: number, force: boolean = false) {
        const ref = this.images[0];
        const img = this.images[index];
        const src: Point[] = [];
        const dst: Point[] = [];
        img.keypoints.forEach((p, k) => {
            const q = ref.keypoints[k];
            if (q && !p.disabled && !q.disabled) {
                src.push(p);
                dst.push(q);
            }
        });

        let model = this.transformModel;

        if (src.length < 2) {
            if (force) {
                // Use corners if there are no keypoints
                const pts = [
                    { x: 0, y: 0 },
                    { x: img.image.width, y: 0 },
                    { x: img.image.width, y: img.image.height },
                    { x: 0, y: img.image.height },
                ];
                src.length = 0;
                dst.length = 0;
                for (const p of pts) {
                    src.push(p);
                    dst.push(this.warpPoint(index, 0, p));
                }
            } else {
                img.fitWarning = null;
                return;
            }
        }

        const relative = estimateTransform(
            model,
            src,
            dst,
        );
        if (!relative) {
            this.setFitWarning(
                img,
                "degenerate keypoints (coincident or collinear)",
            );
            return;
        }
        const m = multiplyMatrix(ref.transform, relative);
        if (!isProperWarp(m, img.image.width, img.image.height)) {
            this.setFitWarning(img, "fit would fold or flip the image");
            return;
        }
        img.transform = m;
        img.fitWarning = null;
    }

    private setFitWarning(img: AligningImage, warning: string) {
        // Fits run on every drag step: only log changes
        if (img.fitWarning !== warning) {
            console.warn(`${img.image.file_name}: ${warning}`);
        }
        img.fitWarning = warning;
    }
}
