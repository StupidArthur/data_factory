import { Routes, Route } from 'react-router-dom'
import ConfigList from './pages/ConfigList'
import ConfigEdit from './pages/ConfigEdit'

function App() {
  return (
    <Routes>
      <Route path="/" element={<ConfigList />} />
      <Route path="/config_edit" element={<ConfigEdit />} />
      <Route path="/config_edit/:id" element={<ConfigEdit />} />
    </Routes>
  )
}

export default App
