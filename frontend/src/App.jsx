import { useState, useEffect } from 'react'
import workflowImg from './assets/workflow.png'

function App() {
  const [currentPage, setCurrentPage] = useState('product') // 'product' or 'showcase'
  const [activeDemo, setActiveDemo] = useState('bug')
  const [simulating, setSimulating] = useState(false)
  const [simulatedLogs, setSimulatedLogs] = useState([])
  const [logProgress, setLogProgress] = useState(0)
  
  // FAQ Accordion states
  const [expandedFaq, setExpandedFaq] = useState(null)

  const toggleFaq = (index) => {
    setExpandedFaq(expandedFaq === index ? null : index)
  }

  // Expanded Simulation steps definitions (including Future Scope cases)
  const simulations = {
    bug: {
      title: "Application crashes on login",
      body: "When I click login, the app freezes and throws a connection timeout error.",
      categories: ["bug"],
      confidence: 0.97,
      logs: [
        "Received webhook: Event=issues, Delivery=dlv-bug-104",
        "Webhook signature verified successfully. Secret verified.",
        "Saving WebhookEvent issues to PostgreSQL cache. Status: pending.",
        "Celery task process_webhook_event[518df2f4] enqueued via Redis.",
        "Celery Worker processing task process_webhook_event...",
        "Triage Analysis complete. Predicted Categories: ['bug'] | Confidence: 0.97",
        "Checking metadata variables... OS: missing, Error logs: missing.",
        "Generating context-aware checklist response comment...",
        "GitHub API Call: POST /repos/demo-owner/demo-repo/issues/104/comments",
        "Comment posted successfully. Celery task processed in 38ms."
      ],
      resultComment: `🤖 **PRobot Triage Assistant**

Sorry to hear that the application is crashing on login, let's troubleshoot the connection error together.

Please edit your description and provide the following missing details:
- [ ] Logs
- [ ] Environment details

Once you update these details, we'll continue reviewing your report. Thank you!`
    },
    docs: {
      title: "Installation process is missing",
      body: "I am trying to run the app but there are no installation guidelines in the README.",
      categories: ["documentation"],
      confidence: 0.94,
      logs: [
        "Received webhook: Event=issues, Delivery=dlv-doc-101",
        "Webhook signature verified successfully.",
        "Saving WebhookEvent issues to PostgreSQL. Status: pending.",
        "Celery task process_webhook_event[65847334] enqueued.",
        "Celery Worker processing task...",
        "Triage Analysis complete. Predicted Categories: ['documentation'] | Confidence: 0.94",
        "Checking metadata variables... Section reference: missing, Correction suggestion: missing.",
        "Generating documentation-specific questions...",
        "GitHub API Call: POST /repos/demo-owner/demo-repo/issues/101/comments",
        "Comment posted successfully. Celery task completed."
      ],
      resultComment: `🤖 **PRobot Triage Assistant**

It seems like you're having trouble with the documentation or installation instructions, let's work together to clarify this.

Please edit your description and provide the following missing details:
- [ ] Which section is incorrect?
- [ ] Expected behavior?
- [ ] Suggested correction?

Once you update these details, we'll continue reviewing your report. Thank you!`
    },
    enhancement: {
      title: "Add dark mode support",
      body: "It would be great to have dark mode option in the settings menu.",
      categories: ["enhancement", "feature-request"],
      confidence: 0.98,
      logs: [
        "Received webhook: Event=issues, Delivery=dlv-en-102",
        "Webhook signature verified successfully.",
        "Saving WebhookEvent issues to PostgreSQL cache.",
        "Celery task process_webhook_event[a4b5c6d7] enqueued.",
        "Celery Worker processing task...",
        "Triage Analysis complete. Predicted Categories: ['enhancement', 'feature-request'] | Confidence: 0.98",
        "No debugging metadata required for enhancement. Triage checklist skipped.",
        "Auto-labeling: Applying labels ['enhancement', 'feature-request'] via GitHub API...",
        "GitHub API Call: POST /repos/demo-owner/demo-repo/issues/102/labels",
        "Labels applied successfully. Celery task completed."
      ],
      resultComment: null,
      appliedLabels: ["enhancement", "feature-request"]
    },
    release_notes: {
      title: "Generate release notes for v1.3",
      body: "Draft the automated release log representing the features merged this sprint.",
      categories: ["ai-release-notes"],
      confidence: 0.99,
      logs: [
        "Received webhook: Event=issues, Delivery=dlv-notes-99",
        "Webhook signature verified successfully.",
        "Celery Worker received task: process_release_notes_trigger",
        "Fetching all merged PRs between v1.2 and v1.3 from PostgreSQL...",
        "Found 8 merged PRs: #101 (docs), #102 (enhancement), #104 (bug fix), etc.",
        "Invoking LLM Summarizer. Synthesizing release highlights...",
        "Release Notes draft generated successfully.",
        "GitHub API Call: POST /repos/demo-owner/demo-repo/releases",
        "Release log v1.3 draft posted. Celery task completed."
      ],
      resultComment: `🚀 **PRobot AI Release Notes - v1.3**

### 🌟 Features Added
- **Smart Auto Labeling**: Applied labels to tickets dynamically depending on intent (#102)
- **RAG Documentation Search**: Integrated ChromaDB vector store search query (#103)

### 🐛 Bug Fixes
- **Startup Connection Crashes**: Fixed Celery environment startup exceptions (#104)
- **README instructions**: Documented correct port configuration details (#101)`
    },
    onboarding: {
      title: "Setup guidance needed for new developer",
      body: "Hi, I just joined the repository. How do I start the development server?",
      categories: ["contributor-onboarding"],
      confidence: 0.95,
      logs: [
        "Received webhook: Event=issue_comment, Delivery=dlv-onboard-88",
        "Webhook signature verified successfully.",
        "Celery Worker received task: process_webhook_event",
        "Triage Analysis complete. Predicted: ['contributor-onboarding'] | Confidence: 0.95",
        "Invoking RAG Knowledge assistant. Searching local repository files...",
        "Retrieved documents: README.md, docs/CONTRIBUTING.md. Synthesizing answer...",
        "GitHub API Call: POST /repos/demo-owner/demo-repo/issues/105/comments",
        "Comment posted successfully. Celery task completed."
      ],
      resultComment: `🤖 **PRobot Knowledge Assistant**

Welcome to the project! Here are the setup steps from our repository documentation:

1. **Clone and Navigate**: \`cd PRobot/backend\`
2. **Environment Setup**: Copy \`.env.example\` to \`.env\` and configure variables.
3. **Install Dependencies**: Run \`make install\` or \`pip install -r requirements.txt\`
4. **Launch Server**: Run \`make run\` (Server starts at \`http://127.0.0.1:8000\`)`
    },
    duplicate_detect: {
      title: "Login page crashes (Duplicate Check)",
      body: "When I open the app, it crashes immediately on the main login screen.",
      categories: ["duplicate-detection"],
      confidence: 0.96,
      logs: [
        "Received webhook: Event=issues, Delivery=dlv-dup-901",
        "Webhook signature verified successfully. Secret verified.",
        "Saving WebhookEvent issues to PostgreSQL cache. Status: pending.",
        "Celery task process_webhook_event[d3f2a1b9] enqueued via Redis.",
        "Celery Worker processing task process_webhook_event...",
        "Triage Analysis complete. Predicted Categories: ['bug'] | Confidence: 0.96",
        "Generating title and body text embeddings...",
        "Querying ChromaDB vector database namespace for similarities...",
        "Potential Duplicate Detected: Match found with Issue #10 'Login page crashes' (Cosine Similarity: 0.94)",
        "Posting duplicate notification and closing current issue #32...",
        "GitHub API Call: POST /repos/demo-owner/demo-repo/issues/32/comments",
        "GitHub API Call: PATCH /repos/demo-owner/demo-repo/issues/32 (state: closed, labels: ['duplicate'])",
        "Comment posted and issue closed. Celery task processed in 45ms."
      ],
      resultComment: `🤖 **PRobot Duplicate Detector**

Potential duplicate detected. This issue is highly similar to Issue #10 (Login page crashes).

We are closing this issue to consolidate discussion in the main thread. Please follow #10 for updates. Thank you!`,
      appliedLabels: ["duplicate"]
    },
    pr_guardian: {
      title: "Update database connection pool (PR Quality)",
      body: "Fix database pool leaks.",
      categories: ["pr-quality-guardian"],
      confidence: 0.99,
      logs: [
        "Received webhook: Event=pull_request, Action=opened, Delivery=dlv-pr-702",
        "Webhook signature verified successfully.",
        "Celery task process_webhook_event[8c7b6a5d] enqueued.",
        "Celery Worker processing pull request event...",
        "PR Quality Guardian Engine scanning PR changes...",
        "Checking PR Description length: 24 chars (Threshold: >50 chars) ➔ FAIL",
        "Checking Linked Issue reference in description: None found ➔ FAIL",
        "Scanning modified files: ['backend/app/core/db.py'] ➔ Source files updated.",
        "Checking corresponding unit tests: No new files found in 'tests/' ➔ FAIL",
        "Generating QA Quality checklist comment...",
        "GitHub API Call: POST /repos/demo-owner/demo-repo/issues/45/comments",
        "PR evaluation completed. Checklist posted."
      ],
      resultComment: `🤖 **PRobot PR Quality Guardian**

Please address the following check items before merging:
- [ ] PR description too short.
- [ ] No linked issue detected.
- [ ] Tests missing.`,
      appliedLabels: ["needs-work"]
    },
    knowledge_assistant: {
      title: "How do I start the server? (RAG Guide)",
      body: "I checked the root folder but couldn't find the start script. How do I boot PostgreSQL and the server?",
      categories: ["knowledge-assistant"],
      confidence: 0.98,
      logs: [
        "Received webhook: Event=issue_comment, Delivery=dlv-rag-304",
        "Webhook signature verified successfully.",
        "Celery task process_webhook_event[e4d3c2b1] enqueued.",
        "Triage classified event as QA/repository-guidance request.",
        "Invoking RAG Knowledge search engine...",
        "Generating text embedding for question: 'How do I start the server?'",
        "ChromaDB search completed: retrieved README.md (similarity 0.89) and postgres guide (similarity 0.85).",
        "Formulating AI response using retrieved repository documents...",
        "GitHub API Call: POST /repos/demo-owner/demo-repo/issues/88/comments",
        "Comment posted. Celery task completed."
      ],
      resultComment: `🤖 **PRobot Knowledge Assistant**

Run \`make run\`. PostgreSQL is available on port 5432.`
    }
  }

  // Handle simulation run
  const runSimulation = () => {
    setSimulating(true)
    setSimulatedLogs([])
    setLogProgress(0)
  }

  useEffect(() => {
    if (!simulating) return

    const currentLogs = simulations[activeDemo].logs
    if (logProgress < currentLogs.length) {
      const timer = setTimeout(() => {
        setSimulatedLogs((prev) => [...prev, currentLogs[logProgress]])
        setLogProgress((prev) => prev + 1)
      }, 300)
      return () => clearTimeout(timer)
    } else {
      setSimulating(false)
    }
  }, [simulating, logProgress, activeDemo])

  // Reset simulation when active demo tab changes
  useEffect(() => {
    setSimulatedLogs([])
    setLogProgress(0)
    setSimulating(false)
  }, [activeDemo])

  return (
    <div className="bg-slate-950 text-slate-100 font-sans min-h-screen selection:bg-purple-600 selection:text-white pb-16">
      {/* BACKGROUND GLOWS (Inspired by RAZE purple space nebula) */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-purple-900/15 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-violet-900/10 rounded-full blur-[140px]"></div>
      </div>

      {/* FLOAT PILLED NAVBAR */}
      <div className="sticky top-6 z-50 flex justify-center px-4">
        <nav className="bg-slate-950/80 backdrop-blur-lg border border-slate-900 px-6 py-3 rounded-full flex items-center justify-between gap-12 w-full max-w-4xl shadow-2xl shadow-purple-950/20">
          <div className="flex items-center gap-2">
            <span className="text-xl">🌌</span>
            <span className="font-extrabold text-lg bg-gradient-to-r from-white via-purple-300 to-indigo-300 bg-clip-text text-transparent">
              PRobot
            </span>
          </div>
          <div className="flex gap-6 font-medium text-xs text-slate-400">
            <button
              onClick={() => setCurrentPage('product')}
              className={`hover:text-slate-100 transition-colors uppercase tracking-widest ${
                currentPage === 'product' ? 'text-purple-400 font-bold' : ''
              }`}
            >
              Product
            </button>
            <button
              onClick={() => setCurrentPage('showcase')}
              className={`hover:text-slate-100 transition-colors uppercase tracking-widest ${
                currentPage === 'showcase' ? 'text-purple-400 font-bold' : ''
              }`}
            >
              Showcase & About
            </button>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/HemantDhaker12/PRobot"
              target="_blank"
              rel="noreferrer"
              className="bg-purple-950/30 border border-purple-900/50 hover:bg-purple-950/50 px-3.5 py-1.5 rounded-full text-[10px] font-semibold text-purple-300 transition-all flex items-center gap-1.5"
            >
              🐙 Source Code
            </a>
            <a
              href="https://github.com/HemantDhaker12/PRobot-demo"
              target="_blank"
              rel="noreferrer"
              className="bg-purple-950/30 border border-purple-900/50 hover:bg-purple-950/50 px-3.5 py-1.5 rounded-full text-[10px] font-semibold text-purple-300 transition-all flex items-center gap-1.5"
            >
              🚀 Demo Check
            </a>
          </div>
        </nav>
      </div>

      {/* PAGE 1: PRODUCT (LANDING PAGE) */}
      {currentPage === 'product' && (
        <main className="relative z-10 max-w-6xl mx-auto px-6">
          {/* HERO SECTION (RAZE AESTHETIC: Two-column layout with glowing portals and floating workflow illustration) */}
          <section className="relative py-16 md:py-24 overflow-hidden z-10">
            {/* Glowing Space Portal Ring Background */}
            <div className="absolute top-1/2 right-10 -translate-y-1/2 w-[450px] h-[450px] bg-gradient-to-tr from-purple-500/10 to-indigo-600/10 rounded-full blur-[100px] animate-pulse-glow pointer-events-none z-0"></div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
              {/* Left Column: Copy & Actions */}
              <div className="lg:col-span-6 flex flex-col items-start text-left">
                <div className="inline-flex items-center gap-2 bg-purple-500/10 text-purple-400 border border-purple-500/20 px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest mb-6">
                  🌠 HEAVEN HILL PRESENTATION
                </div>
                
                <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-none mb-6 bg-gradient-to-r from-white via-purple-100 to-purple-300 bg-clip-text text-transparent">
                  PRobot
                </h1>
                <p className="text-lg md:text-xl font-medium text-purple-300 mb-4 tracking-wide">
                  AI-Powered GitHub Maintainer Assistant
                </p>
                <p className="text-sm md:text-base text-slate-400 max-w-xl mb-8 leading-relaxed">
                  Automates issue triage, labeling, duplicate detection, PR reviews, and repository knowledge retrieval.
                  Built by the **Heaven Hill** automation team to maximize repository uptime and maintainer energy.
                </p>

                <div className="flex flex-wrap items-center gap-4">
                  <a
                    href="#demo"
                    className="bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white text-xs font-bold uppercase tracking-widest px-8 py-3.5 rounded-full shadow-lg shadow-purple-500/20 transition-all transform hover:-translate-y-0.5"
                  >
                    View Demo
                  </a>
                  <a
                    href="#features"
                    className="bg-slate-900 border border-slate-800 hover:bg-slate-850 text-slate-300 text-xs font-bold uppercase tracking-widest px-8 py-3.5 rounded-full transition-all transform hover:-translate-y-0.5"
                  >
                    Explore Features
                  </a>
                </div>
              </div>

              {/* Right Column: Visual Graphic and portal/animations */}
              <div className="lg:col-span-6 flex justify-center lg:justify-end">
                <div className="relative w-full max-w-md aspect-square flex items-center justify-center">
                  {/* Glowing Portal Orb behind the image */}
                  <div className="absolute w-[80%] h-[80%] bg-purple-600/10 rounded-full blur-3xl animate-pulse-glow z-0"></div>
                  
                  {/* Decorative orbital dashed line */}
                  <div className="absolute w-[95%] h-[95%] rounded-full border border-purple-500/10 border-dashed animate-spin [animation-duration:40s] pointer-events-none z-0"></div>
                  
                  {/* Floating badge 1: Real-time telemetry */}
                  <div className="absolute -top-4 -left-4 bg-slate-900/95 border border-purple-500/30 px-3.5 py-2 rounded-2xl shadow-xl z-20 animate-float text-left backdrop-blur-md">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
                      <span className="text-[9px] font-extrabold uppercase tracking-widest text-slate-400">Triage Engine</span>
                    </div>
                    <div className="text-[10px] font-bold text-slate-200 mt-0.5">Webhook Active</div>
                  </div>

                  {/* Floating badge 2: Agent Response */}
                  <div className="absolute -bottom-2 -right-4 bg-slate-900/95 border border-indigo-500/30 px-3.5 py-2 rounded-2xl shadow-xl z-20 animate-float-delayed text-left backdrop-blur-md">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px]">🤖</span>
                      <span className="text-[9px] font-extrabold uppercase tracking-widest text-indigo-400">PRobot AI</span>
                    </div>
                    <div className="text-[10px] font-bold text-slate-200 mt-0.5">Labels & PR Evaluated</div>
                  </div>

                  {/* Glassmorphic border container for the image */}
                  <div className="relative z-10 w-full rounded-3xl border border-white/10 p-2 bg-slate-950/40 backdrop-blur-sm shadow-2xl shadow-purple-950/20 overflow-hidden animate-float">
                    <div className="absolute inset-0 bg-gradient-to-tr from-purple-500/5 via-transparent to-indigo-500/5 pointer-events-none"></div>
                    <img 
                      src={workflowImg} 
                      alt="PRobot GitHub Pull Request Workflow" 
                      className="w-full h-auto rounded-2xl object-cover hover:scale-105 transition-transform duration-700"
                    />
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* FEATURES SECTION (Beautiful Cards showing Implemented Features & Code Examples) */}
          <section id="features" className="py-20 scroll-mt-24">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-extrabold tracking-tight text-white mb-2 uppercase tracking-wider">
                Autonomous AI Engines
              </h2>
              <div className="h-0.5 w-16 bg-purple-500 mx-auto mt-4"></div>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Feature 1: Smart Issue Triage */}
              <div className="bg-slate-900/60 border border-slate-850 p-6 rounded-2xl backdrop-blur flex flex-col justify-between hover:border-purple-500/30 transition-all duration-300">
                <div>
                  <div className="text-purple-400 font-bold text-lg mb-3 flex items-center gap-2">
                    <span>📝</span> Smart Issue Triage
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    Analyzes issue content and automatically asks for missing information such as logs, OS details, reproduction steps, and environment configuration.
                  </p>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl font-mono text-[10px] text-purple-300/90 border border-slate-900">
                  <div className="text-slate-500 mb-1 border-b border-slate-900 pb-1">⚡ Example: Input / Output</div>
                  <strong className="text-slate-400">Issue:</strong> "Application crashes on login"<br />
                  <strong className="text-purple-400">PRobot:</strong> "Logs are missing. Environment details are missing."
                </div>
              </div>

              {/* Feature 2: Auto Labeling */}
              <div className="bg-slate-900/60 border border-slate-850 p-6 rounded-2xl backdrop-blur flex flex-col justify-between hover:border-purple-500/30 transition-all duration-300">
                <div>
                  <div className="text-purple-400 font-bold text-lg mb-3 flex items-center gap-2">
                    <span>🏷️</span> Auto Labeling
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    Uses AI classification models to parse the intent behind open reports and pull requests, applying precise labels immediately.
                  </p>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl font-mono text-[10px] text-purple-300/90 border border-slate-900">
                  <div className="text-slate-500 mb-1 border-b border-slate-900 pb-1">⚡ Example: Auto Tag mapping</div>
                  "Bug Report" ➔ <span className="text-rose-400 bg-rose-950/40 px-1 rounded">bug</span><br />
                  "README Missing" ➔ <span className="text-yellow-400 bg-yellow-950/40 px-1 rounded">documentation</span><br />
                  "Dark Mode Request" ➔ <span className="text-green-400 bg-green-950/40 px-1 rounded">enhancement</span>
                </div>
              </div>

              {/* Feature 3: Duplicate Issue Detection */}
              <div className="bg-slate-900/60 border border-slate-850 p-6 rounded-2xl backdrop-blur flex flex-col justify-between hover:border-purple-500/30 transition-all duration-300">
                <div>
                  <div className="text-purple-400 font-bold text-lg mb-3 flex items-center gap-2">
                    <span>🔍</span> Duplicate Detection
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    Uses semantic text search and vectorized database embeddings to detect similar issues before developers waste time review logging.
                  </p>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl font-mono text-[10px] text-purple-300/90 border border-slate-900">
                  <div className="text-slate-500 mb-1 border-b border-slate-900 pb-1">⚡ Example: Cosine similarity</div>
                  #10: "Login page crashes"<br />
                  #32: "Application fails after login"<br />
                  <strong className="text-purple-400">PRobot:</strong> Potential duplicate detected.
                </div>
              </div>

              {/* Feature 4: PR Quality Guardian */}
              <div className="bg-slate-900/60 border border-slate-850 p-6 rounded-2xl backdrop-blur flex flex-col justify-between hover:border-purple-500/30 transition-all duration-300">
                <div>
                  <div className="text-purple-400 font-bold text-lg mb-3 flex items-center gap-2">
                    <span>🛡️</span> PR Quality Guardian
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    Reviews pull requests automatically. Checks description quality, linked issue references, code test coverage, and breaking change variables.
                  </p>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl font-mono text-[10px] text-purple-300/90 border border-slate-900">
                  <div className="text-slate-500 mb-1 border-b border-slate-900 pb-1">⚡ Example: Comment feedback</div>
                  - PR description too short.<br />
                  - No linked issue detected.<br />
                  - Tests missing.
                </div>
              </div>

              {/* Feature 5: Repository Knowledge Assistant */}
              <div className="bg-slate-900/60 border border-slate-850 p-6 rounded-2xl backdrop-blur flex flex-col justify-between hover:border-purple-500/30 transition-all duration-300">
                <div>
                  <div className="text-purple-400 font-bold text-lg mb-3 flex items-center gap-2">
                    <span>📖</span> Knowledge Assistant
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    RAG-powered assistant trained on repository markdown files, guides, and resolved historical issues to answer questions automatically.
                  </p>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl font-mono text-[10px] text-purple-300/90 border border-slate-900">
                  <div className="text-slate-500 mb-1 border-b border-slate-900 pb-1">⚡ Example: RAG answering</div>
                  <strong className="text-slate-400">Q:</strong> "How do I start the server?"<br />
                  <strong className="text-purple-400">PRobot:</strong> "Run make run. PostgreSQL is on port 5432."
                </div>
              </div>

              {/* Background Processing Engine */}
              <div className="bg-slate-900/60 border border-slate-850 p-6 rounded-2xl backdrop-blur flex flex-col justify-between hover:border-purple-500/30 transition-all duration-300">
                <div>
                  <div className="text-purple-400 font-bold text-lg mb-3 flex items-center gap-2">
                    <span>⚙</span> Worker Architecture
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    Runs on Celery background task loops, powered by Redis brokers. De-couples incoming webhook HTTP replies from heavy LLM execution times.
                  </p>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl font-mono text-[10px] text-purple-300/90 border border-slate-900">
                  <div className="text-slate-500 mb-1 border-b border-slate-900 pb-1">⚡ Performance Stat</div>
                  HTTP Webhook Intake: <span className="text-emerald-400">&lt;10ms</span><br />
                  AI Task Execution: Asynchronous (Isolated)
                </div>
              </div>
            </div>
          </section>

          {/* INTERACTIVE WEBHOOK SIMULATOR WITH EXPANDED SCENARIOS */}
          <section id="demo" className="py-20 border-t border-slate-900 scroll-mt-24">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-extrabold tracking-tight text-white mb-2 uppercase tracking-wider">
                E2E Interactive Webhook Simulator
              </h2>
              <div className="h-0.5 w-16 bg-purple-500 mx-auto mt-4 mb-6"></div>
              <p className="text-sm text-slate-400 max-w-xl mx-auto">
                Trigger mock webhook payloads (including future scope models!) to watch Celery log lines populate in the console and view the GitHub outcome.
              </p>
            </div>

            <div className="grid lg:grid-cols-3 gap-8 items-start">
              {/* Event trigger column */}
              <div className="flex flex-col gap-4">
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-900 pb-2">
                  Select Simulator Payload
                </div>
                
                {/* Scrollable buttons container */}
                <div className="flex flex-col gap-3 max-h-[380px] overflow-y-auto pr-2 scrollbar-thin">
                  {/* 1. Bug */}
                  <button
                    onClick={() => setActiveDemo('bug')}
                    disabled={simulating}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      activeDemo === 'bug' ? 'bg-slate-900 border-purple-500 shadow-md' : 'bg-slate-900/30 border-slate-900 hover:border-slate-800'
                    } ${simulating ? 'opacity-50' : ''}`}
                  >
                    <div className="text-[9px] font-bold uppercase tracking-wider text-rose-400 mb-1">Bug Issue</div>
                    <div className="font-bold text-xs text-slate-200">{simulations.bug.title}</div>
                  </button>

                  {/* 2. Docs */}
                  <button
                    onClick={() => setActiveDemo('docs')}
                    disabled={simulating}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      activeDemo === 'docs' ? 'bg-slate-900 border-purple-500 shadow-md' : 'bg-slate-900/30 border-slate-900 hover:border-slate-800'
                    } ${simulating ? 'opacity-50' : ''}`}
                  >
                    <div className="text-[9px] font-bold uppercase tracking-wider text-yellow-400 mb-1">Doc Issue</div>
                    <div className="font-bold text-xs text-slate-200">{simulations.docs.title}</div>
                  </button>

                  {/* 3. Enhancement */}
                  <button
                    onClick={() => setActiveDemo('enhancement')}
                    disabled={simulating}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      activeDemo === 'enhancement' ? 'bg-slate-900 border-purple-500 shadow-md' : 'bg-slate-900/30 border-slate-900 hover:border-slate-800'
                    } ${simulating ? 'opacity-50' : ''}`}
                  >
                    <div className="text-[9px] font-bold uppercase tracking-wider text-emerald-400 mb-1">Enhancement</div>
                    <div className="font-bold text-xs text-slate-200">{simulations.enhancement.title}</div>
                  </button>

                  {/* 4. Duplicate Check */}
                  <button
                    onClick={() => setActiveDemo('duplicate_detect')}
                    disabled={simulating}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      activeDemo === 'duplicate_detect' ? 'bg-slate-900 border-purple-500 shadow-md' : 'bg-slate-900/30 border-slate-900 hover:border-slate-800'
                    } ${simulating ? 'opacity-50' : ''}`}
                  >
                    <div className="text-[9px] font-bold uppercase tracking-wider text-cyan-400 mb-1">Duplicate Check</div>
                    <div className="font-bold text-xs text-slate-200">{simulations.duplicate_detect.title}</div>
                  </button>

                  {/* 5. PR Quality Guardian */}
                  <button
                    onClick={() => setActiveDemo('pr_guardian')}
                    disabled={simulating}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      activeDemo === 'pr_guardian' ? 'bg-slate-900 border-purple-500 shadow-md' : 'bg-slate-900/30 border-slate-900 hover:border-slate-800'
                    } ${simulating ? 'opacity-50' : ''}`}
                  >
                    <div className="text-[9px] font-bold uppercase tracking-wider text-blue-400 mb-1">PR Quality Guardian</div>
                    <div className="font-bold text-xs text-slate-200">{simulations.pr_guardian.title}</div>
                  </button>

                  {/* 6. Repository Knowledge Assistant */}
                  <button
                    onClick={() => setActiveDemo('knowledge_assistant')}
                    disabled={simulating}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      activeDemo === 'knowledge_assistant' ? 'bg-slate-900 border-purple-500 shadow-md' : 'bg-slate-900/30 border-slate-900 hover:border-slate-800'
                    } ${simulating ? 'opacity-50' : ''}`}
                  >
                    <div className="text-[9px] font-bold uppercase tracking-wider text-indigo-400 mb-1">Repository Knowledge</div>
                    <div className="font-bold text-xs text-slate-200">{simulations.knowledge_assistant.title}</div>
                  </button>

                  {/* 7. Release Notes (Future Scope) */}
                  <button
                    onClick={() => setActiveDemo('release_notes')}
                    disabled={simulating}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      activeDemo === 'release_notes' ? 'bg-slate-900 border-purple-500 shadow-md' : 'bg-slate-900/30 border-slate-900 hover:border-slate-800'
                    } ${simulating ? 'opacity-50' : ''}`}
                  >
                    <div className="text-[9px] font-bold uppercase tracking-wider text-purple-400 mb-1">🌠 Future Scope: AI Release Notes</div>
                    <div className="font-bold text-xs text-slate-200">{simulations.release_notes.title}</div>
                  </button>

                  {/* 8. Onboarding (Future Scope) */}
                  <button
                    onClick={() => setActiveDemo('onboarding')}
                    disabled={simulating}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      activeDemo === 'onboarding' ? 'bg-slate-900 border-purple-500 shadow-md' : 'bg-slate-900/30 border-slate-900 hover:border-slate-800'
                    } ${simulating ? 'opacity-50' : ''}`}
                  >
                    <div className="text-[9px] font-bold uppercase tracking-wider text-purple-400 mb-1">🌠 Future Scope: Developer Onboarding</div>
                    <div className="font-bold text-xs text-slate-200">{simulations.onboarding.title}</div>
                  </button>
                </div>

                <button
                  onClick={runSimulation}
                  disabled={simulating}
                  className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white font-bold text-xs uppercase tracking-widest py-3.5 rounded-xl shadow-lg transition-all"
                >
                  {simulating ? 'Simulating...' : '⚡ Trigger Webhook Event'}
                </button>
              </div>

              {/* Logs terminal & output */}
              <div className="lg:col-span-2 flex flex-col gap-6">
                {/* Console Logs */}
                <div className="bg-slate-900 border border-slate-850 rounded-2xl p-5 shadow-xl">
                  <div className="text-xs font-bold text-slate-400 mb-3 uppercase tracking-wider">PRobot Celery Console Logs</div>
                  <div className="bg-slate-950 p-4 rounded-xl font-mono text-[10px] h-44 overflow-y-auto text-emerald-400 flex flex-col gap-1.5 scroll-smooth border border-slate-900">
                    {simulatedLogs.length === 0 ? (
                      <span className="text-slate-600 italic">Console idle. Trigger an issue/action to output logs.</span>
                    ) : (
                      simulatedLogs.map((log, idx) => {
                        const isWarning = log.includes("missing") || log.includes("Checking") || log.includes("FAIL")
                        return (
                          <div key={idx} className={isWarning ? "text-amber-300" : "text-emerald-400"}>
                            {log}
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>

                {/* Final GitHub Output */}
                <div className="bg-slate-900 border border-slate-850 rounded-2xl p-5 shadow-xl min-h-[160px]">
                  <div className="text-xs font-bold text-slate-400 mb-3 uppercase tracking-wider">GitHub Visual Feedback</div>
                  {simulatedLogs.length === 0 ? (
                    <div className="text-slate-500 text-xs italic">Simulate an event above to inspect result comment and label statuses.</div>
                  ) : logProgress < simulations[activeDemo].logs.length ? (
                    <div className="flex items-center gap-3 text-xs text-slate-400 animate-pulse">
                      <span className="h-2 w-2 bg-purple-500 rounded-full animate-ping"></span>
                      <span>Processing payload through FastAPI backend & Celery task...</span>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-4">
                      {/* Classification details */}
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Classified category:</span>
                        {simulations[activeDemo].categories.map((c) => (
                          <span key={c} className="text-[9px] font-bold px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-900">
                            {c}
                          </span>
                        ))}
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider ml-4">Confidence:</span>
                        <span className="text-[10px] font-bold text-slate-300">{simulations[activeDemo].confidence}</span>
                      </div>

                      {/* Comment body or label result */}
                      {simulations[activeDemo].resultComment ? (
                        <div className="bg-slate-950 p-4 rounded-xl text-xs text-slate-300 border border-slate-900 whitespace-pre-line relative text-left">
                          <div className="absolute top-0 right-0 p-2 text-[7px] font-extrabold uppercase bg-slate-900 text-slate-500 rounded-bl tracking-widest">
                            Comment Posted on GitHub
                          </div>
                          {simulations[activeDemo].resultComment}
                          {simulations[activeDemo].appliedLabels && (
                            <div className="mt-3 flex items-center gap-1.5 border-t border-slate-900 pt-2.5">
                              <span className="text-[9px] text-slate-500">Labels Applied:</span>
                              {simulations[activeDemo].appliedLabels.map((lbl) => (
                                <span key={lbl} className="text-[9px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900">
                                  {lbl}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="bg-slate-950 p-4 rounded-xl flex items-center justify-between border border-slate-900 text-left">
                          <span className="text-xs text-slate-400 font-medium">Triage Status: Completed successfully (No checklist comment required).</span>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[9px] text-slate-500">Labels Applied:</span>
                            {simulations[activeDemo].appliedLabels && simulations[activeDemo].appliedLabels.map((lbl) => (
                              <span key={lbl} className="text-[9px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900">
                                {lbl}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* SCREENSHOTS / VISUAL ASSETS GALLERY */}
          <section className="py-20 border-t border-slate-900">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-extrabold tracking-tight text-white mb-2 uppercase tracking-wider">
                System Interface Preview
              </h2>
              <div className="h-0.5 w-16 bg-purple-500 mx-auto mt-4"></div>
            </div>

            <div className="grid md:grid-cols-2 gap-8">
              {/* Graphic Mockup 1 */}
              <div className="bg-slate-900 border border-slate-850 p-3 rounded-2xl shadow-xl">
                <div className="bg-slate-950 aspect-video rounded-xl border border-slate-900 flex flex-col justify-center items-center text-center p-6 relative overflow-hidden">
                  <div className="text-4xl mb-2">📊</div>
                  <div className="font-bold text-xs text-slate-200 mb-1">Automated Triage Metrics Dashboard</div>
                  <p className="text-[10px] text-slate-500 max-w-xs leading-relaxed">
                    Live telemetry indicating webhook queues, Celery worker latency metrics, and issue duplicate statistics.
                  </p>
                  {/* Decorative chart lines */}
                  <div className="flex gap-1 items-end absolute bottom-3 left-4 right-4 h-8 opacity-20">
                    <div className="bg-purple-500 w-full h-[20%]"></div>
                    <div className="bg-purple-500 w-full h-[40%]"></div>
                    <div className="bg-purple-500 w-full h-[30%]"></div>
                    <div className="bg-purple-500 w-full h-[70%]"></div>
                    <div className="bg-purple-500 w-full h-[90%]"></div>
                  </div>
                </div>
                <div className="text-center text-[10px] font-semibold text-slate-400 mt-2.5">
                  Figure 1: Maintainer Triage Performance UI Mockup
                </div>
              </div>

              {/* Graphic Mockup 2 */}
              <div className="bg-slate-900 border border-slate-850 p-3 rounded-2xl shadow-xl">
                <div className="bg-slate-950 aspect-video rounded-xl border border-slate-900 flex flex-col justify-center items-center text-center p-6 relative overflow-hidden">
                  <div className="text-4xl mb-2">🛡</div>
                  <div className="font-bold text-xs text-slate-200 mb-1">ChromaDB Vector Namespace Monitor</div>
                  <p className="text-[10px] text-slate-500 max-w-xs leading-relaxed">
                    Vectorized chunks and document schemas loaded dynamically into ChromaDB database namespaces.
                  </p>
                  <div className="flex flex-col gap-1 w-full mt-4 text-[8px] font-mono text-left text-slate-500">
                    <div className="bg-slate-900/60 p-1 rounded border border-slate-900 flex justify-between"><span>✓ doc_chunk_readme_1</span><span>Cosine Similarity: 0.88</span></div>
                    <div className="bg-slate-900/60 p-1 rounded border border-slate-900 flex justify-between"><span>✓ issue_resolved_104_3</span><span>Cosine Similarity: 0.92</span></div>
                  </div>
                </div>
                <div className="text-center text-[10px] font-semibold text-slate-400 mt-2.5">
                  Figure 2: ChromaDB Knowledge Index Management
                </div>
              </div>
            </div>
          </section>

          {/* DEMO VIDEO SECTION */}
          <section className="py-20 border-t border-slate-900 text-center">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl font-extrabold tracking-wider text-white mb-2 uppercase">
                Watch PRobot in Action
              </h2>
              <div className="h-0.5 w-16 bg-purple-500 mx-auto mt-4 mb-6"></div>
              <p className="text-sm text-slate-400 max-w-xl mx-auto mb-10 leading-relaxed">
                See how PRobot autonomously handles webhook payloads, executes semantic duplicate checks, evaluates PR test coverage, and posts RAG-powered triage comments on GitHub in real time.
              </p>

              <div className="bg-slate-900 border border-slate-850 p-4 rounded-3xl shadow-xl aspect-video overflow-hidden">
                <iframe 
                  src="https://drive.google.com/file/d/1k3ewZk03e5WglU52mTDMejrSUeHVsS20/preview" 
                  className="w-full h-full rounded-2xl border-0"
                  allow="autoplay"
                  allowFullScreen
                  title="PRobot Demo Walkthrough"
                ></iframe>
              </div>

              <div className="mt-8 flex flex-wrap justify-center gap-4">
                <a
                  href="https://drive.google.com/file/d/1k3ewZk03e5WglU52mTDMejrSUeHVsS20/view?usp=sharing"
                  target="_blank"
                  rel="noreferrer"
                  className="bg-slate-900 border border-slate-850 hover:bg-slate-800 text-slate-300 text-xs font-bold uppercase tracking-widest px-6 py-3 rounded-full transition-all transform hover:-translate-y-0.5"
                >
                  Open Demo in New Tab
                </a>
                <a
                  href="https://drive.google.com/file/d/1k3ewZk03e5WglU52mTDMejrSUeHVsS20/preview"
                  target="_blank"
                  rel="noreferrer"
                  className="bg-purple-950/30 border border-purple-900/50 hover:bg-purple-950/50 text-purple-300 text-xs font-bold uppercase tracking-widest px-6 py-3 rounded-full transition-all flex items-center gap-2 transform hover:-translate-y-0.5"
                >
                  🔗 Open Fullscreen Demo
                </a>
              </div>
            </div>
          </section>

          {/* TECH STACK CARDS */}
          <section id="tech-stack" className="py-20 border-t border-slate-900/60 scroll-mt-24">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-extrabold tracking-tight text-white mb-2 uppercase tracking-wider">
                Technology Stack
              </h2>
              <div className="h-0.5 w-16 bg-purple-500 mx-auto mt-4"></div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900/40 border border-slate-850 p-5 rounded-xl flex flex-col items-center justify-center text-center">
                <div className="text-3xl mb-1">🚀</div>
                <div className="font-bold text-xs text-slate-200">FastAPI</div>
                <div className="text-[9px] text-slate-500 mt-0.5">Python Web Server</div>
              </div>
              <div className="bg-slate-900/40 border border-slate-850 p-5 rounded-xl flex flex-col items-center justify-center text-center">
                <div className="text-3xl mb-1">🐘</div>
                <div className="font-bold text-xs text-slate-200">PostgreSQL</div>
                <div className="text-[9px] text-slate-500 mt-0.5">Relational DB (SQLAlchemy)</div>
              </div>
              <div className="bg-slate-900/40 border border-slate-850 p-5 rounded-xl flex flex-col items-center justify-center text-center">
                <div className="text-3xl mb-1">🎈</div>
                <div className="font-bold text-xs text-slate-200">Redis</div>
                <div className="text-[9px] text-slate-500 mt-0.5">Celery Broker & Cache</div>
              </div>
              <div className="bg-slate-900/40 border border-slate-850 p-5 rounded-xl flex flex-col items-center justify-center text-center">
                <div className="text-3xl mb-1">🥬</div>
                <div className="font-bold text-xs text-slate-200">Celery</div>
                <div className="text-[9px] text-slate-500 mt-0.5">Async Task Queue</div>
              </div>
              <div className="bg-slate-900/40 border border-slate-850 p-5 rounded-xl flex flex-col items-center justify-center text-center">
                <div className="text-3xl mb-1">🤖</div>
                <div className="font-bold text-xs text-slate-200">Groq Llama 3.3</div>
                <div className="text-[9px] text-slate-500 mt-0.5">AI Engine Integration</div>
              </div>
              <div className="bg-slate-900/40 border border-slate-850 p-5 rounded-xl flex flex-col items-center justify-center text-center">
                <div className="text-3xl mb-1">🐳</div>
                <div className="font-bold text-xs text-slate-200">Docker</div>
                <div className="text-[9px] text-slate-500 mt-0.5">Orchestration</div>
              </div>
              <div className="bg-slate-900/40 border border-slate-850 p-5 rounded-xl flex flex-col items-center justify-center text-center">
                <div className="text-3xl mb-1">🔎</div>
                <div className="font-bold text-xs text-slate-200">ChromaDB</div>
                <div className="text-[9px] text-slate-500 mt-0.5">Vector Database (RAG)</div>
              </div>
              <div className="bg-slate-900/40 border border-slate-850 p-5 rounded-xl flex flex-col items-center justify-center text-center">
                <div className="text-3xl mb-1">🐙</div>
                <div className="font-bold text-xs text-slate-200">GitHub REST API</div>
                <div className="text-[9px] text-slate-500 mt-0.5">Webhook Integration</div>
              </div>
            </div>
          </section>
        </main>
      )}

      {/* PAGE 2: SHOWCASE (DETAILS, ARCHITECTURE, ABOUT PAGE) */}
      {currentPage === 'showcase' && (
        <main className="relative z-10 max-w-4xl mx-auto px-6 py-12 flex flex-col gap-20">
          {/* TEAM / ABOUT SECTION */}
          <section className="bg-slate-900/30 border border-purple-500/10 p-8 rounded-3xl relative overflow-hidden backdrop-blur">
            <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-2xl"></div>
            <div className="text-[10px] font-bold text-purple-400 uppercase tracking-widest mb-3">Maintainer Team</div>
            <h2 className="text-4xl font-extrabold text-white mb-2">Heaven Hill</h2>
            <div className="h-0.5 w-12 bg-purple-500 mb-6"></div>
            
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="font-extrabold text-lg text-slate-200">Hemant Dhaker</h3>
                <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mt-1">
                  Full Stack & AI Engineer / Automation Backend Engineer
                </p>
                <div className="flex flex-wrap gap-4 mt-3">
                  <a 
                    href="https://github.com/HemantDhaker12/" 
                    target="_blank" 
                    rel="noreferrer" 
                    className="text-xs text-purple-400 hover:text-purple-300 font-bold transition-all flex items-center gap-1.5"
                  >
                    🐙 GitHub
                  </a>
                  <a 
                    href="https://www.linkedin.com/in/hemant-dhaker-a95044292/" 
                    target="_blank" 
                    rel="noreferrer" 
                    className="text-xs text-purple-400 hover:text-purple-300 font-bold transition-all flex items-center gap-1.5"
                  >
                    💼 LinkedIn
                  </a>
                  <a 
                    href="https://x.com/Hemant10191" 
                    target="_blank" 
                    rel="noreferrer" 
                    className="text-xs text-purple-400 hover:text-purple-300 font-bold transition-all flex items-center gap-1.5"
                  >
                    🐦 Twitter / X
                  </a>
                </div>
              </div>
              <span className="text-slate-600 text-xs">Based in India • 2026</span>
            </div>
          </section>

          {/* PROBLEM STATEMENT */}
          <section>
            <h2 className="text-2xl font-bold text-white mb-4 uppercase tracking-wider">The Problem Statement</h2>
            <div className="h-0.5 w-12 bg-purple-500 mb-6"></div>
            <p className="text-sm text-slate-400 leading-relaxed mb-6">
              Open-source software forms the digital foundation of modern tech stacks. However, repository maintenance is exhausting. Maintaining a project requires review hours spent triaging tickets, labeling issues, scanning for duplicates, checking test coverage, and responding to onboarding questions.
            </p>
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs font-semibold text-slate-300">
              <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl flex items-center gap-2.5">❌ Triaging issues manually</div>
              <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl flex items-center gap-2.5">❌ Finding duplicate tickets</div>
              <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl flex items-center gap-2.5">❌ Answering repetitive FAQs</div>
              <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl flex items-center gap-2.5">❌ Scanning pull request coverage</div>
              <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl flex items-center gap-2.5">❌ Manually routing label tags</div>
            </div>
          </section>

          {/* DETAILED ARCHITECTURE DIAGRAM */}
          <section>
            <h2 className="text-2xl font-bold text-white mb-4 uppercase tracking-wider">Architecture Flowchart</h2>
            <div className="h-0.5 w-12 bg-purple-500 mb-8"></div>
            
            {/* Visual Step flowchart vertical block */}
            <div className="flex flex-col gap-4 relative pl-6 border-l border-slate-900">
              {/* Step 1 */}
              <div className="relative">
                <span className="absolute -left-[30px] top-1 h-3 w-3 bg-purple-500 rounded-full"></span>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl">
                  <div className="font-extrabold text-xs text-slate-200 mb-1">1. GitHub Webhook Trigger</div>
                  <p className="text-[10px] text-slate-400">GitHub sends a secure HMAC-SHA256 signed event payload representing issue/comment activity.</p>
                </div>
              </div>
              {/* Step 2 */}
              <div className="relative">
                <span className="absolute -left-[30px] top-1 h-3 w-3 bg-purple-500 rounded-full"></span>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl">
                  <div className="font-extrabold text-xs text-slate-200 mb-1">2. FastAPI Verification</div>
                  <p className="text-[10px] text-slate-400">The FastAPI endpoint validates HMAC signatures, inserts the event record to PostgreSQL, enqueues the Celery worker task, and responds HTTP 202 accepted in &lt;10ms.</p>
                </div>
              </div>
              {/* Step 3 */}
              <div className="relative">
                <span className="absolute -left-[30px] top-1 h-3 w-3 bg-purple-500 rounded-full"></span>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl">
                  <div className="font-extrabold text-xs text-slate-200 mb-1">3. Redis Queue Isolation</div>
                  <p className="text-[10px] text-slate-400">The Redis broker buffers task coordinates to isolate web server throughput from AI model compute queues.</p>
                </div>
              </div>
              {/* Step 4 */}
              <div className="relative">
                <span className="absolute -left-[30px] top-1 h-3 w-3 bg-purple-500 rounded-full"></span>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl">
                  <div className="font-extrabold text-xs text-slate-200 mb-1">4. Celery Worker Execution</div>
                  <p className="text-[10px] text-slate-400">Background tasks invoke AI engines asynchronously, reading and caching settings dynamically.</p>
                </div>
              </div>
              {/* Step 5 */}
              <div className="relative">
                <span className="absolute -left-[30px] top-1 h-3 w-3 bg-purple-500 rounded-full"></span>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl">
                  <div className="font-extrabold text-xs text-slate-200 mb-1">5. Groq AI + Vector Store Reasoning</div>
                  <p className="text-[10px] text-slate-400">ChromaDB searches document vectors, and Groq-hosted Llama-3.3 LLM categorizes descriptions and templates missing details.</p>
                </div>
              </div>
              {/* Step 6 */}
              <div className="relative">
                <span className="absolute -left-[30px] top-1 h-3 w-3 bg-purple-500 rounded-full"></span>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl">
                  <div className="font-extrabold text-xs text-slate-200 mb-1">6. GitHub Actions / REST API Output</div>
                  <p className="text-[10px] text-slate-400">PRobot posts a custom markdown triage checklist or updates labels dynamically on the repository.</p>
                </div>
              </div>
            </div>
          </section>

          {/* FUTURE SCOPE */}
          <section>
            <h2 className="text-2xl font-bold text-white mb-4 uppercase tracking-wider">Future Scope Roadmap</h2>
            <div className="h-0.5 w-12 bg-purple-500 mb-8"></div>
            
            <div className="grid sm:grid-cols-2 gap-6">
              {/* Card 1 */}
              <div className="bg-slate-900/30 border border-slate-850 p-5 rounded-2xl">
                <div className="font-bold text-sm text-slate-200 mb-1">Multi-Repository Support</div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Support thousands of repositories simultaneously with secure environment context switching.
                </p>
              </div>
              {/* Card 2 */}
              <div className="bg-slate-900/30 border border-slate-850 p-5 rounded-2xl">
                <div className="font-bold text-sm text-slate-200 mb-1">Maintainer Analytics</div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Visualize issue categories, resolution duration, label counts, and contributor statistics on custom dashboard charts.
                </p>
              </div>
              {/* Card 3 */}
              <div className="bg-slate-900/30 border border-slate-850 p-5 rounded-2xl">
                <div className="font-bold text-sm text-slate-200 mb-1">Slack/Discord Integration</div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Send live event telemetry and critical triage notifications directly to team communication portals.
                </p>
              </div>
              {/* Card 4 */}
              <div className="bg-slate-900/30 border border-slate-850 p-5 rounded-2xl">
                <div className="font-bold text-sm text-slate-200 mb-1">AI Release Notes</div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Analyze pull request descriptions and code changes to build categorized changelog summaries automatically upon tag releases.
                </p>
              </div>
              {/* Card 5 */}
              <div className="bg-slate-900/30 border border-slate-850 p-5 rounded-2xl">
                <div className="font-bold text-sm text-slate-200 mb-1">Contributor Onboarding</div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Provide step-by-step setup guides to first-time contributors based on repository setup documentation.
                </p>
              </div>
              {/* Card 6 */}
              <div className="bg-slate-900/30 border border-slate-850 p-5 rounded-2xl">
                <div className="font-bold text-sm text-slate-200 mb-1">Autonomous Issue Resolution</div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Review code logs, suggest patch files, and generate pull requests to fix basic bugs autonomously.
                </p>
              </div>
            </div>
          </section>

          {/* FAQ SECTION (Accordion) */}
          <section>
            <h2 className="text-2xl font-bold text-white mb-4 uppercase tracking-wider">Frequently Asked Questions</h2>
            <div className="h-0.5 w-12 bg-purple-500 mb-8"></div>
            
            <div className="flex flex-col gap-4">
              {/* FAQ 1 */}
              <div className="bg-slate-900 border border-slate-850 rounded-xl overflow-hidden">
                <button
                  onClick={() => toggleFaq(1)}
                  className="w-full px-6 py-4 text-left font-bold text-xs text-slate-200 hover:bg-slate-850 flex justify-between items-center transition-all"
                >
                  <span>What problem does PRobot solve?</span>
                  <span>{expandedFaq === 1 ? '−' : '+'}</span>
                </button>
                {expandedFaq === 1 && (
                  <div className="px-6 pb-4 pt-1 text-xs text-slate-400 leading-relaxed border-t border-slate-850 bg-slate-950/40">
                    PRobot automates the heavy workload associated with triaging incoming issues, finding duplicate tickets, routing labels, and guiding contributors, saving maintainers hundreds of manual hours.
                  </div>
                )}
              </div>

              {/* FAQ 2 */}
              <div className="bg-slate-900 border border-slate-850 rounded-xl overflow-hidden">
                <button
                  onClick={() => toggleFaq(2)}
                  className="w-full px-6 py-4 text-left font-bold text-xs text-slate-200 hover:bg-slate-850 flex justify-between items-center transition-all"
                >
                  <span>Does PRobot replace human maintainers?</span>
                  <span>{expandedFaq === 2 ? '−' : '+'}</span>
                </button>
                {expandedFaq === 2 && (
                  <div className="px-6 pb-4 pt-1 text-xs text-slate-400 leading-relaxed border-t border-slate-850 bg-slate-950/40">
                    No. PRobot acts as an automated co-pilot. It handles the repetitive initial triage checks and gathers information so that maintainers have complete data when they inspect the issues.
                  </div>
                )}
              </div>

              {/* FAQ 3 */}
              <div className="bg-slate-900 border border-slate-850 rounded-xl overflow-hidden">
                <button
                  onClick={() => toggleFaq(3)}
                  className="w-full px-6 py-4 text-left font-bold text-xs text-slate-200 hover:bg-slate-850 flex justify-between items-center transition-all"
                >
                  <span>How does duplicate detection work?</span>
                  <span>{expandedFaq === 3 ? '−' : '+'}</span>
                </button>
                {expandedFaq === 3 && (
                  <div className="px-6 pb-4 pt-1 text-xs text-slate-400 leading-relaxed border-t border-slate-850 bg-slate-950/40">
                    It generates text embeddings using FastEmbed and indexes them in a ChromaDB database. When a new issue arrives, it performs a vector similarity query to search for similar existing descriptions.
                  </div>
                )}
              </div>

              {/* FAQ 4 */}
              <div className="bg-slate-900 border border-slate-850 rounded-xl overflow-hidden">
                <button
                  onClick={() => toggleFaq(4)}
                  className="w-full px-6 py-4 text-left font-bold text-xs text-slate-200 hover:bg-slate-850 flex justify-between items-center transition-all"
                >
                  <span>Is repository data stored securely?</span>
                  <span>{expandedFaq === 4 ? '−' : '+'}</span>
                </button>
                {expandedFaq === 4 && (
                  <div className="px-6 pb-4 pt-1 text-xs text-slate-400 leading-relaxed border-t border-slate-850 bg-slate-950/40">
                    Yes. All database credentials, secrets, and tokens are loaded strictly via Docker .env files at runtime. Triage runs in private containers and only outputs comments on your repository.
                  </div>
                )}
              </div>

              {/* FAQ 5 */}
              <div className="bg-slate-900 border border-slate-850 rounded-xl overflow-hidden">
                <button
                  onClick={() => toggleFaq(5)}
                  className="w-full px-6 py-4 text-left font-bold text-xs text-slate-200 hover:bg-slate-850 flex justify-between items-center transition-all"
                >
                  <span>Can it work with private repositories?</span>
                  <span>{expandedFaq === 5 ? '−' : '+'}</span>
                </button>
                {expandedFaq === 5 && (
                  <div className="px-6 pb-4 pt-1 text-xs text-slate-400 leading-relaxed border-t border-slate-850 bg-slate-950/40">
                    Yes, it can run on private repositories by adjusting scopes on the Personal Access Token (PAT) inside .env to allow reading and commenting on private repositories.
                  </div>
                )}
              </div>

              {/* FAQ 6 */}
              <div className="bg-slate-900 border border-slate-850 rounded-xl overflow-hidden">
                <button
                  onClick={() => toggleFaq(6)}
                  className="w-full px-6 py-4 text-left font-bold text-xs text-slate-200 hover:bg-slate-850 flex justify-between items-center transition-all"
                >
                  <span>Which AI model is used?</span>
                  <span>{expandedFaq === 6 ? '−' : '+'}</span>
                </button>
                {expandedFaq === 6 && (
                  <div className="px-6 pb-4 pt-1 text-xs text-slate-400 leading-relaxed border-t border-slate-850 bg-slate-950/40">
                    We use Groq's high-speed API running Llama-3.3-70b-versatile, which provides lightning-fast reasoning and structured JSON output for triage analysis.
                  </div>
                )}
              </div>
            </div>
          </section>
        </main>
      )}

      {/* FOOTER */}
      <footer className="max-w-6xl mx-auto px-6 pt-16 border-t border-slate-900 text-center relative z-10">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <span>🌌</span>
            <span className="font-extrabold text-slate-500">HEAVEN HILL • PRobot</span>
          </div>
          <div>
            Automation & Engineering presentation. Built with React and Tailwind CSS.
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
