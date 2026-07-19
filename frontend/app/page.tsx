"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Activity, Database, Users, Cpu, Layers, Share2, Award, Terminal, Dna, HelpCircle
} from "lucide-react";

export default function DashboardPage() {
  const [patients, setPatients] = useState<number | null>(null);
  const [datasets, setDatasets] = useState<number | null>(null);
  const [embeddings, setEmbeddings] = useState<number | null>(null);

  useEffect(() => {
    api.health().then((h: any) => {
      setPatients(h.n_patients ?? 0);
      setDatasets(h.n_datasets ?? 0);
      setEmbeddings(h.n_embeddings ?? 0);
    }).catch(() => {
      api.patients().then((p) => setPatients(p.length)).catch(() => setPatients(0));
      setDatasets(0);
      setEmbeddings(0);
    });
  }, []);

  const metrics = [
    { label: "Patients Processed",       value: patients !== null ? patients.toLocaleString() : "—", icon: Users,    color: "text-violet-400" },
    { label: "Datasets Standardized",    value: datasets !== null ? `${datasets} Active` : "—",      icon: Database, color: "text-sky-400"    },
    { label: "Representations Generated", value: embeddings !== null ? embeddings.toLocaleString() : "—",       icon: Cpu,      color: "text-emerald-400"},
    { label: "Research Tasks Supported",  value: "2 Benchmarks",  icon: Award,    color: "text-pink-400"   },
  ];

  const contributions = [
    {
      title: "1. Universal Hormonal Schema (UHS)",
      desc: "An open data format that aligns clinical variables, sensor telemetry, and patient logs into a standardized timeline."
    },
    {
      title: "2. Hormone State Foundation (HSF)",
      desc: "A foundation temporal representation model converting longitudinal multimodal data into reusable 128-d embeddings."
    },
    {
      title: "3. Representation Registry",
      desc: "A central database layer for indexing, sharing, and querying generated HSF representations for cohort analysis."
    },
    {
      title: "4. Benchmark Framework",
      desc: "A standardized evaluation center running cross-validation tasks (phase classification, hormone prediction) to score model performance."
    },
    {
      title: "5. Research API",
      desc: "A developer-ready query interface exposing UHS, HSF inference, and similarity comparisons to downstream applications."
    }
  ];

  const downstreamTasks = [
    {
      name: "Menstrual Phase Classification",
      desc: "Predicting biological cycle phases from unaligned wearable sensor telemetry.",
      metric: "Phase Classification Benchmark"
    },
    {
      name: "Hormone Level Regression",
      desc: "Estimating absolute estrogen/progesterone levels from non-invasive wearable signals.",
      metric: "Hormone Regression Benchmark"
    },
    {
      name: "Cohort Trajectory Comparison",
      desc: "Measuring alignment and distance of patients' dynamic trajectories using DTW + Cosine scoring.",
      metric: "Representation Comparison Service"
    }
  ];

  const workflow = [
    "Dataset Ingestion",
    "UHS Standardization",
    "Timeline Compilation",
    "HSF Representation Engine",
    "Registry Indexing",
    "Benchmark Validation",
    "Downstream Tasks"
  ];

  const ecosystem = [
    { name: "Researchers", desc: "Access clean UHS cohorts instantly" },
    { name: "Universities", desc: "Benchmark novel temporal architectures" },
    { name: "Hospitals", desc: "Extract longitudinal representation vectors" },
    { name: "Health AI Startups", desc: "Fine-tune HSF for target clinical tasks" },
    { name: "Foundation Models", desc: "Consume pre-trained embeddings directly" }
  ];

  return (
    <div className="max-w-4xl space-y-12 pb-16">
      {/* 1. HERO */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-medium bg-violet-950/40 text-violet-300 border border-violet-800/30">
          <Terminal size={10} /> Hack-Nation Finalist Entry
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-zinc-100 font-sans">HormoneOS</h1>
        <p className="text-sm text-zinc-400">
          Open Research Infrastructure for Longitudinal Women&apos;s Hormonal AI
        </p>
      </div>

      {/* RESEARCH METRICS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-zinc-900/50 border border-zinc-800/80 rounded-xl p-4 space-y-2">
            <Icon size={16} className={color} />
            <p className="text-xl font-bold text-zinc-100">{value}</p>
            <p className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider">{label}</p>
          </div>
        ))}
      </div>

      {/* 2. WHY HORMONEOS EXISTS */}
      <div className="bg-zinc-900 border border-violet-900/35 rounded-xl p-6 space-y-3 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-24 h-24 bg-violet-600/5 blur-2xl rounded-full" />
        <h3 className="text-xs font-semibold text-violet-400 uppercase tracking-widest">Why HormoneOS Exists</h3>
        <p className="text-sm text-zinc-300 leading-relaxed font-medium">
          Every research group repeatedly spends time integrating heterogeneous women&apos;s health datasets before they can even begin training AI models. HormoneOS standardizes this process through a reusable research infrastructure, allowing researchers to focus on scientific discovery instead of data integration.
        </p>
      </div>

      {/* 3. PROBLEM & RESEARCH GAP */}
      <div className="grid md:grid-cols-2 gap-5">
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center gap-2 text-zinc-300">
            <HelpCircle size={15} className="text-zinc-500" />
            <h3 className="text-xs font-semibold uppercase tracking-widest">The Problem</h3>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Disconnected health timelines (wearables, hormone labs, symptom logs) are locked in siloed, consumer-facing applications, blocking comparative biomedical research.
          </p>
        </div>
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center gap-2 text-zinc-300">
            <Layers size={15} className="text-zinc-500" />
            <h3 className="text-xs font-semibold uppercase tracking-widest">The Research Gap</h3>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Current systems focus on isolated patient interfaces instead of reusable representation models. Researchers spend 80% of their energy engineering bespoke ETL code instead of analyzing clinical representations.
          </p>
        </div>
      </div>

      {/* 4. SCIENTIFIC CONTRIBUTIONS */}
      <div className="space-y-4">
        <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Scientific Contributions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {contributions.map(({ title, desc }) => (
            <div key={title} className="bg-zinc-900/30 border border-zinc-800/80 rounded-xl p-5 space-y-2">
              <h3 className="text-xs font-bold text-zinc-200">{title}</h3>
              <p className="text-xs text-zinc-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 5. RESEARCH WORKFLOW */}
      <div className="space-y-4">
        <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Research Workflow</h2>
        <div className="bg-zinc-900/20 border border-zinc-800/60 rounded-xl p-6 overflow-x-auto">
          <div className="flex items-center gap-2 min-w-[700px] py-2">
            {workflow.map((item, idx) => (
              <div key={item} className="flex items-center gap-2">
                <div className="bg-zinc-900 border border-zinc-800 px-3 py-2 rounded-lg text-center shrink-0">
                  <p className="text-[10px] font-mono text-zinc-400 font-semibold">{item}</p>
                </div>
                {idx < workflow.length - 1 && (
                  <span className="text-zinc-700 font-mono text-xs select-none">➜</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 6. ARCHITECTURE */}
      <div className="grid md:grid-cols-2 gap-5">
        <div className="bg-zinc-900 border border-violet-900/30 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Dna size={16} className="text-violet-400" />
              <p className="text-xs text-violet-400 font-bold uppercase tracking-widest">Universal Hormonal Schema (UHS)</p>
            </div>
            <p className="text-xs text-zinc-300 leading-relaxed">
              Maps unaligned wearable telemetry, symptom inputs, glucose, and lab results into a clean, validated schema. Built with extensibility to support emerging EHR schemas.
            </p>
          </div>
          <p className="text-[10px] text-zinc-500 mt-4 italic border-t border-zinc-800/60 pt-3">
            *Planned compatibility with HL7 FHIR health interoperability standards.
          </p>
        </div>
        <div className="bg-zinc-900 border border-sky-900/30 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <Cpu size={16} className="text-sky-400" />
            <p className="text-xs text-sky-400 font-bold uppercase tracking-widest">Hormone State Foundation (HSF)</p>
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed">
            HSF is a foundation representation model that converts longitudinal multimodal women&apos;s health data into reusable AI embeddings for downstream research tasks.
          </p>
        </div>
      </div>

      {/* 7. EXAMPLE DOWNSTREAM RESEARCH TASKS */}
      <div className="space-y-4">
        <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Example Downstream Research Tasks</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {downstreamTasks.map(({ name, desc, metric }) => (
            <div key={name} className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex flex-col justify-between space-y-4">
              <div className="space-y-2">
                <h3 className="text-xs font-bold text-zinc-200">{name}</h3>
                <p className="text-[11px] text-zinc-400 leading-relaxed">{desc}</p>
              </div>
              <div className="border-t border-zinc-800/60 pt-3">
                <span className="text-[9px] font-mono text-zinc-500">{metric}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 8. RESEARCH ECOSYSTEM */}
      <div className="space-y-4">
        <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Research Ecosystem</h2>
        <div className="bg-zinc-900/20 border border-zinc-800/60 rounded-xl p-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {ecosystem.map(({ name, desc }) => (
              <div key={name} className="bg-zinc-900/50 border border-zinc-800 p-4 rounded-xl space-y-1 text-center flex flex-col justify-between">
                <h4 className="text-xs font-bold text-zinc-200">{name}</h4>
                <p className="text-[10px] text-zinc-500 leading-relaxed mt-1">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
