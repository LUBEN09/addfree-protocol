// Placeholder webpack config for web extension build
module.exports = {
  mode: 'development',
  entry: './src/background.js',
  output: {
    filename: 'background.bundle.js',
    path: __dirname + '/dist'
  }
};
