/** @odoo-module **/

/** Register the plain (non-dynamic) building blocks in the block manager. */
export function registerStaticBlocks(editor) {
    const bm = editor.BlockManager;
    const base = { category: "Layout" };

    bm.add("rb-text", {
        ...base,
        label: "Text",
        content: '<p style="padding:4px">Insert your text here</p>',
        media: '<i class="fa fa-font"></i>',
    });
    bm.add("rb-heading", {
        ...base,
        label: "Heading",
        content: "<h2>Heading</h2>",
        media: '<i class="fa fa-header"></i>',
    });
    bm.add("rb-image", {
        ...base,
        label: "Image",
        content: { type: "image" },
        media: '<i class="fa fa-image"></i>',
    });
    bm.add("rb-divider", {
        ...base,
        label: "Divider",
        content: '<hr/>',
        media: '<i class="fa fa-minus"></i>',
    });
    bm.add("rb-columns", {
        ...base,
        label: "2 Columns",
        content:
            '<div class="row"><div class="col-6" style="padding:8px">Column 1</div>' +
            '<div class="col-6" style="padding:8px">Column 2</div></div>',
        media: '<i class="fa fa-columns"></i>',
    });
    bm.add("rb-container", {
        ...base,
        label: "Container",
        content: '<div style="padding:8px;min-height:40px"></div>',
        media: '<i class="fa fa-square-o"></i>',
    });
    bm.add("rb-table", {
        ...base,
        label: "Table",
        content:
            '<table class="table"><thead><tr><th>Column</th></tr></thead>' +
            "<tbody><tr><td>Cell</td></tr></tbody></table>",
        media: '<i class="fa fa-table"></i>',
    });
}
