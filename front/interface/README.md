# Front-end reactive interface

This folder contains the code for the JS components, as well as for the stylesheets.

## Installation for development

### Basic setup

If you want to develop those components, you need first to [install pnpm](https://pnpm.io/installation) or [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm), for example this way:

```bash
# Install pnpm
curl -fsSL https://get.pnpm.io/install.sh | sh -
```

You then need to initialize (p)npm in the interface folder, and install all required packages:

```bash
cd interface # if not already in the folder
pnpm install # or npm install
```

You can then start the vite compiler from the interface folder:

```bash
pnpm run build --watch # or npm run dev
```

This will start a vite server that will provide the js and css files, and update them on-the-go when you modify them.

### More efficient development

`pnpm run build --watch` is reactive, but pretty slow (bulma is a bit heavy). Moreover, it provides minified output, good for committing but not for debugging.

Vite comes with a more efficient way to test the changes, that require a bit more setup.

From the interface folder, instead of running `pnpm run build --watch`, run:

```bash
pnpm run dev
```

This will start a vite server that will provide the js and css files. Now, to have them fetched in the django templates, you need to modify the file [shared/templates/demowebsite/base.html](../shared/templates/demowebsite/base.html#L9), and modify:

```html
{% if debug and False %}{# Set true to enable to develop locally using pnpm run dev #}
```

to:

```html
{% if debug and True %}
```

**WARNING**: do not commit this change, or future developers won't be able to test their changes without running `pnpm run dev`.

With this method:
- js updates on-the-go inside the browser, enabling very fast development
- css too, but slower (because of bulma)
- js debugging contains source maps, so you can debug the original files

It's better to commit production static files. To generate them (js & css), run:

```bash
# in front/interface
pnpm run build
```

## Source code organization

### Usage

As the JS is only used in specific templates, this is not a Svelte app, but a Svelte component library providing with mounting functions, to be called when needed.

The main entry point for the code is [src/main.ts](src/main.ts) ; it exposes the mounting functions into `window.DemoTools`. They can then be called in the django templates **only by wrapping the call into a `document.addEventListener("DOMContentLoaded", () => { init...() })`**.

### Apps

The code is grouped into Apps, mirroring the django folders. Many shared components are available in the [shared](shared) folder. The SimilarityApp uses the ClusterApp.

Each app declare its components, among which a main component `App.svelte`. The apps also declare their types and util converters (from django data to internal structures), and sometimes a reactive state.

### External dependencies

We use [bits-ui](https://bits-ui.com) to provide with some UI components. We also use [iconify](https://iconify.design) for icons, and [bulma](https://bulma.io) for styling.

### Stylesheets

Svelte can handle stylesheets within the components, but as there are many shared elements, and svelte in-component styling has some scope issues with bits-ui, all the styles are outsourced to a [sass](sass) folder. Its structure also mirrors the apps structure.
