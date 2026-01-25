import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryProvider } from './providers/QueryProvider';
import { theme } from './theme/theme';
import { Layout } from './components/Layout';
import { SearchPage } from './pages/SearchPage';
import { ResultsPage } from './pages/ResultsPage';
import { QueriesPage } from './pages/QueriesPage';
import { AboutPage } from './pages/AboutPage';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

function App() {
  return (
    <QueryProvider>
      <MantineProvider theme={theme}>
        <Notifications />
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<SearchPage />} />
              <Route path="/results/*" element={<ResultsPage />} />
              <Route path="/queries" element={<QueriesPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </MantineProvider>
    </QueryProvider>
  );
}

export default App;
