const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const candidates = [
  path.join(root, 'node_modules', '@hotwired', 'turbo', 'dist', 'turbo.es2017-umd.js'),
  path.join(root, 'node_modules', '@hotwired', 'turbo', 'dist', 'turbo.es2017-umd.min.js'),
];
const source = candidates.find(fs.existsSync);
if (!source) {
  throw new Error('Turbo UMD bundle was not found. Run pnpm install before building assets.');
}

const destination = path.join(root, 'backend', 'app', 'static', 'js', 'turbo.js');
fs.copyFileSync(source, destination);
console.log(`Copied ${path.relative(root, source)} → ${path.relative(root, destination)}`);

const chartSource = path.join(root, 'node_modules', 'chart.js', 'dist', 'chart.umd.js');
if (!fs.existsSync(chartSource)) {
  throw new Error('Chart.js UMD bundle was not found. Run pnpm install before building assets.');
}
const chartDestination = path.join(root, 'backend', 'app', 'static', 'js', 'chart.js');
fs.copyFileSync(chartSource, chartDestination);
console.log(`Copied ${path.relative(root, chartSource)} → ${path.relative(root, chartDestination)}`);
