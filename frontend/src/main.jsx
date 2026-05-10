// Entry point — equivalent to Python's if __name__ == "__main__"
// React.StrictMode catches subtle bugs in development (renders components twice to expose side effects)
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./App.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
