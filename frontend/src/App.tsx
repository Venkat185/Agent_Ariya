import {
  FormEvent,
  KeyboardEvent,
  Suspense,
  lazy,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  AnalysisHistoryItem,
  Artifact,
  DatasetFull,
  DatasetProfile,
  analyzeDataset,
  fetchFullDataset,
  profileDataset
} from "./lib/api";

const PlotlyArtifact = lazy(() => import("./components/PlotlyArtifact"));

function AssistantSummary({ text }: { text: string }) {
  return (
    <div className="message-text">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </div>
  );
}

const STARTER_PROMPTS = [
  "Summarize this dataset and highlight key insights",
  "What are the strongest trends and patterns?",
  "Find anomalies and explain their impact",
  "Which variables correlate most strongly?"
];

function ArtifactView({ artifact }: { artifact: Artifact }) {
  if (artifact.type === "plotly" && artifact.plotly_json) {
    return (
      <div className="artifact artifact-chart">
        {artifact.title && <div className="artifact-title">{artifact.title}</div>}
        <Suspense fallback={<div className="artifact-loading">Loading chart…</div>}>
          <PlotlyArtifact plotlyJson={artifact.plotly_json} />
        </Suspense>
      </div>
    );
  }

  if (artifact.type === "image" && artifact.image_base64) {
    return (
      <div className="artifact artifact-image">
        {artifact.title && <div className="artifact-title">{artifact.title}</div>}
        <img
          src={`data:image/png;base64,${artifact.image_base64}`}
          alt={artifact.title ?? "Generated visualization"}
          className="artifact-img"
        />
      </div>
    );
  }

  if (artifact.type === "table" && artifact.columns && artifact.rows) {
    return (
      <div className="artifact artifact-table">
        {artifact.title && <div className="artifact-title">{artifact.title}</div>}
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                {artifact.columns.map((column) => (
                  <th key={column}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {artifact.rows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {artifact.columns?.map((column) => (
                    <td key={`${rowIndex}-${column}`}>{String(row[column] ?? "")}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="artifact artifact-text">
      {artifact.title && <div className="artifact-title">{artifact.title}</div>}
      <pre className="code-block">{artifact.text ?? "No output"}</pre>
    </div>
  );
}

function HumanFileSize({ bytes }: { bytes: number }) {
  const kb = bytes / 1024;
  const mb = kb / 1024;
  return <>{mb >= 1 ? `${mb.toFixed(2)} MB` : `${kb.toFixed(1)} KB`}</>;
}

function FullDataModal({
  data,
  loading,
  onClose
}: {
  data: DatasetFull | null;
  loading: boolean;
  onClose: () => void;
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <div>
            <h3>{data?.filename ?? "Full dataset"}</h3>
            {data && (
              <p className="muted small">
                Showing {data.returned_rows.toLocaleString()} of{" "}
                {data.total_rows.toLocaleString()} rows · {data.columns.length} columns
              </p>
            )}
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>
        <div className="modal-body">
          {loading && <p className="muted">Loading full dataset…</p>}
          {!loading && data && (
            <div className="table-scroll full-data-scroll">
              <table>
                <thead>
                  <tr>
                    {data.columns.map((column) => (
                      <th key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {data.columns.map((column) => (
                        <td key={`${rowIndex}-${column}`}>{String(row[column] ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

type Message =
  | { kind: "user"; id: string; content: string }
  | { kind: "assistant"; id: string; analysis: AnalysisHistoryItem }
  | { kind: "pending"; id: string; content: string };

type Theme = "light" | "dark";

function AriyaLogo({ size = 28 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="ariya-logo-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--accent)" />
          <stop offset="100%" stopColor="#e08a5e" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="40" height="40" rx="10" fill="url(#ariya-logo-grad)" />
      <g
        transform="translate(8 8)"
        stroke="#fff"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      >
        <path d="M18 17a1 1 0 0 0-1 1v1a2 2 0 1 0 2-2z" />
        <path d="M20.97 3.61a.45.45 0 0 0-.58-.58C10.2 6.6 6.6 10.2 3.03 20.39a.45.45 0 0 0 .58.58C13.8 17.4 17.4 13.8 20.97 3.61" />
        <path d="m6.707 6.707 10.586 10.586" />
        <path d="M7 5a2 2 0 1 0-2 2h1a1 1 0 0 0 1-1z" />
      </g>
    </svg>
  );
}

function SunIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [profiling, setProfiling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  const [showFullData, setShowFullData] = useState(false);
  const [fullData, setFullData] = useState<DatasetFull | null>(null);
  const [fullDataLoading, setFullDataLoading] = useState(false);
  const [showCode, setShowCode] = useState<Record<string, boolean>>({});

  const fileInputRef = useRef<HTMLInputElement>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);
  const messageRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window === "undefined") return "light";
    const stored = window.localStorage.getItem("ariya-theme") as Theme | null;
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    window.localStorage.setItem("ariya-theme", theme);
  }, [theme]);

  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) return;
    if (lastMessage.kind === "user" || lastMessage.kind === "pending") {
      threadEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const scrollToMessage = (id: string) => {
    const target = messageRefs.current[id];
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const fileDetails = useMemo(() => {
    if (!profile) return null;
    return `${profile.filename}`;
  }, [profile]);

  const onFileChange = async (nextFile: File | null) => {
    setError(null);
    if (!nextFile) return;

    setProfile(null);
    setSessionId(null);
    setMessages([]);
    setFullData(null);
    setProfiling(true);
    try {
      const nextProfile = await profileDataset(nextFile);
      setProfile(nextProfile);
      setSessionId(nextProfile.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to profile dataset.");
    } finally {
      setProfiling(false);
    }
  };

  const openFullData = async () => {
    if (!sessionId) return;
    setShowFullData(true);
    if (fullData && fullData.session_id === sessionId) return;
    setFullDataLoading(true);
    try {
      const data = await fetchFullDataset(sessionId);
      setFullData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load full dataset.");
    } finally {
      setFullDataLoading(false);
    }
  };

  const onSubmit = async (event?: FormEvent) => {
    event?.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    if (!sessionId) {
      setError("Upload a CSV dataset first.");
      return;
    }

    const userMsgId = `u-${Date.now()}`;
    const pendingId = `p-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { kind: "user", id: userMsgId, content: trimmed },
      { kind: "pending", id: pendingId, content: "Analyzing your data…" }
    ]);
    setQuery("");
    setLoading(true);
    setError(null);

    try {
      const response = await analyzeDataset({
        query: trimmed,
        sessionId
      });
      const analysis: AnalysisHistoryItem = {
        query: response.query,
        summary: response.summary,
        code: response.code,
        artifacts: response.artifacts
      };
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== pendingId),
        { kind: "assistant", id: `a-${Date.now()}`, analysis }
      ]);
      setSessionId(response.session_id);
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== pendingId));
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const onPromptKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSubmit();
    }
  };

  const newChat = () => {
    setMessages([]);
    setError(null);
    setProfile(null);
    setSessionId(null);
    setFullData(null);
    setQuery("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-identity">
            <AriyaLogo />
            <span>Ariya</span>
          </div>
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setTheme((prev) => (prev === "light" ? "dark" : "light"))}
            aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
            title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
          >
            <span className={`theme-toggle-track theme-${theme}`}>
              <span className="theme-toggle-icon theme-toggle-sun">
                <SunIcon />
              </span>
              <span className="theme-toggle-icon theme-toggle-moon">
                <MoonIcon />
              </span>
              <span className="theme-toggle-thumb" />
            </span>
          </button>
        </div>

        <button type="button" className="new-chat-btn" onClick={newChat}>
          <span>+ New analysis</span>
        </button>

        <div className="sidebar-section">
          <label className="sidebar-upload">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
            />
            <span>{profile ? "Replace dataset" : "Upload CSV"}</span>
          </label>
          {profiling && <p className="muted small">Profiling dataset…</p>}
          {fileDetails && (
            <div className="dataset-card">
              <div className="dataset-filename">{fileDetails}</div>
              {profile && (
                <div className="dataset-meta">
                  <span>{profile.rows.toLocaleString()} rows</span>
                  <span>·</span>
                  <span>{profile.columns} cols</span>
                  <span>·</span>
                  <span>
                    <HumanFileSize bytes={profile.file_size_bytes} />
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {messages.length > 0 && (
          <div className="sidebar-section">
            <div className="sidebar-heading">Conversation</div>
            <ul className="conversation-list">
              {messages
                .filter((m): m is Extract<Message, { kind: "user" }> => m.kind === "user")
                .map((m) => (
                  <li
                    key={m.id}
                    className="conversation-item"
                    title={m.content}
                    onClick={() => scrollToMessage(m.id)}
                  >
                    {m.content.slice(0, 60)}
                  </li>
                ))}
            </ul>
          </div>
        )}

        <div className="sidebar-footer">
          <span className="muted small">AI data analyst</span>
        </div>
      </aside>

      <main className="main">
        {!profile && messages.length === 0 && (
          <div className="welcome">
            <h1 className="welcome-title">What data would you like to explore today?</h1>
            <p className="welcome-subtitle">
              Upload a CSV file and ask questions in plain English. I'll analyze it and create
              visualizations, tables, and insights for you.
            </p>

            <label className="upload-dropzone">
              <input
                type="file"
                accept=".csv"
                onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
              />
              <div className="upload-dropzone-content">
                <div className="upload-icon">↑</div>
                <div>
                  <strong>Upload your CSV</strong>
                  <p className="muted small">Click to browse or drag and drop</p>
                </div>
              </div>
            </label>
          </div>
        )}

        {profile && (
          <section className="dataset-preview">
            <div className="dataset-preview-head">
              <div>
                <h2>Dataset preview</h2>
                <p className="muted small">
                  First 5 rows · {profile.columns} columns · {profile.rows.toLocaleString()} total
                  rows
                </p>
              </div>
              <button type="button" className="ghost-btn" onClick={openFullData}>
                View full data →
              </button>
            </div>
            <div className="table-scroll preview-scroll">
              <table>
                <thead>
                  <tr>
                    {profile.column_profiles.map((column) => (
                      <th key={column.name}>
                        <div className="column-head">
                          <span>{column.name}</span>
                          <span className="column-type">{column.dtype}</span>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {profile.preview_rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {profile.column_profiles.map((column) => (
                        <td key={`${rowIndex}-${column.name}`}>
                          {String(row[column.name] ?? "")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {messages.length > 0 && (
          <section className="thread">
            {messages.map((message) => {
              if (message.kind === "user") {
                return (
                  <div
                    key={message.id}
                    className="message message-user"
                    ref={(el) => {
                      messageRefs.current[message.id] = el;
                    }}
                  >
                    <div className="message-bubble">{message.content}</div>
                  </div>
                );
              }
              if (message.kind === "pending") {
                return (
                  <div
                    key={message.id}
                    className="message message-assistant"
                    ref={(el) => {
                      messageRefs.current[message.id] = el;
                    }}
                  >
                    <div className="avatar">
                      <AriyaLogo size={22} />
                    </div>
                    <div className="message-content">
                      <div className="typing">
                        <span />
                        <span />
                        <span />
                      </div>
                    </div>
                  </div>
                );
              }
              const { analysis } = message;
              const codeOpen = !!showCode[message.id];
              return (
                <div
                  key={message.id}
                  className="message message-assistant"
                  ref={(el) => {
                    messageRefs.current[message.id] = el;
                  }}
                >
                  <div className="avatar">
                    <AriyaLogo size={22} />
                  </div>
                  <div className="message-content">
                    <AssistantSummary text={analysis.summary} />

                    {analysis.artifacts.length > 0 && (
                      <div className="artifact-grid">
                        {analysis.artifacts.map((artifact, index) => (
                          <ArtifactView
                            key={`${message.id}-${artifact.type}-${index}`}
                            artifact={artifact}
                          />
                        ))}
                      </div>
                    )}

                    {analysis.code && (
                      <div className="code-toggle">
                        <button
                          type="button"
                          className="link-btn"
                          onClick={() =>
                            setShowCode((prev) => ({ ...prev, [message.id]: !prev[message.id] }))
                          }
                        >
                          {codeOpen ? "Hide code" : "Show generated Python"}
                        </button>
                        {codeOpen && <pre className="code-block">{analysis.code}</pre>}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            <div ref={threadEndRef} />
          </section>
        )}

        {error && <p className="error">{error}</p>}

        <div className="composer-wrap">
          <form className="composer" onSubmit={onSubmit}>
            {profile && messages.length === 0 && (
              <div className="chip-row">
                {STARTER_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="chip"
                    onClick={() => setQuery(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}

            <div className="composer-inner">
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={onPromptKeyDown}
                rows={1}
                placeholder={
                  profile
                    ? "Ask a question about your data…"
                    : "Upload a CSV first, then ask anything"
                }
                disabled={!profile || loading}
              />
              <button
                type="submit"
                className="send-btn"
                disabled={loading || !profile || !query.trim()}
                aria-label="Send"
              >
                {loading ? "…" : "↑"}
              </button>
            </div>
            <p className="composer-hint muted small">
              Press Enter to send · Shift + Enter for a new line
            </p>
          </form>
        </div>
      </main>

      {showFullData && (
        <FullDataModal
          data={fullData}
          loading={fullDataLoading}
          onClose={() => setShowFullData(false)}
        />
      )}
    </div>
  );
}
