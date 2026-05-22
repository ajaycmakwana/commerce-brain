import 'core-js/stable'
import 'regenerator-runtime/runtime'
import ReactDOM from 'react-dom'
import App from './components/App'
import './index.css'

window.React = require('react')

// Render directly — no Experience Cloud Shell dependency
ReactDOM.render(
  <App />,
  document.getElementById('root')
)
