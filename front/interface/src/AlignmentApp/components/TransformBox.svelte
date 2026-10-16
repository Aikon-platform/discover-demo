<script lang="ts">
    import {
        applyTransform,
        aroundPoint,
        identityMatrix,
        invertMatrix,
        multiplyMatrix,
        quadOrientation,
        rectToQuad,
        rotationMatrix,
        scaleMatrix,
        translationMatrix,
        type Quad,
        type TransformMatrix,
        type TransformModel,
    } from "../transform";

    interface Props {
        /** Image -> world transform being edited */
        transform: TransformMatrix;
        /** World -> screen (container pixels) transform */
        view: TransformMatrix;
        width: number;
        height: number;
        onChange: (m: TransformMatrix) => void;
        onDragStart?: () => void;
        onDragEnd?: () => void;
        /** Transform model: scale, scale+rotate, affine, homography */
        transformModel: TransformModel;
    }

    let {
        transform,
        view,
        width,
        height,
        onChange,
        onDragStart,
        onDragEnd,
        transformModel,
    }: Props = $props();

    // Derive freeform from transform model
    // freeform is true for homography (perspective): handles move corners.
    // In affine mode, corners scale and side handles skew.
    const freeform = $derived(transformModel === "homographic");
    const affine = $derived(transformModel === "affine");
    const keepAspectRatio = $derived(transformModel === "scale" || transformModel === "scale+rotate");

    type Point = { x: number; y: number };

    // Handles as (u, v) fractions of the image size, clockwise from top-left
    const HANDLES: [number, number][] = [
        [0, 0],
        [0.5, 0],
        [1, 0],
        [1, 0.5],
        [1, 1],
        [0.5, 1],
        [0, 1],
        [0, 0.5],
    ];
    const HANDLE_SIZE = 9;
    const ROTATE_OFFSET = 28; // px, distance of the rotation handle above the box
    const ROTATE_SNAP = Math.PI / 12; // 15°, with Shift
    const MIN_SCALE = 1e-3;
    const RESIZE_CURSORS = [
        "ew-resize",
        "nwse-resize",
        "ns-resize",
        "nesw-resize",
    ];

    // Pivot, as (u, v) fractions of the image size: it follows the image
    let pivot = $state({ u: 0.5, v: 0.5 });

    let svg: SVGSVGElement;

    // Image -> screen
    const screen = $derived(multiplyMatrix(view, transform));
    const toScreen = (u: number, v: number) =>
        applyTransform(screen, u * width, v * height);

    // Image corners as (u, v), clockwise from top-left
    const CORNERS: [number, number][] = [
        [0, 0],
        [1, 0],
        [1, 1],
        [0, 1],
    ];

    const corners = $derived(CORNERS.map(([u, v]) => toScreen(u, v)) as Quad);
    const center = $derived(toScreen(0.5, 0.5));
    const handles = $derived(
        HANDLES.map(([u, v]) => {
            const p = toScreen(u, v);
            const side = u === 0.5 || v === 0.5;
            return {
                u,
                v,
                side,
                ...p,
                cursor: freeform ? "move" : resizeCursor(p, affine && side),
            };
        }),
    );
    const topMid = $derived(toScreen(0.5, 0));
    const rotateHandle = $derived.by(() => {
        const dx = topMid.x - center.x;
        const dy = topMid.y - center.y;
        const len = Math.hypot(dx, dy);
        const [nx, ny] = len > 1e-6 ? [dx / len, dy / len] : [0, -1];
        return {
            x: topMid.x + nx * ROTATE_OFFSET,
            y: topMid.y + ny * ROTATE_OFFSET,
        };
    });
    const pivotScreen = $derived(toScreen(pivot.u, pivot.v));

    // Pick the resize cursor closest to the handle direction on screen
    function resizeCursor(p: Point, skew = false): string {
        if (skew) return "move";
        const angle = Math.atan2(p.y - center.y, p.x - center.x);
        const octant = Math.round(angle / (Math.PI / 4));
        return RESIZE_CURSORS[((octant % 4) + 4) % 4];
    }

    type Operation =
        | { kind: "move" }
        | { kind: "rotate" }
        | { kind: "pivot" }
        | { kind: "scale"; u: number; v: number }
        | { kind: "skew"; u: number; v: number }
        | { kind: "distort"; corners: number[] };

    interface Drag {
        op: Operation;
        start: Point;
        transform0: TransformMatrix;
        view0: TransformMatrix;
        invView0: TransformMatrix;
        screen0: TransformMatrix;
        invScreen0: TransformMatrix;
        corners0: Quad;
    }

    let drag: Drag | null = null;

    function pointer(e: PointerEvent): Point {
        const rect = svg.getBoundingClientRect();
        return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    }

    function startDrag(e: PointerEvent, op: Operation) {
        if (e.button !== 0) return;
        const transform0 = $state.snapshot(transform);
        const view0 = $state.snapshot(view);
        const screen0 = multiplyMatrix(view0, transform0);
        const invView0 = invertMatrix(view0);
        const invScreen0 = invertMatrix(screen0);
        if (!invView0 || !invScreen0) return;

        e.preventDefault();
        e.stopPropagation();
        (e.currentTarget as Element).setPointerCapture(e.pointerId);
        drag = {
            op,
            start: pointer(e),
            transform0,
            view0,
            invView0,
            screen0,
            invScreen0,
            corners0: $state.snapshot(corners) as Quad,
        };
        onDragStart?.();
    }

    function endDrag() {
        if (!drag) return;
        drag = null;
        onDragEnd?.();
    }

    // Apply a screen-space transform on top of the initial one
    function inScreen(d: Drag, m: TransformMatrix): TransformMatrix {
        return multiplyMatrix(
            d.invView0,
            multiplyMatrix(m, multiplyMatrix(d.view0, d.transform0)),
        );
    }

    const clampScale = (s: number) =>
        Math.abs(s) < MIN_SCALE ? (s < 0 ? -MIN_SCALE : MIN_SCALE) : s;

    // Scale along the image axes, in image-local coordinates
    function scaled(d: Drag, u: number, v: number, p: Point, e: PointerEvent) {
        const local = applyTransform(d.invScreen0, p.x, p.y);
        const hx = u * width;
        const hy = v * height;
        // Anchor: opposite handle, or pivot with Ctrl
        const [ax, ay] = e.ctrlKey
            ? [pivot.u * width, pivot.v * height]
            : [(1 - u) * width, (1 - v) * height];
        const dx = hx - ax;
        const dy = hy - ay;
        const onX = u !== 0.5 && Math.abs(dx) > 1e-9;
        const onY = v !== 0.5 && Math.abs(dy) > 1e-9;

        let sx = onX ? (local.x - ax) / dx : 1;
        let sy = onY ? (local.y - ay) / dy : 1;

        if (e.shiftKey || keepAspectRatio) {
            // Corner: project pointer on the anchor -> handle diagonal
            const s =
                onX && onY
                    ? ((local.x - ax) * dx + (local.y - ay) * dy) /
                      (dx * dx + dy * dy)
                    : onX
                      ? sx
                      : sy;
            sx = sy = s;
        }

        return multiplyMatrix(
            d.transform0,
            aroundPoint(scaleMatrix(clampScale(sx), clampScale(sy)), ax, ay),
        );
    }

    // Skew along the edge of a side handle, in image-local coordinates: the
    // handle follows the pointer along the edge, the opposite edge (or the
    // pivot line with Ctrl) stays fixed
    function skewed(d: Drag, u: number, v: number, p: Point, e: PointerEvent) {
        const local = applyTransform(d.invScreen0, p.x, p.y);
        const hx = u * width;
        const hy = v * height;
        const horizontal = u === 0.5; // top/bottom edge: shear along x
        const [ax, ay] = e.ctrlKey
            ? [pivot.u * width, pivot.v * height]
            : [(1 - u) * width, (1 - v) * height];
        const dist = horizontal ? hy - ay : hx - ax;
        if (Math.abs(dist) < 1e-9) return d.transform0;
        const k = horizontal ? (local.x - hx) / dist : (local.y - hy) / dist;
        const shear = horizontal
            ? { ...identityMatrix(), c: k }
            : { ...identityMatrix(), b: k };
        return multiplyMatrix(d.transform0, aroundPoint(shear, ax, ay));
    }

    // Corners (indices in CORNERS) moved by the handle at (u, v) in freeform
    // mode: the corner itself, or both ends of an edge
    function handleCorners(u: number, v: number): number[] {
        return CORNERS.flatMap(([cu, cv], k) =>
            (u === 0.5 || cu === u) && (v === 0.5 || cv === v) ? [k] : [],
        );
    }

    // Move some corners by the pointer delta, and solve for the perspective
    // transform. Null if the resulting quad would fold or flip.
    function distorted(d: Drag, moved: number[], p: Point) {
        const dx = p.x - d.start.x;
        const dy = p.y - d.start.y;
        const quad = d.corners0.map((c, k) =>
            moved.includes(k) ? { x: c.x + dx, y: c.y + dy } : c,
        ) as Quad;
        const orientation = quadOrientation(quad);
        if (orientation === 0 || orientation !== quadOrientation(d.corners0)) {
            return null;
        }
        const m = rectToQuad(width, height, quad);
        return m && multiplyMatrix(d.invView0, m);
    }

    function onPointerMove(e: PointerEvent) {
        if (!drag) return;
        const d = drag;
        const p = pointer(e);

        switch (d.op.kind) {
            case "move":
                onChange(
                    inScreen(
                        d,
                        translationMatrix(p.x - d.start.x, p.y - d.start.y),
                    ),
                );
                break;
            case "rotate": {
                // Only allow rotation for scale+rotate, affine, and homography models
                if (transformModel === "scale") break;
                const c = applyTransform(
                    d.screen0,
                    pivot.u * width,
                    pivot.v * height,
                );
                let angle =
                    Math.atan2(p.y - c.y, p.x - c.x) -
                    Math.atan2(d.start.y - c.y, d.start.x - c.x);
                if (e.shiftKey)
                    angle = Math.round(angle / ROTATE_SNAP) * ROTATE_SNAP;
                onChange(
                    inScreen(d, aroundPoint(rotationMatrix(angle), c.x, c.y)),
                );
                break;
            }
            case "pivot": {
                const local = applyTransform(d.invScreen0, p.x, p.y);
                pivot = { u: local.x / width, v: local.y / height };
                break;
            }
            case "scale":
                onChange(scaled(d, d.op.u, d.op.v, p, e));
                break;
            case "skew":
                onChange(skewed(d, d.op.u, d.op.v, p, e));
                break;
            case "distort": {
                const m = distorted(d, d.op.corners, p);
                if (m) onChange(m);
                break;
            }
        }
    }
</script>

<svg
    bind:this={svg}
    class="transform-box"
    onpointermove={onPointerMove}
    onpointerup={endDrag}
    onpointercancel={endDrag}
>
    <polygon
        class="body"
        points={corners.map((p) => `${p.x},${p.y}`).join(" ")}
        onpointerdown={(e) => startDrag(e, { kind: "move" })}
    />
    {#if transformModel !== "scale"}
        <line
            class="rotate-stem"
            x1={topMid.x}
            y1={topMid.y}
            x2={rotateHandle.x}
            y2={rotateHandle.y}
        />
    {/if}
    {#each handles as h}
        <rect
            class="handle"
            x={h.x - HANDLE_SIZE / 2}
            y={h.y - HANDLE_SIZE / 2}
            width={HANDLE_SIZE}
            height={HANDLE_SIZE}
            style="cursor: {h.cursor}"
            onpointerdown={(e) =>
                startDrag(
                    e,
                    freeform
                        ? { kind: "distort", corners: handleCorners(h.u, h.v) }
                        : {
                              kind: affine && h.side ? "skew" : "scale",
                              u: h.u,
                              v: h.v,
                          },
                )}
        />
    {/each}
    {#if transformModel !== "scale"}
        <circle
            class="handle rotate"
            cx={rotateHandle.x}
            cy={rotateHandle.y}
            r={HANDLE_SIZE / 2 + 1}
            onpointerdown={(e) => startDrag(e, { kind: "rotate" })}
        />
    {/if}
    <g
        class="pivot"
        transform="translate({pivotScreen.x} {pivotScreen.y})"
        onpointerdown={(e) => startDrag(e, { kind: "pivot" })}
    >
        <circle r="6" />
        <line x1="-10" y1="0" x2="10" y2="0" />
        <line x1="0" y1="-10" x2="0" y2="10" />
    </g>
</svg>

<style>
    .transform-box {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        overflow: visible;
        pointer-events: none;
    }

    .transform-box > * {
        pointer-events: all;
        touch-action: none;
    }

    .body {
        fill: transparent;
        stroke: #4da3ff;
        stroke-width: 1;
        cursor: move;
    }

    .rotate-stem {
        stroke: #4da3ff;
        stroke-width: 1;
        pointer-events: none;
    }

    .handle {
        fill: #fff;
        stroke: #4da3ff;
        stroke-width: 1.5;
    }

    .handle.rotate {
        cursor: grab;
    }

    .pivot {
        cursor: crosshair;
    }

    .pivot circle {
        fill: rgba(255, 255, 255, 0.2);
        stroke: #fff;
        stroke-width: 1.5;
    }

    .pivot line {
        stroke: #fff;
        stroke-width: 1.5;
    }
</style>
