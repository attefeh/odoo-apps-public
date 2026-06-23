/** @odoo-module **/

/**
 * Caches the field list of each model so trait dropdowns can be built
 * synchronously after a one-off async fetch.
 */
export class FieldPicker {
    constructor(orm) {
        this.orm = orm;
        this.cache = {};
    }

    /** Return (and cache) the field descriptors for a model. */
    async load(model) {
        if (!model) {
            return [];
        }
        if (!this.cache[model]) {
            this.cache[model] = await this.orm.call(
                "report.builder.template",
                "get_model_fields",
                [model]
            );
        }
        return this.cache[model];
    }

    /** Synchronous accessor; returns [] if not loaded yet. */
    get(model) {
        return this.cache[model] || [];
    }

    /** x2many fields of a model (candidates for loops). */
    x2manyFields(model) {
        return this.get(model).filter((f) => f.is_x2many);
    }

    /** Find a field descriptor by technical name. */
    find(model, name) {
        return this.get(model).find((f) => f.name === name);
    }
}
