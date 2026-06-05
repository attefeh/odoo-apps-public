/** @odoo-module **/

import { registry } from "@web/core/registry";

// Replaces the upstream `tour_service`
// (web_tour/static/src/js/tour_service.js:294) with an inert no-op. Even a
// direct `odoo.startTour(...)` call from the browser console or a URL
// parameter falls through to an empty function, so tours cannot start by any
// path: auto-start at session boot, manual start, recorder, or URL trigger.
const disabledTourService = {
    dependencies: [],
    start() {
        const noop = () => {};
        odoo.startTour = noop;
        odoo.isTourReady = () => Promise.resolve(false);
        return {
            startTour: noop,
            startTourRecorder: noop,
        };
    },
};

registry
    .category("services")
    .add("tour_service", disabledTourService, { force: true });
