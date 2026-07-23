const fs = require('fs');
let f = fs.readFileSync('railway_file_server.py','utf8');

// In _USER template, change delMyFile to use DELETE method
const old = "delMyFile(id){if(!confirm('确定删除?'))return;fetch('/delete/'+id,{method:'POST',credentials:'include'})";
const neu = "delMyFile(id){if(!confirm('确定删除?'))return;fetch('/delete/'+id,{method:'DELETE',credentials:'include'})";

if(f.includes(old)) {
  f = f.replace(old, neu);
  // In admin, delFile already uses DELETE method
  fs.writeFileSync('railway_file_server.py', f, 'utf8');
  console.log('Fixed delMyFile method to DELETE');
} else {
  console.log('Pattern not found, checking...');
  const idx = f.indexOf('delMyFile');
  if(idx >= 0) console.log('Found at', idx, ':', f.substring(idx, idx+200));
  else console.log('delMyFile not found');
}
