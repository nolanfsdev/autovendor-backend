// src/App.jsx
import { useState } from "react";

/* -------------------------------------------------
 *  Simple PDF-upload front-end for AutoVendor
 * -------------------------------------------------*/
export default function App() {
  const [file, setFile]         = useState(null);       // PDF file object
  const [isUploading, setBusy]  = useState(false);      // spinner toggle
  const [result, setResult]     = useState(null);       // backend response
  const [error, setError]       = useState(null);       // error message

  // ↳ Handle <input type="file" …>
  function handleSelect(e) {
    setError(null);
    setResult(null);
    const f = e.target.files?.[0];
    if (f && !f.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }
    setFile(f);
  }

  // ↳ POST /upload to FastAPI
  async function handleUpload() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file, file.name);

      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const { detail } = await res.json();
        throw new Error(detail || `Upload failed (${res.status})`);
      }

      const data = await res.json(); // { flags: { … } }
      setResult(data.flags);
    } catch (err) {
      setError(err.message || "Unknown error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex flex-col items-center gap-6 p-10 font-sans">
      {/* ---------- Upload Card ---------- */}
      <section className="w-full max-w-md rounded-xl border p-6 shadow">
        <h1 className="mb-4 text-xl font-semibold text-center">Upload a Contract</h1>

        <input
          type="file"
          accept="application/pdf"
          onChange={handleSelect}
          className="w-full mb-4 file:mr-3 file:rounded-lg file:border-0 file:bg-indigo-600 file:px-4 file:py-2 file:text-white"
        />

        <button
          onClick={handleUpload}
          disabled={!file || isUploading}
          className={`w-full rounded-lg bg-indigo-600 py-2 font-medium text-white 
                     hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300`}
        >
          {isUploading ? "Uploading…" : "Upload"}
        </button>

        {/* ---------- Status ---------- */}
        {error && (
          <p className="mt-4 rounded bg-red-100 p-3 text-sm text-red-700">{error}</p>
        )}

        {result && (
          <pre className="mt-4 overflow-auto rounded bg-gray-100 p-4 text-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </section>
    </main>
  );
}
