const fs = require('fs');
const f = fs.readFileSync('railway_file_server.py','utf8');

// Find delMyFile in _USER context
const idx = f.indexOf('delMyFile');
if(idx >= 0) {
  console.log('=== delMyFile ===');
  console.log(f.substring(idx, idx+250));
}

// Check delete route
const d = f.indexOf("app.delete('/delete/{fid}')");
console.log('\n=== delete route at ===');
console.log(d >= 0 ? f.substring(d, d+100) : 'NOT FOUND');

// Check if POST delete exists
const dp = f.indexOf("app.post('/delete/");
console.log('\n=== post delete ===');
console.log(dp >= 0 ? f.substring(dp, dp+100) : 'NOT FOUND');
