'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  getCases, createCase, submitCase, getCaseEvaluations, getCaseReport,
  getDashboardStats, getAgents, submitFeedback, getDomains, getAuditLogs,
  cloneCase, overrideVerdict
} from '@/lib/api';

// ─── Icon Components ───────────────────────────────────
const Icons = {
  Dashboard: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>
    </svg>
  ),
  Cases: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/>
    </svg>
  ),
  NewCase: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
    </svg>
  ),
  Agents: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  ),
  Audit: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    </svg>
  ),
  Brain: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a8 8 0 0 0-8 8c0 3.4 2 6 5 7.5V20h6v-2.5c3-1.5 5-4.1 5-7.5a8 8 0 0 0-8-8z"/><line x1="12" y1="20" x2="12" y2="22"/>
    </svg>
  ),
  Check: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
  ),
  X: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
  ),
  TrendUp: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
  ),
  Star: () => (
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
  ),
  Copy: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
  ),
};

// ─── Verdict Badge ─────────────────────────────────────
function VerdictBadge({ verdict }) {
  const cls = `nx-badge nx-badge-${verdict || 'draft'}`;
  return <span className={cls}>{verdict || 'N/A'}</span>;
}

// ─── Status Badge ──────────────────────────────────────
function StatusBadge({ status }) {
  const cls = `nx-badge nx-badge-${status || 'draft'}`;
  return <span className={cls}>{(status || 'draft').replace('_', ' ')}</span>;
}

// ─── Confidence Ring ───────────────────────────────────
function ConfidenceRing({ value, size = 64 }) {
  const pct = Math.round(value);
  const color = pct >= 75 ? '#00E676' : pct >= 50 ? '#FFD600' : '#FF5252';
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div style={{ width: size, height: size, position: 'relative' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="4" />
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <div style={{
        position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontWeight: 800, fontSize: size * 0.22, color
      }}>
        {pct}%
      </div>
    </div>
  );
}

// ─── Dashboard Page ────────────────────────────────────
function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats().then(setStats).catch(() => setStats(null)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="nx-loading"><div className="nx-spinner" /></div>;

  const s = stats || { total_cases: 0, total_verdicts: 0, total_feedback: 0, average_confidence: 0, average_consensus: 0, human_overrides: 0, average_rating: 0, cases_by_status: {}, cases_by_domain: {}, agent_performance: [] };

  return (
    <div className="animate-fade-in">
      <div className="nx-page-header">
        <h2>Decision Intelligence Dashboard</h2>
        <p>Real-time overview of your jury evaluation platform</p>
      </div>

      <div className="nx-stat-grid stagger">
        <div className="nx-stat-card">
          <div className="stat-icon" style={{ background: 'rgba(108, 92, 231, 0.2)' }}>
            <Icons.Cases />
          </div>
          <div className="stat-value" style={{ color: '#A29BFE' }}>{s.total_cases}</div>
          <div className="stat-label">Total Cases</div>
        </div>
        <div className="nx-stat-card">
          <div className="stat-icon" style={{ background: 'rgba(0, 230, 118, 0.2)' }}>
            <Icons.Check />
          </div>
          <div className="stat-value" style={{ color: '#00E676' }}>{s.total_verdicts}</div>
          <div className="stat-label">Verdicts Delivered</div>
        </div>
        <div className="nx-stat-card">
          <div className="stat-icon" style={{ background: 'rgba(0, 210, 255, 0.2)' }}>
            <Icons.TrendUp />
          </div>
          <div className="stat-value" style={{ color: '#00D2FF' }}>{s.average_confidence?.toFixed(1) || 0}%</div>
          <div className="stat-label">Avg Confidence</div>
        </div>
        <div className="nx-stat-card">
          <div className="stat-icon" style={{ background: 'rgba(255, 214, 0, 0.2)' }}>
            <Icons.Star />
          </div>
          <div className="stat-value" style={{ color: '#FFD600' }}>{s.average_rating?.toFixed(1) || 0}</div>
          <div className="stat-label">Avg Feedback Rating</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="nx-card">
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '20px' }}>Cases by Domain</h3>
          {Object.keys(s.cases_by_domain).length === 0 ? (
            <p style={{ color: 'var(--nx-text-muted)', fontSize: '14px' }}>No cases yet. Create your first case to get started.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {Object.entries(s.cases_by_domain).map(([domain, count]) => (
                <div key={domain} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ width: '100px', fontSize: '13px', fontWeight: 600, textTransform: 'capitalize', color: 'var(--nx-text-secondary)' }}>{domain}</span>
                  <div style={{ flex: 1, height: '8px', background: 'var(--nx-bg-primary)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${(count / s.total_cases) * 100}%`, height: '100%', background: 'var(--nx-gradient-primary)', borderRadius: '4px', transition: 'width 0.5s ease' }} />
                  </div>
                  <span style={{ fontSize: '14px', fontWeight: 700, minWidth: '24px' }}>{count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="nx-card">
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '20px' }}>Agent Performance</h3>
          {s.agent_performance.length === 0 ? (
            <p style={{ color: 'var(--nx-text-muted)', fontSize: '14px' }}>No agent evaluations yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {s.agent_performance.map((agent) => (
                <div key={agent.agent_name} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ width: '130px', fontSize: '13px', fontWeight: 600, color: 'var(--nx-text-secondary)' }}>{agent.agent_name}</span>
                  <ConfidenceRing value={agent.average_confidence} size={40} />
                  <span style={{ fontSize: '12px', color: 'var(--nx-text-muted)' }}>{agent.total_evaluations} evals</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Cases List Page ───────────────────────────────────
function CasesPage({ onViewCase }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadCases = useCallback(() => {
    setLoading(true);
    getCases().then(setCases).catch(() => setCases([])).finally(() => setLoading(false));
  }, []);

  useEffect(() => { loadCases(); }, [loadCases]);

  if (loading) return <div className="nx-loading"><div className="nx-spinner" /></div>;

  return (
    <div className="animate-fade-in">
      <div className="nx-page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Case Manager</h2>
          <p>View, manage, and track all decision cases</p>
        </div>
      </div>

      {cases.length === 0 ? (
        <div className="nx-empty-state">
          <Icons.Cases />
          <h3 style={{ marginBottom: '8px', color: 'var(--nx-text-secondary)' }}>No Cases Yet</h3>
          <p>Create your first decision case to get started with jury evaluation.</p>
        </div>
      ) : (
        <div className="nx-card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="nx-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Domain</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody className="stagger">
              {cases.map((c) => (
                <tr key={c.id} style={{ cursor: 'pointer' }} onClick={() => onViewCase(c.id)}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{c.title}</div>
                    <div style={{ fontSize: '12px', color: 'var(--nx-text-muted)', marginTop: '2px' }}>
                      {c.description?.substring(0, 80)}...
                    </div>
                  </td>
                  <td><span style={{ textTransform: 'capitalize', fontWeight: 500 }}>{c.domain}</span></td>
                  <td><StatusBadge status={c.status} /></td>
                  <td style={{ color: 'var(--nx-text-muted)', fontSize: '13px' }}>
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <button className="nx-btn nx-btn-ghost nx-btn-sm" onClick={(e) => { e.stopPropagation(); onViewCase(c.id); }}>
                      View →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── New Case Page ─────────────────────────────────────
function NewCasePage({ onCaseCreated }) {
  const [form, setForm] = useState({ title: '', description: '', domain: 'business' });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      // Step 1: Create the case
      const created = await createCase(form);
      // Step 2: Submit for evaluation
      const verdict = await submitCase(created.id, { agent_count: 5, aggregation_mode: 'weighted_voting' });
      // Step 3: Get the report
      const report = await getCaseReport(created.id);
      const evaluations = await getCaseEvaluations(created.id);
      setResult({ case: created, verdict, report, evaluations });
      if (onCaseCreated) onCaseCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return <CaseResultView result={result} onBack={() => setResult(null)} />;
  }

  return (
    <div className="animate-fade-in">
      <div className="nx-page-header">
        <h2>Submit New Case</h2>
        <p>Describe your decision scenario for multi-agent jury evaluation</p>
      </div>

      <div className="nx-card" style={{ maxWidth: '800px' }}>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label className="nx-label">Case Title</label>
            <input
              className="nx-input"
              placeholder="e.g., Market Entry Decision for Southeast Asia"
              value={form.title}
              onChange={(e) => setForm({...form, title: e.target.value})}
              required
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label className="nx-label">Domain</label>
            <select
              className="nx-input nx-select"
              value={form.domain}
              onChange={(e) => setForm({...form, domain: e.target.value})}
            >
              <option value="legal">⚖️ Legal & Judicial</option>
              <option value="hr">👥 Human Resources</option>
              <option value="business">📊 Business Strategy</option>
              <option value="healthcare">🏥 Healthcare</option>
              <option value="policy">🏛️ Governance & Policy</option>
            </select>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label className="nx-label">Case Description</label>
            <textarea
              className="nx-input nx-textarea"
              placeholder="Describe the decision scenario in detail. Include all relevant facts, constraints, stakeholders, and desired outcomes. The more detail you provide, the better the jury evaluation will be..."
              style={{ minHeight: '200px' }}
              value={form.description}
              onChange={(e) => setForm({...form, description: e.target.value})}
              required
              minLength={20}
            />
          </div>

          {error && (
            <div style={{ background: 'rgba(255,82,82,0.1)', border: '1px solid rgba(255,82,82,0.2)', borderRadius: '10px', padding: '12px 16px', marginBottom: '20px', color: '#FF5252', fontSize: '14px' }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', gap: '12px' }}>
            <button type="submit" className="nx-btn nx-btn-primary" disabled={submitting || !form.title || !form.description}>
              {submitting ? (
                <>
                  <div className="nx-spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />
                  Evaluating with Jury...
                </>
              ) : (
                <>
                  <Icons.Brain />
                  Submit for Jury Evaluation
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Case Result View ──────────────────────────────────
function CaseResultView({ result, onBack }) {
  const { verdict, report, evaluations } = result || {};
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(0);
  const [feedbackSent, setFeedbackSent] = useState(false);

  const handleFeedback = async () => {
    if (feedbackRating > 0 && result?.case?.id) {
      await submitFeedback({ case_id: result.case.id, outcome_rating: feedbackRating }).catch(() => {});
      setFeedbackSent(true);
    }
  };

  if (!verdict) return null;

  const verdictColors = { approve: '#00E676', reject: '#FF5252', escalate: '#FF9100' };

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '28px' }}>
        <button className="nx-btn nx-btn-ghost" onClick={onBack}>← Back</button>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 800 }}>{result.case?.title}</h2>
          <p style={{ color: 'var(--nx-text-muted)', fontSize: '13px' }}>{result.case?.domain?.toUpperCase()} • Case ID: {result.case?.id?.substring(0, 8)}...</p>
        </div>
      </div>

      {/* Verdict Hero Card */}
      <div className="nx-card" style={{ marginBottom: '24px', background: `linear-gradient(135deg, ${verdictColors[verdict.final_verdict]}15, transparent)`, borderColor: `${verdictColors[verdict.final_verdict]}30` }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px' }}>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--nx-text-muted)', marginBottom: '8px' }}>Final Verdict</div>
            <div style={{ fontSize: '36px', fontWeight: 900, color: verdictColors[verdict.final_verdict], textTransform: 'uppercase', letterSpacing: '-1px' }}>
              {verdict.final_verdict}
            </div>
            <div style={{ marginTop: '8px', fontSize: '14px', color: 'var(--nx-text-secondary)' }}>
              {verdict.agent_count} agents evaluated • {verdict.aggregation_mode.replace(/_/g, ' ')}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '32px', alignItems: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <ConfidenceRing value={verdict.composite_confidence} size={80} />
              <div style={{ fontSize: '11px', color: 'var(--nx-text-muted)', marginTop: '4px' }}>Confidence</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <ConfidenceRing value={verdict.consensus_level * 100} size={80} />
              <div style={{ fontSize: '11px', color: 'var(--nx-text-muted)', marginTop: '4px' }}>Consensus</div>
            </div>
          </div>
        </div>

        {verdict.requires_human_review === 1 && (
          <div style={{ marginTop: '16px', background: 'rgba(255,145,0,0.1)', border: '1px solid rgba(255,145,0,0.2)', borderRadius: '10px', padding: '12px 16px', fontSize: '13px', color: '#FF9100' }}>
            ⚠️ Human review required — Agent consensus is below 60%
          </div>
        )}
      </div>

      {/* Agent Evaluations */}
      <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px' }}>Juror Agent Breakdown</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }} className="stagger">
        {evaluations?.map((ev, i) => (
          <div key={i} className="nx-agent-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '15px' }}>{ev.agent_name}</div>
                <div style={{ fontSize: '11px', color: 'var(--nx-text-muted)', marginTop: '2px' }}>{ev.reasoning_chain?.focus_area}</div>
              </div>
              <VerdictBadge verdict={ev.verdict} />
            </div>
            <div style={{ display: 'flex', gap: '16px', marginBottom: '12px' }}>
              <ConfidenceRing value={ev.confidence_score} size={48} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '12px', color: 'var(--nx-text-muted)' }}>Weight: {ev.weight_at_evaluation?.toFixed(2)}</div>
                <div style={{ fontSize: '12px', color: 'var(--nx-text-muted)' }}>Contribution: {ev.weight_contribution?.toFixed(3)}</div>
              </div>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--nx-text-secondary)', lineHeight: '1.5', borderTop: '1px solid var(--nx-border)', paddingTop: '12px' }}>
              {ev.reasoning_chain?.verdict_rationale}
            </div>
          </div>
        ))}
      </div>

      {/* Decision Drivers */}
      {verdict.decision_drivers?.length > 0 && (
        <div className="nx-card" style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Key Decision Drivers</h3>
          {verdict.decision_drivers.map((d, i) => (
            <div key={i} style={{ display: 'flex', gap: '12px', marginBottom: '16px', paddingBottom: '16px', borderBottom: i < verdict.decision_drivers.length - 1 ? '1px solid var(--nx-border)' : 'none' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: 'rgba(108,92,231,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 800, color: 'var(--nx-primary-light)', flexShrink: 0 }}>
                {i + 1}
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: '14px' }}>{d.agent} <VerdictBadge verdict={d.verdict} /></div>
                <div style={{ fontSize: '13px', color: 'var(--nx-text-secondary)', marginTop: '4px' }}>{d.reasoning}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Report Summary */}
      {report?.recommendation_text && (
        <div className="nx-card" style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px' }}>📋 Recommendation</h3>
          <p style={{ color: 'var(--nx-text-secondary)', lineHeight: '1.7', fontSize: '14px' }}>
            {report.recommendation_text}
          </p>
        </div>
      )}

      {/* Feedback Section */}
      <div className="nx-card">
        <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px' }}>💡 Submit Outcome Feedback</h3>
        <p style={{ color: 'var(--nx-text-muted)', fontSize: '13px', marginBottom: '16px' }}>
          Help the RL engine learn — rate the quality of this verdict after implementing the decision.
        </p>
        {feedbackSent ? (
          <div style={{ color: '#00E676', fontWeight: 600 }}>✓ Feedback submitted! Agent weights will be updated.</div>
        ) : (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {[1, 2, 3, 4, 5].map((star) => (
              <button key={star} onClick={() => setFeedbackRating(star)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '28px', color: star <= feedbackRating ? '#FFD600' : 'var(--nx-text-muted)', transition: 'all 0.2s' }}>
                ★
              </button>
            ))}
            {feedbackRating > 0 && (
              <button className="nx-btn nx-btn-primary nx-btn-sm" onClick={handleFeedback} style={{ marginLeft: '12px' }}>
                Submit Rating
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Case Detail Page ──────────────────────────────────
function CaseDetailPage({ caseId, onBack }) {
  const [caseData, setCaseData] = useState(null);
  const [evaluations, setEvaluations] = useState(null);
  const [report, setReport] = useState(null);
  const [verdict, setVerdict] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getCases().then(cases => cases.find(c => c.id === caseId)),
      getCaseEvaluations(caseId).catch(() => null),
      getCaseReport(caseId).catch(() => null),
    ]).then(([c, evals, rep]) => {
      setCaseData(c);
      setEvaluations(evals);
      setReport(rep);
      if (c?.status === 'verdict_ready' || c?.status === 'closed') {
        import('@/lib/api').then(api => api.getVerdict(caseId).then(setVerdict).catch(() => null));
      }
    }).finally(() => setLoading(false));
  }, [caseId]);

  if (loading) return <div className="nx-loading"><div className="nx-spinner" /></div>;
  if (!caseData) return <div className="nx-empty-state"><p>Case not found</p><button className="nx-btn nx-btn-secondary" onClick={onBack}>← Back</button></div>;

  if (verdict && evaluations) {
    return <CaseResultView result={{ case: caseData, verdict, evaluations, report }} onBack={onBack} />;
  }

  return (
    <div className="animate-fade-in">
      <button className="nx-btn nx-btn-ghost" onClick={onBack} style={{ marginBottom: '20px' }}>← Back to Cases</button>
      <div className="nx-card">
        <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: '8px' }}>{caseData.title}</h2>
        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
          <StatusBadge status={caseData.status} />
          <span style={{ color: 'var(--nx-text-muted)', fontSize: '13px' }}>{caseData.domain?.toUpperCase()}</span>
        </div>
        <p style={{ color: 'var(--nx-text-secondary)', lineHeight: '1.7' }}>{caseData.description}</p>
        {caseData.status === 'draft' && (
          <button className="nx-btn nx-btn-primary" style={{ marginTop: '20px' }}
            onClick={async () => {
              const v = await submitCase(caseId);
              setVerdict(v);
              const evals = await getCaseEvaluations(caseId);
              setEvaluations(evals);
              const rep = await getCaseReport(caseId);
              setReport(rep);
              setCaseData(prev => ({ ...prev, status: 'verdict_ready' }));
            }}>
            <Icons.Brain /> Submit for Evaluation
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Agents Page ───────────────────────────────────────
function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAgents().then(setAgents).catch(() => setAgents([])).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="nx-loading"><div className="nx-spinner" /></div>;

  const archetypeColors = {
    risk_analyst: '#FF5252',
    growth_advocate: '#00E676',
    financial_modeler: '#00D2FF',
    ethical_reviewer: '#FFD600',
    devils_advocate: '#FF9100',
  };

  return (
    <div className="animate-fade-in">
      <div className="nx-page-header">
        <h2>Juror Agent Framework</h2>
        <p>5 specialized AI agents that independently evaluate every case</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }} className="stagger">
        {agents.map((agent) => {
          const color = archetypeColors[agent.archetype] || '#A29BFE';
          return (
            <div key={agent.archetype} className="nx-agent-card" style={{ borderColor: `${color}25` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: `${color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icons.Agents />
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '16px' }}>{agent.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--nx-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{agent.archetype.replace(/_/g, ' ')}</div>
                </div>
              </div>
              <p style={{ color: 'var(--nx-text-secondary)', fontSize: '13px', lineHeight: '1.6', marginBottom: '16px' }}>
                {agent.description}
              </p>
              <div style={{ borderTop: '1px solid var(--nx-border)', paddingTop: '12px' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color, marginBottom: '8px' }}>Key Questions</div>
                {agent.reasoning_priors?.key_questions?.map((q, i) => (
                  <div key={i} style={{ fontSize: '12px', color: 'var(--nx-text-muted)', padding: '3px 0', display: 'flex', gap: '6px' }}>
                    <span style={{ color }}>•</span> {q}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Audit Log Page ────────────────────────────────────
function AuditPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAuditLogs({ limit: '100' }).then(setLogs).catch(() => setLogs([])).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="nx-loading"><div className="nx-spinner" /></div>;

  return (
    <div className="animate-fade-in">
      <div className="nx-page-header">
        <h2>Audit Trail</h2>
        <p>Tamper-evident, append-only log of all system actions</p>
      </div>

      {logs.length === 0 ? (
        <div className="nx-empty-state">
          <Icons.Audit />
          <h3 style={{ color: 'var(--nx-text-secondary)' }}>No Audit Entries Yet</h3>
          <p>Actions will be logged here as you use the platform.</p>
        </div>
      ) : (
        <div className="nx-card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="nx-table">
            <thead>
              <tr>
                <th>Action</th>
                <th>Entity</th>
                <th>Details</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{log.action?.replace(/_/g, ' ')}</td>
                  <td>
                    <span style={{ textTransform: 'capitalize' }}>{log.entity_type}</span>
                    {log.entity_id && <span style={{ color: 'var(--nx-text-muted)', fontSize: '11px', marginLeft: '4px' }}>#{log.entity_id?.substring(0, 8)}</span>}
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--nx-text-muted)', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {JSON.stringify(log.details)?.substring(0, 80)}
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--nx-text-muted)' }}>
                    {log.created_at ? new Date(log.created_at).toLocaleString() : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Domains Page ──────────────────────────────────────
function DomainsPage() {
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDomains().then(setDomains).catch(() => setDomains([])).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="nx-loading"><div className="nx-spinner" /></div>;

  const domainIcons = { legal: '⚖️', hr: '👥', business: '📊', healthcare: '🏥', policy: '🏛️' };

  return (
    <div className="animate-fade-in">
      <div className="nx-page-header">
        <h2>Domain Profiles</h2>
        <p>Industry-specific configurations for agent personas, reward functions, and aggregation modes</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '20px' }} className="stagger">
        {domains.map((d) => (
          <div key={d.id} className="nx-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <span style={{ fontSize: '28px' }}>{domainIcons[d.domain_key] || '🔧'}</span>
              <div>
                <div style={{ fontWeight: 700, fontSize: '16px' }}>{d.name}</div>
                <div style={{ fontSize: '11px', color: 'var(--nx-text-muted)', textTransform: 'uppercase' }}>{d.domain_key}</div>
              </div>
            </div>
            <p style={{ color: 'var(--nx-text-secondary)', fontSize: '13px', lineHeight: '1.6', marginBottom: '16px' }}>{d.description}</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '13px' }}>
              <div style={{ color: 'var(--nx-text-muted)' }}>Agents: <span style={{ color: 'var(--nx-text-primary)', fontWeight: 600 }}>{d.agent_count}</span></div>
              <div style={{ color: 'var(--nx-text-muted)' }}>Mode: <span style={{ color: 'var(--nx-text-primary)', fontWeight: 600 }}>{d.aggregation_mode.replace(/_/g, ' ')}</span></div>
              <div style={{ color: 'var(--nx-text-muted)' }}>Human Review: <span style={{ color: d.requires_human_review ? '#FF9100' : '#00E676', fontWeight: 600 }}>{d.requires_human_review ? 'Required' : 'Optional'}</span></div>
              <div style={{ color: 'var(--nx-text-muted)' }}>Max Weight: <span style={{ color: 'var(--nx-text-primary)', fontWeight: 600 }}>{(d.max_weight_per_agent * 100).toFixed(0)}%</span></div>
            </div>
            {d.disclaimer_text && (
              <div style={{ marginTop: '12px', padding: '10px 12px', background: 'rgba(255,145,0,0.08)', borderRadius: '8px', fontSize: '12px', color: '#FF9100', lineHeight: '1.5' }}>
                ⚠️ {d.disclaimer_text}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}


// ─── Main App Shell ────────────────────────────────────
export default function Home() {
  const [activePage, setActivePage] = useState('dashboard');
  const [selectedCaseId, setSelectedCaseId] = useState(null);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Icons.Dashboard },
    { id: 'cases', label: 'Cases', icon: Icons.Cases },
    { id: 'new-case', label: 'New Case', icon: Icons.NewCase },
    { id: 'agents', label: 'Juror Agents', icon: Icons.Agents },
    { id: 'domains', label: 'Domains', icon: Icons.Brain },
    { id: 'audit', label: 'Audit Trail', icon: Icons.Audit },
  ];

  const handleViewCase = (caseId) => {
    setSelectedCaseId(caseId);
    setActivePage('case-detail');
  };

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <DashboardPage />;
      case 'cases':
        return <CasesPage onViewCase={handleViewCase} />;
      case 'new-case':
        return <NewCasePage onCaseCreated={() => setActivePage('cases')} />;
      case 'agents':
        return <AgentsPage />;
      case 'domains':
        return <DomainsPage />;
      case 'audit':
        return <AuditPage />;
      case 'case-detail':
        return <CaseDetailPage caseId={selectedCaseId} onBack={() => setActivePage('cases')} />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="nx-app">
      {/* Sidebar */}
      <aside className="nx-sidebar">
        <div className="nx-logo">
          <h1>NirnayX</h1>
          <p>Decision Intelligence</p>
        </div>
        <nav className="nx-nav">
          {navItems.map((item) => (
            <button key={item.id}
              className={`nx-nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => { setActivePage(item.id); setSelectedCaseId(null); }}
            >
              <item.icon />
              {item.label}
            </button>
          ))}
        </nav>
        <div style={{ padding: '16px 12px', borderTop: '1px solid var(--nx-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--nx-gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '13px' }}>
              DU
            </div>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>Demo User</div>
              <div style={{ fontSize: '11px', color: 'var(--nx-text-muted)' }}>Admin</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="nx-main">
        <div className="nx-content">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}
