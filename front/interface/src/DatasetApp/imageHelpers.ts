/**
 * Open a file, resize it and reformat as JPEG
 * @param file
 * @param max_size
 */
export async function preprocessImage(file: File, max_size: number = 2048, callback: (blob: Blob | null) => void) {
    if (!file.type.startsWith("image/")) {
        throw new Error("File is not an image");
    }

    const reader = new FileReader();
    reader.readAsArrayBuffer(file);

    reader.onload = function (event) {
      if (!event.target?.result) {
        throw new Error("Failed to read file");
      }
      const blob = new Blob([event.target.result as ArrayBuffer]);
      window.URL = window.URL || window.webkitURL;
      const blobURL = window.URL.createObjectURL(blob);

      // helper Image object
      var image = new Image();
      image.src = blobURL;

      image.onload = function() {
        resizeImage(image, max_size, callback);
      }
    };
}

/**
 * Resize an image, reformat as JPEG and call a callback with the result
 * @param image
 * @param max_size
 * @param callback
 * @returns
 */
export function resizeImage(image: HTMLImageElement, max_size: number = 2048, callback: (blob: Blob | null) => void) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        throw new Error("Failed to get canvas context");
    }

    const width = image.width;
    const height = image.height;

    if (width > max_size || height > max_size) {
        const ratio = Math.min(max_size / width, max_size / height);
        canvas.width = width * ratio;
        canvas.height = height * ratio;
        ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    } else {
        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    }

    return canvas.toBlob(callback, "image/jpeg", 0.85);
}
