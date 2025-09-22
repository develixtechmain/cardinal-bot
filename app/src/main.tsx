import {StrictMode} from "react";

import "./global-styles.css";
import {createRoot} from "react-dom/client";

import App from "./App";
import "./errorHandlers";

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <App />
    </StrictMode>
);
