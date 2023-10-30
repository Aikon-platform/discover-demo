var path = require('path')
var webpack = require('webpack')
 
module.exports = {
  entry: './src/index.tsx',
  output: {
    path: path.resolve(__dirname, '../shared/static/dist/'),
    publicPath: '/static/dist/',
    filename: 'build.js',
    library: 'DemoTools',
  },
  plugins: [
  ],
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif|ico)$/i,
        type: 'asset/resource',
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  devtool: 'source-map',
  mode: 'development'
}