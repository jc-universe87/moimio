import React from 'react'
import ReactDOM from 'react-dom/client'
// v50c-3c-1a: polyfill HTML5 drag-and-drop events on touch devices
// (tablet, phone, touch-laptop). Side-effect import — just patches the
// browser's pointer events to dispatch drag events.
import 'drag-drop-touch'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
