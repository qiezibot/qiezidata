// Script to upload image to file input
(async () => {
  const input = document.querySelector('input[type="file"][accept*="image"]');
  if (!input) return 'no input found';
  
  // Create a test image via canvas
  const canvas = document.createElement('canvas');
  canvas.width = 800;
  canvas.height = 600;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#8B5CF6';
  ctx.fillRect(0, 0, 800, 600);
  ctx.fillStyle = 'white';
  ctx.font = 'bold 48px Arial';
  ctx.textAlign = 'center';
  ctx.fillText('TEST', 400, 300);
  
  const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', 0.9));
  const file = new File([blob], 'test.jpg', {type: 'image/jpeg'});
  const dt = new DataTransfer();
  dt.items.add(file);
  
  // Set files on input and trigger change
  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'files').set;
  nativeInputValueSetter.call(input, dt.files);
  input.dispatchEvent(new Event('change', {bubbles: true}));
  
  return 'uploaded ' + file.name + ' size: ' + file.size;
})();
