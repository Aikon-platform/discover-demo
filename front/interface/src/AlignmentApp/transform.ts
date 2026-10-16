// Transformation Matrix of format
// [ a  c  0  e ]   Column-major: a,b,0,g, c,d,0,h, 0,0,1,0, e,f,0,i
// [ b  d  0  f ]
// [ 0  0  1  0 ]
// [ g  h  0  i ]
export interface TransformMatrix {
    a: number;
    b: number;
    c: number;
    d: number;
    e: number;
    f: number;
    g: number;
    h: number;
    i: number;
}

export function identityMatrix(): TransformMatrix {
    return {
        a: 1,
        b: 0,
        c: 0,
        d: 1,
        e: 0,
        f: 0,
        g: 0,
        h: 0,
        i: 1,
    };
}

export function initialMatrix(width: number, height: number): TransformMatrix {
    const scale = 500 / Math.hypot(width, height);
    return {
        ...identityMatrix(),
        a: scale,
        d: scale,
        e: (-scale * width) / 2,
        f: (-scale * height) / 2,
    };
}

export function translationMatrix(tx: number, ty: number): TransformMatrix {
    return { ...identityMatrix(), e: tx, f: ty };
}

export function scaleMatrix(sx: number, sy: number): TransformMatrix {
    return { ...identityMatrix(), a: sx, d: sy };
}

export function rotationMatrix(theta: number): TransformMatrix {
    const cos = Math.cos(theta);
    const sin = Math.sin(theta);
    return { ...identityMatrix(), a: cos, b: sin, c: -sin, d: cos };
}

// Conjugate m so that it operates around (x, y) instead of the origin
export function aroundPoint(
    m: TransformMatrix,
    x: number,
    y: number,
): TransformMatrix {
    return multiplyMatrix(
        translationMatrix(x, y),
        multiplyMatrix(m, translationMatrix(-x, -y)),
    );
}

// Matrix utilities
export function invertMatrix(m: TransformMatrix): TransformMatrix | null {
    const { a, b, c, d, e, f, g, h, i } = m;

    // Compute determinant of 3x3 matrix
    const det = a * (d * i - f * h) - c * (b * i - f * g) + e * (b * h - d * g);

    if (Math.abs(det) < 1e-10) {
        return null;
    }

    const invDet = 1 / det;

    // Adjugate = transpose of cofactor matrix
    // For matrix M = [[a,c,e],[b,d,f],[g,h,i]], adjugate is:
    // [[ d*i-f*h,  e*h-c*i,  c*f-d*e ],
    //  [ f*g-b*i,  a*i-e*g,  b*e-a*f ],
    //  [ b*h-d*g,  c*g-a*h,  a*d-b*c ]]
    // Then map back to [[a,c,e],[b,d,f],[g,h,i]] layout
    return {
        a: (d * i - f * h) * invDet,
        b: (f * g - b * i) * invDet,
        c: (e * h - c * i) * invDet,
        d: (a * i - e * g) * invDet,
        e: (c * f - d * e) * invDet,
        f: (b * e - a * f) * invDet,
        g: (b * h - d * g) * invDet,
        h: (c * g - a * h) * invDet,
        i: (a * d - b * c) * invDet,
    };
}

export function multiplyMatrix(
    m1: TransformMatrix,
    m2: TransformMatrix,
): TransformMatrix {
    return {
        a: m1.a * m2.a + m1.c * m2.b + m1.e * m2.g,
        b: m1.b * m2.a + m1.d * m2.b + m1.f * m2.g,
        c: m1.a * m2.c + m1.c * m2.d + m1.e * m2.h,
        d: m1.b * m2.c + m1.d * m2.d + m1.f * m2.h,
        e: m1.a * m2.e + m1.c * m2.f + m1.e * m2.i,
        f: m1.b * m2.e + m1.d * m2.f + m1.f * m2.i,
        g: m1.g * m2.a + m1.h * m2.b + m1.i * m2.g,
        h: m1.g * m2.c + m1.h * m2.d + m1.i * m2.h,
        i: m1.g * m2.e + m1.h * m2.f + m1.i * m2.i,
    };
}

export function applyTransform(
    m: TransformMatrix,
    x: number,
    y: number,
): { x: number; y: number } {
    const w = m.g * x + m.h * y + m.i;
    return {
        x: (m.a * x + m.c * y + m.e) / w,
        y: (m.b * x + m.d * y + m.f) / w,
    };
}

type Point = { x: number; y: number };
export type Quad = [Point, Point, Point, Point];

// Projective transform mapping the (0, 0) - (width, height) rectangle onto
// quad (clockwise from top-left), or null if the quad is degenerate.
// Square -> quad solution from Heckbert, "Fundamentals of Texture Mapping", 1989
export function rectToQuad(
    width: number,
    height: number,
    quad: Quad,
): TransformMatrix | null {
    const [p0, p1, p2, p3] = quad;
    const dx1 = p1.x - p2.x;
    const dy1 = p1.y - p2.y;
    const dx2 = p3.x - p2.x;
    const dy2 = p3.y - p2.y;
    const dx3 = p0.x - p1.x + p2.x - p3.x;
    const dy3 = p0.y - p1.y + p2.y - p3.y;

    const den = dx1 * dy2 - dx2 * dy1;
    if (Math.abs(den) < 1e-10) {
        return null;
    }
    const g = (dx3 * dy2 - dx2 * dy3) / den;
    const h = (dx1 * dy3 - dx3 * dy1) / den;

    const square: TransformMatrix = {
        a: p1.x - p0.x + g * p1.x,
        b: p1.y - p0.y + g * p1.y,
        c: p3.x - p0.x + h * p3.x,
        d: p3.y - p0.y + h * p3.y,
        e: p0.x,
        f: p0.y,
        g,
        h,
        i: 1,
    };
    return multiplyMatrix(square, scaleMatrix(1 / width, 1 / height));
}

// Signed orientation of a quad if it is strictly convex, 0 otherwise
export function quadOrientation(quad: Quad): number {
    let sign = 0;
    for (let k = 0; k < 4; k++) {
        const p = quad[k];
        const q = quad[(k + 1) % 4];
        const r = quad[(k + 2) % 4];
        const cross = (q.x - p.x) * (r.y - q.y) - (q.y - p.y) * (r.x - q.x);
        if (Math.abs(cross) < 1e-9) return 0;
        const s = Math.sign(cross);
        if (sign !== 0 && s !== sign) return 0;
        sign = s;
    }
    return sign;
}

// Whether m maps the (0, 0) - (width, height) rectangle onto a strictly convex
// quad of the same orientation, without crossing the horizon (w > 0)
export function isProperWarp(
    m: TransformMatrix,
    width: number,
    height: number,
): boolean {
    if (!Object.values(m).every(Number.isFinite)) return false;
    const rect: Quad = [
        { x: 0, y: 0 },
        { x: width, y: 0 },
        { x: width, y: height },
        { x: 0, y: height },
    ];
    // w is affine, so positive at the corners means positive on the whole rect
    if (rect.some((p) => m.g * p.x + m.h * p.y + m.i <= 0)) return false;
    const quad = rect.map((p) => applyTransform(m, p.x, p.y)) as Quad;
    const orientation = quadOrientation(quad);
    return orientation !== 0 && orientation === quadOrientation(rect);
}

// Keypoint-based estimation

export type TransformModel = "scale" | "scalexy" | "scale+rotate" | "scalexy+rotate" | "affine" | "homographic";

// Relative eigenvalue below which a least-squares system is considered singular
const RANK_EPS = 1e-10;

// Similarity moving points to zero centroid and sqrt(2) mean distance
// (Hartley normalization), or null if all points coincide
function normalization(points: Point[]): TransformMatrix | null {
    const n = points.length;
    const cx = points.reduce((s, p) => s + p.x, 0) / n;
    const cy = points.reduce((s, p) => s + p.y, 0) / n;
    const meanDist =
        points.reduce((s, p) => s + Math.hypot(p.x - cx, p.y - cy), 0) / n;
    if (meanDist < 1e-9) return null;
    const s = Math.SQRT2 / meanDist;
    return multiplyMatrix(scaleMatrix(s, s), translationMatrix(-cx, -cy));
}

// Eigen decomposition of a symmetric matrix (cyclic Jacobi), eigenvalues in
// ascending order, vectors[k] being the unit eigenvector of values[k]
function symmetricEigen(m: number[][]): {
    values: number[];
    vectors: number[][];
} {
    const n = m.length;
    const a = m.map((row) => [...row]);
    const v = a.map((row, r) => row.map((_, c): number => (r === c ? 1 : 0)));

    for (let sweep = 0; sweep < 64; sweep++) {
        let off = 0;
        let norm = 0;
        for (let p = 0; p < n; p++) {
            norm += a[p][p] ** 2;
            for (let q = p + 1; q < n; q++) off += a[p][q] ** 2;
        }
        if (off <= 1e-30 * norm) break;

        for (let p = 0; p < n; p++) {
            for (let q = p + 1; q < n; q++) {
                if (a[p][q] === 0) continue;
                // Rotation in the (p, q) plane zeroing a[p][q]
                const theta = (a[q][q] - a[p][p]) / (2 * a[p][q]);
                const t =
                    (theta >= 0 ? 1 : -1) /
                    (Math.abs(theta) + Math.sqrt(theta * theta + 1));
                const c = 1 / Math.sqrt(t * t + 1);
                const s = t * c;
                for (let k = 0; k < n; k++) {
                    const akp = a[k][p];
                    const akq = a[k][q];
                    a[k][p] = c * akp - s * akq;
                    a[k][q] = s * akp + c * akq;
                }
                for (let k = 0; k < n; k++) {
                    const apk = a[p][k];
                    const aqk = a[q][k];
                    a[p][k] = c * apk - s * aqk;
                    a[q][k] = s * apk + c * aqk;
                }
                for (let k = 0; k < n; k++) {
                    const vkp = v[k][p];
                    const vkq = v[k][q];
                    v[k][p] = c * vkp - s * vkq;
                    v[k][q] = s * vkp + c * vkq;
                }
            }
        }
    }

    const order = a.map((_, k) => k).sort((i, j) => a[i][i] - a[j][j]);
    return {
        values: order.map((k) => a[k][k]),
        vectors: order.map((k) => v.map((row) => row[k])),
    };
}

// Normal equations (sum of rows^T rows)
function gram(rows: number[][]): number[][] {
    const n = rows[0].length;
    const m = Array.from({ length: n }, () => new Array(n).fill(0));
    for (const row of rows) {
        for (let r = 0; r < n; r++) {
            for (let c = 0; c < n; c++) m[r][c] += row[r] * row[c];
        }
    }
    return m;
}

function fitRotation(
    src: Point[],
    dst: Point[],
    isotropic?: boolean,
): TransformMatrix | null {
    // Points are centered: only rotation and scale remain, as a + ib
    let re = 0;
    let im = 0;
    let den = 0;
    for (let k = 0; k < src.length; k++) {
        const p = src[k];
        const q = dst[k];
        re += p.x * q.x + p.y * q.y;
        im += p.x * q.y - p.y * q.x;
        den += p.x * p.x + p.y * p.y;
    }
    if (den < 1e-12) return null;

    if (isotropic) {
        const a = re / den;
        const b = im / den;
        if (Math.hypot(a, b) < 1e-6) return null;
        return { ...identityMatrix(), a, b, c: -b, d: a };
    }

    // Anisotropic: rotation + independent x/y scale (no shear). For a fixed
    // angle the optimal sx, sy are a linear least squares solution, and for
    // fixed sx, sy the optimal angle is the usual rotation-only fit (as
    // above) between the scaled src points and dst; alternating the two
    // exact steps converges to the joint least-squares solution.
    const sxxDen = src.reduce((s, p) => s + p.x * p.x, 0);
    const syyDen = src.reduce((s, p) => s + p.y * p.y, 0);
    if (sxxDen < 1e-12 || syyDen < 1e-12) return null;

    let theta = Math.atan2(im, re);
    let sx = 1;
    let sy = 1;
    for (let iter = 0; iter < 20; iter++) {
        const cos = Math.cos(theta);
        const sin = Math.sin(theta);
        let sxNum = 0;
        let syNum = 0;
        for (let k = 0; k < src.length; k++) {
            const p = src[k];
            const q = dst[k];
            sxNum += cos * p.x * q.x + sin * p.x * q.y;
            syNum += -sin * p.y * q.x + cos * p.y * q.y;
        }
        sx = sxNum / sxxDen;
        sy = syNum / syyDen;

        let rotRe = 0;
        let rotIm = 0;
        for (let k = 0; k < src.length; k++) {
            const p = src[k];
            const q = dst[k];
            const px = sx * p.x;
            const py = sy * p.y;
            rotRe += px * q.x + py * q.y;
            rotIm += px * q.y - py * q.x;
        }
        theta = Math.atan2(rotIm, rotRe);
    }

    if (Math.hypot(sx, sy) < 1e-6) return null;
    const cos = Math.cos(theta);
    const sin = Math.sin(theta);
    return {
        ...identityMatrix(),
        a: sx * cos,
        b: sx * sin,
        c: -sy * sin,
        d: sy * cos,
    };
}

function fitAffine(src: Point[], dst: Point[]): TransformMatrix | null {
    const rows = src.map((p) => [p.x, p.y, 1]);
    const { values, vectors } = symmetricEigen(gram(rows));
    // Collinear points leave the system under-determined
    if (values[0] < RANK_EPS * values[2]) return null;

    // Least squares solution via the eigen decomposition
    const solve = (rhs: number[]) => {
        const x = [0, 0, 0];
        for (let k = 0; k < 3; k++) {
            const coef =
                vectors[k].reduce((s, vk, r) => s + vk * rhs[r], 0) / values[k];
            for (let r = 0; r < 3; r++) x[r] += coef * vectors[k][r];
        }
        return x;
    };
    const sumRows = (coord: (q: Point) => number) =>
        [0, 1, 2].map((r) =>
            rows.reduce((s, row, k) => s + row[r] * coord(dst[k]), 0),
        );
    const [a, c, e] = solve(sumRows((q) => q.x));
    const [b, d, f] = solve(sumRows((q) => q.y));
    return { a, b, c, d, e, f, g: 0, h: 0, i: 1 };
}

// Direct linear transform: h spans the null space of the stacked constraints
function fitHomography(src: Point[], dst: Point[]): TransformMatrix | null {
    const rows = src.flatMap((p, k) => {
        const q = dst[k];
        return [
            [p.x, p.y, 1, 0, 0, 0, -q.x * p.x, -q.x * p.y, -q.x],
            [0, 0, 0, p.x, p.y, 1, -q.y * p.x, -q.y * p.y, -q.y],
        ];
    });
    const { values, vectors } = symmetricEigen(gram(rows));
    // A second (near) null vector means the solution is not unique
    if (values[1] < RANK_EPS * values[8]) return null;
    const [a, c, e, b, d, f, g, h, i] = vectors[0];
    return { a, b, c, d, e, f, g, h, i };
}

// Fit non-uniform scaling (anisotropic)
function fitScale(
    src: Point[],
    dst: Point[],
    isotropic?: boolean,
): TransformMatrix | null {
    // We want to find sx, sy such that dst[k] ≈ [sx, 0, 0; 0, sy, 0; 0, 0, 1] * src[k]
    // This is equivalent to: q.x ≈ sx * p.x and q.y ≈ sy * p.y
    // We solve for sx and sy using least squares (independent equations)
    let sxNum = 0;
    let sxDen = 0;
    let syNum = 0;
    let syDen = 0;

    for (let k = 0; k < src.length; k++) {
        const p = src[k];
        const q = dst[k];
        sxNum += p.x * q.x;
        sxDen += p.x * p.x;
        syNum += p.y * q.y;
        syDen += p.y * p.y;
    }

    if (isotropic) {
        sxDen += syDen;
        sxNum += syNum;
        const scale = sxDen > 1e-12 ? sxNum / sxDen : 0;
        if (Math.abs(scale) < 1e-6) return null;
        return { ...identityMatrix(), a: scale, d: scale };
    }

    const sx = sxDen > 1e-12 ? sxNum / sxDen : 1;
    const sy = syDen > 1e-12 ? syNum / syDen : 1;
    if (Math.abs(sx) < 1e-6 || Math.abs(sy) < 1e-6) return null;
    return { ...identityMatrix(), a: sx, d: sy };
}

// Least squares transform of the given model mapping src[k] onto dst[k],
// or null if the points are too few or in a degenerate configuration
export function estimateTransform(
    model: TransformModel,
    src: Point[],
    dst: Point[],
): TransformMatrix | null {
    if (src.length !== dst.length || src.length < 2) {
        return null;
    }
    const normSrc = normalization(src);
    const normDst = normalization(dst);
    const invNormDst = normDst && invertMatrix(normDst);
    if (!normSrc || !normDst || !invNormDst) return null;

    const s = src.map((p) => applyTransform(normSrc, p.x, p.y));
    const d = dst.map((p) => applyTransform(normDst, p.x, p.y));

    // Fit the appropriate model
    let fit;
    if (model === "scale" || model === "scalexy") {
        fit = fitScale(s, d, model === "scale" || src.length == 2);
    } else if (model === "scale+rotate" || model === "scalexy+rotate" || src.length < 3) {
        fit = fitRotation(s, d, model === "scale+rotate" || src.length == 2);
    } else if (model === "affine" || src.length < 4) {
        fit = fitAffine(s, d);
    } else {
        fit = fitHomography(s, d);
    }
    if (!fit) return null;

    const m = multiplyMatrix(invNormDst, multiplyMatrix(fit, normSrc));
    if (Math.abs(m.i) < 1e-12) return null;
    const scale = 1 / m.i;
    const result = Object.fromEntries(
        Object.entries(m).map(([k, x]) => [k, x * scale]),
    ) as unknown as TransformMatrix;
    return Object.values(result).every(Number.isFinite) ? result : null;
}

export function matrixToCss(m: TransformMatrix): string {
    // Embed 3x3 projective matrix into 4x4 for CSS matrix3d
    // [ a  c  0  e ]   Column-major: a,b,0,g, c,d,0,h, 0,0,1,0, e,f,0,i
    // [ b  d  0  f ]
    // [ 0  0  1  0 ]
    // [ g  h  0  i ]
    return `matrix3d(${m.a}, ${m.b}, 0, ${m.g}, ${m.c}, ${m.d}, 0, ${m.h}, 0, 0, 1, 0, ${m.e}, ${m.f}, 0, ${m.i})`;
}
