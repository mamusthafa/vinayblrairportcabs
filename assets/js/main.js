/**
 * BLR Airport Cab — Main Interaction Script
 * Mobile drawer navigation, FAQ accordions, sticky header, modal handler.
 */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Drawer Navigation & Backdrop Handler
    var menuToggle = document.getElementById('mobileNavToggle') || document.querySelector('.mobile-nav-toggle');
    var drawerClose = document.getElementById('mobileDrawerClose') || document.querySelector('.mobile-drawer-close');
    var mainNav = document.getElementById('mainNavigation') || document.querySelector('.main-navigation');
    var backdrop = document.getElementById('mobileNavBackdrop') || document.querySelector('.mobile-nav-backdrop');

    function openMobileMenu() {
      if (mainNav) mainNav.classList.add('open');
      if (backdrop) backdrop.classList.add('open');
      if (menuToggle) {
        menuToggle.setAttribute('aria-expanded', 'true');
        menuToggle.classList.add('active');
        menuToggle.innerHTML = '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"/></svg>';
      }
      document.body.classList.add('mobile-nav-open');
    }

    function closeMobileMenu() {
      if (mainNav) mainNav.classList.remove('open');
      if (backdrop) backdrop.classList.remove('open');
      if (menuToggle) {
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.classList.remove('active');
        menuToggle.innerHTML = '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16"/></svg>';
      }
      document.body.classList.remove('mobile-nav-open');
    }

    if (menuToggle) {
      menuToggle.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var isOpen = mainNav && mainNav.classList.contains('open');
        if (isOpen) {
          closeMobileMenu();
        } else {
          openMobileMenu();
        }
      });
    }

    if (drawerClose) {
      drawerClose.addEventListener('click', function (e) {
        e.preventDefault();
        closeMobileMenu();
      });
    }

    if (backdrop) {
      backdrop.addEventListener('click', function () {
        closeMobileMenu();
      });
    }

    // Close mobile drawer on Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mainNav && mainNav.classList.contains('open')) {
        closeMobileMenu();
      }
    });

    // Mobile Dropdown Accordion Toggles
    var dropdownToggles = document.querySelectorAll('.nav-dropdown-toggle');
    dropdownToggles.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var parentItem = btn.closest('.has-dropdown');
        if (parentItem) {
          var isExpanded = parentItem.classList.contains('dropdown-open');
          // Close other open mobile dropdowns
          document.querySelectorAll('.has-dropdown.dropdown-open').forEach(function (other) {
            if (other !== parentItem) {
              other.classList.remove('dropdown-open');
              var otherBtn = other.querySelector('.nav-dropdown-toggle');
              if (otherBtn) otherBtn.setAttribute('aria-expanded', 'false');
            }
          });
          if (isExpanded) {
            parentItem.classList.remove('dropdown-open');
            btn.setAttribute('aria-expanded', 'false');
          } else {
            parentItem.classList.add('dropdown-open');
            btn.setAttribute('aria-expanded', 'true');
          }
        }
      });
    });

    // Close mobile drawer when terminal destination links are clicked
    if (mainNav) {
      mainNav.querySelectorAll('a').forEach(function (link) {
        link.addEventListener('click', function () {
          // If modal trigger, close mobile menu and let modal open
          if (link.getAttribute('data-open-modal')) {
            closeMobileMenu();
            return;
          }
          // Normal links: close drawer
          closeMobileMenu();
        });
      });
    }

    // 2. FAQ Accordion Toggle
    var faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(function (item) {
      var question = item.querySelector('.faq-question');
      if (question) {
        question.addEventListener('click', function () {
          var isActive = item.classList.contains('active');
          // Close others
          faqItems.forEach(function (other) {
            other.classList.remove('active');
          });
          if (!isActive) {
            item.classList.add('active');
          }
        });
      }
    });

    // 3. Quick Booking Modal Handler
    var modalTriggers = document.querySelectorAll('[data-open-modal="booking-modal"]');
    var modalOverlay = document.getElementById('booking-modal');
    var modalClose = document.querySelectorAll('.modal-close');

    if (modalOverlay) {
      modalTriggers.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          modalOverlay.classList.add('open');
          document.body.style.overflow = 'hidden';
        });
      });

      modalClose.forEach(function (btn) {
        btn.addEventListener('click', function () {
          modalOverlay.classList.remove('open');
          document.body.style.overflow = '';
        });
      });

      modalOverlay.addEventListener('click', function (e) {
        if (e.target === modalOverlay) {
          modalOverlay.classList.remove('open');
          document.body.style.overflow = '';
        }
      });

      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modalOverlay.classList.contains('open')) {
          modalOverlay.classList.remove('open');
          document.body.style.overflow = '';
        }
      });
    }

    // 4. Header Shadow on Scroll
    var header = document.querySelector('.site-header');
    if (header) {
      window.addEventListener('scroll', function () {
        if (window.scrollY > 20) {
          header.classList.add('scrolled');
        } else {
          header.classList.remove('scrolled');
        }
      }, { passive: true });
    }
  });
})();
