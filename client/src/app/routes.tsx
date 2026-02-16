import { createBrowserRouter } from "react-router-dom";
import WelcomePage from "../pages/WelcomePage";
import FindingsPage from "../pages/FindingsPage";
import OptimizationPage from "../pages/OptimizationPage";

export const router = createBrowserRouter([
  { path: "/", element: <WelcomePage /> },
  { path: "/findings", element: <FindingsPage /> },
  { path: "/optimization", element: <OptimizationPage /> },
]);
