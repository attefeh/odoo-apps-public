/** @odoo-module **/

import { registerStaticBlocks } from "./blocks_static";
import { registerDynamicComponents } from "./blocks_dynamic";

/**
 * Initialise a GrapesJS editor inside ``el`` and register our blocks.
 *
 * GrapesJS is shipped as a UMD bundle in static/lib and attaches itself to the
 * global scope (like Chart.js), so we read it from ``window``.
 *
 * @param {HTMLElement} el  container element for the editor
 * @param {Object} ctx      { picker, rootModel }
 * @returns {Object} the GrapesJS editor instance
 */
export function buildEditor(el, ctx) {
    const grapesjs = window.grapesjs;
    if (!grapesjs) {
        throw new Error("GrapesJS library failed to load");
    }

    const editor = grapesjs.init({
        container: el,
        height: "100%",
        fromElement: false,
        storageManager: false,
        // Keep the canvas self-contained; report styling comes from Odoo at print.
        canvas: {},
        blockManager: { appendTo: ctx.blocksEl },
        traitManager: { appendTo: ctx.traitsEl },
        layerManager: { appendTo: ctx.layersEl },
        selectorManager: { appendTo: ctx.stylesEl },
        styleManager: { appendTo: ctx.stylesEl },
        panels: { defaults: [] },
    });

    registerDynamicComponents(editor, ctx);
    registerStaticBlocks(editor);

    return editor;
}
