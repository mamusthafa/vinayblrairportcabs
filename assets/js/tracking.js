/**
 * BLR Airport Cab — Conversion & Analytics Tracking
 * Integrates with Google Tag Manager, GA4, and Google Ads.
 */

(function () {
  'use strict';

  // Initialize dataLayer
  window.dataLayer = window.dataLayer || [];

  /**
   * Helper to dispatch standard analytics events
   * @param {string} eventName
   * @param {Object} eventParams
   */
  window.trackCabEvent = function (eventName, eventParams) {
    var params = Object.assign({
      page_path: window.location.pathname,
      page_title: document.title,
      timestamp: new Date().toISOString()
    }, eventParams || {});

    window.dataLayer.push({
      event: eventName,
      cab_data: params
    });

    // Also trigger gtag if present
    if (typeof window.gtag === 'function') {
      window.gtag('event', eventName, params);
    }

    if (window.console && window.location.hostname === 'localhost') {
      console.log('[BLR Cab Analytics]', eventName, params);
    }
  };

  document.addEventListener('DOMContentLoaded', function () {
    // 1. Phone Call Clicks
    document.querySelectorAll('a[href^="tel:"]').forEach(function (el) {
      el.addEventListener('click', function () {
        window.trackCabEvent('phone_click', {
          destination_number: el.getAttribute('href').replace('tel:', ''),
          click_location: el.dataset.trackLocation || 'page_element'
        });
      });
    });

    // 2. WhatsApp Direct Clicks
    document.querySelectorAll('a[href*="wa.me"], a[href*="api.whatsapp.com"]').forEach(function (el) {
      el.addEventListener('click', function () {
        window.trackCabEvent('whatsapp_click', {
          click_location: el.dataset.trackLocation || 'page_element'
        });
      });
    });
  });
})();
