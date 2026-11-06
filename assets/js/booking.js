/**
 * BLR Airport Cab — Interactive Booking Form Engine
 * Handles service tabs, field validation, context awareness, and WhatsApp message construction.
 */

(function () {
  'use strict';

  var WHATSAPP_PHONE = '919180182667';

  function initBookingWidgets() {
    var widgets = document.querySelectorAll('.booking-widget-container');
    if (!widgets.length) return;

    widgets.forEach(function (widget) {
      setupSingleWidget(widget);
    });
  }

  function setupSingleWidget(widget) {
    var tabs = widget.querySelectorAll('.tab-btn');
    var form = widget.querySelector('.booking-form');
    var serviceInput = widget.querySelector('input[name="service_type"]');
    var pickupGroup = widget.querySelector('.group-pickup');
    var dropGroup = widget.querySelector('.group-drop');
    var pickupInput = widget.querySelector('input[name="pickup_location"]');
    var dropInput = widget.querySelector('input[name="drop_location"]');
    var dateInput = widget.querySelector('input[name="travel_date"]');
    var timeInput = widget.querySelector('input[name="travel_time"]');
    var vehicleSelect = widget.querySelector('select[name="vehicle_type"]');
    var packageSelectGroup = widget.querySelector('.group-package-select');
    var flightGroup = widget.querySelector('.group-flight');

    // 1. Constrain Travel Date: Minimum is today
    if (dateInput) {
      var today = new Date();
      var yyyy = today.getFullYear();
      var mm = String(today.getMonth() + 1).padStart(2, '0');
      var dd = String(today.getDate()).padStart(2, '0');
      dateInput.min = yyyy + '-' + mm + '-' + dd;
      if (!dateInput.value) {
        dateInput.value = yyyy + '-' + mm + '-' + dd;
      }
    }

    // 2. Set default time to current time + 2 hours
    if (timeInput && !timeInput.value) {
      var now = new Date();
      now.setHours(now.getHours() + 2);
      var hh = String(now.getHours()).padStart(2, '0');
      var min = String(now.getMinutes()).padStart(2, '0');
      timeInput.value = hh + ':' + min;
    }

    // 3. Tab Switching Function
    function switchTab(tabId) {
      tabs.forEach(function (btn) {
        if (btn.dataset.tab === tabId) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });

      if (serviceInput) serviceInput.value = tabId;

      // Adjust fields based on tab
      if (tabId === 'airport-drop') {
        if (dropInput) {
          dropInput.value = 'Kempegowda International Airport (BLR)';
          dropInput.setAttribute('readonly', 'readonly');
        }
        if (pickupInput) {
          pickupInput.removeAttribute('readonly');
          if (pickupInput.value === 'Kempegowda International Airport (BLR)') {
            pickupInput.value = '';
          }
          pickupInput.placeholder = 'Enter Bengaluru address / locality (e.g. Indiranagar)';
        }
        if (flightGroup) flightGroup.style.display = 'none';
        if (packageSelectGroup) packageSelectGroup.style.display = 'none';
        if (pickupGroup) pickupGroup.style.display = 'flex';
        if (dropGroup) dropGroup.style.display = 'flex';
      } else if (tabId === 'airport-pickup') {
        if (pickupInput) {
          pickupInput.value = 'Kempegowda International Airport (BLR)';
          pickupInput.setAttribute('readonly', 'readonly');
        }
        if (dropInput) {
          dropInput.removeAttribute('readonly');
          if (dropInput.value === 'Kempegowda International Airport (BLR)') {
            dropInput.value = '';
          }
          dropInput.placeholder = 'Enter drop address in Bengaluru (e.g. Whitefield)';
        }
        if (flightGroup) flightGroup.style.display = 'grid';
        if (packageSelectGroup) packageSelectGroup.style.display = 'none';
        if (pickupGroup) pickupGroup.style.display = 'flex';
        if (dropGroup) dropGroup.style.display = 'flex';
      } else if (tabId === 'local-package') {
        if (pickupInput) {
          pickupInput.removeAttribute('readonly');
          if (pickupInput.value === 'Kempegowda International Airport (BLR)') pickupInput.value = '';
          pickupInput.placeholder = 'Enter pickup locality (e.g. Koramangala)';
        }
        if (packageSelectGroup) packageSelectGroup.style.display = 'flex';
        if (dropGroup) dropGroup.style.display = 'none';
        if (flightGroup) flightGroup.style.display = 'none';
        if (pickupGroup) pickupGroup.style.display = 'flex';
      } else if (tabId === 'outstation') {
        if (pickupInput) {
          pickupInput.removeAttribute('readonly');
          if (pickupInput.value === 'Kempegowda International Airport (BLR)') pickupInput.value = '';
          pickupInput.placeholder = 'Enter Bangalore pickup address';
        }
        if (dropInput) {
          dropInput.removeAttribute('readonly');
          if (dropInput.value === 'Kempegowda International Airport (BLR)') dropInput.value = '';
          dropInput.placeholder = 'Destination City (e.g. Mysore, Coorg, Ooty, Tirupati)';
        }
        if (dropGroup) dropGroup.style.display = 'flex';
        if (flightGroup) flightGroup.style.display = 'none';
        if (packageSelectGroup) packageSelectGroup.style.display = 'none';
        if (pickupGroup) pickupGroup.style.display = 'flex';
      }
    }

    tabs.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        switchTab(this.dataset.tab);
      });
    });

    // 4. Auto-detect context from page URL or data-attribute
    var defaultTab = widget.dataset.defaultTab;
    if (!defaultTab) {
      var path = window.location.pathname;
      if (path.indexOf('bangalore-to-airport-cab') !== -1) {
        defaultTab = 'airport-drop';
      } else if (path.indexOf('bangalore-airport-pickup') !== -1) {
        defaultTab = 'airport-pickup';
      } else if (path.indexOf('bangalore-local-taxi') !== -1 || path.indexOf('bangalore-hourly-cab-rental') !== -1 || path.indexOf('bangalore-sightseeing') !== -1) {
        defaultTab = 'local-package';
      } else if (path.indexOf('bangalore-outstation-cabs') !== -1) {
        defaultTab = 'outstation';
      } else {
        defaultTab = 'airport-drop';
      }
    }
    switchTab(defaultTab);

    // 5. Handle Form Submission -> Build WhatsApp Message
    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();

        // Validation
        var nameInput = form.querySelector('input[name="customer_name"]');
        var phoneInput = form.querySelector('input[name="customer_phone"]');
        var consentCheck = form.querySelector('input[name="consent"]');

        var name = nameInput ? nameInput.value.trim() : '';
        var phone = phoneInput ? phoneInput.value.trim() : '';

        if (!name) {
          alert('Please enter your name.');
          if (nameInput) nameInput.focus();
          return;
        }

        // Validate 10-digit phone
        var cleanPhone = phone.replace(/[^0-9]/g, '');
        if (cleanPhone.length < 10) {
          alert('Please enter a valid 10-digit mobile number.');
          if (phoneInput) phoneInput.focus();
          return;
        }

        if (consentCheck && !consentCheck.checked) {
          alert('Please agree to share these details for your cab enquiry.');
          consentCheck.focus();
          return;
        }

        var serviceType = serviceInput ? serviceInput.value : 'Airport Transfer';
        var serviceLabel = 'Airport Transfer';
        if (serviceType === 'airport-drop') serviceLabel = 'Airport Drop (City → BLR Airport)';
        if (serviceType === 'airport-pickup') serviceLabel = 'Airport Pickup (BLR Airport → City)';
        if (serviceType === 'local-package') serviceLabel = 'Bangalore Local Cab Package';
        if (serviceType === 'outstation') serviceLabel = 'Outstation Cab Journey';

        var pickupLoc = pickupInput ? pickupInput.value.trim() : '';
        var dropLoc = dropInput ? dropInput.value.trim() : '';
        var travelDate = dateInput ? dateInput.value : '';
        var travelTime = timeInput ? timeInput.value : '';
        var vehicle = vehicleSelect ? vehicleSelect.value : 'Sedan';
        var passengersInput = form.querySelector('select[name="passengers"]');
        var passengers = passengersInput ? passengersInput.value : '1-2';
        var notesInput = form.querySelector('textarea[name="special_requests"]');
        var notes = notesInput ? notesInput.value.trim() : '';

        var pkgSelect = form.querySelector('select[name="package_duration"]');
        var selectedPkg = (pkgSelect && serviceType === 'local-package') ? pkgSelect.value : '';

        var flightNumInput = form.querySelector('input[name="flight_number"]');
        var flightNum = (flightNumInput && serviceType === 'airport-pickup') ? flightNumInput.value.trim() : '';

        // Construct clean WhatsApp text
        var msgLines = [
          '🚖 *BLR AIRPORT CAB — BOOKING ENQUIRY*',
          '━━━━━━━━━━━━━━━━━━━━',
          '• *Service:* ' + serviceLabel,
          '• *Pickup:* ' + (pickupLoc || 'Not specified'),
          (serviceType !== 'local-package' ? '• *Drop:* ' + (dropLoc || 'Not specified') : '• *Package:* ' + (selectedPkg || 'Standard City Package')),
          '• *Date:* ' + travelDate,
          '• *Time:* ' + travelTime,
          '• *Vehicle:* ' + vehicle,
          '• *Passengers:* ' + passengers,
          (flightNum ? '• *Flight:* ' + flightNum : ''),
          (notes ? '• *Notes:* ' + notes : ''),
          '━━━━━━━━━━━━━━━━━━━━',
          '• *Customer Name:* ' + name,
          '• *Mobile:* ' + phone,
          '',
          'Please confirm vehicle availability and rate quote. Thank you!'
        ].filter(function (line) { return line !== ''; });

        var waText = encodeURIComponent(msgLines.join('\n'));
        var waUrl = 'https://wa.me/' + WHATSAPP_PHONE + '?text=' + waText;

        // Analytics conversion events
        if (typeof window.trackCabEvent === 'function') {
          window.trackCabEvent('whatsapp_enquiry', {
            service_type: serviceType,
            vehicle: vehicle,
            pickup_location: pickupLoc,
            drop_location: dropLoc
          });
          window.trackCabEvent('lead_form_submit', {
            form_id: 'booking_widget_form'
          });
        }

        // Open WhatsApp in new tab / app
        window.open(waUrl, '_blank');
      });
    }
  }

  document.addEventListener('DOMContentLoaded', initBookingWidgets);
})();
