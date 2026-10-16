import { type TPrimitive } from "./types";

export function ellipsis(str: string, maxLen: number) {
    if (maxLen < 0 || str.length <= maxLen) return str;
    if (maxLen < 12) return str.slice(0, maxLen) + "...";
    return str.slice(0, Math.max(5, maxLen - 12)) + "..." + str.slice(-Math.min(9, maxLen - 5));
}

export function unquote(v: any): any {
    if (typeof v === "string") {
        v = v.replace(/^["']|["']$/g, "")
    }
    return v
}

export const isObject = (o: any): boolean => o?.constructor === Object;

export const isString = (s: any): boolean => (typeof s === "string" || s instanceof String)

export const isArray = (a: any): boolean => Array.isArray(a)

export const isBoolean = (b: any): boolean => typeof b === "boolean";

/**
 * a string is a valid URL, starting http(s)
 * copied from: https://stackoverflow.com/a/43467144
 */
export const isValidHttpUrl = (s: string): boolean => {
    let url;
    try {
        url = new URL(s);
    } catch (_) {
        return false;
    }
    return url.protocol === "http:" || url.protocol === "https:";
}

/**
 * `s` may be a string, number or boolean. return `true` if it is a representation of a boolean, false otherwise.
 */
export const maybeBooleanToBoolean = (s: string|number|boolean|null): boolean => {
    s = unquote(s);
    return [true, "true", "1", 1].some(x => s === x);
}

/** abstract function generating validators: if `currentValue` is not in `allowedValues`, return `defaultValue` */
export function enforceValue(allowedValues:TPrimitive[], defaultValue:TPrimitive = ""): Function {
    return (currentValue:TPrimitive): TPrimitive => {
        currentValue = unquote(currentValue);

        return allowedValues.includes(currentValue)
            ? currentValue
            : defaultValue;
    }
}

export function enforceBooleanValue(defaultValue: boolean): Function {
    return enforceValue([true, false], defaultValue)
}

/**
 * if a value is nullish, return defaultValue.
 * a custom `resolver` function can be passed to check for specific constraints (i.e., is an array empty ?):
 * if it returns false, then `defaultValue` is returned.
 */
export function valueOrDefault(defaultValue: any, resolver: ((value:any)=>boolean)|undefined) {
    return (value: any) => {
        if (resolver) {
            return resolver(value) ? value : defaultValue;
        }
        return value || defaultValue
    };
}

/**
 * update a key-value pair of search parameters, without reloading the page (otherwise, would trigger infinite loop)
 * if `validateValueFunc` is provided, also validate `paramValue`.
 *
 * about using widow.history, see: https://stackoverflow.com/a/70591485
 *
 * NOTE: value must be JSON-stringifiable
 */
export function updateUrlSearchParams(validateValueFunc: Function|undefined, paramName: string, paramValue: any): any {
    // unquote so that url-to-form binding works with and without quoptes
    paramValue = unquote(paramValue);
    // don't JSON-stringify strings: JSON-stringifying a string will add ""
    // around it which will mess up url-to-form binding
    paramValue =  isArray(paramValue) || isObject(paramValue)
        ? JSON.stringify(paramValue)
        : paramValue;

    if (validateValueFunc) {
        paramValue = validateValueFunc(paramValue);
    }

    const url = new URL(window.location.href);
    url.searchParams.set(paramName, paramValue);
    window.history.pushState(null, '', url.toString());
    return paramValue
}

/**
 * split a CSV line into an array of fields, using double-quotes to escape commas
 */
export function parseCSVLine(line: string): string[] {
    if (line.indexOf('"') === -1) return line.split(",");

    const fields: string[] = [];
    let pos = 0;
    const len = line.length;

    while (pos <= len) {
        if (pos < len && line.charCodeAt(pos) === 34 /* " */) {
            pos++;
            let end = pos;
            let hasEscaped = false;
            while (end < len) {
                const q = line.indexOf('"', end);
                if (q === -1) {
                    end = len;
                    break;
                }
                if (q + 1 < len && line.charCodeAt(q + 1) === 34) {
                    hasEscaped = true;
                    end = q + 2;
                } else {
                    end = q;
                    break;
                }
            }
            const raw = line.substring(pos, end);
            fields.push(hasEscaped ? raw.replaceAll('""', '"') : raw);
            pos = end + 1;
            if (pos < len) pos++;
        } else {
            const comma = line.indexOf(",", pos);
            if (comma === -1) {
                fields.push(line.substring(pos));
                break;
            }
            fields.push(line.substring(pos, comma));
            pos = comma + 1;
        }
    }
    return fields;
}
