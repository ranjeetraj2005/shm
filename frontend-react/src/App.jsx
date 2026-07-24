import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import AdminPage from './pages/AdminPage';
import SubmitPage from './pages/SubmitPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<SubmitPage />} />
          <Route path="admin" element={<AdminPage />} />
          <Route path="report/:id" element={<SubmitPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
