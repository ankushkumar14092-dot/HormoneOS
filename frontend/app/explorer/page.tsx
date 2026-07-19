"use client";
import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api";
import type { Patient } from "@/types";
import { UploadCloud, CheckCircle, AlertCircle, FileText, RefreshCw } from "lucide-react";

interface DatasetInfo {
  name: string;
  version: string;
  sha256_hash: string;
  transformation_history: { timestamp: string; operator: string; action: string }[];
  created_at: string;
}

export default function ExplorerPage() {
  const [datasetsList, setDatasetsList] = useState<DatasetInfo[]>([]);
  const [selectedDatasetName, setSelectedDatasetName] = useState<string>("");
  const [dataset, setDataset]   = useState<DatasetInfo | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [error, setError]       = useState<string | null>(null);

  // Uploader State
  const [inputName, setInputName] = useState("");
  const [inputVersion, setInputVersion] = useState("1.0.0");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.patients().then(setPatients).catch(() => {});

    // Fetch all registered datasets dynamically from backend list API
    api.datasets()
      .then((list) => {
        setDatasetsList(list);
        if (list.length > 0) {
          setSelectedDatasetName(list[0].name);
        } else {
          setError("No registered datasets found in the database. Use the uploader below to ingest custom timelines.");
        }
      })
      .catch(() => {
        setError("Backend offline — start the FastAPI server.");
      });
  }, []);

  useEffect(() => {
    if (!selectedDatasetName) return;
    
    api.datasetVersions(selectedDatasetName)
      .then((data) => {
        if (data && data.name) {
          setDataset(data);
          setError(null);
        } else {
          throw new Error("Invalid response format");
        }
      })
      .catch((err) => {
        setError(err.message || "Failed to load dataset details");
      });
  }, [selectedDatasetName]);

  // Dynamic Background Processing Polling
  useEffect(() => {
    if (!uploading || !selectedDatasetName) return;
    const interval = setInterval(() => {
      api.datasetVersions(selectedDatasetName)
        .then((data) => {
          if (data && data.name) {
            setDataset(data);
            const history = data.transformation_history || [];
            if (history.length > 0) {
              const lastAction = history[history.length - 1].action;
              setUploadProgress(lastAction);
              if (lastAction.includes("Completed") || lastAction.includes("Failed")) {
                setUploading(false);
                clearInterval(interval);
                // Refresh list of subjects and datasets
                api.patients().then(setPatients).catch(() => {});
                api.datasets().then(setDatasetsList).catch(() => {});
              }
            }
          }
        })
        .catch(() => {});
    }, 2000);
    return () => clearInterval(interval);
  }, [uploading, selectedDatasetName]);

  // Drag and Drop Handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      uploadFile(e.target.files[0]);
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  async function uploadFile(file: File) {
    if (!inputName.trim()) {
      alert("Please specify a Dataset Name before uploading files.");
      return;
    }
    setUploading(true);
    setUploadProgress("Uploading data file to repository...");
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", inputName.trim());
    formData.append("version", inputVersion.trim() || "1.0.0");

    try {
      const res = await fetch("http://localhost:8000/api/v1/datasets/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        throw new Error("Upload failed. Verify file parameters and server status.");
      }
      const data = await res.json();
      
      // Auto select the new dataset to poll status
      setSelectedDatasetName(data.name);
      setUploadProgress("File uploaded successfully. Registering pipeline workflow...");
    } catch (e: any) {
      setError(e.message || "Failed to upload and standardize dataset.");
      setUploading(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-8 pb-16">
      <div>
        <h1 className="text-xl font-semibold text-zinc-100 font-sans tracking-tight">Dataset Registry</h1>
        <p className="text-sm text-zinc-500 mt-1">Cryptographic hashes, data versions, and transformation lineage</p>
      </div>

      {error && (
        <div className="bg-red-950/40 border border-red-800 rounded-xl p-4 text-sm text-red-400 flex items-center gap-2">
          <AlertCircle size={16} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Dataset Block */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Ingest New Dataset</h2>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-[10px] text-zinc-500 font-semibold uppercase">Dataset Name</label>
            <input
              type="text"
              placeholder="e.g. mcphases-v1.0.0"
              className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 focus:border-violet-500 rounded-lg px-3 py-1.5 text-xs text-zinc-200 focus:outline-none transition-colors"
              value={inputName}
              onChange={(e) => setInputName(e.target.value)}
              disabled={uploading}
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] text-zinc-500 font-semibold uppercase">Version Tag</label>
            <input
              type="text"
              placeholder="e.g. 1.0.0"
              className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 focus:border-violet-500 rounded-lg px-3 py-1.5 text-xs text-zinc-200 focus:outline-none transition-colors"
              value={inputVersion}
              onChange={(e) => setInputVersion(e.target.value)}
              disabled={uploading}
            />
          </div>
        </div>

        {/* Drag Drop Area */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={triggerFileSelect}
          className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center gap-2 cursor-pointer transition-all duration-300 ${
            dragActive 
              ? "border-violet-500 bg-violet-950/10" 
              : "border-zinc-800 hover:border-zinc-700 bg-zinc-950/20"
          } ${uploading ? "pointer-events-none opacity-50" : ""}`}
        >
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".zip,.json,.xpt"
            onChange={handleFileChange}
            disabled={uploading}
          />
          <UploadCloud size={28} className={dragActive ? "text-violet-400" : "text-zinc-600"} />
          <p className="text-xs text-zinc-300 text-center font-medium">
            Drag &amp; drop <span className="text-violet-400">mcPHASES.zip</span>, NHANES <span className="text-violet-400">.xpt</span> files, or custom UHS <span className="text-violet-400">.json</span> files here
          </p>
          <p className="text-[10px] text-zinc-500">or click to browse local files</p>
        </div>

        {/* Upload Progress Logger */}
        {uploading && (
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 flex items-center gap-3">
            <RefreshCw className="animate-spin text-violet-400 shrink-0" size={15} />
            <div className="space-y-0.5 flex-1">
              <p className="text-[10px] text-zinc-500 font-semibold uppercase">UHS Pipeline Active</p>
              <p className="text-xs text-zinc-300">{uploadProgress}</p>
            </div>
          </div>
        )}
      </div>

      {/* Dataset Selection Dropdown */}
      {datasetsList.length > 0 && (
        <div className="flex items-center gap-3 bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <label className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Select Registered Dataset</label>
          <select
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-1.5 text-xs text-zinc-200"
            value={selectedDatasetName}
            onChange={(e) => setSelectedDatasetName(e.target.value)}
          >
            {datasetsList.map((d) => (
              <option key={d.name} value={d.name}>{d.name} (v{d.version})</option>
            ))}
          </select>
        </div>
      )}

      {dataset ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-zinc-100">{dataset.name}</span>
            <span className="text-xs bg-violet-900/50 text-violet-300 px-2 py-0.5 rounded-full">v{dataset.version}</span>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-zinc-500">SHA-256 Checksum</p>
            <p className="text-xs font-mono text-zinc-400 break-all">{dataset.sha256_hash}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-zinc-500">Registration Date</p>
            <p className="text-xs text-zinc-400">{new Date(dataset.created_at).toLocaleString()}</p>
          </div>

          <div>
            <p className="text-xs text-zinc-500 mb-2">Ingestion &amp; Transformation History</p>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {dataset.transformation_history?.map((t, i) => (
                <div key={i} className="border border-zinc-800 rounded-lg p-3 space-y-1 bg-zinc-950/20">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-violet-400 font-medium">{t.operator}</span>
                    <span className="text-[10px] text-zinc-600">{new Date(t.timestamp).toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-zinc-400">{t.action}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : !error ? (
        <div className="text-sm text-zinc-600">Loading dataset registry data…</div>
      ) : null}

      {/* Cohort Entities */}
      <div>
        <h2 className="text-xs font-semibold text-zinc-500 mb-3 uppercase tracking-widest">
          Cohort Subjects ({patients.length})
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {patients.map((p) => (
            <div key={p.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 space-y-1">
              <p className="text-xs font-bold text-zinc-300">Subject ID: {p.id}</p>
              <p className="text-[10px] text-zinc-500">Birth Year: {p.birth_year ?? "—"}</p>
              <p className="text-[9px] font-mono text-zinc-600 truncate">{p.uuid}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
