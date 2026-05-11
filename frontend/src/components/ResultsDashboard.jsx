import { Button } from "@/components/ui/button";

const RISK_COLORS = {
  critical: { text: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/30", ring: "#ef4444", bar: "bg-red-500" },
  high:     { text: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/30", ring: "#f97316", bar: "bg-orange-500" },
  medium:   { text: "text-yellow-400", bg: "bg-yellow-500/10", border: "border-yellow-500/30", ring: "#eab308", bar: "bg-yellow-500" },
  low:      { text: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30", ring: "#10b981", bar: "bg-emerald-500" },
};

const CATEGORY_ICONS = {
  DATA_BREACH:    "🔑",
  INFRASTRUCTURE: "🖥️",
  PHISHING:       "🎣",
  IMPERSONATION:  "👤",
  STALKING:       "📍",
  REPUTATIONAL:   "📝",
};

function scoreColors(score) {
  if (score >= 75) return RISK_COLORS.critical;
  if (score >= 50) return RISK_COLORS.high;
  if (score >= 25) return RISK_COLORS.medium;
  return RISK_COLORS.low;
}

function ScoreRing({ score, riskLevel }) {
  const colors = RISK_COLORS[riskLevel] || RISK_COLORS.low;
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex h-40 w-40 shrink-0 items-center justify-center">
      <svg className="absolute inset-0 -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="rgb(39 39 42)" strokeWidth="8" />
        <circle
          cx="60" cy="60" r={radius} fill="none"
          stroke={colors.ring} strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
      </svg>
      <div className="flex flex-col items-center">
        <span className={`font-display text-4xl font-black ${colors.text}`}>{score}</span>
        <span className="text-xs text-zinc-500">/100</span>
      </div>
    </div>
  );
}

function PlatformCard({ finding }) {
  const { platform, found, url, error } = finding;

  let dot, dotClass, labelClass, label, borderClass, bgClass;
  if (found) {
    dot = "●"; dotClass = "text-red-400";
    label = "Found"; labelClass = "text-red-400";
    borderClass = "border-red-500/20"; bgClass = "bg-red-500/5";
  } else if (error) {
    dot = "◌"; dotClass = "text-zinc-600";
    label = "Unavailable"; labelClass = "text-zinc-600";
    borderClass = "border-zinc-800/40"; bgClass = "bg-zinc-900/20";
  } else {
    dot = "○"; dotClass = "text-emerald-400";
    label = "Not found"; labelClass = "text-emerald-500";
    borderClass = "border-emerald-500/10"; bgClass = "bg-zinc-900/20";
  }

  return (
    <div className={`flex items-start gap-2.5 rounded-lg border p-3 ${borderClass} ${bgClass}`}>
      <span className={`mt-0.5 font-mono text-sm ${dotClass}`}>{dot}</span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-zinc-200">{platform}</p>
        <p className={`text-xs ${labelClass}`}>{label}</p>
        {found && url && (
          <a
            href={url} target="_blank" rel="noopener noreferrer"
            className="mt-0.5 block truncate text-[10px] text-zinc-600 transition-colors hover:text-indigo-400"
          >
            {url.replace(/^https?:\/\//, "").slice(0, 40)}
          </a>
        )}
        {error && (
          <p className="mt-0.5 truncate text-[10px] text-zinc-700" title={error}>
            {error.split("—")[0].trim()}
          </p>
        )}
      </div>
    </div>
  );
}

export default function ResultsDashboard({ results, onNewScan }) {
  const { query, query_type, findings = [], threat_report } = results;
  const report = threat_report || {};
  const riskLevel = report.risk_level || "low";
  const colors = RISK_COLORS[riskLevel] || RISK_COLORS.low;
  const score = Math.round(report.overall_score || 0);

  const foundCount = findings.filter(f => f.found).length;
  const errorCount = findings.filter(f => !f.found && f.error).length;
  const cleanCount = findings.length - foundCount - errorCount;

  return (
    <div className="relative z-10 mx-auto max-w-6xl px-6 pb-16 pt-8 md:px-12">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400">Scan Complete</p>
          <h2 className="font-display mt-1 text-xl font-bold text-white">
            Results for{" "}
            <span className="text-indigo-300">{query}</span>
            <span className="ml-2 rounded-full border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-xs font-normal text-zinc-400">
              {query_type}
            </span>
          </h2>
          <p className="mt-1 text-xs text-zinc-500">
            {foundCount} exposed · {cleanCount} clean · {errorCount} unavailable · {findings.length} platforms scanned
          </p>
        </div>
        <Button
          onClick={onNewScan}
          className="shrink-0 cursor-pointer border border-zinc-700 bg-zinc-800/50 text-sm text-zinc-300 hover:bg-zinc-700"
        >
          ← New Scan
        </Button>
      </div>

      {/* Score card */}
      <div className={`mb-6 flex flex-col gap-6 rounded-2xl border p-6 backdrop-blur-sm sm:flex-row sm:items-center ${colors.border} ${colors.bg}`}>
        <ScoreRing score={score} riskLevel={riskLevel} />
        <div className="flex-1">
          <span className={`inline-block rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wide ${colors.text} ${colors.border} bg-zinc-900/60`}>
            {riskLevel} risk
          </span>
          <p className="mt-3 text-sm leading-relaxed text-zinc-300">
            {report.summary || "Scan complete."}
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Categories */}
        <div className="lg:col-span-1">
          <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-zinc-400">
            Risk Categories
          </h3>
          <div className="flex flex-col gap-3">
            {(report.category_scores || []).map(cat => {
              const c = scoreColors(cat.score);
              return (
                <div key={cat.category} className="rounded-xl border border-zinc-800/60 bg-zinc-900/40 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-sm font-medium text-zinc-200">
                      <span>{CATEGORY_ICONS[cat.category] || "⚠️"}</span>
                      <span className="capitalize">{cat.category.replace(/_/g, " ")}</span>
                    </span>
                    <span className={`text-sm font-bold ${c.text}`}>{Math.round(cat.score)}</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${c.bar}`}
                      style={{ width: `${cat.score}%` }}
                    />
                  </div>
                  {cat.warnings?.length > 0 && (
                    <p className="mt-2 text-[11px] leading-relaxed text-zinc-500">{cat.warnings[0]}</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Platforms + Recommendations */}
        <div className="flex flex-col gap-6 lg:col-span-2">
          {/* Platform grid */}
          <div>
            <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-zinc-400">
              Platform Findings
            </h3>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-3 xl:grid-cols-4">
              {findings.map(f => (
                <PlatformCard key={f.platform} finding={f} />
              ))}
            </div>
          </div>

          {/* Recommendations */}
          {(report.recommendations || []).length > 0 && (
            <div>
              <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-zinc-400">
                Recommendations
              </h3>
              <div className="flex flex-col gap-2">
                {report.recommendations.map((rec, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-zinc-800/50 bg-zinc-900/30 px-4 py-3 text-sm leading-relaxed text-zinc-300"
                  >
                    {rec}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
