/** @odoo-module **/

/**
 * Dynamic, data-bound building blocks: Field, Loop and Condition.
 *
 * Each is a custom GrapesJS component type whose binding lives in
 * ``data-rb-*`` attributes (so ``editor.getHtml()`` always serialises it).
 * The server compiler turns those attributes into QWeb directives.
 *
 * ``ctx`` carries { picker, rootModel } so trait dropdowns can be built from
 * the model's field list.
 */

function scopeFor(component, ctx) {
    // Walk up to the nearest Loop ancestor to resolve the binding scope.
    let node = component && component.parent && component.parent();
    while (node) {
        const fe = node.getAttributes ? node.getAttributes()["data-rb-foreach"] : null;
        const as = node.getAttributes ? node.getAttributes()["data-rb-as"] : null;
        if (fe && as) {
            const relName = String(fe).split(".").pop();
            const rel = ctx.picker.find(ctx.rootModel, relName);
            return { alias: as, model: (rel && rel.relation) || ctx.rootModel };
        }
        node = node.parent && node.parent();
    }
    return { alias: "doc", model: ctx.rootModel };
}

function buildSelect(options, current) {
    const sel = document.createElement("select");
    sel.className = "form-select form-select-sm";
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "— select —";
    sel.appendChild(blank);
    for (const opt of options) {
        const o = document.createElement("option");
        o.value = opt.value;
        o.textContent = opt.label;
        if (opt.value === current) {
            o.selected = true;
        }
        sel.appendChild(o);
    }
    return sel;
}

export function registerDynamicComponents(editor, ctx) {
    const dc = editor.DomComponents;
    const tm = editor.TraitManager;

    // --- custom trait: pick a field for the current scope -------------------
    tm.addType("rb-field-ref", {
        createInput({ component }) {
            const scope = scopeFor(component, ctx);
            const fields = ctx.picker.get(scope.model).map((f) => ({
                value: `${scope.alias}.${f.name}`,
                label: `${f.string} (${f.name})`,
            }));
            const current = component.getAttributes()["data-rb-field"] || "";
            const sel = buildSelect(fields, current);
            sel.addEventListener("change", () => {
                const val = sel.value;
                component.addAttributes({ "data-rb-field": val, "data-rb-out": "field" });
                const label = sel.options[sel.selectedIndex].textContent;
                component.components(val ? label : "Field");
            });
            return sel;
        },
    });

    // --- custom trait: pick an x2many field to repeat over ------------------
    tm.addType("rb-loop-ref", {
        createInput({ component }) {
            const scope = scopeFor(component, ctx);
            const x2m = ctx.picker.x2manyFields(scope.model).map((f) => ({
                value: `${scope.alias}.${f.name}`,
                label: `${f.string} (${f.name})`,
            }));
            const current = component.getAttributes()["data-rb-foreach"] || "";
            const sel = buildSelect(x2m, current);
            sel.addEventListener("change", () => {
                const val = sel.value;
                const attrs = { "data-rb-foreach": val };
                if (!component.getAttributes()["data-rb-as"]) {
                    attrs["data-rb-as"] = "line";
                }
                component.addAttributes(attrs);
                // Preload the related model's fields for inner Field traits.
                const relName = String(val).split(".").pop();
                const rel = ctx.picker.find(scope.model, relName);
                if (rel && rel.relation) {
                    ctx.picker.load(rel.relation);
                }
            });
            return sel;
        },
    });

    // --- Field --------------------------------------------------------------
    dc.addType("rb-field", {
        isComponent: (el) => el.hasAttribute && el.hasAttribute("data-rb-field"),
        model: {
            defaults: {
                name: "Field",
                droppable: false,
                attributes: { "data-rb-field": "", "data-rb-out": "field" },
                traits: [
                    { type: "rb-field-ref", name: "data-rb-field", label: "Field" },
                    { type: "text", name: "data-rb-field", label: "Expression",
                      changeProp: false },
                ],
            },
        },
    });

    // --- Loop ---------------------------------------------------------------
    dc.addType("rb-loop", {
        isComponent: (el) =>
            el.getAttribute && el.getAttribute("data-rb-foreach") !== null,
        model: {
            defaults: {
                name: "Loop",
                droppable: true,
                attributes: { "data-rb-foreach": "", "data-rb-as": "line" },
                traits: [
                    { type: "rb-loop-ref", name: "data-rb-foreach", label: "Repeat over" },
                    { type: "text", name: "data-rb-as", label: "Repeat as" },
                    { type: "text", name: "data-rb-if", label: "Only if (optional)" },
                ],
            },
        },
    });

    // --- Condition ----------------------------------------------------------
    dc.addType("rb-condition", {
        isComponent: (el) =>
            el.getAttribute &&
            el.getAttribute("data-rb-if") !== null &&
            el.getAttribute("data-rb-foreach") === null,
        model: {
            defaults: {
                name: "Condition",
                droppable: true,
                attributes: { "data-rb-if": "" },
                traits: [
                    { type: "text", name: "data-rb-if", label: "Show when" },
                ],
            },
        },
    });

    // --- blocks -------------------------------------------------------------
    const bm = editor.BlockManager;
    bm.add("rb-block-field", {
        category: "Data",
        label: "Field",
        media: '<i class="fa fa-tag"></i>',
        content: '<span data-rb-field="" data-rb-out="field">Field</span>',
    });
    bm.add("rb-block-loop", {
        category: "Data",
        label: "Loop",
        media: '<i class="fa fa-repeat"></i>',
        content:
            '<div data-rb-foreach="" data-rb-as="line" ' +
            'style="border:1px dashed #bbb;padding:6px;min-height:30px">' +
            "<span data-rb-field=\"line.display_name\" data-rb-out=\"field\">Line field</span></div>",
    });
    bm.add("rb-block-condition", {
        category: "Data",
        label: "Condition",
        media: '<i class="fa fa-question-circle"></i>',
        content:
            '<div data-rb-if="" ' +
            'style="border:1px dotted #bbb;padding:6px;min-height:30px">' +
            "Conditional content</div>",
    });
}
