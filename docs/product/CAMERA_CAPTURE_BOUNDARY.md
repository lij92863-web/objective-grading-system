# Camera and Capture Boundary

The product supports three practical inputs:

1. Manual upload of JPG/JPEG/PNG files.
2. Polling a teacher-selected folder for new JPG/JPEG/PNG files.
3. Browser camera capture with `navigator.mediaDevices`, followed by a normal
   image upload to the local server.

The browser can use only cameras visible to the operating system and browser.
If a phone or other device is exposed by a driver as a Windows camera, it may
appear in that list. Connecting a phone with an ordinary USB data cable usually
provides file transfer only and does **not** let this product control the phone
camera.

The backend never claims to enumerate or control USB phone cameras. The camera
probe reports availability gracefully; lack of a camera does not stop manual or
watched-folder capture.

All sources converge on the same safe operation: validate an image extension
and payload, copy bytes below the session upload directory, calculate SHA-256,
deduplicate, then create a queued `CaptureJob`. File names never determine
student identity or answers. Future device integrations must produce the same
upload contract and cannot call recognition or finalization directly.
