/* Project specific Javascript goes here. */

// Avatar Cropper functionality
(function() {
  'use strict';

  let cropper = null;

  // Wait for Cropper.js to be available (retry mechanism)
  function waitForCropper(callback, maxAttempts) {
    let attempts = 0;
    const check = function() {
      attempts++;
      if (typeof Cropper !== 'undefined') {
        callback();
      } else if (attempts < maxAttempts) {
        setTimeout(check, 100);
      } else {
        console.error('Cropper.js failed to load after', maxAttempts, 'attempts');
      }
    };
    check();
  }

  // Initialize cropper when modal content is loaded via HTMX
  document.body.addEventListener('htmx:afterSettle', function(event) {
    if (event.detail.target.id === 'avatar-modal-content') {
      waitForCropper(initAvatarCropper, 50);
    }
  });

  function initAvatarCropper() {
    const avatarInput = document.getElementById('avatar-input');
    const cropperContainer = document.getElementById('cropper-container');
    const cropperImage = document.getElementById('cropper-image');
    const previewContainer = document.getElementById('preview-container');
    const uploadBtn = document.getElementById('upload-avatar-btn');
    const rotateLeftBtn = document.getElementById('rotate-left');
    const rotateRightBtn = document.getElementById('rotate-right');
    const uploadForm = document.getElementById('avatar-upload-form');

    if (!avatarInput || !cropperImage) {
      console.log('Avatar cropper: missing elements');
      return;
    }

    // Check if Cropper.js is loaded
    if (typeof Cropper === 'undefined') {
      console.error('Cropper.js is not loaded!');
      return;
    }
    console.log('Avatar cropper: initialized, Cropper.js available');

    // Handle file selection
    avatarInput.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (!file) return;

      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file.');
        return;
      }

      // Validate file size (1MB max)
      if (file.size > 1024 * 1024) {
        alert('Image is too large. Maximum size is 1MB.');
        return;
      }

      const reader = new FileReader();
      reader.onload = function(event) {
        // Destroy existing cropper if any
        if (cropper) {
          cropper.destroy();
          cropper = null;
        }

        // Show cropper container
        cropperContainer.classList.remove('d-none');
        previewContainer.classList.remove('d-none');
        uploadBtn.classList.remove('d-none');

        // Function to initialize cropper
        function initCropperOnImage() {
          console.log('Image ready, initializing Cropper.js');
          try {
            // Initialize Cropper.js after image is loaded
            cropper = new Cropper(cropperImage, {
              aspectRatio: 1,
              viewMode: 1,
              dragMode: 'move',
              autoCropArea: 1,
              restore: false,
              guides: true,
              center: true,
              highlight: false,
              cropBoxMovable: true,
              cropBoxResizable: true,
              toggleDragModeOnDblclick: false,
              preview: '#avatar-preview',
            });
            console.log('Cropper.js initialized successfully', cropper);
          } catch (err) {
            console.error('Error initializing Cropper.js:', err);
          }
        }

        // Set image source and wait for it to load
        cropperImage.src = event.target.result;

        // Handle both cached and non-cached images
        if (cropperImage.complete && cropperImage.naturalHeight !== 0) {
          // Image already loaded (cached)
          initCropperOnImage();
        } else {
          // Wait for image to load
          cropperImage.onload = initCropperOnImage;
          cropperImage.onerror = function() {
            console.error('Failed to load image');
          };
        }
      };
      reader.readAsDataURL(file);
    });

    // Rotation buttons
    if (rotateLeftBtn) {
      rotateLeftBtn.addEventListener('click', function() {
        if (cropper) cropper.rotate(-90);
      });
    }

    if (rotateRightBtn) {
      rotateRightBtn.addEventListener('click', function() {
        if (cropper) cropper.rotate(90);
      });
    }

    // Handle form submission with HTMX
    if (uploadForm) {
      uploadForm.addEventListener('htmx:configRequest', function(event) {
        if (!cropper) return;

        // Get the cropped canvas
        const canvas = cropper.getCroppedCanvas({
          width: 400,
          height: 400,
          imageSmoothingEnabled: true,
          imageSmoothingQuality: 'high',
        });

        // Convert canvas to blob and add to form data
        canvas.toBlob(function(blob) {
          // Create FormData with the blob
          const formData = new FormData();
          formData.append('avatar', blob, 'avatar.png');

          // Get CSRF token
          const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
          formData.append('csrfmiddlewaretoken', csrfToken);

          // Submit via fetch instead of letting HTMX handle it
          fetch(uploadForm.getAttribute('hx-post'), {
            method: 'POST',
            body: formData,
            headers: {
              'HX-Request': 'true',
            },
          })
          .then(response => {
            // Get the HX-Trigger header
            const trigger = response.headers.get('HX-Trigger');
            return response.text().then(html => ({ html, trigger }));
          })
          .then(({ html, trigger }) => {
            document.getElementById('avatar-modal-content').innerHTML = html;
            // Trigger any HTMX events
            if (trigger) {
              document.body.dispatchEvent(new CustomEvent('avatarUpdated'));
            }
          })
          .catch(error => {
            console.error('Upload failed:', error);
            alert('Upload failed. Please try again.');
          });
        }, 'image/png', 0.9);

        // Prevent HTMX from processing
        event.preventDefault();
      });
    }
  }

  // Clean up cropper when modal is hidden
  document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('avatarCropModal');
    if (modal) {
      modal.addEventListener('hidden.bs.modal', function() {
        if (cropper) {
          cropper.destroy();
          cropper = null;
        }
      });
    }
  });
})();
