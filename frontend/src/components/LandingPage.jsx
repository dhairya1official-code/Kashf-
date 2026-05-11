import { useState, useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import ResultsDashboard from "@/components/ResultsDashboard";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

const stats = [
    { value: "20+", label: "Platforms Scanned" },
    { value: "< 60s", label: "Scan Time" },
    { value: "100%", label: "Local & Private" },
];

const features = [
    {
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="size-5">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.3-4.3" />
                <path d="M11 8a3 3 0 0 0-3 3" />
            </svg>
        ),
        title: "Scout",
        desc: "Autonomously discovers hidden accounts across thousands of platforms.",
    },
    {
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="size-5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                <path d="m9 12 2 2 4-4" />
            </svg>
        ),
        title: "Auditor",
        desc: "Analyzes data clusters locally to calculate your Privacy Threat Score.",
    },
    {
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="size-5">
                <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
                <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
                <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
                <line x1="2" x2="22" y1="2" y2="22" />
            </svg>
        ),
        title: "Ghost",
        desc: "Auto-generates GDPR/CCPA-compliant takedown notices to data brokers.",
    },
];

export default function LandingPage() {
    const [query, setQuery] = useState("");
    const [scanPhase, setScanPhase] = useState("idle"); // "idle" | "scanning" | "complete"
    const [taskId, setTaskId] = useState(null);
    const [progress, setProgress] = useState(0);
    const [scanResults, setScanResults] = useState(null);
    const [error, setError] = useState(null);
    const pollRef = useRef(null);

    const queryType = query.includes("@") ? "email" : "username";

    const handleSubmit = async (e) => {
        e.preventDefault();
        const trimmed = query.trim();
        if (!trimmed) return;

        setError(null);
        setScanPhase("scanning");
        setProgress(0);

        try {
            const res = await fetch(`${API_BASE}/search`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: trimmed, query_type: queryType }),
            });
            if (!res.ok) {
                const body = await res.json().catch(() => ({}));
                throw new Error(body.detail || `Server error ${res.status}`);
            }
            const data = await res.json();
            setTaskId(data.task_id);
        } catch (err) {
            setError(err.message);
            setScanPhase("idle");
        }
    };

    useEffect(() => {
        if (!taskId) return;

        const poll = async () => {
            try {
                const res = await fetch(`${API_BASE}/results/${taskId}`);
                if (!res.ok) return;
                const data = await res.json();
                setProgress(data.progress || 0);

                if (data.status === "completed") {
                    clearInterval(pollRef.current);
                    setScanResults(data);
                    setScanPhase("complete");
                } else if (data.status === "failed") {
                    clearInterval(pollRef.current);
                    setError("Scan failed — please try again");
                    setScanPhase("idle");
                }
            } catch {
                // ignore transient polling errors
            }
        };

        pollRef.current = setInterval(poll, 2000);
        poll(); // immediate first check
        return () => clearInterval(pollRef.current);
    }, [taskId]);

    const handleNewScan = () => {
        clearInterval(pollRef.current);
        setScanPhase("idle");
        setTaskId(null);
        setScanResults(null);
        setProgress(0);
        setError(null);
    };

    // ── Results view ──────────────────────────────────────────────────
    if (scanPhase === "complete" && scanResults) {
        return (
            <div className="relative min-h-screen overflow-hidden font-sans">
                <div className="orb orb-1" />
                <div className="orb orb-2" />
                <nav className="relative z-10 flex items-center justify-between px-6 py-5 md:px-12 lg:px-20">
                    <div className="flex items-center gap-2.5">
                        <div className="relative flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-5">
                                <circle cx="11" cy="11" r="8" />
                                <path d="m21 21-4.3-4.3" />
                            </svg>
                        </div>
                        <span className="font-display text-xl font-bold tracking-tight text-white">Kashf</span>
                    </div>
                </nav>
                <ResultsDashboard results={scanResults} onNewScan={handleNewScan} />
            </div>
        );
    }

    // ── Landing page ──────────────────────────────────────────────────
    const isScanning = scanPhase === "scanning";

    return (
        <div className="relative min-h-screen overflow-hidden font-sans">
            {/* ===== Background Effects ===== */}
            <div className="cyber-grid">
                <div className="circuit-line" />
                <div className="circuit-line" />
                <div className="circuit-line" />
                <div className="circuit-line" />
            </div>

            <div className="orb orb-1" />
            <div className="orb orb-2" />
            <div className="orb orb-3" />

            <div className="scan-line" />
            <div className="noise-overlay" />

            {/* ===== Navbar ===== */}
            <nav className="relative z-10 flex items-center justify-between px-6 py-5 md:px-12 lg:px-20">
                <div className="flex items-center gap-2.5">
                    <div className="relative flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-5">
                            <circle cx="11" cy="11" r="8" />
                            <path d="m21 21-4.3-4.3" />
                        </svg>
                    </div>
                    <span className="font-display text-xl font-bold tracking-tight text-white">
                        Kashf
                    </span>
                </div>

                <div className="hidden items-center gap-6 md:flex">
                    <a href="#features" className="text-sm text-zinc-400 transition-colors hover:text-white">
                        Features
                    </a>
                    <a href="#how-it-works" className="text-sm text-zinc-400 transition-colors hover:text-white">
                        How It Works
                    </a>
                    <div className="h-4 w-px bg-zinc-700" />
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        AMD Slingshot 2026
                    </span>
                </div>
            </nav>

            {/* ===== Hero Section ===== */}
            <main className="relative z-10 flex flex-col items-center justify-center px-6 pt-16 pb-24 md:pt-24 lg:pt-32">
                {/* Badge */}
                <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/5 px-4 py-1.5 backdrop-blur-sm">
                    <span className="h-2 w-2 rounded-full bg-indigo-400 animate-pulse" />
                    <span className="text-xs font-medium tracking-wide text-indigo-300 uppercase">
                        Agentic AI · Privacy Auditor
                    </span>
                </div>

                {/* Headline */}
                <h1
                    id="hero-headline"
                    className="font-display max-w-4xl text-center text-4xl font-extrabold leading-[1.1] tracking-tight sm:text-5xl md:text-6xl lg:text-7xl"
                >
                    <span className="text-white">Uncover Your</span>
                    <br />
                    <span className="gradient-text">Digital Shadow</span>
                </h1>

                {/* Subline */}
                <p
                    id="hero-subline"
                    className="mt-6 max-w-2xl text-center text-base leading-relaxed text-zinc-400 sm:text-lg md:text-xl"
                >
                    Enter your email or username to map your scattered footprint across the internet.
                    <span className="hidden sm:inline"> See what the web knows about you — </span>
                    <span className="hidden sm:inline font-medium text-zinc-300">before someone else does.</span>
                </p>

                {/* ===== CTA Form ===== */}
                <form
                    id="scan-form"
                    onSubmit={handleSubmit}
                    className="relative mt-10 flex w-full max-w-xl flex-col gap-3 sm:flex-row sm:gap-0"
                >
                    <div className="pulse-ring rounded-xl hidden sm:block" />

                    <div className="relative flex-1">
                        <Input
                            id="query-input"
                            type="text"
                            placeholder={isScanning ? `Scanning… ${progress}%` : "Email or username…"}
                            value={isScanning ? "" : query}
                            onChange={(e) => setQuery(e.target.value)}
                            disabled={isScanning}
                            required
                            className="glow-input h-12 rounded-xl border-zinc-700/50 bg-zinc-900/80 pl-11 pr-4 text-sm text-white placeholder:text-zinc-500 backdrop-blur-sm sm:rounded-r-none sm:border-r-0 md:text-base disabled:opacity-60"
                        />
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-zinc-500"
                        >
                            <circle cx="11" cy="11" r="8" />
                            <path d="m21 21-4.3-4.3" />
                        </svg>
                    </div>

                    <Button
                        id="scan-button"
                        type="submit"
                        disabled={isScanning || !query.trim()}
                        className="glow-button h-12 cursor-pointer rounded-xl px-7 text-sm font-semibold tracking-wide text-white sm:rounded-l-none md:text-base disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        {isScanning ? (
                            <span className="flex items-center gap-2">
                                <svg className="size-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                Scanning…
                            </span>
                        ) : (
                            <span className="flex items-center gap-2">
                                Initiate Scan
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-4">
                                    <path d="M5 12h14" />
                                    <path d="m12 5 7 7-7 7" />
                                </svg>
                            </span>
                        )}
                    </Button>
                </form>

                {/* Progress bar */}
                {isScanning && (
                    <div className="mt-4 w-full max-w-xl">
                        <div className="h-1 w-full overflow-hidden rounded-full bg-zinc-800">
                            <div
                                className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                        <p className="mt-2 text-center text-xs text-zinc-500">
                            Scanning 20 platforms for <span className="text-zinc-300">{query}</span>…
                        </p>
                    </div>
                )}

                {/* Query type hint */}
                {!isScanning && query.trim() && (
                    <p className="mt-2 text-xs text-zinc-600">
                        Detected as{" "}
                        <span className="text-indigo-400 font-medium">{queryType}</span>
                    </p>
                )}

                {/* Error */}
                {error && (
                    <p className="mt-3 flex items-center gap-1.5 text-sm text-red-400">
                        <span>⚠</span> {error}
                    </p>
                )}

                {/* Privacy note */}
                {!isScanning && (
                    <p className="mt-4 flex items-center gap-1.5 text-xs text-zinc-500">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="size-3.5 text-emerald-500">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                        </svg>
                        100% local processing. Your data never leaves your machine.
                    </p>
                )}

                {/* ===== Stats Bar ===== */}
                <div className="mt-16 grid w-full max-w-2xl grid-cols-3 gap-4 md:mt-20">
                    {stats.map((stat, i) => (
                        <div
                            key={i}
                            className="fade-in-up flex flex-col items-center gap-1 rounded-xl border border-zinc-800/50 bg-zinc-900/30 px-4 py-5 backdrop-blur-sm transition-colors hover:border-indigo-500/20 hover:bg-zinc-900/50"
                        >
                            <span className="font-display text-xl font-bold text-white sm:text-2xl">
                                {stat.value}
                            </span>
                            <span className="text-xs font-medium tracking-wider text-zinc-500 uppercase">
                                {stat.label}
                            </span>
                        </div>
                    ))}
                </div>

                {/* ===== Features Section ===== */}
                <section id="features" className="mt-24 w-full max-w-4xl md:mt-32">
                    <div className="mb-12 text-center">
                        <span className="text-xs font-semibold tracking-widest text-indigo-400 uppercase">
                            How It Works
                        </span>
                        <h2 className="font-display mt-3 text-2xl font-bold text-white sm:text-3xl">
                            Three Autonomous AI Agents
                        </h2>
                        <p className="mt-3 text-sm text-zinc-400 sm:text-base">
                            Our agentic AI architecture operates in three phases, all processed locally on your AMD Ryzen&trade; AI NPU.
                        </p>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-3">
                        {features.map((feat, i) => (
                            <div
                                key={i}
                                className="group relative flex flex-col gap-4 rounded-2xl border border-zinc-800/60 bg-zinc-900/40 p-6 backdrop-blur-sm transition-all duration-300 hover:border-indigo-500/30 hover:bg-zinc-900/60 hover:shadow-lg hover:shadow-indigo-500/5"
                            >
                                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 transition-colors group-hover:bg-indigo-500/20">
                                    {feat.icon}
                                </div>
                                <span className="font-mono text-xs text-zinc-600">
                                    0{i + 1}
                                </span>
                                <h3 className="font-display text-lg font-semibold text-white">
                                    The {feat.title}
                                </h3>
                                <p className="text-sm leading-relaxed text-zinc-400">
                                    {feat.desc}
                                </p>
                                <div className="absolute inset-0 -z-10 rounded-2xl bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                            </div>
                        ))}
                    </div>
                </section>

                {/* ===== Footer ===== */}
                <footer className="mt-24 flex flex-col items-center gap-3 border-t border-zinc-800/50 pt-8 md:mt-32">
                    <div className="flex items-center gap-4 text-xs text-zinc-500">
                        <span>Built with ❤️ for AMD Slingshot 2026</span>
                        <span className="h-3 w-px bg-zinc-700" />
                        <span>Team Kashf</span>
                    </div>
                    <p className="text-[11px] text-zinc-600">
                        © 2026 Kashf — Agentic AI Privacy Auditor. All rights reserved.
                    </p>
                </footer>
            </main>
        </div>
    );
}
