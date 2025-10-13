// Webpack Entry Point

// Vendor libraries
import $ from 'jquery';
window.jQuery = window.$ = $;

import './jquery-expose.js';
import 'query-command-supported';
import 'textarea-caret';
import * as cbor from 'cbor-js';

// D3 - selective imports for tree shaking
import {
  select,
  scaleLinear,
  scaleBand,
  scaleSymlog,
  scaleOrdinal,
  axisBottom,
  axisLeft,
  stack,
  stackOrderNone,
  stackOffsetNone,
  sum,
  max,
  format,
  interpolate
} from 'd3';

window.CBOR = cbor;
window.d3 = {
  select,
  scaleLinear,
  scaleBand,
  scaleSymlog,
  scaleOrdinal,
  axisBottom,
  axisLeft,
  stack,
  stackOrderNone,
  stackOffsetNone,
  sum,
  max,
  format,
  interpolate
};

window.NotifyModules = window.NotifyModules || {};

// Core modules
import './modules/init.js';
import './modules/uswds-modules.js';
import './modules/show-hide-content.js';
import { registerModule, initModules } from './moduleRegistry.js';

// Local modules
import './radioSelect.js';
import './liveSearch.js';
import './preventDuplicateFormSubmissions.js';
import { ErrorBanner } from './errorBanner.js';
import './notifyModal.js';
import './timeoutPopup.js';
import { initCurrentYear } from './date.js';
import { initLoginAlert } from './loginAlert.js';
import './sidenav.js';
import './validation.js';
import './scrollPosition.js';

initCurrentYear();
initLoginAlert();

// NotifyModules
import './copyToClipboard.js';
import './enhancedTextbox.js';
import './fileUpload.js';
import './errorTracking.js';
import './templateFolderForm.js';
import './collapsibleCheckboxes.js';
import './radioSlider.js';
import './updateStatus.js';
import './main.js';
import './listEntry.js';
import './stick-to-window-when-scrolling.js';
import './totalMessagesChart.js';
import './activityChart.js';
import './job-polling.js';
